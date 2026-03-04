"""Gate evaluation for v0.1 declared gates."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from . import audit_queries
from .contract_validator import ContractValidator
from .ledger_store import DuplicateRecordError, LedgerStore
from .mutation_guard import MutationGuard
from .replay_engine import ReplayEngine


@dataclass
class GateResult:
    gate_id: str
    passed: bool
    details: str


class GateRunner:
    """Runs v0.1 merge/runtime/release gate predicates."""

    def __init__(self, validator: ContractValidator) -> None:
        self._validator = validator

    def run_v01_gates(
        self,
        manifest: dict[str, Any],
        attempts: list[dict[str, Any]],
        precommits: list[dict[str, Any]],
        snapshots: list[dict[str, Any]],
        updates: list[dict[str, Any]],
        events: list[dict[str, Any]],
        telemetry_events: list[dict[str, Any]] | None = None,
        migrations: list[dict[str, Any]] | None = None,
    ) -> list[GateResult]:
        if events is None:
            raise ValueError("events_required_for_gate_evaluation")
        results: list[GateResult] = []
        projection = self._validator.replay_projection(manifest)
        attempts_input = list(attempts)
        precommits_input = list(precommits)
        snapshots_input = list(snapshots)
        updates_input = list(updates)
        telemetry_input = list(telemetry_events or [])
        migrations_input = list(migrations or [])

        canonical_events_ok = True
        canonical_events_details = "event ledger is canonical and typed views are bound by id/hash equivalence"
        attempts_list: list[dict[str, Any]] = attempts_input
        precommits_list: list[dict[str, Any]] = precommits_input
        snapshots_list: list[dict[str, Any]] = snapshots_input
        updates_list: list[dict[str, Any]] = updates_input
        telemetry_events_list: list[dict[str, Any]] = telemetry_input
        migrations_list: list[dict[str, Any]] = migrations_input
        safe_mode_transitions: list[dict[str, Any]] = []
        quarantine_decisions: list[dict[str, Any]] = []
        anchor_audits: list[dict[str, Any]] = []
        canonical_events_ok = canonical_events_ok and audit_queries.event_ledger_integrity_valid(
            events,
            manifest,
        )
        canonical_views = self._typed_views_from_events(events)
        attempts_list = canonical_views["attempts"]
        precommits_list = canonical_views["precommits"]
        snapshots_list = canonical_views["snapshots"]
        updates_list = canonical_views["updates"]
        telemetry_events_list = canonical_views["telemetry_events"]
        migrations_list = canonical_views["migrations"]
        safe_mode_transitions = canonical_views["safe_mode_transitions"]
        quarantine_decisions = canonical_views["quarantine_decisions"]
        anchor_audits = canonical_views["anchor_audits"]
        typed_views_supplied = any(
            [
                bool(attempts_input),
                bool(precommits_input),
                bool(telemetry_input),
                bool(snapshots_input),
                bool(updates_input),
                bool(migrations_input),
            ]
        )
        if typed_views_supplied:
            canonical_events_ok = canonical_events_ok and audit_queries.event_typed_views_consistent(
                events,
                attempts_input,
                precommits_input,
                telemetry_input,
                snapshots_input,
                updates_input,
                migrations_input,
            )

        # Runtime gates
        replay_fields_ok = all(k in manifest for k in projection.keys())
        replay_fields_ok = replay_fields_ok and bool(manifest.get("replay_fingerprint"))
        results.append(
            GateResult(
                gate_id="G-RUN-V01-RPL",
                passed=replay_fields_ok,
                details="replay tuple fields and fingerprint present",
            )
        )

        nomix_ok = True
        for attempt in attempts_list:
            if audit_queries.has_mixed_semantics(attempt, projection):
                nomix_ok = False
            if not audit_queries.residual_provenance_aligned(attempt, projection):
                nomix_ok = False
        for snapshot in snapshots_list:
            if audit_queries.has_mixed_semantics(snapshot, projection):
                nomix_ok = False
        results.append(
            GateResult(
                gate_id="G-RUN-V01-NOMIX",
                passed=canonical_events_ok and nomix_ok,
                details="attempt/snapshot version pointers match replay projection",
            )
        )

        preq_runtime_ok = audit_queries.precommit_bindings_consistent(attempts_list, precommits_list)
        preq_runtime_ok = preq_runtime_ok and audit_queries.telemetry_window_bindings_consistent(
            attempts_list,
            telemetry_events_list,
            precommits_list,
            events=events,
        )
        results.append(
            GateResult(
                gate_id="G-RUN-V01-PREQ",
                passed=canonical_events_ok and preq_runtime_ok,
                details=(
                    "attempts bind to prior precommit artifacts with hash/id/timestamp ordering, "
                    "identity integrity, intended-vs-observed semantic coherence, and telemetry-window integrity"
                ),
            )
        )
        preqseq_runtime_ok = True
        preqseq_runtime_details = (
            "ledger sequence enforces precommit-before-response_submitted-before-attempt_observed"
        )
        if canonical_events_ok:
            preqseq_runtime_ok = audit_queries.precommit_response_sequence_coherent(
                events
            )
        else:
            preqseq_runtime_ok = False
            preqseq_runtime_details = "event ledger integrity invalid for precommit authenticity sequence gate"
        results.append(
            GateResult(
                gate_id="G-RUN-V01-PREQSEQ",
                passed=preqseq_runtime_ok,
                details=preqseq_runtime_details,
            )
        )

        evtbind_runtime_ok = True
        evtbind_runtime_details = (
            "canonical event ledger payloads are equivalent to typed record lists (ids and hashes)"
        )
        evtbind_runtime_ok = canonical_events_ok
        evtbind_runtime_details = canonical_events_details
        results.append(
            GateResult(
                gate_id="G-RUN-V01-EVTBIND",
                passed=evtbind_runtime_ok,
                details=evtbind_runtime_details,
            )
        )

        logatomic_runtime_ok = all(not self._validator.validate_state_update_event(u) for u in updates_list)
        results.append(
            GateResult(
                gate_id="G-RUN-V01-LOGATOMIC",
                passed=canonical_events_ok and logatomic_runtime_ok,
                details="diagnosis updates satisfy atomicity and outcome semantics",
            )
        )

        provref_runtime_ok = audit_queries.provenance_snapshot_ref_integrity(
            attempts_list,
            snapshots_list,
        )
        results.append(
            GateResult(
                gate_id="G-RUN-V01-PROVREF",
                passed=canonical_events_ok and provref_runtime_ok,
                details="attempt provenance snapshot references exist and precede attempts",
            )
        )

        refint_runtime_ok = audit_queries.updates_referentially_integral(attempts_list, updates_list)
        results.append(
            GateResult(
                gate_id="G-RUN-V01-REFINT",
                passed=canonical_events_ok and refint_runtime_ok,
                details="state updates have valid source attempts and partition/eligibility consistency",
            )
        )

        updsnap_runtime_ok = audit_queries.updates_snapshot_ref_integrity(updates_list, snapshots_list)
        results.append(
            GateResult(
                gate_id="G-RUN-V01-UPDSNAPREF",
                passed=canonical_events_ok and updsnap_runtime_ok,
                details="state updates reference known snapshot lineage ids (__genesis__ or committed snapshot ids)",
            )
        )

        gov_runtime_ok = True
        gov_runtime_details = (
            "governance event payload contracts and safe-mode transition sequence are valid "
            "(safe_mode_transition/quarantine_decision/anchor_audit) and state_update "
            "safe_mode_profile_id matches active safe-mode transition profile"
        )
        if canonical_events_ok:
            for transition in safe_mode_transitions:
                gov_runtime_ok = gov_runtime_ok and not self._validator.validate_safe_mode_transition_event(
                    transition, manifest
                )
            for decision in quarantine_decisions:
                gov_runtime_ok = gov_runtime_ok and not self._validator.validate_quarantine_decision_event(
                    decision, manifest
                )
            for audit_event in anchor_audits:
                gov_runtime_ok = gov_runtime_ok and not self._validator.validate_anchor_audit_event(
                    audit_event, manifest
                )
            gov_runtime_ok = gov_runtime_ok and audit_queries.safe_mode_transition_sequence_coherent(
                safe_mode_transitions,
                events=events,
            )
            gov_runtime_ok = gov_runtime_ok and audit_queries.safe_mode_update_profile_bindings_consistent(
                events
            )
        else:
            gov_runtime_ok = False
            gov_runtime_details = "event ledger integrity invalid for governance-event gate"
        results.append(
            GateResult(
                gate_id="G-RUN-V01-GOVEVENTS",
                passed=gov_runtime_ok,
                details=gov_runtime_details,
            )
        )

        replaystate_ok = True
        replay_details = "replay-derived state hash verified against latest snapshot checkpoint"
        evord_ok = True
        evord_details = "event ledger integrity is valid (ids, types, run bindings, payload/header coherence, sequence uniqueness)"
        replay_store = LedgerStore()
        try:
            replay_store.put_manifest(manifest)
            if canonical_events_ok:
                replay_store.events_by_run[manifest["run_id"]] = list(events)
            else:
                evord_ok = False
                evord_details = "event ledger integrity invalid for EVORD"
                replaystate_ok = False
                replay_details = "event ledger integrity invalid for replay state verification"

            if canonical_events_ok:
                replay_result = ReplayEngine(self._validator, MutationGuard()).replay_run(
                    manifest["run_id"], replay_store
                )
                if replay_result.errors:
                    replaystate_ok = False
                    replay_details = "replay errors present"
                elif replay_result.last_verified_snapshot_hash:
                    replaystate_ok = replay_result.final_state_hash == replay_result.last_verified_snapshot_hash
                    if not replaystate_ok:
                        replay_details = "replay final hash mismatches latest snapshot checkpoint hash"
        except DuplicateRecordError:
            replaystate_ok = False
            replay_details = "replay ledger append failed during gate materialization"
            evord_ok = False
            evord_details = "event ledger materialization failed"
        except (KeyError, TypeError, ValueError) as exc:
            replaystate_ok = False
            replay_details = f"replay gate materialization failed:{type(exc).__name__}"
            evord_ok = False
            evord_details = f"event ledger materialization failed:{type(exc).__name__}"
        results.append(
            GateResult(
                gate_id="G-RUN-V01-EVORD",
                passed=evord_ok,
                details=evord_details,
            )
        )
        results.append(
            GateResult(
                gate_id="G-RUN-V01-REPLAYSTATE",
                passed=replaystate_ok,
                details=replay_details,
            )
        )

        # Merge gates
        bundle_ids_ok = (
            audit_queries.records_unique_by_id(attempts_list, "attempt_id")
            and audit_queries.records_unique_by_id(precommits_list, "precommit_event_id")
            and audit_queries.records_unique_by_id(precommits_list, "attempt_id")
            and audit_queries.records_unique_by_id(telemetry_events_list, "telemetry_event_id")
            and audit_queries.records_unique_by_id(migrations_list, "migration_event_id")
            and audit_queries.records_unique_by_id(snapshots_list, "snapshot_id")
            and audit_queries.records_unique_by_id(updates_list, "update_id")
        )
        bundle_ids_ok = bundle_ids_ok and not audit_queries.duplicate_ids_with_conflicting_payload(
            attempts_list, "attempt_id"
        )
        bundle_ids_ok = bundle_ids_ok and not audit_queries.duplicate_ids_with_conflicting_payload(
            precommits_list, "precommit_event_id"
        )
        bundle_ids_ok = bundle_ids_ok and not audit_queries.duplicate_ids_with_conflicting_payload(
            telemetry_events_list, "telemetry_event_id"
        )
        bundle_ids_ok = bundle_ids_ok and not audit_queries.duplicate_ids_with_conflicting_payload(
            migrations_list, "migration_event_id"
        )
        bundle_ids_ok = bundle_ids_ok and not audit_queries.duplicate_ids_with_conflicting_payload(
            snapshots_list, "snapshot_id"
        )
        bundle_ids_ok = bundle_ids_ok and not audit_queries.duplicate_ids_with_conflicting_payload(
            updates_list, "update_id"
        )
        run_ref_ok = (
            all(a.get("run_id") == manifest.get("run_id") for a in attempts_list)
            and all(p.get("run_id") == manifest.get("run_id") for p in precommits_list)
            and all(t.get("run_id") == manifest.get("run_id") for t in telemetry_events_list)
            and all(m.get("run_id") == manifest.get("run_id") for m in migrations_list)
            and all(s.get("run_id") == manifest.get("run_id") for s in snapshots_list)
            and all(u.get("run_id") == manifest.get("run_id") for u in updates_list)
            and all(st.get("run_id") == manifest.get("run_id") for st in safe_mode_transitions)
            and all(q.get("run_id") == manifest.get("run_id") for q in quarantine_decisions)
            and all(a.get("run_id") == manifest.get("run_id") for a in anchor_audits)
        )
        ledger_ok = True
        ledger_ok = ledger_ok and not self._validator.validate_manifest(manifest)
        for attempt in attempts_list:
            ledger_ok = ledger_ok and not self._validator.validate_attempt(attempt, manifest)
        for precommit in precommits_list:
            ledger_ok = ledger_ok and not self._validator.validate_attempt_precommit(precommit, manifest)
        for telemetry_event in telemetry_events_list:
            ledger_ok = ledger_ok and not self._validator.validate_attempt_telemetry_event(
                telemetry_event, manifest
            )
        for migration in migrations_list:
            ledger_ok = ledger_ok and not self._validator.validate_state_migration_event(
                migration, manifest
            )
        for snapshot in snapshots_list:
            ledger_ok = ledger_ok and not self._validator.validate_state_snapshot(snapshot, manifest)
        for transition in safe_mode_transitions:
            ledger_ok = ledger_ok and not self._validator.validate_safe_mode_transition_event(
                transition, manifest
            )
        for decision in quarantine_decisions:
            ledger_ok = ledger_ok and not self._validator.validate_quarantine_decision_event(
                decision, manifest
            )
        for audit_event in anchor_audits:
            ledger_ok = ledger_ok and not self._validator.validate_anchor_audit_event(
                audit_event, manifest
            )
        ledger_ok = ledger_ok and audit_queries.precommit_bindings_consistent(attempts_list, precommits_list)
        ledger_ok = ledger_ok and audit_queries.telemetry_window_bindings_consistent(
            attempts_list,
            telemetry_events_list,
            precommits_list,
            events=events,
        )
        ledger_ok = ledger_ok and audit_queries.migration_manifest_lineage_coherent(
            manifest,
            migrations_list,
        )
        ledger_ok = ledger_ok and audit_queries.timeline_records_consistent(
            manifest,
            attempts_list,
            precommits_list,
            telemetry_events_list,
            snapshots_list,
            updates_list,
            migrations_list,
            safe_mode_transitions,
            quarantine_decisions,
            anchor_audits,
        )
        ledger_ok = ledger_ok and audit_queries.safe_mode_transition_sequence_coherent(
            safe_mode_transitions,
            events=events,
        )
        ledger_ok = ledger_ok and audit_queries.provenance_snapshot_ref_integrity(
            attempts_list,
            snapshots_list,
        )
        ledger_ok = ledger_ok and audit_queries.updates_snapshot_ref_integrity(updates_list, snapshots_list)
        ledger_ok = ledger_ok and bundle_ids_ok and run_ref_ok and canonical_events_ok
        results.append(
            GateResult(
                gate_id="G-MRG-V01-LEDGER",
                passed=ledger_ok,
                details="attempt/precommit/snapshot contracts valid with binding, idempotency, and version pointers",
            )
        )

        policydec_ok = True
        policydec_prefixes = (
            "attempt_policy_decision_",
            "attempt_decision_trace_decision_id_missing_from_policy_decisions",
            "attempt_decision_trace_policy_domain_mismatch:",
        )
        for attempt in attempts_list:
            attempt_errors = self._validator.validate_attempt(attempt, manifest)
            if any(
                err.startswith(policydec_prefixes[0])
                or err == policydec_prefixes[1]
                or err.startswith(policydec_prefixes[2])
                for err in attempt_errors
            ):
                policydec_ok = False
                break
        results.append(
            GateResult(
                gate_id="G-MRG-V01-POLICYDEC",
                passed=canonical_events_ok and policydec_ok,
                details="policy_decisions required fields and decision_traces decision join",
            )
        )

        logatomic_merge_ok = all(not self._validator.validate_state_update_event(u) for u in updates_list)
        results.append(
            GateResult(
                gate_id="G-MRG-V01-LOGATOMIC",
                passed=canonical_events_ok and logatomic_merge_ok,
                details="state-update append/application status and atomicity rules valid",
            )
        )

        valid_attempts: list[dict[str, Any]] = []
        for attempt in attempts_list:
            if not self._validator.validate_attempt(attempt, manifest):
                valid_attempts.append(attempt)
        refint_merge_ok = audit_queries.updates_referentially_integral(valid_attempts, updates_list)
        results.append(
            GateResult(
                gate_id="G-MRG-V01-REFINT",
                passed=canonical_events_ok and refint_merge_ok,
                details="updates reference validated attempts with consistent partition authorization/eligibility",
            )
        )

        cbgsoft_ok = all(not self._validator.validate_attempt_diagnosis_semantics(a) for a in attempts_list)
        results.append(
            GateResult(
                gate_id="G-MRG-V01-CBGSOFT",
                passed=canonical_events_ok and cbgsoft_ok,
                details="assistance/channel/eligibility/reason/allowed-partition semantics are consistent",
            )
        )

        calgovlog_ok = all(audit_queries.governor_fields_present(u) for u in updates_list)
        results.append(
            GateResult(
                gate_id="G-MRG-V01-CALGOVLOG",
                passed=canonical_events_ok and calgovlog_ok,
                details="state updates include calibration-governor fields",
            )
        )

        explog_ok = all(
            not self._validator.validate_decision_traces_contract(a.get("decision_traces"))
            for a in attempts_list
        )
        results.append(
            GateResult(
                gate_id="G-MRG-V01-EXPLOG",
                passed=canonical_events_ok and explog_ok,
                details="decision trace probabilities normalized and chosen probability matches",
            )
        )

        govlog_merge_ok = True
        govlog_merge_details = (
            "governance event logs satisfy mechanical contracts, deterministic safe-mode "
            "sequence semantics, and state-update safe_mode_profile_id binding to active transition profile"
        )
        for transition in safe_mode_transitions:
            govlog_merge_ok = govlog_merge_ok and not self._validator.validate_safe_mode_transition_event(
                transition, manifest
            )
        for decision in quarantine_decisions:
            govlog_merge_ok = govlog_merge_ok and not self._validator.validate_quarantine_decision_event(
                decision, manifest
            )
        for audit_event in anchor_audits:
            govlog_merge_ok = govlog_merge_ok and not self._validator.validate_anchor_audit_event(
                audit_event, manifest
            )
        govlog_merge_ok = govlog_merge_ok and audit_queries.safe_mode_transition_sequence_coherent(
            safe_mode_transitions,
            events=events,
        )
        if canonical_events_ok:
            govlog_merge_ok = govlog_merge_ok and audit_queries.safe_mode_update_profile_bindings_consistent(
                events
            )
        else:
            govlog_merge_ok = False
            govlog_merge_details = "event ledger integrity invalid for governance log gate"
        results.append(
            GateResult(
                gate_id="G-MRG-V01-GOVLOG",
                passed=govlog_merge_ok,
                details=govlog_merge_details,
            )
        )

        evtbind_merge_ok = True
        evtbind_merge_details = (
            "typed record lists and event ledger represent identical payload world (id/hash equivalence)"
        )
        evtbind_merge_ok = canonical_events_ok
        evtbind_merge_details = canonical_events_details
        results.append(
            GateResult(
                gate_id="G-MRG-V01-EVTBIND",
                passed=evtbind_merge_ok,
                details=evtbind_merge_details,
            )
        )

        # Release gate
        ope_level = manifest.get("ope_support_level")
        support_report = audit_queries.compute_ope_support_report(attempts_list, manifest)
        propensity_logs_present = audit_queries.propensity_logs_present_for_targets(support_report)
        opeclass_ok = True
        if ope_level == "none":
            opeclass_ok = True
        elif ope_level == "propensity_only":
            opeclass_ok = bool(support_report.get("valid_contract", False)) and propensity_logs_present
        elif ope_level == "full_support":
            opeclass_ok = bool(support_report.get("full_support_ready", False))
        else:
            opeclass_ok = False
        opeclass_ok = canonical_events_ok and opeclass_ok
        results.append(
            GateResult(
                gate_id="G-REL-V01-OPECLASS",
                passed=opeclass_ok,
                details=(
                    f"valid_contract={support_report.get('valid_contract')}; "
                    f"target_trace_kinds={support_report.get('target_trace_kinds')}; "
                    f"propensity_logs_present={propensity_logs_present}; "
                    f"thresholds_pass={support_report.get('thresholds_pass')}; "
                    f"support_checks_pass={support_report.get('support_checks_pass')}; "
                    f"full_support_ready={support_report.get('full_support_ready')}; "
                    "propensity_only requires valid target-kind propensity logs; "
                    "full_support requires thresholded overlap/support plus policy support checks"
                ),
            )
        )
        return results

    def _typed_views_from_events(self, events: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
        return {
            "attempts": audit_queries.event_payloads_by_type(events, "attempt_observed"),
            "precommits": audit_queries.event_payloads_by_type(events, "attempt_precommitted"),
            "telemetry_events": audit_queries.event_payloads_by_type(events, "attempt_telemetry"),
            "snapshots": audit_queries.event_payloads_by_type(events, "snapshot_checkpoint"),
            "updates": audit_queries.event_payloads_by_type(events, "state_update"),
            "migrations": audit_queries.event_payloads_by_type(events, "state_migration"),
            "safe_mode_transitions": audit_queries.event_payloads_by_type(events, "safe_mode_transition"),
            "quarantine_decisions": audit_queries.event_payloads_by_type(events, "quarantine_decision"),
            "anchor_audits": audit_queries.event_payloads_by_type(events, "anchor_audit"),
        }
