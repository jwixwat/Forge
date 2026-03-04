"""Acceptance tests for v0.1 implementation plan."""

from __future__ import annotations

import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from forge_v01.contract_validator import ContractValidator
from forge_v01.constants import EVENT_ID_PREFIX_BY_TYPE
from forge_v01.gate_runner import GateRunner
from forge_v01.ledger_store import DuplicateRecordError, LedgerStore
from forge_v01.mutation_guard import MutationGuard
from forge_v01.replay_engine import ReplayEngine
from tests.fixtures import (
    clone,
    make_anchor_audit_event,
    make_attempt,
    make_attempt_precommit,
    make_attempt_telemetry_events,
    make_manifest,
    make_quarantine_decision_event,
    make_safe_mode_transition_event,
    make_state_migration,
    make_state_snapshot,
    make_state_update,
)
from forge_v01.utils import sha256_json


def _gate(results, gate_id):
    for r in results:
        if r.gate_id == gate_id:
            return r
    raise KeyError(gate_id)


def _telemetry_for_attempts(manifest, attempts):
    telemetry_events = []
    for attempt in attempts:
        telemetry_events.extend(make_attempt_telemetry_events(manifest, attempt))
    return telemetry_events


def _events_from_typed_records(
    manifest,
    attempts,
    precommits,
    telemetry_events,
    snapshots,
    updates,
    migrations=None,
):
    run_id = manifest["run_id"]
    records = []
    migrations = migrations or []
    typed_order = [
        ("state_migration", migrations, "migration_event_id", "migration_ts_utc"),
        ("attempt_precommitted", precommits, "precommit_event_id", "presented_ts_utc"),
        ("attempt_telemetry", telemetry_events, "telemetry_event_id", "telemetry_ts_utc"),
        ("attempt_observed", attempts, "attempt_id", "attempt_ts_utc"),
        ("state_update", updates, "update_id", "update_ts_utc"),
        ("snapshot_checkpoint", snapshots, "snapshot_id", "snapshot_ts_utc"),
    ]
    sequence_no = 1
    written_base = datetime(2026, 2, 27, 18, 30, 0, tzinfo=timezone.utc)
    for event_type, payloads, id_field, ts_field in typed_order:
        for payload in payloads:
            payload_id = payload.get(id_field)
            event_id = f"{EVENT_ID_PREFIX_BY_TYPE[event_type]}{payload_id}"
            event_ts = payload.get(ts_field, "2026-02-27T18:30:00Z")
            records.append(
                {
                    "event_id": event_id,
                    "event_ts_utc": event_ts,
                    "event_type": event_type,
                    "run_id": run_id,
                    "session_id": payload.get("session_id"),
                    "causal_refs": [],
                    "payload": payload,
                    "ledger_sequence_no": sequence_no,
                    "event_written_ts_utc": (written_base + timedelta(seconds=sequence_no)).isoformat().replace(
                        "+00:00", "Z"
                    ),
                }
            )
            sequence_no += 1
    return records


class TestV01Acceptance(unittest.TestCase):
    """AT-V01-1..8 acceptance set from the v0.1 plan."""

    def setUp(self) -> None:
        self.validator = ContractValidator()
        self.gates = GateRunner(self.validator)
        self.guard = MutationGuard()
        self.replay = ReplayEngine(self.validator, self.guard)

    def _run_gates(
        self,
        manifest,
        attempts,
        precommits,
        snapshots,
        updates,
        **kwargs,
    ):
        if kwargs.get("telemetry_events") is None:
            kwargs["telemetry_events"] = _telemetry_for_attempts(manifest, attempts)
        if "events" not in kwargs:
            kwargs["events"] = _events_from_typed_records(
                manifest,
                attempts,
                precommits,
                kwargs.get("telemetry_events") or [],
                snapshots,
                updates,
                kwargs.get("migrations") or [],
            )
        return self.gates.run_v01_gates(
            manifest,
            attempts,
            precommits,
            snapshots,
            updates,
            **kwargs,
        )

    def test_at_v01_1_manifest_projection_integrity(self) -> None:
        manifest = make_manifest()
        attempt = make_attempt(manifest)
        precommit = make_attempt_precommit(manifest, attempt)
        snapshot = make_state_snapshot(manifest)
        update = make_state_update(manifest)

        results = self._run_gates(
            manifest,
            [attempt],
            [precommit],
            [snapshot],
            [update],
            telemetry_events=_telemetry_for_attempts(manifest, [attempt]),
        )
        self.assertTrue(_gate(results, "G-RUN-V01-RPL").passed)
        self.assertTrue(_gate(results, "G-RUN-V01-NOMIX").passed)
        self.assertTrue(_gate(results, "G-RUN-V01-REPLAYSTATE").passed)

    def test_at_v01_2_attempt_ingest_happy_path(self) -> None:
        manifest = make_manifest()
        attempt = make_attempt(manifest)
        errors = self.validator.validate_attempt(attempt, manifest)
        self.assertEqual(errors, [])

    def test_at_v01_3_reject_mixed_semantics(self) -> None:
        manifest = make_manifest()
        attempt = make_attempt(manifest)
        precommit = make_attempt_precommit(manifest, attempt)
        attempt["version_pointers"]["policy_version"] = "policy.v9.9.9"
        results = self._run_gates(manifest, [attempt], [precommit], [], [])
        self.assertFalse(_gate(results, "G-RUN-V01-NOMIX").passed)

    def test_at_v01_4_idempotent_duplicate_attempt_replay(self) -> None:
        manifest = make_manifest()
        with tempfile.TemporaryDirectory() as tmp:
            store = LedgerStore(tmp)
            store.put_manifest(manifest)
            attempt = make_attempt(manifest)
            precommit = make_attempt_precommit(manifest, attempt)
            store.append_attempt_precommit(precommit)
            for telemetry_event in make_attempt_telemetry_events(manifest, attempt):
                store.append_attempt_telemetry(telemetry_event)
            store.append_attempt(attempt)
            with self.assertRaises(DuplicateRecordError):
                store.append_attempt(clone(attempt))

            result = self.replay.replay_run(manifest["run_id"], store)
            self.assertEqual(result.attempts_seen, 1)
            self.assertEqual(result.attempts_applied, 1)

    def test_at_v01_4b_duplicate_snapshot_rejected(self) -> None:
        manifest = make_manifest()
        with tempfile.TemporaryDirectory() as tmp:
            store = LedgerStore(tmp)
            store.put_manifest(manifest)
            snapshot = make_state_snapshot(manifest)
            store.append_state_snapshot(snapshot)
            with self.assertRaises(DuplicateRecordError):
                store.append_state_snapshot(clone(snapshot))

    def test_at_v01_4c_disk_readback_replay_after_fresh_store(self) -> None:
        manifest = make_manifest(run_id="run_disk_readback_replay")
        attempt = make_attempt(manifest, attempt_id="att_disk_readback_001")
        precommit = make_attempt_precommit(manifest, attempt)
        telemetry_events = make_attempt_telemetry_events(manifest, attempt)

        with tempfile.TemporaryDirectory() as tmp:
            writer = LedgerStore(tmp)
            writer.put_manifest(manifest)
            writer.append_attempt_precommit(precommit)
            for telemetry_event in telemetry_events:
                writer.append_attempt_telemetry(telemetry_event)
            writer.append_attempt(attempt)

            replay_before = self.replay.replay_run(manifest["run_id"], writer)
            self.assertEqual(replay_before.errors, [])
            self.assertEqual(replay_before.attempts_seen, 1)
            self.assertEqual(replay_before.attempts_applied, 1)

            reader = LedgerStore(tmp)
            loaded_manifest = reader.get_manifest(manifest["run_id"])
            self.assertEqual(loaded_manifest["run_id"], manifest["run_id"])
            self.assertEqual(len(reader.get_precommits(manifest["run_id"])), 1)
            self.assertEqual(len(reader.get_attempt_telemetry(manifest["run_id"])), len(telemetry_events))
            self.assertEqual(len(reader.get_attempts(manifest["run_id"])), 1)
            self.assertEqual(len(reader.get_events(manifest["run_id"])), 4)

            replay_after = self.replay.replay_run(manifest["run_id"], reader)
            self.assertEqual(replay_after.errors, [])
            self.assertEqual(replay_after.attempts_seen, replay_before.attempts_seen)
            self.assertEqual(replay_after.attempts_applied, replay_before.attempts_applied)
            self.assertEqual(replay_after.final_state_hash, replay_before.final_state_hash)

            # Sequence continuity after restart: next appended event should continue from prior max.
            anchor_event = make_anchor_audit_event(
                manifest,
                event_id="evt_anchor_readback_seq_0001",
            )
            reader.append_anchor_audit(anchor_event)
            events = reader.get_events(manifest["run_id"])
            max_seq = max(int(e["ledger_sequence_no"]) for e in events)
            self.assertEqual(max_seq, 5)

    def test_at_v01_5_log_atomic_diagnosis_mutation(self) -> None:
        manifest = make_manifest()
        applied_update = make_state_update(manifest, mutation_outcome="applied")
        blocked_update = make_state_update(
            manifest,
            update_id="upd_000124",
            mutation_outcome="blocked_by_governor",
            governor_decision="freeze",
            suppression_reason="calibration_freeze",
        )
        failed_update = make_state_update(
            manifest,
            update_id="upd_000125",
            mutation_outcome="failed_due_to_integrity",
        )

        self.assertEqual(self.validator.validate_state_update_event(applied_update), [])
        self.assertEqual(self.validator.validate_state_update_event(blocked_update), [])
        self.assertEqual(self.validator.validate_state_update_event(failed_update), [])

        allowed = self.guard.evaluate(applied_update)
        governor_blocked = self.guard.evaluate(blocked_update)
        integrity_blocked = self.guard.evaluate(failed_update)
        self.assertTrue(allowed.allowed)
        self.assertFalse(governor_blocked.allowed)
        self.assertFalse(integrity_blocked.allowed)

    def test_at_v01_6_decision_traces_policy_decisions_join_integrity(self) -> None:
        manifest = make_manifest()
        attempt = make_attempt(manifest)
        self.assertEqual(self.validator.validate_attempt(attempt, manifest), [])

        broken = clone(attempt)
        broken["decision_traces"][0]["decision_id"] = "pol_missing"
        errors = self.validator.validate_attempt(broken, manifest)
        self.assertIn("attempt_decision_trace_decision_id_missing_from_policy_decisions", errors)

        bad_version = make_attempt(manifest)
        bad_version["policy_decisions"][0]["policy_version"] = "policy.v9.9.9"
        errors = self.validator.validate_attempt(bad_version, manifest)
        self.assertIn("attempt_policy_decision_policy_version_mismatch_manifest[0]", errors)

    def test_at_v01_7_soft_closed_book_diagnosis_routing(self) -> None:
        manifest = make_manifest()
        attempt = make_attempt(manifest, assistance_mode="open_book")
        precommit = make_attempt_precommit(manifest, attempt)
        results = self._run_gates(manifest, [attempt], [precommit], [], [])
        self.assertTrue(_gate(results, "G-MRG-V01-CBGSOFT").passed)

        bad = clone(attempt)
        bad["allowed_update_partitions"] = ["diagnosis_state"]
        bad_precommit = make_attempt_precommit(manifest, bad)
        results_bad = self._run_gates(manifest, [bad], [bad_precommit], [], [])
        self.assertFalse(_gate(results_bad, "G-MRG-V01-CBGSOFT").passed)

    def test_at_v01_9_closed_book_semantics_invariant_enforced(self) -> None:
        manifest = make_manifest()

        open_book_lie = make_attempt(
            manifest,
            assistance_mode="open_book",
            diagnosis_update_eligibility="eligible",
            ineligibility_reason="none",
            allowed_update_partitions=["diagnosis_state"],
        )
        errors = self.validator.validate_attempt(open_book_lie, manifest)
        self.assertIn("attempt_non_diagnostic_or_assisted_must_be_ineligible", errors)
        self.assertIn("attempt_ineligible_allows_diagnosis_state", errors)
        self.assertIn("attempt_ineligibility_reason_mismatch_semantics", errors)

        learning_channel_lie = make_attempt(
            manifest,
            assistance_mode="closed_book",
            evidence_channel="C_learning",
            diagnosis_update_eligibility="eligible",
            ineligibility_reason="none",
            allowed_update_partitions=["diagnosis_state"],
        )
        errors = self.validator.validate_attempt(learning_channel_lie, manifest)
        self.assertIn("attempt_non_diagnostic_or_assisted_must_be_ineligible", errors)
        self.assertIn("attempt_ineligible_allows_diagnosis_state", errors)
        self.assertIn("attempt_ineligibility_reason_mismatch_semantics", errors)

        reason_mismatch = make_attempt(manifest, assistance_mode="open_book")
        reason_mismatch["ineligibility_reason"] = "channel_not_diagnostic"
        errors = self.validator.validate_attempt(reason_mismatch, manifest)
        self.assertIn("attempt_ineligibility_reason_mismatch_semantics", errors)

        both_invalid_wrong_reason = make_attempt(
            manifest,
            assistance_mode="tool_assisted",
            evidence_channel="C_learning",
            ineligibility_reason="assistance_mode_not_closed_book",
        )
        errors = self.validator.validate_attempt(both_invalid_wrong_reason, manifest)
        self.assertIn("attempt_ineligibility_reason_mismatch_semantics", errors)

        precommits = [
            make_attempt_precommit(manifest, open_book_lie),
            make_attempt_precommit(manifest, learning_channel_lie),
            make_attempt_precommit(manifest, reason_mismatch),
            make_attempt_precommit(manifest, both_invalid_wrong_reason),
        ]
        results = self._run_gates(
            manifest,
            [open_book_lie, learning_channel_lie, reason_mismatch, both_invalid_wrong_reason],
            precommits,
            [],
            [],
        )
        self.assertFalse(_gate(results, "G-MRG-V01-CBGSOFT").passed)

    def test_at_v01_10_residual_provenance_alignment_enforced(self) -> None:
        manifest = make_manifest()

        bad_sensor = make_attempt(
            manifest,
            residual_provenance_overrides={"sensor_model_version": "sensor.v9.9.9"},
        )
        errors = self.validator.validate_attempt(bad_sensor, manifest)
        self.assertIn("attempt_residual_provenance_mismatch_manifest:sensor_model_version", errors)
        self.assertIn(
            "attempt_residual_provenance_mismatch_version_pointers:sensor_model_version",
            errors,
        )

        bad_obs = make_attempt(
            manifest,
            residual_provenance_overrides={"obs_encoder_version": "obsenc.v9.9.9"},
        )
        errors = self.validator.validate_attempt(bad_obs, manifest)
        self.assertIn("attempt_residual_provenance_mismatch_manifest:obs_encoder_version", errors)
        self.assertIn(
            "attempt_residual_provenance_mismatch_version_pointers:obs_encoder_version",
            errors,
        )

        bad_hyp = make_attempt(
            manifest,
            residual_provenance_overrides={"hypothesis_space_hash": "hyp_hash_BAD"},
        )
        errors = self.validator.validate_attempt(bad_hyp, manifest)
        self.assertIn("attempt_residual_provenance_mismatch_manifest:hypothesis_space_hash", errors)
        self.assertIn(
            "attempt_residual_provenance_mismatch_version_pointers:hypothesis_space_hash",
            errors,
        )

        missing_field = make_attempt(manifest)
        del missing_field["residual_inputs"]["provenance"]["sensor_model_version"]
        errors = self.validator.validate_attempt(missing_field, manifest)
        self.assertIn("attempt_residual_provenance_missing:sensor_model_version", errors)

        precommits = [
            make_attempt_precommit(manifest, bad_sensor),
            make_attempt_precommit(manifest, bad_obs),
            make_attempt_precommit(manifest, bad_hyp),
            make_attempt_precommit(manifest, missing_field),
        ]
        results = self._run_gates(
            manifest,
            [bad_sensor, bad_obs, bad_hyp, missing_field],
            precommits,
            [],
            [],
        )
        self.assertFalse(_gate(results, "G-RUN-V01-NOMIX").passed)

    def test_at_v01_11_update_outcome_status_distinction(self) -> None:
        manifest = make_manifest()
        freeze_block = make_state_update(
            manifest,
            mutation_outcome="blocked_by_governor",
            governor_decision="freeze",
            suppression_reason="calibration_freeze",
        )
        policy_skip = make_state_update(
            manifest,
            update_id="upd_000124",
            mutation_outcome="skipped_by_policy",
            suppression_reason="policy_skip",
        )
        integrity_fail = make_state_update(
            manifest,
            update_id="upd_000125",
            mutation_outcome="failed_due_to_integrity",
        )
        append_fail = make_state_update(
            manifest,
            update_id="upd_000126",
            diagnosis_log_write_status="failed",
        )

        for update in (freeze_block, policy_skip, integrity_fail, append_fail):
            self.assertEqual(self.validator.validate_state_update_event(update), [])

        gate_results = self._run_gates(
            manifest,
            [],
            [],
            [],
            [freeze_block, policy_skip, integrity_fail, append_fail],
        )
        self.assertTrue(_gate(gate_results, "G-RUN-V01-LOGATOMIC").passed)
        self.assertTrue(_gate(gate_results, "G-MRG-V01-LOGATOMIC").passed)

    def test_at_v01_11b_governed_transform_enforced(self) -> None:
        manifest = make_manifest()
        update = make_state_update(manifest, mutation_outcome="applied")
        bad_transform = clone(update)
        bad_transform["state_patch"]["value"] = 0.9
        bad_transform["post_state_hash"] = "sha256:bad_post_hash"
        errors = self.validator.validate_state_update_event(bad_transform)
        self.assertIn("state_update_governed_transform_mismatch", errors)

        freeze_applied = make_state_update(
            manifest,
            update_id="upd_freeze_applied",
            mutation_outcome="applied",
            governor_decision="freeze",
        )
        freeze_errors = self.validator.validate_state_update_event(freeze_applied)
        self.assertIn("state_update_freeze_cannot_apply_diagnosis_mutation", freeze_errors)

    def test_at_v01_11c_profile_multiplier_semantics_enforced(self) -> None:
        manifest = make_manifest(run_id="run_profile_multiplier_semantics")

        sensor_bad = make_state_update(
            manifest,
            update_id="upd_sensor_multiplier_bad",
            mutation_outcome="applied",
        )
        sensor_bad["safe_mode_profile_id"] = "SG_SENSOR_UNRELIABLE_GUARD"
        sensor_bad_errors = self.validator.validate_state_update_event(sensor_bad)
        self.assertIn("state_update_profile_multiplier_mismatch", sensor_bad_errors)

        sensor_good = clone(sensor_bad)
        sensor_good["applied_update_multiplier"] = 0.10
        sensor_good["state_patch"]["value"] = 0.10
        sensor_good_errors = self.validator.validate_state_update_event(sensor_good)
        self.assertEqual(sensor_good_errors, [])

        panic_applied = make_state_update(
            manifest,
            update_id="upd_panic_applied_bad",
            mutation_outcome="applied",
        )
        panic_applied["safe_mode_profile_id"] = "SP_MANUAL_PANIC"
        panic_applied["applied_update_multiplier"] = 0.00
        panic_applied["state_patch"]["value"] = 0.00
        panic_errors = self.validator.validate_state_update_event(panic_applied)
        self.assertIn("state_update_panic_profile_cannot_apply_diagnosis_mutation", panic_errors)

    def test_at_v01_11d_replay_enforces_profile_multiplier_semantics(self) -> None:
        manifest = make_manifest(run_id="run_replay_profile_multiplier_semantics")
        attempt = make_attempt(manifest, attempt_id="att_replay_profile_multiplier_001")
        precommit = make_attempt_precommit(manifest, attempt)
        update = make_state_update(
            manifest,
            update_id="upd_replay_profile_multiplier_bad",
            source_attempt_id=attempt["attempt_id"],
            mutation_outcome="applied",
        )
        update["safe_mode_profile_id"] = "SG_SENSOR_UNRELIABLE_GUARD"
        # Keep default 0.50 to violate SG_SENSOR_UNRELIABLE_GUARD fixed multiplier 0.10.
        with tempfile.TemporaryDirectory() as tmp:
            store = LedgerStore(tmp)
            store.put_manifest(manifest)
            store.append_attempt_precommit(precommit)
            for telemetry_event in make_attempt_telemetry_events(manifest, attempt):
                store.append_attempt_telemetry(telemetry_event)
            store.append_attempt(attempt)
            store.append_state_update(update)
            replay_result = self.replay.replay_run(manifest["run_id"], store)
            self.assertTrue(
                any("state_update_profile_multiplier_mismatch" in e for e in replay_result.errors)
            )

    def test_at_v01_12_likelihood_sketch_validation_enforced(self) -> None:
        manifest = make_manifest()

        negative_prob = make_attempt(manifest)
        negative_prob["residual_inputs"]["likelihood_sketch"]["predicted_observation_distribution"][0]["p"] = -0.1
        errors = self.validator.validate_attempt(negative_prob, manifest)
        self.assertIn("attempt_likelihood_distribution_probability_invalid[0]", errors)

        not_normalized = make_attempt(manifest)
        not_normalized["residual_inputs"]["likelihood_sketch"]["predicted_observation_distribution"] = [
            {"obs_key": "SLOT(a=pass,b=fail)", "p": 0.5},
            {"obs_key": "SLOT(a=pass,b=pass)", "p": 0.5},
            {"obs_key": "SLOT(a=fail,b=fail)", "p": 0.5},
        ]
        errors = self.validator.validate_attempt(not_normalized, manifest)
        self.assertIn("attempt_likelihood_distribution_not_normalized", errors)

        duplicate_obs_key = make_attempt(manifest)
        duplicate_obs_key["residual_inputs"]["likelihood_sketch"]["predicted_observation_distribution"] = [
            {"obs_key": "SLOT(a=pass,b=fail)", "p": 0.5},
            {"obs_key": "SLOT(a=pass,b=fail)", "p": 0.5},
        ]
        errors = self.validator.validate_attempt(duplicate_obs_key, manifest)
        self.assertIn(
            "attempt_likelihood_distribution_duplicate_obs_key:SLOT(a=pass,b=fail)",
            errors,
        )

        unknown_obs = make_attempt(manifest)
        unknown_obs["residual_inputs"]["likelihood_sketch"]["predicted_observation_distribution"] = [
            {"obs_key": "SLOT(a=unknown,b=unknown)", "p": 1.0},
        ]
        errors = self.validator.validate_attempt(unknown_obs, manifest)
        self.assertIn(
            "attempt_likelihood_distribution_obs_key_unknown:SLOT(a=unknown,b=unknown)",
            errors,
        )

        missing_distribution = make_attempt(manifest)
        del missing_distribution["residual_inputs"]["likelihood_sketch"]["predicted_observation_distribution"]
        errors = self.validator.validate_attempt(missing_distribution, manifest)
        self.assertIn("attempt_likelihood_sketch_missing:predicted_observation_distribution", errors)

        bad_top_hypothesis = make_attempt(manifest)
        del bad_top_hypothesis["residual_inputs"]["likelihood_sketch"]["top_hypotheses"][0]["likelihood"]
        errors = self.validator.validate_attempt(bad_top_hypothesis, manifest)
        self.assertIn("attempt_likelihood_top_hypothesis_missing_fields[0]", errors)

        precommits = [
            make_attempt_precommit(manifest, negative_prob),
            make_attempt_precommit(manifest, not_normalized),
            make_attempt_precommit(manifest, duplicate_obs_key),
            make_attempt_precommit(manifest, unknown_obs),
            make_attempt_precommit(manifest, missing_distribution),
            make_attempt_precommit(manifest, bad_top_hypothesis),
        ]
        gate_results = self._run_gates(
            manifest,
            [negative_prob, not_normalized, duplicate_obs_key, unknown_obs, missing_distribution, bad_top_hypothesis],
            precommits,
            [],
            [],
        )
        self.assertFalse(_gate(gate_results, "G-MRG-V01-LEDGER").passed)

    def test_at_v01_13_multi_trace_join_and_distribution_support(self) -> None:
        manifest = make_manifest()
        feedback_trace = {
            "decision_id": "pol_0002",
            "trace_kind": "feedback",
            "candidate_actions": [
                {"action_id": "FB:minimal_hint", "p": 0.7},
                {"action_id": "FB:scaffolded_hint", "p": 0.3},
            ],
            "chosen_action_id": "FB:minimal_hint",
            "chosen_action_probability": 0.7,
        }
        feedback_decision = {
            "decision_id": "pol_0002",
            "policy_domain": "other",
            "policy_version": manifest["policy_version"],
            "rule_id": "feedback.micro.randomized",
            "scope_type": "attempt",
            "scope_id": "att_000001",
            "outcome": "applied",
            "commit_status": "committed",
            "reason_code": "feedback_experiment_arm",
            "decision_ts_utc": "2026-02-27T18:30:00Z",
            "entropy_floor_met": True,
            "min_support_met": True,
            "support_check_status": "pass",
        }

        valid_multi = make_attempt(
            manifest,
            extra_decision_traces=[feedback_trace],
            extra_policy_decisions=[feedback_decision],
        )
        self.assertEqual(self.validator.validate_attempt(valid_multi, manifest), [])
        valid_gates = self._run_gates(
            manifest,
            [valid_multi],
            [make_attempt_precommit(manifest, valid_multi)],
            [],
            [],
        )
        self.assertTrue(_gate(valid_gates, "G-MRG-V01-POLICYDEC").passed)
        self.assertTrue(_gate(valid_gates, "G-MRG-V01-EXPLOG").passed)

        missing_join = make_attempt(
            manifest,
            extra_decision_traces=[feedback_trace],
        )
        errors = self.validator.validate_attempt(missing_join, manifest)
        self.assertIn("attempt_decision_trace_decision_id_missing_from_policy_decisions", errors)

        non_normalized = make_attempt(
            manifest,
            extra_decision_traces=[
                {
                    "decision_id": "pol_0002",
                    "trace_kind": "feedback",
                    "candidate_actions": [
                        {"action_id": "FB:minimal_hint", "p": 0.8},
                        {"action_id": "FB:scaffolded_hint", "p": 0.5},
                    ],
                    "chosen_action_id": "FB:minimal_hint",
                    "chosen_action_probability": 0.8,
                }
            ],
            extra_policy_decisions=[feedback_decision],
        )
        errors = self.validator.validate_attempt(non_normalized, manifest)
        self.assertIn("attempt_decision_trace[1]_probabilities_not_normalized", errors)

        duplicate_trace_id = make_attempt(
            manifest,
            extra_decision_traces=[
                {
                    "decision_id": "pol_0001",
                    "trace_kind": "feedback",
                    "candidate_actions": [{"action_id": "FB:minimal_hint", "p": 1.0}],
                    "chosen_action_id": "FB:minimal_hint",
                    "chosen_action_probability": 1.0,
                }
            ],
            extra_policy_decisions=[feedback_decision],
        )
        errors = self.validator.validate_attempt(duplicate_trace_id, manifest)
        self.assertIn("attempt_decision_trace_duplicate_decision_id:pol_0001", errors)

    def test_at_v01_14_replay_reconstructs_state_and_matches_checkpoint(self) -> None:
        manifest = make_manifest()
        attempt = make_attempt(manifest)
        update = make_state_update(manifest)
        snapshot = make_state_snapshot(manifest)

        with tempfile.TemporaryDirectory() as tmp:
            store = LedgerStore(tmp)
            store.put_manifest(manifest)
            store.append_attempt_precommit(make_attempt_precommit(manifest, attempt))
            for telemetry_event in make_attempt_telemetry_events(manifest, attempt):
                store.append_attempt_telemetry(telemetry_event)
            store.append_attempt(attempt)
            store.append_state_update(update)
            store.append_state_snapshot(snapshot)

            result = self.replay.replay_run(manifest["run_id"], store)
            self.assertEqual(result.errors, [])
            self.assertEqual(result.checkpoints_verified, 1)
            self.assertEqual(result.final_state_hash, snapshot["state_hash"])

    def test_at_v01_15_snapshot_tamper_detected_by_replay(self) -> None:
        manifest = make_manifest()
        attempt = make_attempt(manifest)
        update = make_state_update(manifest)
        snapshot = make_state_snapshot(manifest)
        snapshot["state_hash"] = "sha256:tampered"

        with tempfile.TemporaryDirectory() as tmp:
            store = LedgerStore(tmp)
            store.put_manifest(manifest)
            store.append_attempt_precommit(make_attempt_precommit(manifest, attempt))
            for telemetry_event in make_attempt_telemetry_events(manifest, attempt):
                store.append_attempt_telemetry(telemetry_event)
            store.append_attempt(attempt)
            store.append_state_update(update)
            store.append_state_snapshot(snapshot)

            result = self.replay.replay_run(manifest["run_id"], store)
            self.assertTrue(any("state_hash" in e for e in result.errors))

    def test_at_v01_16_event_taxonomy_rejects_unknown_event_type(self) -> None:
        manifest = make_manifest()
        with tempfile.TemporaryDirectory() as tmp:
            store = LedgerStore(tmp)
            store.put_manifest(manifest)
            with self.assertRaises(DuplicateRecordError):
                store.append_event(
                    {
                        "event_id": "evt_unknown_001",
                        "event_ts_utc": "2026-02-27T18:40:00Z",
                        "event_type": "unknown_event",
                        "run_id": manifest["run_id"],
                        "session_id": "session_0001",
                        "causal_refs": [],
                        "payload": {"run_id": manifest["run_id"]},
                    }
                )

    def test_at_v01_16b_governance_event_contracts_enforced(self) -> None:
        manifest = make_manifest(run_id="run_governance_contracts")
        safe_transition = make_safe_mode_transition_event(manifest)
        quarantine_decision = make_quarantine_decision_event(manifest)
        anchor_audit = make_anchor_audit_event(manifest)

        self.assertEqual(
            self.validator.validate_safe_mode_transition_event(safe_transition, manifest),
            [],
        )
        self.assertEqual(
            self.validator.validate_quarantine_decision_event(quarantine_decision, manifest),
            [],
        )
        self.assertEqual(
            self.validator.validate_anchor_audit_event(anchor_audit, manifest),
            [],
        )

        bad_transition = clone(safe_transition)
        bad_transition["next_state"] = "SAFE_PANIC"
        transition_errors = self.validator.validate_safe_mode_transition_event(
            bad_transition, manifest
        )
        self.assertIn("safe_mode_transition_next_state_mismatch", transition_errors)

        bad_quarantine = clone(quarantine_decision)
        bad_quarantine["action"] = "quarantine"
        bad_quarantine["threshold_crossed"] = False
        quarantine_errors = self.validator.validate_quarantine_decision_event(
            bad_quarantine, manifest
        )
        self.assertIn(
            "quarantine_decision_quarantine_action_requires_threshold_crossed",
            quarantine_errors,
        )

        bad_anchor_audit = clone(anchor_audit)
        bad_anchor_audit["anchors_sampled"] = 1
        bad_anchor_errors = self.validator.validate_anchor_audit_event(
            bad_anchor_audit, manifest
        )
        self.assertIn("anchor_audit_quota_not_met", bad_anchor_errors)

    def test_at_v01_16c_governance_events_gate_and_replay_enforced(self) -> None:
        manifest = make_manifest(run_id="run_governance_replay")
        attempt = make_attempt(manifest, attempt_id="att_governance_001")
        precommit = make_attempt_precommit(manifest, attempt)
        update = make_state_update(manifest, source_attempt_id=attempt["attempt_id"])
        snapshot = make_state_snapshot(manifest, snapshot_id="snap_governance_001")

        with tempfile.TemporaryDirectory() as tmp:
            store = LedgerStore(tmp)
            store.put_manifest(manifest)
            store.append_attempt_precommit(precommit)
            for telemetry_event in make_attempt_telemetry_events(manifest, attempt):
                store.append_attempt_telemetry(telemetry_event)
            store.append_attempt(attempt)
            store.append_state_update(update)
            store.append_state_snapshot(snapshot)

            safe_transition = make_safe_mode_transition_event(
                manifest,
                event_id="evt_safe_mode_001",
                prior_state="NORMAL",
                trigger_set=["TRG-CALIBRATION-ALARM"],
            )
            quarantine_decision = make_quarantine_decision_event(
                manifest,
                event_id="evt_quarantine_001",
            )
            anchor_audit = make_anchor_audit_event(
                manifest,
                event_id="evt_anchor_audit_001",
            )
            store.append_safe_mode_transition(safe_transition)
            store.append_quarantine_decision(quarantine_decision)
            store.append_anchor_audit(anchor_audit)

            good_results = self._run_gates(
                manifest,
                [attempt],
                [precommit],
                [snapshot],
                [update],
                events=store.get_events(manifest["run_id"]),
            )
            self.assertTrue(_gate(good_results, "G-RUN-V01-GOVEVENTS").passed)
            self.assertTrue(_gate(good_results, "G-MRG-V01-GOVLOG").passed)

            bad_transition = clone(safe_transition)
            bad_transition["event_id"] = "evt_safe_mode_002"
            bad_transition["prior_state"] = "SAFE_PANIC"
            store.append_safe_mode_transition(bad_transition)

            bad_results = self._run_gates(
                manifest,
                [attempt],
                [precommit],
                [snapshot],
                [update],
                events=store.get_events(manifest["run_id"]),
            )
            self.assertFalse(_gate(bad_results, "G-RUN-V01-GOVEVENTS").passed)
            self.assertFalse(_gate(bad_results, "G-MRG-V01-GOVLOG").passed)

            replay_result = self.replay.replay_run(manifest["run_id"], store)
            self.assertTrue(
                any("safe_mode_transition" in e for e in replay_result.errors)
            )

    def test_at_v01_16f_events_required_for_event_dependent_runtime_gates(self) -> None:
        bootstrap = {
            "source_run_id": "run_prev_evt_req",
            "source_snapshot_id": "snap_prev_evt_req",
            "source_state_hash": "sha256:source_state_evt_req",
            "source_replay_fingerprint": "sha256:replay_evt_req",
        }
        manifest = make_manifest(
            run_id="run_events_required_runtime",
            timeline_id="timeline_learner_001",
            epoch_index=2,
            predecessor_run_id="run_prev_evt_req",
            bootstrap_snapshot_ref=bootstrap,
            migration_event_id="mig_evt_req_001",
        )
        attempt = make_attempt(manifest, attempt_id="att_evt_req_001")
        precommit = make_attempt_precommit(manifest, attempt)
        with self.assertRaisesRegex(ValueError, "events_required_for_gate_evaluation"):
            self._run_gates(
                manifest,
                [attempt],
                [precommit],
                [],
                [],
                telemetry_events=make_attempt_telemetry_events(manifest, attempt),
                migrations=[make_state_migration(manifest)],
                events=None,
            )

    def test_at_v01_16d_safe_mode_profile_binding_enforced(self) -> None:
        manifest = make_manifest(run_id="run_safe_mode_profile_binding")
        attempt = make_attempt(manifest, attempt_id="att_safe_mode_profile_001")
        precommit = make_attempt_precommit(manifest, attempt)
        update = make_state_update(
            manifest,
            update_id="upd_safe_mode_profile_001",
            source_attempt_id=attempt["attempt_id"],
        )
        snapshot = make_state_snapshot(manifest, snapshot_id="snap_safe_mode_profile_001")

        with tempfile.TemporaryDirectory() as tmp:
            store = LedgerStore(tmp)
            store.put_manifest(manifest)
            # Activate a non-calibration guarded profile before updates.
            active_transition = make_safe_mode_transition_event(
                manifest,
                event_id="evt_safe_mode_binding_001",
                prior_state="NORMAL",
                trigger_set=["TRG-SENSOR-UNRELIABLE-HIGH"],
            )
            active_transition["profile_id"] = "SG_SENSOR_UNRELIABLE_GUARD"
            active_transition["profile_parent_state"] = "SAFE_GUARDED"
            active_transition[
                "policy_bundle_hash"
            ] = "sha256:policy_bundle_sg_sensor_unreliable_guard_v0_0_0"
            store.append_safe_mode_transition(active_transition)
            store.append_attempt_precommit(precommit)
            for telemetry_event in make_attempt_telemetry_events(manifest, attempt):
                store.append_attempt_telemetry(telemetry_event)
            store.append_attempt(attempt)
            # update.safe_mode_profile_id defaults to SG_CALIBRATION_GUARD (mismatch).
            store.append_state_update(update)
            store.append_state_snapshot(snapshot)

            results = self._run_gates(
                manifest,
                [attempt],
                [precommit],
                [snapshot],
                [update],
                events=store.get_events(manifest["run_id"]),
            )
            self.assertFalse(_gate(results, "G-RUN-V01-GOVEVENTS").passed)
            self.assertFalse(_gate(results, "G-MRG-V01-GOVLOG").passed)

            replay_result = self.replay.replay_run(manifest["run_id"], store)
            self.assertTrue(
                any(
                    "safe_mode_profile_id_mismatch_active_transition" in e
                    for e in replay_result.errors
                )
            )

    def test_at_v01_16e_state_update_profile_ontology_enforced(self) -> None:
        manifest = make_manifest(run_id="run_state_update_profile_ontology")
        update = make_state_update(
            manifest,
            update_id="upd_profile_ontology_001",
        )
        update["safe_mode_profile_id"] = "UNKNOWN_PROFILE"
        errors = self.validator.validate_state_update_event(update)
        self.assertIn("state_update_safe_mode_profile_id_invalid", errors)

    def test_at_v01_17_update_attempt_referential_integrity_gates(self) -> None:
        manifest = make_manifest()
        attempt = make_attempt(manifest)
        precommit = make_attempt_precommit(manifest, attempt)
        update = make_state_update(manifest)

        good = self._run_gates(manifest, [attempt], [precommit], [], [update])
        self.assertTrue(_gate(good, "G-RUN-V01-REFINT").passed)
        self.assertTrue(_gate(good, "G-MRG-V01-REFINT").passed)

        missing_attempt = self._run_gates(manifest, [], [], [], [update])
        self.assertFalse(_gate(missing_attempt, "G-RUN-V01-REFINT").passed)
        self.assertFalse(_gate(missing_attempt, "G-MRG-V01-REFINT").passed)

        ineligible_attempt = make_attempt(
            manifest,
            assistance_mode="open_book",
        )
        bad_update = make_state_update(
            manifest,
            update_id="upd_000999",
            source_attempt_id=ineligible_attempt["attempt_id"],
            target_partition="diagnosis_state",
        )
        ref_fail = self._run_gates(
            manifest,
            [ineligible_attempt],
            [make_attempt_precommit(manifest, ineligible_attempt)],
            [],
            [bad_update],
        )
        self.assertFalse(_gate(ref_fail, "G-RUN-V01-REFINT").passed)
        self.assertFalse(_gate(ref_fail, "G-MRG-V01-REFINT").passed)

        retention_ok_update = make_state_update(
            manifest,
            update_id="upd_001000",
            source_attempt_id=ineligible_attempt["attempt_id"],
            target_partition="learning_retention_state",
        )
        retention_ok = self._run_gates(
            manifest,
            [ineligible_attempt],
            [make_attempt_precommit(manifest, ineligible_attempt)],
            [],
            [retention_ok_update],
        )
        self.assertTrue(_gate(retention_ok, "G-RUN-V01-REFINT").passed)
        self.assertTrue(_gate(retention_ok, "G-MRG-V01-REFINT").passed)

        multi_partition_attempt = make_attempt(
            manifest,
            attempt_id="att_multi_001",
            allowed_update_partitions=["diagnosis_state", "learning_retention_state"],
        )
        diagnosis_update = make_state_update(
            manifest,
            update_id="upd_multi_diag",
            source_attempt_id=multi_partition_attempt["attempt_id"],
            target_partition="diagnosis_state",
        )
        retention_update = make_state_update(
            manifest,
            update_id="upd_multi_ret",
            source_attempt_id=multi_partition_attempt["attempt_id"],
            target_partition="learning_retention_state",
        )
        multi_ok = self._run_gates(
            manifest,
            [multi_partition_attempt],
            [make_attempt_precommit(manifest, multi_partition_attempt)],
            [],
            [diagnosis_update, retention_update],
        )
        self.assertTrue(_gate(multi_ok, "G-RUN-V01-REFINT").passed)
        self.assertTrue(_gate(multi_ok, "G-MRG-V01-REFINT").passed)

    def test_at_v01_18_target_partition_bypass_blocked(self) -> None:
        manifest = make_manifest()
        attempt = make_attempt(
            manifest,
            assistance_mode="open_book",
            allowed_update_partitions=["learning_retention_state"],
        )
        precommit = make_attempt_precommit(manifest, attempt)
        malicious_update = make_state_update(manifest, update_id="upd_bypass_001")
        malicious_update["source_attempt_id"] = attempt["attempt_id"]
        malicious_update["state_patch"]["partition"] = "diagnosis_state"

        errors = self.validator.validate_state_update_event(malicious_update)
        self.assertEqual(errors, [])

        gate_results = self._run_gates(
            manifest,
            [attempt],
            [precommit],
            [],
            [malicious_update],
        )
        self.assertFalse(_gate(gate_results, "G-RUN-V01-REFINT").passed)
        self.assertFalse(_gate(gate_results, "G-MRG-V01-REFINT").passed)

        with tempfile.TemporaryDirectory() as tmp:
            store = LedgerStore(tmp)
            store.put_manifest(manifest)
            store.append_attempt_precommit(precommit)
            for telemetry_event in make_attempt_telemetry_events(manifest, attempt):
                store.append_attempt_telemetry(telemetry_event)
            store.append_attempt(attempt)
            store.append_state_update(malicious_update)
            replay_result = self.replay.replay_run(manifest["run_id"], store)
            self.assertTrue(
                any("partition_not_authorized_by_source_attempt:diagnosis_state" in e for e in replay_result.errors)
            )

    def test_at_v01_18b_replay_detects_base_value_mismatch_for_governed_update(self) -> None:
        manifest = make_manifest(run_id="run_governor_base_mismatch")
        attempt = make_attempt(manifest, attempt_id="att_governor_base_mismatch")
        precommit = make_attempt_precommit(manifest, attempt)
        telemetry_events = make_attempt_telemetry_events(manifest, attempt)
        update = make_state_update(
            manifest,
            update_id="upd_governor_base_mismatch",
            source_attempt_id=attempt["attempt_id"],
            mutation_outcome="applied",
        )
        update["base_value_at_proposal"] = 0.2
        update["state_patch"]["value"] = 0.6

        with tempfile.TemporaryDirectory() as tmp:
            store = LedgerStore(tmp)
            store.put_manifest(manifest)
            store.append_attempt_precommit(precommit)
            for telemetry_event in telemetry_events:
                store.append_attempt_telemetry(telemetry_event)
            store.append_attempt(attempt)
            store.append_state_update(update)
            replay_result = self.replay.replay_run(manifest["run_id"], store)
            self.assertTrue(
                any("base_value_mismatch_pre_state" in e for e in replay_result.errors)
            )

    def test_at_v01_8_ope_support_classification(self) -> None:
        manifest = make_manifest(ope_support_level="propensity_only")
        attempt = make_attempt(manifest, deterministic_policy=True)
        results = self._run_gates(
            manifest,
            [attempt],
            [make_attempt_precommit(manifest, attempt)],
            [],
            [],
        )
        self.assertTrue(_gate(results, "G-REL-V01-OPECLASS").passed)

        manifest_missing_logs = make_manifest(
            run_id="run_ope_propensity_missing_logs",
            ope_support_level="propensity_only",
        )
        missing_logs_results = self._run_gates(
            manifest_missing_logs,
            [],
            [],
            [],
            [],
        )
        self.assertFalse(_gate(missing_logs_results, "G-REL-V01-OPECLASS").passed)

        manifest_bad = make_manifest(run_id="run_2", ope_support_level="full_support")
        attempt_bad = make_attempt(manifest_bad, deterministic_policy=True)
        results_bad = self._run_gates(
            manifest_bad,
            [attempt_bad],
            [make_attempt_precommit(manifest_bad, attempt_bad)],
            [],
            [],
        )
        self.assertFalse(_gate(results_bad, "G-REL-V01-OPECLASS").passed)

        feedback_trace = {
            "decision_id": "pol_0002",
            "trace_kind": "feedback",
            "candidate_actions": [
                {"action_id": "FB:minimal_hint", "p": 0.7},
                {"action_id": "FB:scaffolded_hint", "p": 0.3},
            ],
            "chosen_action_id": "FB:minimal_hint",
            "chosen_action_probability": 0.7,
        }
        feedback_decision = {
            "decision_id": "pol_0002",
            "policy_domain": "other",
            "policy_version": "policy.v0.0.0",
            "rule_id": "feedback.micro.randomized",
            "scope_type": "attempt",
            "scope_id": "att_000001",
            "outcome": "applied",
            "commit_status": "committed",
            "reason_code": "feedback_experiment_arm",
            "decision_ts_utc": "2026-02-27T18:30:00Z",
            "entropy_floor_met": True,
            "min_support_met": True,
            "support_check_status": "pass",
        }

        # Deterministic routing + randomized feedback is still deterministic for routing OPE.
        manifest_mixed = make_manifest(run_id="run_3", ope_support_level="full_support")
        attempt_mixed = make_attempt(
            manifest_mixed,
            deterministic_policy=True,
            extra_decision_traces=[feedback_trace],
            extra_policy_decisions=[feedback_decision],
        )
        results_mixed = self._run_gates(
            manifest_mixed,
            [attempt_mixed],
            [make_attempt_precommit(manifest_mixed, attempt_mixed)],
            [],
            [],
        )
        self.assertFalse(_gate(results_mixed, "G-REL-V01-OPECLASS").passed)

        # Randomized routing can qualify for full_support under this v0.1 gate.
        manifest_good = make_manifest(run_id="run_4", ope_support_level="full_support")
        attempt_good = make_attempt(
            manifest_good,
            deterministic_policy=False,
            extra_decision_traces=[feedback_trace],
            extra_policy_decisions=[feedback_decision],
        )
        # Full support requires explicit routing support checks in addition to stochastic routing.
        attempt_good["policy_decisions"][0]["entropy_floor_met"] = True
        attempt_good["policy_decisions"][0]["min_support_met"] = True
        attempt_good["policy_decisions"][0]["support_check_status"] = "pass"
        attempt_good["precommit_hash"] = sha256_json(
            self.validator.precommit_projection_from_attempt(attempt_good)
        )
        results_good = self._run_gates(
            manifest_good,
            [attempt_good],
            [make_attempt_precommit(manifest_good, attempt_good)],
            [],
            [],
        )
        self.assertTrue(_gate(results_good, "G-REL-V01-OPECLASS").passed)

    def test_at_v01_8b_ope_full_support_thresholds_enforced(self) -> None:
        manifest_missing_routing = make_manifest(
            run_id="run_ope_missing_routing",
            ope_support_level="full_support",
            ope_claim_contract={
                "target_trace_kinds": ["feedback"],
                "context_axes": ["probe_family_id", "assistance_mode_derived", "evidence_channel"],
                "min_stochastic_fraction": 0.20,
                "min_candidate_probability": 0.05,
                "min_chosen_probability": 0.05,
                "min_entropy_bits": 0.0,
                "min_context_coverage_fraction": 0.50,
                "min_decisions_per_context": 1,
            },
        )
        manifest_errors = self.validator.validate_manifest(manifest_missing_routing)
        self.assertIn("manifest_full_support_requires_routing_target", manifest_errors)

        manifest_sparse = make_manifest(run_id="run_ope_sparse", ope_support_level="full_support")
        attempts_sparse = []
        precommits_sparse = []
        for idx in range(11):
            attempt = make_attempt(
                manifest_sparse,
                attempt_id=f"att_sparse_{idx:04d}",
                deterministic_policy=(idx < 10),
            )
            attempt["policy_decisions"][0]["entropy_floor_met"] = True
            attempt["policy_decisions"][0]["min_support_met"] = True
            attempt["policy_decisions"][0]["support_check_status"] = "pass"
            attempt["precommit_hash"] = sha256_json(
                self.validator.precommit_projection_from_attempt(attempt)
            )
            attempts_sparse.append(attempt)
            precommits_sparse.append(make_attempt_precommit(manifest_sparse, attempt))
        sparse_results = self._run_gates(
            manifest_sparse,
            attempts_sparse,
            precommits_sparse,
            [],
            [],
        )
        self.assertFalse(_gate(sparse_results, "G-REL-V01-OPECLASS").passed)

        manifest_low_p = make_manifest(
            run_id="run_ope_low_p",
            ope_support_level="full_support",
            ope_claim_contract={
                "target_trace_kinds": ["routing"],
                "context_axes": ["probe_family_id", "assistance_mode_derived", "evidence_channel"],
                "min_stochastic_fraction": 0.0,
                "min_candidate_probability": 0.05,
                "min_chosen_probability": 0.05,
                "min_entropy_bits": 0.0,
                "min_context_coverage_fraction": 0.0,
                "min_decisions_per_context": 1,
            },
        )
        attempt_low_p = make_attempt(manifest_low_p, deterministic_policy=False)
        attempt_low_p["decision_traces"][0]["candidate_actions"] = [
            {"action_id": "MEASURE:pf_0001", "p": 0.99},
            {"action_id": "DISCRIMINATE:pf_0002", "p": 0.01},
        ]
        attempt_low_p["decision_traces"][0]["chosen_action_id"] = "MEASURE:pf_0001"
        attempt_low_p["decision_traces"][0]["chosen_action_probability"] = 0.99
        attempt_low_p["policy_decisions"][0]["entropy_floor_met"] = True
        attempt_low_p["policy_decisions"][0]["min_support_met"] = True
        attempt_low_p["policy_decisions"][0]["support_check_status"] = "pass"
        attempt_low_p["precommit_hash"] = sha256_json(
            self.validator.precommit_projection_from_attempt(attempt_low_p)
        )
        low_p_results = self._run_gates(
            manifest_low_p,
            [attempt_low_p],
            [make_attempt_precommit(manifest_low_p, attempt_low_p)],
            [],
            [],
        )
        self.assertFalse(_gate(low_p_results, "G-REL-V01-OPECLASS").passed)

    def test_at_v01_19_prequential_integrity_enforced(self) -> None:
        manifest = make_manifest()
        attempt = make_attempt(manifest)
        precommit = make_attempt_precommit(manifest, attempt)

        missing_precommit = self._run_gates(manifest, [attempt], [], [], [])
        self.assertFalse(_gate(missing_precommit, "G-RUN-V01-PREQ").passed)
        self.assertFalse(_gate(missing_precommit, "G-MRG-V01-LEDGER").passed)

        late_precommit = clone(precommit)
        late_precommit["presented_ts_utc"] = "2026-02-27T18:30:01Z"
        late_precommit["precommit_hash"] = sha256_json(
            self.validator.precommit_projection_from_record(late_precommit)
        )
        late_results = self._run_gates(manifest, [attempt], [late_precommit], [], [])
        self.assertFalse(_gate(late_results, "G-RUN-V01-PREQ").passed)
        self.assertFalse(_gate(late_results, "G-MRG-V01-LEDGER").passed)

        posthoc_propensity_attempt = clone(attempt)
        posthoc_propensity_attempt["decision_traces"][0]["candidate_actions"] = [
            {"action_id": "MEASURE:pf_0001", "p": 0.5},
            {"action_id": "DISCRIMINATE:pf_0002", "p": 0.5},
        ]
        posthoc_propensity_attempt["decision_traces"][0]["chosen_action_probability"] = 0.5
        posthoc_propensity_attempt["precommit_hash"] = sha256_json(
            self.validator.precommit_projection_from_attempt(posthoc_propensity_attempt)
        )
        propensity_results = self._run_gates(
            manifest,
            [posthoc_propensity_attempt],
            [precommit],
            [],
            [],
        )
        self.assertFalse(_gate(propensity_results, "G-RUN-V01-PREQ").passed)
        self.assertFalse(_gate(propensity_results, "G-MRG-V01-LEDGER").passed)

        posthoc_forecast_attempt = clone(attempt)
        posthoc_forecast_attempt["residual_inputs"]["likelihood_sketch"]["predicted_observation_distribution"] = [
            {"obs_key": "SLOT(a=pass,b=fail)", "p": 0.9},
            {"obs_key": "SLOT(a=pass,b=pass)", "p": 0.05},
            {"obs_key": "SLOT(a=fail,b=fail)", "p": 0.05},
        ]
        posthoc_forecast_attempt["precommit_hash"] = sha256_json(
            self.validator.precommit_projection_from_attempt(posthoc_forecast_attempt)
        )
        forecast_results = self._run_gates(
            manifest,
            [posthoc_forecast_attempt],
            [precommit],
            [],
            [],
        )
        self.assertFalse(_gate(forecast_results, "G-RUN-V01-PREQ").passed)
        self.assertFalse(_gate(forecast_results, "G-MRG-V01-LEDGER").passed)

        # Post-hoc semantic relabeling (measurement vs learning) must fail bindings.
        relabeled_channel_attempt = clone(attempt)
        relabeled_channel_attempt["evidence_channel"] = "C_learning"
        relabeled_channel_attempt["diagnosis_update_eligibility"] = "ineligible"
        relabeled_channel_attempt["ineligibility_reason"] = "channel_not_diagnostic"
        relabeled_channel_attempt["allowed_update_partitions"] = ["learning_retention_state"]
        relabeled_channel_attempt["precommit_hash"] = sha256_json(
            self.validator.precommit_projection_from_attempt(relabeled_channel_attempt)
        )
        relabeled_channel_results = self._run_gates(
            manifest,
            [relabeled_channel_attempt],
            [precommit],
            [],
            [],
        )
        self.assertFalse(_gate(relabeled_channel_results, "G-RUN-V01-PREQ").passed)
        self.assertFalse(_gate(relabeled_channel_results, "G-MRG-V01-LEDGER").passed)

    def test_at_v01_34_precommit_intended_vs_observed_assistance_monotonic(self) -> None:
        manifest = make_manifest(run_id="run_precommit_assistance_monotonic")

        # Intended=open_book, observed=closed_book ("better than intended") is invalid.
        attempt_intended_open = make_attempt(
            manifest,
            attempt_id="att_monotonic_001",
            assistance_mode="open_book",
        )
        attempt_intended_open["evidence_channel_intended"] = "B_measurement"
        attempt_intended_open["assistance_contract_intended"] = "open_book"
        attempt_intended_open["diagnosis_update_eligibility_intended"] = "ineligible"
        attempt_intended_open["ineligibility_reason_intended"] = "assistance_mode_not_closed_book"
        attempt_intended_open["allowed_update_partitions_intended"] = ["learning_retention_state"]
        attempt_intended_open["precommit_hash"] = sha256_json(
            self.validator.precommit_projection_from_attempt(attempt_intended_open)
        )
        precommit_intended_open = make_attempt_precommit(manifest, attempt_intended_open)

        observed_better = clone(attempt_intended_open)
        observed_better["assistance_mode"] = "closed_book"
        observed_better["diagnosis_update_eligibility"] = "eligible"
        observed_better["ineligibility_reason"] = "none"
        observed_better["allowed_update_partitions"] = ["diagnosis_state"]
        observed_better["precommit_hash"] = sha256_json(
            self.validator.precommit_projection_from_attempt(observed_better)
        )
        better_results = self._run_gates(
            manifest,
            [observed_better],
            [precommit_intended_open],
            [],
            [],
        )
        self.assertFalse(_gate(better_results, "G-RUN-V01-PREQ").passed)
        self.assertFalse(_gate(better_results, "G-MRG-V01-LEDGER").passed)

        # Intended=closed_book, observed=open_book ("worse than intended") is valid.
        attempt_intended_closed = make_attempt(
            manifest,
            attempt_id="att_monotonic_002",
            assistance_mode="closed_book",
        )
        attempt_intended_closed["evidence_channel_intended"] = "B_measurement"
        attempt_intended_closed["assistance_contract_intended"] = "closed_book"
        attempt_intended_closed["diagnosis_update_eligibility_intended"] = "eligible"
        attempt_intended_closed["ineligibility_reason_intended"] = "none"
        attempt_intended_closed["allowed_update_partitions_intended"] = ["diagnosis_state"]
        attempt_intended_closed["precommit_hash"] = sha256_json(
            self.validator.precommit_projection_from_attempt(attempt_intended_closed)
        )
        precommit_intended_closed = make_attempt_precommit(manifest, attempt_intended_closed)

        observed_worse = clone(attempt_intended_closed)
        observed_worse["assistance_mode"] = "open_book"
        observed_worse["assistance_mode_derived"] = "open_book"
        observed_worse["diagnosis_update_eligibility"] = "ineligible"
        observed_worse["ineligibility_reason"] = "assistance_mode_not_closed_book"
        observed_worse["allowed_update_partitions"] = ["learning_retention_state"]
        observed_worse["precommit_hash"] = sha256_json(
            self.validator.precommit_projection_from_attempt(observed_worse)
        )
        worse_results = self._run_gates(
            manifest,
            [observed_worse],
            [precommit_intended_closed],
            [],
            [],
            telemetry_events=_telemetry_for_attempts(manifest, [observed_worse]),
        )
        self.assertTrue(_gate(worse_results, "G-RUN-V01-PREQ").passed)
        self.assertTrue(_gate(worse_results, "G-MRG-V01-LEDGER").passed)

    def test_at_v01_35_telemetry_derived_assistance_enforced(self) -> None:
        manifest = make_manifest(run_id="run_assistance_derivation_001")
        attempt = make_attempt(manifest, attempt_id="att_assist_001", assistance_mode="closed_book")
        precommit = make_attempt_precommit(manifest, attempt)
        telemetry_events = make_attempt_telemetry_events(manifest, attempt)
        telemetry_events[0]["telemetry_kind"] = "tool_call"

        results = self._run_gates(
            manifest,
            [attempt],
            [precommit],
            [],
            [],
            telemetry_events=telemetry_events,
        )
        self.assertFalse(_gate(results, "G-RUN-V01-PREQ").passed)
        self.assertFalse(_gate(results, "G-RUN-V01-REPLAYSTATE").passed)

    def test_at_v01_41_telemetry_window_completeness_enforced(self) -> None:
        manifest = make_manifest(run_id="run_telemetry_window_completeness")
        attempt = make_attempt(manifest, attempt_id="att_tel_win_001")
        precommit = make_attempt_precommit(manifest, attempt)
        telemetry_events = make_attempt_telemetry_events(manifest, attempt)
        extra_event = clone(telemetry_events[0])
        extra_event["telemetry_event_id"] = "tel_att_tel_win_001_extra"
        extra_event["payload_hash"] = "sha256:telemetry_extra"
        telemetry_events.append(extra_event)

        results = self._run_gates(
            manifest,
            [attempt],
            [precommit],
            [],
            [],
            telemetry_events=telemetry_events,
        )
        self.assertFalse(_gate(results, "G-RUN-V01-PREQ").passed)
        self.assertFalse(_gate(results, "G-MRG-V01-LEDGER").passed)

    def test_at_v01_42_telemetry_before_presented_rejected(self) -> None:
        manifest = make_manifest(run_id="run_telemetry_before_presented")
        attempt = make_attempt(manifest, attempt_id="att_tel_win_002")
        precommit = make_attempt_precommit(manifest, attempt)
        telemetry_events = make_attempt_telemetry_events(manifest, attempt)
        telemetry_events[0]["telemetry_ts_utc"] = "2026-02-27T18:29:58Z"

        results = self._run_gates(
            manifest,
            [attempt],
            [precommit],
            [],
            [],
            telemetry_events=telemetry_events,
        )
        self.assertFalse(_gate(results, "G-RUN-V01-PREQ").passed)
        self.assertFalse(_gate(results, "G-MRG-V01-LEDGER").passed)

    def test_at_v01_43_telemetry_exact_window_passes(self) -> None:
        manifest = make_manifest(run_id="run_telemetry_exact_window")
        attempt = make_attempt(manifest, attempt_id="att_tel_win_003")
        attempt["telemetry_event_ids"] = [
            "tel_att_tel_win_003_001",
            "tel_att_tel_win_003_002",
        ]
        attempt["telemetry_event_ids_intended"] = [
            "tel_att_tel_win_003_001",
            "tel_att_tel_win_003_002",
        ]
        attempt["precommit_hash"] = sha256_json(
            self.validator.precommit_projection_from_attempt(attempt)
        )
        precommit = make_attempt_precommit(manifest, attempt)
        telemetry_events = make_attempt_telemetry_events(manifest, attempt)

        results = self._run_gates(
            manifest,
            [attempt],
            [precommit],
            [],
            [],
            telemetry_events=telemetry_events,
        )
        self.assertTrue(_gate(results, "G-RUN-V01-PREQ").passed)
        self.assertTrue(_gate(results, "G-MRG-V01-LEDGER").passed)

    def test_at_v01_36_epoch_lineage_requires_migration_for_non_initial_runs(self) -> None:
        bootstrap = {
            "source_run_id": "run_prev_001",
            "source_snapshot_id": "snap_prev_001",
            "source_state_hash": "sha256:source_state_prev",
            "source_replay_fingerprint": "sha256:replay_prev",
        }
        manifest = make_manifest(
            run_id="run_epoch_002",
            timeline_id="timeline_learner_001",
            epoch_index=2,
            predecessor_run_id="run_prev_001",
            bootstrap_snapshot_ref=bootstrap,
            migration_event_id="mig_0001",
        )
        attempt = make_attempt(manifest, attempt_id="att_epoch_002_001")
        precommit = make_attempt_precommit(manifest, attempt)
        telemetry_events = make_attempt_telemetry_events(manifest, attempt)

        results = self._run_gates(
            manifest,
            [attempt],
            [precommit],
            [],
            [],
            telemetry_events=telemetry_events,
            migrations=[],
            include_future_gates=True,
        )
        self.assertFalse(_gate(results, "G-RUN-VNEXT-LINEAGE").passed)
        self.assertFalse(_gate(results, "G-MRG-V01-LEDGER").passed)

    def test_at_v01_36b_vnext_gates_not_emitted_by_default(self) -> None:
        bootstrap = {
            "source_run_id": "run_prev_001",
            "source_snapshot_id": "snap_prev_001",
            "source_state_hash": "sha256:source_state_prev",
            "source_replay_fingerprint": "sha256:replay_prev",
        }
        manifest = make_manifest(
            run_id="run_epoch_002_default_vnext",
            timeline_id="timeline_learner_001",
            epoch_index=2,
            predecessor_run_id="run_prev_001",
            bootstrap_snapshot_ref=bootstrap,
            migration_event_id="mig_0001",
        )
        attempt = make_attempt(manifest, attempt_id="att_epoch_002_default_vnext_001")
        precommit = make_attempt_precommit(manifest, attempt)
        telemetry_events = make_attempt_telemetry_events(manifest, attempt)

        results = self._run_gates(
            manifest,
            [attempt],
            [precommit],
            [],
            [],
            telemetry_events=telemetry_events,
            migrations=[],
        )
        gate_ids = {r.gate_id for r in results}
        self.assertNotIn("G-RUN-VNEXT-LINEAGE", gate_ids)
        self.assertNotIn("G-RUN-VNEXT-MIGSEQ", gate_ids)

    def test_at_v01_37_migration_must_precede_precommits_in_epoch_runs(self) -> None:
        bootstrap = {
            "source_run_id": "run_prev_002",
            "source_snapshot_id": "snap_prev_002",
            "source_state_hash": "sha256:source_state_prev_002",
            "source_replay_fingerprint": "sha256:replay_prev_002",
        }
        manifest = make_manifest(
            run_id="run_epoch_003",
            timeline_id="timeline_learner_001",
            epoch_index=2,
            predecessor_run_id="run_prev_002",
            bootstrap_snapshot_ref=bootstrap,
            migration_event_id="mig_0002",
        )
        migration = make_state_migration(manifest)
        attempt = make_attempt(manifest, attempt_id="att_epoch_003_001")
        precommit = make_attempt_precommit(manifest, attempt)
        telemetry_events = make_attempt_telemetry_events(manifest, attempt)

        with tempfile.TemporaryDirectory() as tmp:
            store = LedgerStore(tmp)
            store.put_manifest(manifest)
            # Intentionally append precommit before migration to violate sequencing.
            store.append_attempt_precommit(precommit)
            store.append_state_migration(migration)
            for telemetry_event in telemetry_events:
                store.append_attempt_telemetry(telemetry_event)
            store.append_attempt(attempt)

            results = self._run_gates(
                manifest,
                [attempt],
                [precommit],
                [],
                [],
                events=store.get_events(manifest["run_id"]),
                telemetry_events=telemetry_events,
                migrations=[migration],
                include_future_gates=True,
            )
            self.assertFalse(_gate(results, "G-RUN-VNEXT-MIGSEQ").passed)
            self.assertFalse(_gate(results, "G-RUN-V01-REPLAYSTATE").passed)

    def test_at_v01_38_timeline_replay_across_epochs(self) -> None:
        timeline_id = "timeline_learner_001"
        manifest_epoch1 = make_manifest(
            run_id="run_tl_001",
            timeline_id=timeline_id,
            epoch_index=1,
        )
        attempt_epoch1 = make_attempt(manifest_epoch1, attempt_id="att_tl_001")
        precommit_epoch1 = make_attempt_precommit(manifest_epoch1, attempt_epoch1)
        telemetry_epoch1 = make_attempt_telemetry_events(manifest_epoch1, attempt_epoch1)

        bootstrap = {
            "source_run_id": manifest_epoch1["run_id"],
            "source_snapshot_id": "__genesis__",
            "source_state_hash": "sha256:source_state_tl",
            "source_replay_fingerprint": manifest_epoch1["replay_fingerprint"],
        }
        manifest_epoch2 = make_manifest(
            run_id="run_tl_002",
            timeline_id=timeline_id,
            epoch_index=2,
            predecessor_run_id=manifest_epoch1["run_id"],
            bootstrap_snapshot_ref=bootstrap,
            migration_event_id="mig_tl_002",
        )
        migration_epoch2 = make_state_migration(manifest_epoch2)
        attempt_epoch2 = make_attempt(manifest_epoch2, attempt_id="att_tl_002")
        precommit_epoch2 = make_attempt_precommit(manifest_epoch2, attempt_epoch2)
        telemetry_epoch2 = make_attempt_telemetry_events(manifest_epoch2, attempt_epoch2)

        with tempfile.TemporaryDirectory() as tmp:
            store = LedgerStore(tmp)
            store.put_manifest(manifest_epoch1)
            store.put_manifest(manifest_epoch2)

            store.append_attempt_precommit(precommit_epoch1)
            for telemetry_event in telemetry_epoch1:
                store.append_attempt_telemetry(telemetry_event)
            store.append_attempt(attempt_epoch1)

            store.append_state_migration(migration_epoch2)
            store.append_attempt_precommit(precommit_epoch2)
            for telemetry_event in telemetry_epoch2:
                store.append_attempt_telemetry(telemetry_event)
            store.append_attempt(attempt_epoch2)

            timeline_result = self.replay.replay_timeline(
                timeline_id,
                [manifest_epoch1["run_id"], manifest_epoch2["run_id"]],
                store,
            )
            self.assertEqual(timeline_result.errors, [])
            self.assertEqual(len(timeline_result.run_results), 2)

    def test_at_v01_20_event_order_uses_ledger_sequence(self) -> None:
        manifest = make_manifest(run_id="run_event_order")
        attempt = make_attempt(
            manifest,
            attempt_id="att_order_001",
            allowed_update_partitions=["diagnosis_state", "learning_retention_state"],
        )
        precommit = make_attempt_precommit(manifest, attempt)

        state0 = {"diagnosis_state": {}, "learning_retention_state": {}}
        state1 = {"diagnosis_state": {}, "learning_retention_state": {"exposure_score": 1.0}}
        state2 = {"diagnosis_state": {}, "learning_retention_state": {"exposure_score": 2.0}}

        update_z = make_state_update(
            manifest,
            update_id="upd_z",
            source_attempt_id=attempt["attempt_id"],
            target_partition="learning_retention_state",
        )
        update_z["update_ts_utc"] = "2026-02-27T18:35:00Z"
        update_z["state_patch"]["path"] = "exposure_score"
        update_z["state_patch"]["value"] = 1.0
        update_z["pre_state_hash"] = sha256_json(state0)
        update_z["post_state_hash"] = sha256_json(state1)

        update_a = make_state_update(
            manifest,
            update_id="upd_a",
            source_attempt_id=attempt["attempt_id"],
            target_partition="learning_retention_state",
        )
        update_a["update_ts_utc"] = "2026-02-27T18:35:00Z"
        update_a["state_patch"]["path"] = "exposure_score"
        update_a["state_patch"]["value"] = 2.0
        update_a["pre_state_hash"] = sha256_json(state1)
        update_a["post_state_hash"] = sha256_json(state2)

        snapshot = make_state_snapshot(manifest, snapshot_id="snap_order_001")
        snapshot["state_payload"] = state2
        snapshot["state_hash"] = sha256_json(state2)
        snapshot["source_attempt_ids"] = [attempt["attempt_id"]]

        with tempfile.TemporaryDirectory() as tmp:
            store = LedgerStore(tmp)
            store.put_manifest(manifest)
            store.append_attempt_precommit(precommit)
            for telemetry_event in make_attempt_telemetry_events(manifest, attempt):
                store.append_attempt_telemetry(telemetry_event)
            store.append_attempt(attempt)
            # Append z then a; lexicographic event-id order is opposite.
            store.append_state_update(update_z)
            store.append_state_update(update_a)
            store.append_state_snapshot(snapshot)

            result = self.replay.replay_run(manifest["run_id"], store)
            self.assertEqual(result.errors, [])
            self.assertEqual(result.final_state_hash, sha256_json(state2))

    def test_at_v01_21_invalid_event_sequence_rejected(self) -> None:
        manifest = make_manifest(run_id="run_event_corrupt")
        attempt = make_attempt(manifest, attempt_id="att_corrupt_001")
        precommit = make_attempt_precommit(manifest, attempt)

        with tempfile.TemporaryDirectory() as tmp:
            store = LedgerStore(tmp)
            store.put_manifest(manifest)
            store.append_attempt_precommit(precommit)
            for telemetry_event in make_attempt_telemetry_events(manifest, attempt):
                store.append_attempt_telemetry(telemetry_event)
            store.append_attempt(attempt)

            # Corrupt total order: duplicate ledger sequence number.
            events = store.events_by_run[manifest["run_id"]]
            self.assertGreaterEqual(len(events), 2)
            events[1]["ledger_sequence_no"] = events[0]["ledger_sequence_no"]

            result = self.replay.replay_run(manifest["run_id"], store)
            self.assertTrue(any("event_order:duplicate_sequence" in e for e in result.errors))

    def test_at_v01_21b_empty_event_ledger_rejected(self) -> None:
        manifest = make_manifest(run_id="run_event_empty")
        with tempfile.TemporaryDirectory() as tmp:
            store = LedgerStore(tmp)
            store.put_manifest(manifest)
            result = self.replay.replay_run(manifest["run_id"], store)
            self.assertTrue(any("event_order:empty_event_ledger" in e for e in result.errors))

    def test_at_v01_22_validator_corruption_hardening(self) -> None:
        manifest = make_manifest()
        attempt = make_attempt(manifest)
        precommit = make_attempt_precommit(manifest, attempt)
        update = make_state_update(manifest)

        malformed_attempt = clone(attempt)
        malformed_attempt["policy_decisions"] = [None]
        malformed_attempt["decision_traces"][0]["candidate_actions"] = [None]
        malformed_attempt["decision_traces"][0]["chosen_action_probability"] = "0.7"
        malformed_attempt["residual_inputs"]["provenance"] = []
        malformed_attempt["observation"] = []

        malformed_precommit = clone(precommit)
        malformed_precommit["policy_decisions"] = [None]
        malformed_precommit["decision_traces"][0]["candidate_actions"] = [None]
        malformed_precommit["likelihood_sketch"] = []

        malformed_update = clone(update)
        malformed_update["state_patch"] = []
        malformed_update["applied_update_multiplier"] = "not_a_number"

        malformed_manifest = []

        attempt_errors = self.validator.validate_attempt(malformed_attempt, manifest)
        precommit_errors = self.validator.validate_attempt_precommit(malformed_precommit, manifest)
        update_errors = self.validator.validate_state_update_event(malformed_update)
        manifest_errors = self.validator.validate_manifest(malformed_manifest)  # type: ignore[arg-type]

        self.assertTrue(isinstance(attempt_errors, list) and len(attempt_errors) > 0)
        self.assertTrue(isinstance(precommit_errors, list) and len(precommit_errors) > 0)
        self.assertTrue(isinstance(update_errors, list) and len(update_errors) > 0)
        self.assertTrue(isinstance(manifest_errors, list) and len(manifest_errors) > 0)
        self.assertIn("attempt_decision_trace[0]_candidate_not_object", attempt_errors)
        self.assertIn("attempt_policy_decision_row_not_object[0]", attempt_errors)
        self.assertIn("attempt_decision_trace[0]_candidate_not_object", precommit_errors)
        self.assertIn("attempt_likelihood_sketch_not_object", precommit_errors)
        self.assertIn("state_update_state_patch_not_object", update_errors)
        self.assertIn("manifest_record_not_object", manifest_errors)

    def test_at_v01_22b_event_ledger_integrity_enforced(self) -> None:
        manifest = make_manifest(run_id="run_event_ledger_integrity")
        attempt = make_attempt(manifest, attempt_id="att_event_ledger_integrity")
        precommit = make_attempt_precommit(manifest, attempt)
        telemetry_events = make_attempt_telemetry_events(manifest, attempt)

        with tempfile.TemporaryDirectory() as tmp:
            store = LedgerStore(tmp)
            store.put_manifest(manifest)
            store.append_attempt_precommit(precommit)
            for telemetry_event in telemetry_events:
                store.append_attempt_telemetry(telemetry_event)
            store.append_attempt(attempt)
            events = store.get_events(manifest["run_id"])
            self.assertGreaterEqual(len(events), 2)
            # Corrupt payload/header run binding on one event.
            events[1]["payload"]["run_id"] = "run_payload_mismatch"

            results = self._run_gates(
                manifest,
                [attempt],
                [precommit],
                [],
                [],
                events=events,
                telemetry_events=telemetry_events,
            )
            self.assertFalse(_gate(results, "G-RUN-V01-EVORD").passed)
            self.assertFalse(_gate(results, "G-RUN-V01-EVTBIND").passed)

    def test_at_v01_22d_empty_event_ledger_fails_event_runtime_gates(self) -> None:
        manifest = make_manifest(run_id="run_event_ledger_empty_gates")
        results = self._run_gates(
            manifest,
            [],
            [],
            [],
            [],
            events=[],
            telemetry_events=[],
        )
        self.assertFalse(_gate(results, "G-RUN-V01-EVORD").passed)
        self.assertFalse(_gate(results, "G-RUN-V01-EVTBIND").passed)
        self.assertFalse(_gate(results, "G-RUN-V01-REPLAYSTATE").passed)

    def test_at_v01_22c_replay_conflicting_duplicate_ids_rejected(self) -> None:
        manifest = make_manifest(run_id="run_replay_duplicate_conflicts")
        attempt = make_attempt(manifest, attempt_id="att_dup_conflict_001")
        precommit = make_attempt_precommit(manifest, attempt)
        telemetry_events = make_attempt_telemetry_events(manifest, attempt)

        with tempfile.TemporaryDirectory() as tmp:
            store = LedgerStore(tmp)
            store.put_manifest(manifest)
            store.append_attempt_precommit(precommit)
            for telemetry_event in telemetry_events:
                store.append_attempt_telemetry(telemetry_event)
            store.append_attempt(attempt)

            conflicting_attempt = clone(attempt)
            conflicting_attempt["observation"]["slot_pattern"] = "SLOT(a=pass,b=pass)"
            conflicting_attempt["precommit_hash"] = sha256_json(
                self.validator.precommit_projection_from_attempt(conflicting_attempt)
            )
            store.events_by_run[manifest["run_id"]].append(
                {
                    "event_id": "evt_attempt_observed_retry_conflicting",
                    "event_type": "attempt_observed",
                    "event_ts_utc": attempt["attempt_ts_utc"],
                    "event_written_ts_utc": "2099-01-01T00:00:00.000000Z",
                    "run_id": manifest["run_id"],
                    "session_id": attempt["session_id"],
                    "causal_refs": [],
                    "payload": conflicting_attempt,
                    "ledger_sequence_no": 9999,
                }
            )

            update = make_state_update(
                manifest,
                update_id="upd_dup_conflict_001",
                source_attempt_id=attempt["attempt_id"],
            )
            store.append_state_update(update)
            conflicting_update = clone(update)
            conflicting_update["state_patch"]["value"] = 0.9
            conflicting_update["post_state_hash"] = "sha256:post_conflict"
            store.events_by_run[manifest["run_id"]].append(
                {
                    "event_id": "evt_state_update_retry_conflicting",
                    "event_type": "state_update",
                    "event_ts_utc": update["update_ts_utc"],
                    "event_written_ts_utc": "2099-01-01T00:00:01.000000Z",
                    "run_id": manifest["run_id"],
                    "session_id": update["session_id"],
                    "causal_refs": [],
                    "payload": conflicting_update,
                    "ledger_sequence_no": 10000,
                }
            )

            replay_result = self.replay.replay_run(manifest["run_id"], store)
            self.assertTrue(
                any("duplicate_attempt_id_conflicting_payload" in e for e in replay_result.errors)
            )
            self.assertTrue(
                any("duplicate_update_id_conflicting_payload" in e for e in replay_result.errors)
            )

    def test_at_v01_23_trace_kind_ontology_and_manifest_c14n_version(self) -> None:
        manifest = make_manifest()
        invalid_trace_kind = make_attempt(manifest)
        invalid_trace_kind["decision_traces"][0]["trace_kind"] = "freeform_unknown_kind"
        errors = self.validator.validate_attempt(invalid_trace_kind, manifest)
        self.assertIn(
            "attempt_decision_trace_trace_kind_unknown:freeform_unknown_kind",
            errors,
        )

        bad_manifest = make_manifest(run_id="run_bad_c14n")
        bad_manifest["json_canonicalization_version"] = "bad_version"
        manifest_errors = self.validator.validate_manifest(bad_manifest)
        self.assertIn("manifest_json_canonicalization_version_invalid", manifest_errors)

    def test_at_v01_23b_trace_policy_domain_alignment_enforced(self) -> None:
        manifest = make_manifest(run_id="run_trace_policy_alignment")
        attempt = make_attempt(manifest, attempt_id="att_trace_policy_alignment")
        attempt["policy_decisions"][0]["policy_domain"] = "other"
        attempt["precommit_hash"] = sha256_json(
            self.validator.precommit_projection_from_attempt(attempt)
        )
        errors = self.validator.validate_attempt(attempt, manifest)
        self.assertIn("attempt_decision_trace_policy_domain_mismatch:pol_0001", errors)

        precommit = make_attempt_precommit(manifest, attempt)
        precommit_errors = self.validator.validate_attempt_precommit(precommit, manifest)
        self.assertIn(
            "attempt_precommit_decision_trace_policy_domain_mismatch:pol_0001",
            precommit_errors,
        )

    def test_at_v01_23c_candidate_action_id_uniqueness_enforced(self) -> None:
        manifest = make_manifest(run_id="run_candidate_action_duplicates")
        attempt = make_attempt(manifest, attempt_id="att_candidate_action_dup")
        attempt["decision_traces"][0]["candidate_actions"] = [
            {"action_id": "MEASURE:pf_0001", "p": 0.5},
            {"action_id": "MEASURE:pf_0001", "p": 0.5},
        ]
        attempt["decision_traces"][0]["chosen_action_probability"] = 0.5
        attempt["precommit_hash"] = sha256_json(
            self.validator.precommit_projection_from_attempt(attempt)
        )
        errors = self.validator.validate_attempt(attempt, manifest)
        self.assertIn(
            "attempt_decision_trace[0]_candidate_action_id_duplicate:MEASURE:pf_0001",
            errors,
        )

    def test_at_v01_24_provenance_snapshot_reference_integrity(self) -> None:
        manifest = make_manifest()

        # Missing provenance snapshot should fail runtime/merge provenance gates.
        missing_ref_attempt = make_attempt(
            manifest,
            residual_provenance_overrides={"state_snapshot_id": "snap_missing"},
        )
        missing_ref_precommit = make_attempt_precommit(manifest, missing_ref_attempt)
        missing_ref_results = self._run_gates(
            manifest,
            [missing_ref_attempt],
            [missing_ref_precommit],
            [],
            [],
        )
        self.assertFalse(_gate(missing_ref_results, "G-RUN-V01-PROVREF").passed)
        self.assertFalse(_gate(missing_ref_results, "G-MRG-V01-LEDGER").passed)

        # Referencing a snapshot that exists but is timestamped after attempt should fail.
        late_snapshot_attempt = make_attempt(
            manifest,
            attempt_id="att_late_snapshot",
            residual_provenance_overrides={"state_snapshot_id": "snap_late_001"},
        )
        late_snapshot_precommit = make_attempt_precommit(manifest, late_snapshot_attempt)
        late_snapshot = make_state_snapshot(manifest, snapshot_id="snap_late_001")
        late_snapshot["snapshot_ts_utc"] = "2026-02-27T18:31:00Z"
        late_results = self._run_gates(
            manifest,
            [late_snapshot_attempt],
            [late_snapshot_precommit],
            [late_snapshot],
            [],
        )
        self.assertFalse(_gate(late_results, "G-RUN-V01-PROVREF").passed)
        self.assertFalse(_gate(late_results, "G-MRG-V01-LEDGER").passed)

    def test_at_v01_25_identity_integrity_enforced(self) -> None:
        manifest = make_manifest()
        attempt = make_attempt(manifest)
        attempt["run_id"] = "other_run"
        attempt_errors = self.validator.validate_attempt(attempt, manifest)
        self.assertIn("attempt_run_id_mismatch_manifest", attempt_errors)

        precommit = make_attempt_precommit(manifest, make_attempt(manifest))
        precommit["run_id"] = "other_run"
        precommit_errors = self.validator.validate_attempt_precommit(precommit, manifest)
        self.assertIn("attempt_precommit_run_id_mismatch_manifest", precommit_errors)

        snapshot = make_state_snapshot(manifest)
        snapshot["run_id"] = "other_run"
        snapshot_errors = self.validator.validate_state_snapshot(snapshot, manifest)
        self.assertIn("state_snapshot_run_id_mismatch_manifest", snapshot_errors)

        bad_ids = make_attempt(manifest)
        bad_ids["attempt_id"] = ""
        bad_ids["precommit_hash"] = sha256_json(self.validator.precommit_projection_from_attempt(bad_ids))
        bad_id_errors = self.validator.validate_attempt(bad_ids, manifest)
        self.assertIn("attempt_attempt_id_invalid", bad_id_errors)

    def test_at_v01_26_timestamp_contract_enforced(self) -> None:
        manifest = make_manifest()
        bad_manifest = make_manifest(run_id="run_bad_ts_manifest")
        bad_manifest["run_started_at_utc"] = "2026/02/27 18:15:00"
        self.assertIn("manifest_run_started_at_utc_invalid", self.validator.validate_manifest(bad_manifest))

        bad_attempt = make_attempt(manifest)
        bad_attempt["attempt_ts_utc"] = "not_a_timestamp"
        bad_attempt["precommit_hash"] = sha256_json(self.validator.precommit_projection_from_attempt(bad_attempt))
        attempt_errors = self.validator.validate_attempt(bad_attempt, manifest)
        self.assertIn("attempt_attempt_ts_utc_invalid", attempt_errors)

        bad_precommit = make_attempt_precommit(manifest, make_attempt(manifest))
        bad_precommit["presented_ts_utc"] = "bad_ts"
        bad_precommit["precommit_hash"] = sha256_json(
            self.validator.precommit_projection_from_record(bad_precommit)
        )
        precommit_errors = self.validator.validate_attempt_precommit(bad_precommit, manifest)
        self.assertIn("attempt_precommit_presented_ts_utc_invalid", precommit_errors)

        bad_policy_ts = make_attempt(manifest)
        bad_policy_ts["policy_decisions"][0]["decision_ts_utc"] = "2026-02-27 18:30:00"
        bad_policy_ts["precommit_hash"] = sha256_json(
            self.validator.precommit_projection_from_attempt(bad_policy_ts)
        )
        policy_ts_errors = self.validator.validate_attempt(bad_policy_ts, manifest)
        self.assertIn("attempt_policy_decision_decision_ts_utc_invalid[0]", policy_ts_errors)

    def test_at_v01_27_residual_nested_contract_enforced(self) -> None:
        manifest = make_manifest()
        missing_primitive = make_attempt(manifest)
        del missing_primitive["residual_inputs"]["primitive_inputs"]["schema_invalid"]
        missing_primitive["precommit_hash"] = sha256_json(
            self.validator.precommit_projection_from_attempt(missing_primitive)
        )
        errors = self.validator.validate_attempt(missing_primitive, manifest)
        self.assertIn("attempt_residual_primitive_inputs_missing:schema_invalid", errors)

        bad_derived = make_attempt(manifest)
        bad_derived["residual_inputs"]["derived_inputs"]["max_hypothesis_likelihood"] = "0.72"
        bad_derived["precommit_hash"] = sha256_json(
            self.validator.precommit_projection_from_attempt(bad_derived)
        )
        errors = self.validator.validate_attempt(bad_derived, manifest)
        self.assertIn("attempt_residual_derived_max_hypothesis_likelihood_not_numeric", errors)

    def test_at_v01_28_duplicate_bundle_records_fail_merge_gate(self) -> None:
        manifest = make_manifest()
        attempt = make_attempt(manifest)
        precommit = make_attempt_precommit(manifest, attempt)
        update = make_state_update(manifest, source_attempt_id=attempt["attempt_id"])
        snapshot = make_state_snapshot(manifest)

        results = self._run_gates(
            manifest,
            [attempt, clone(attempt)],
            [precommit],
            [snapshot],
            [update],
        )
        self.assertFalse(_gate(results, "G-MRG-V01-LEDGER").passed)

    def test_at_v01_29_precommit_hash_list_order_is_canonicalized(self) -> None:
        manifest = make_manifest()
        feedback_trace = {
            "decision_id": "pol_0002",
            "trace_kind": "feedback",
            "candidate_actions": [
                {"action_id": "FB:z", "p": 0.4},
                {"action_id": "FB:a", "p": 0.6},
            ],
            "chosen_action_id": "FB:a",
            "chosen_action_probability": 0.6,
        }
        feedback_decision = {
            "decision_id": "pol_0002",
            "policy_domain": "other",
            "policy_version": manifest["policy_version"],
            "rule_id": "feedback.rule",
            "scope_type": "attempt",
            "scope_id": "att_000001",
            "outcome": "applied",
            "commit_status": "committed",
            "reason_code": "feedback",
            "decision_ts_utc": "2026-02-27T18:30:00Z",
            "entropy_floor_met": None,
            "min_support_met": None,
            "support_check_status": "not_applicable",
        }
        attempt = make_attempt(
            manifest,
            deterministic_policy=False,
            extra_decision_traces=[feedback_trace],
            extra_policy_decisions=[feedback_decision],
        )
        original_hash = attempt["precommit_hash"]
        attempt["decision_traces"] = list(reversed(attempt["decision_traces"]))
        attempt["decision_traces"][0]["candidate_actions"] = list(
            reversed(attempt["decision_traces"][0]["candidate_actions"])
        )
        attempt["policy_decisions"] = list(reversed(attempt["policy_decisions"]))
        self.assertEqual(
            original_hash,
            sha256_json(self.validator.precommit_projection_from_attempt(attempt)),
        )
        self.assertEqual(self.validator.validate_attempt(attempt, manifest), [])

    def test_at_v01_30_candidate_probability_non_numeric_hardened(self) -> None:
        manifest = make_manifest()
        malformed = make_attempt(manifest)
        malformed["decision_traces"][0]["candidate_actions"] = [
            {"action_id": "MEASURE:pf_0001", "p": "bad"},
        ]
        malformed["precommit_hash"] = sha256_json(
            self.validator.precommit_projection_from_attempt(malformed)
        )
        errors = self.validator.validate_attempt(malformed, manifest)
        self.assertIn("attempt_decision_trace[0]_candidate_probability_invalid", errors)
        self.assertFalse(any(e.endswith("_internal_exception") for e in errors))

    def test_at_v01_31_update_snapshot_ref_integrity_enforced(self) -> None:
        manifest = make_manifest()
        attempt = make_attempt(manifest)
        precommit = make_attempt_precommit(manifest, attempt)
        bad_update = make_state_update(
            manifest,
            source_attempt_id=attempt["attempt_id"],
        )
        bad_update["snapshot_id"] = "unknown_snapshot_ref"

        results = self._run_gates(
            manifest,
            [attempt],
            [precommit],
            [],
            [bad_update],
        )
        self.assertFalse(_gate(results, "G-RUN-V01-UPDSNAPREF").passed)
        self.assertFalse(_gate(results, "G-MRG-V01-LEDGER").passed)

    def test_at_v01_32_gate_runner_uses_event_sequence_for_replaystate(self) -> None:
        manifest = make_manifest(run_id="run_gate_event_seq")
        attempt = make_attempt(
            manifest,
            attempt_id="att_seq_001",
            allowed_update_partitions=["diagnosis_state", "learning_retention_state"],
        )
        precommit = make_attempt_precommit(manifest, attempt)

        state0 = {"diagnosis_state": {}, "learning_retention_state": {}}
        state1 = {"diagnosis_state": {}, "learning_retention_state": {"exposure_score": 1.0}}
        state2 = {"diagnosis_state": {}, "learning_retention_state": {"exposure_score": 2.0}}

        update1 = make_state_update(
            manifest,
            update_id="upd_seq_1",
            source_attempt_id=attempt["attempt_id"],
            target_partition="learning_retention_state",
        )
        update1["state_patch"]["path"] = "exposure_score"
        update1["state_patch"]["value"] = 1.0
        update1["pre_state_hash"] = sha256_json(state0)
        update1["post_state_hash"] = sha256_json(state1)

        update2 = make_state_update(
            manifest,
            update_id="upd_seq_2",
            source_attempt_id=attempt["attempt_id"],
            target_partition="learning_retention_state",
        )
        update2["state_patch"]["path"] = "exposure_score"
        update2["state_patch"]["value"] = 2.0
        update2["pre_state_hash"] = sha256_json(state1)
        update2["post_state_hash"] = sha256_json(state2)

        snapshot1 = make_state_snapshot(manifest, snapshot_id="snap_seq_1")
        snapshot1["state_payload"] = state1
        snapshot1["state_hash"] = sha256_json(state1)
        snapshot1["snapshot_ts_utc"] = "2026-02-27T18:40:00Z"

        snapshot2 = make_state_snapshot(manifest, snapshot_id="snap_seq_2")
        snapshot2["state_payload"] = state2
        snapshot2["state_hash"] = sha256_json(state2)
        snapshot2["snapshot_ts_utc"] = "2026-02-27T18:20:00Z"

        with tempfile.TemporaryDirectory() as tmp:
            store = LedgerStore(tmp)
            store.put_manifest(manifest)
            store.append_attempt_precommit(precommit)
            for telemetry_event in make_attempt_telemetry_events(manifest, attempt):
                store.append_attempt_telemetry(telemetry_event)
            store.append_attempt(attempt)
            store.append_state_update(update1)
            store.append_state_snapshot(snapshot1)
            store.append_state_update(update2)
            store.append_state_snapshot(snapshot2)

            results = self._run_gates(
                manifest,
                [attempt],
                [precommit],
                [snapshot1, snapshot2],
                [update1, update2],
                events=store.get_events(manifest["run_id"]),
            )
            self.assertTrue(_gate(results, "G-RUN-V01-EVORD").passed)
            self.assertTrue(_gate(results, "G-RUN-V01-REPLAYSTATE").passed)

    def test_at_v01_33_evord_requires_events_input(self) -> None:
        manifest = make_manifest(run_id="run_evord_requires_events")
        attempt = make_attempt(manifest)
        precommit = make_attempt_precommit(manifest, attempt)
        update = make_state_update(manifest, source_attempt_id=attempt["attempt_id"])
        snapshot = make_state_snapshot(manifest)

        with self.assertRaisesRegex(ValueError, "events_required_for_gate_evaluation"):
            self._run_gates(
                manifest,
                [attempt],
                [precommit],
                [snapshot],
                [update],
                events=None,
            )

    def test_at_v01_39_schema_version_dispatch_and_forward_additive_fields(self) -> None:
        manifest = make_manifest()
        self.assertEqual(self.validator.validate_manifest(manifest), [])

        bad_manifest = clone(manifest)
        bad_manifest["schema_version"] = "9.9.9"
        manifest_errors = self.validator.validate_manifest(bad_manifest)
        self.assertIn("manifest_schema_version_unsupported:9.9.9", manifest_errors)

        attempt = make_attempt(manifest)
        attempt["future_optional_field"] = {"new_axis": "value"}
        self.assertEqual(self.validator.validate_attempt(attempt, manifest), [])

        bad_attempt = clone(attempt)
        bad_attempt["schema_version"] = "9.9.9"
        bad_attempt_errors = self.validator.validate_attempt(bad_attempt, manifest)
        self.assertIn("attempt_schema_version_unsupported:9.9.9", bad_attempt_errors)

    def test_at_v01_40_replay_normalization_and_schema_reject(self) -> None:
        manifest = make_manifest(run_id="run_schema_replay_norm")
        normalized_manifest, norm_errors = self.validator.normalize_record_for_replay("manifest", manifest)
        self.assertEqual(norm_errors, [])
        assert normalized_manifest is not None
        self.assertEqual(normalized_manifest["schema_version"], "0.1.0")

        attempt = make_attempt(manifest)
        precommit = make_attempt_precommit(manifest, attempt)
        bad_attempt = clone(attempt)
        bad_attempt["attempt_id"] = "att_bad_schema_replay"
        bad_attempt["schema_version"] = "9.9.9"
        bad_attempt["telemetry_event_ids"] = ["tel_att_bad_schema_replay_001"]
        bad_attempt["telemetry_event_ids_intended"] = ["tel_att_bad_schema_replay_001"]
        bad_attempt["precommit_event_id"] = "pre_att_bad_schema_replay"
        bad_attempt["precommit_hash"] = sha256_json(
            self.validator.precommit_projection_from_attempt(bad_attempt)
        )
        bad_precommit = make_attempt_precommit(manifest, bad_attempt)
        bad_precommit["precommit_event_id"] = bad_attempt["precommit_event_id"]
        bad_precommit["attempt_id"] = bad_attempt["attempt_id"]
        bad_precommit["precommit_hash"] = bad_attempt["precommit_hash"]

        with tempfile.TemporaryDirectory() as tmp:
            store = LedgerStore(tmp)
            store.put_manifest(manifest)
            store.append_attempt_precommit(precommit)
            for telemetry_event in make_attempt_telemetry_events(manifest, attempt):
                store.append_attempt_telemetry(telemetry_event)
            store.append_attempt(attempt)
            store.append_attempt_precommit(bad_precommit)
            for telemetry_event in make_attempt_telemetry_events(manifest, bad_attempt):
                store.append_attempt_telemetry(telemetry_event)
            store.append_attempt(bad_attempt)
            replay_result = self.replay.replay_run(manifest["run_id"], store)
            self.assertTrue(
                any("attempt_schema_version_unsupported:9.9.9" in e for e in replay_result.errors)
            )

    def test_at_v01_44_strict_numeric_helpers_are_enforced(self) -> None:
        manifest = make_manifest(run_id="run_strict_numeric_enforcement")
        bad_manifest = clone(manifest)
        bad_manifest["epoch_index"] = True
        manifest_errors = self.validator.validate_manifest(bad_manifest)
        self.assertIn("manifest_epoch_index_invalid", manifest_errors)

        bad_attempt = make_attempt(manifest, attempt_id="att_strict_numeric_001")
        bad_attempt["residual_inputs"]["primitive_inputs"]["parsing_confidence"] = True
        bad_attempt["precommit_hash"] = sha256_json(
            self.validator.precommit_projection_from_attempt(bad_attempt)
        )
        bad_attempt["precommit_envelope_hash"] = sha256_json(
            self.validator.precommit_envelope_projection_from_attempt(bad_attempt)
        )
        attempt_errors = self.validator.validate_attempt(bad_attempt, manifest)
        self.assertIn("attempt_residual_primitive_parsing_confidence_invalid", attempt_errors)

        bad_contract_manifest = make_manifest(run_id="run_bad_ope_numeric")
        bad_contract_manifest["ope_claim_contract"]["min_candidate_probability"] = True
        contract_errors = self.validator.validate_manifest(bad_contract_manifest)
        self.assertIn(
            "manifest_ope_claim_contract_min_candidate_probability_not_numeric",
            contract_errors,
        )

    def test_at_v01_45_numeric_typecheck_no_raw_isinstance_patterns(self) -> None:
        root = Path(__file__).resolve().parents[1]
        targets = [
            root / "forge_v01" / "contract_validator.py",
            root / "forge_v01" / "audit_queries.py",
            root / "forge_v01" / "replay_engine.py",
        ]
        for path in targets:
            for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
                stripped = line.strip()
                if stripped.startswith("#"):
                    continue
                if "is_strict_" in stripped or "is_probability(" in stripped:
                    continue
                if "isinstance(" in stripped and "(int, float)" in stripped:
                    self.fail(f"forbidden raw numeric isinstance tuple at {path}:{line_no}")
                if "isinstance(" in stripped and ", int)" in stripped:
                    self.fail(f"forbidden raw numeric isinstance int at {path}:{line_no}")


if __name__ == "__main__":
    unittest.main()
