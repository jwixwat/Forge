"""Test fixtures for v0.1 acceptance tests."""

from __future__ import annotations

from copy import deepcopy

from forge_v01.constants import (
    DIAGNOSTIC_EVIDENCE_CHANNELS,
    GENESIS_SNAPSHOT_ID,
    SAFE_MODE_POLICY_BUNDLE_HASHES,
)
from forge_v01.utils import sha256_json


def make_manifest(
    run_id: str = "run_2026_02_27_0001",
    ope_support_level: str = "propensity_only",
    ope_claim_contract: dict | None = None,
    timeline_id: str = "timeline_learner_001",
    epoch_index: int = 1,
    predecessor_run_id: str | None = None,
    bootstrap_snapshot_ref: dict | None = None,
    migration_event_id: str | None = None,
) -> dict:
    manifest = {
        "schema_version": "0.0.0",
        "run_id": run_id,
        "timeline_id": timeline_id,
        "epoch_index": epoch_index,
        "predecessor_run_id": predecessor_run_id,
        "bootstrap_snapshot_ref": bootstrap_snapshot_ref,
        "migration_event_id": migration_event_id,
        "run_started_at_utc": "2026-02-27T18:15:00Z",
        "content_ir_version": "content.v2026.02.27",
        "grader_version": "grader.v0.3.0",
        "sensor_model_version": "sensor.v0.1.0",
        "policy_version": "policy.v0.0.0",
        "engine_build_version": "engine.v0.0.0",
        "prompt_bundle_version": "prompt.v0.0.0",
        "residual_formula_version": "residual.v0.6.0",
        "obs_encoder_version": "obsenc.v0.1.0",
        "hypothesis_space_hash": "hyp_hash_001",
        "decision_rng_version": "rng.v0.1.0",
        "json_canonicalization_version": "forge_json_c14n_v1",
        "ope_support_level": ope_support_level,
        "ope_claim_contract": (
            deepcopy(ope_claim_contract)
            if isinstance(ope_claim_contract, dict)
            else {
                "target_trace_kinds": ["routing"],
                "context_axes": [
                    "probe_family_id",
                    "assistance_mode_derived",
                    "evidence_channel",
                ],
                "min_stochastic_fraction": 0.20,
                "min_candidate_probability": 0.05,
                "min_chosen_probability": 0.05,
                "min_entropy_bits": 0.0,
                "min_context_coverage_fraction": 0.50,
                "min_decisions_per_context": 1,
            }
        ),
        "invariants_charter_version": "0.0.0",
        "safe_mode_spec_version": "0.0.0",
        "canonical_fingerprint": "sha256:canon_001",
        "replay_fingerprint": "sha256:replay_001",
        "git_commit_sha": "0123456789abcdef0123456789abcdef01234567",
        "workspace_dirty": False,
    }
    if epoch_index == 1:
        manifest["predecessor_run_id"] = None
        manifest["bootstrap_snapshot_ref"] = None
        manifest["migration_event_id"] = None
    return manifest


def replay_projection_from_manifest(manifest: dict) -> dict:
    keys = [
        "content_ir_version",
        "grader_version",
        "sensor_model_version",
        "policy_version",
        "engine_build_version",
        "prompt_bundle_version",
        "residual_formula_version",
        "safe_mode_spec_version",
        "invariants_charter_version",
        "obs_encoder_version",
        "hypothesis_space_hash",
        "decision_rng_version",
        "json_canonicalization_version",
        "canonical_fingerprint",
        "replay_fingerprint",
    ]
    return {k: manifest[k] for k in keys}


def _default_diagnosis_semantics(
    assistance_mode: str,
    evidence_channel: str,
) -> tuple[str, str, list[str]]:
    closed_book = assistance_mode == "closed_book"
    diagnostic_channel = evidence_channel in DIAGNOSTIC_EVIDENCE_CHANNELS
    if closed_book and diagnostic_channel:
        return ("eligible", "none", ["diagnosis_state"])
    if not closed_book and diagnostic_channel:
        return ("ineligible", "assistance_mode_not_closed_book", ["learning_retention_state"])
    if closed_book and not diagnostic_channel:
        return ("ineligible", "channel_not_diagnostic", ["learning_retention_state"])
    return ("ineligible", "assistance_and_channel", ["learning_retention_state"])


def _default_residual_provenance(manifest: dict) -> dict:
    return {
        "state_snapshot_id": GENESIS_SNAPSHOT_ID,
        "sensor_model_version": manifest["sensor_model_version"],
        "residual_formula_version": manifest["residual_formula_version"],
        "hypothesis_space_hash": manifest["hypothesis_space_hash"],
        "obs_encoder_version": manifest["obs_encoder_version"],
    }


def _default_likelihood_sketch() -> dict:
    return {
        "top_hypotheses": [
            {"hypothesis_id": "h_001", "likelihood": 0.72},
            {"hypothesis_id": "h_002", "likelihood": 0.19},
        ],
        "predicted_observation_distribution": [
            {"obs_key": "SLOT(a=pass,b=fail)", "p": 0.41},
            {"obs_key": "SLOT(a=pass,b=pass)", "p": 0.37},
            {"obs_key": "SLOT(a=fail,b=fail)", "p": 0.22},
        ],
    }


def _precommit_projection(payload: dict) -> dict:
    decision_traces = payload["decision_traces"]
    normalized_traces: list[dict] = []
    for trace in decision_traces:
        if not isinstance(trace, dict):
            normalized_traces.append(trace)
            continue
        trace_copy = dict(trace)
        candidates = trace_copy.get("candidate_actions")
        if isinstance(candidates, list):
            trace_copy["candidate_actions"] = sorted(
                candidates,
                key=lambda c: str(c.get("action_id", "")) if isinstance(c, dict) else "",
            )
        normalized_traces.append(trace_copy)
    normalized_traces = sorted(
        normalized_traces,
        key=lambda t: str(t.get("decision_id", "")) if isinstance(t, dict) else "",
    )

    policy_decisions = payload["policy_decisions"]
    normalized_decisions = sorted(
        policy_decisions,
        key=lambda d: str(d.get("decision_id", "")) if isinstance(d, dict) else "",
    )

    likelihood_sketch = payload["residual_inputs"]["likelihood_sketch"]
    normalized_likelihood = dict(likelihood_sketch)
    top_hypotheses = normalized_likelihood.get("top_hypotheses")
    if isinstance(top_hypotheses, list):
        normalized_likelihood["top_hypotheses"] = sorted(
            top_hypotheses,
            key=lambda row: str(row.get("hypothesis_id", "")) if isinstance(row, dict) else "",
        )
    distribution = normalized_likelihood.get("predicted_observation_distribution")
    if isinstance(distribution, list):
        normalized_likelihood["predicted_observation_distribution"] = sorted(
            distribution,
            key=lambda row: str(row.get("obs_key", "")) if isinstance(row, dict) else "",
        )

    return {
        "run_id": payload["run_id"],
        "timeline_id": payload["timeline_id"],
        "session_id": payload["session_id"],
        "attempt_id": payload["attempt_id"],
        "learner_id": payload["learner_id"],
        "item_id": payload["item_id"],
        "probe_family_id": payload["probe_family_id"],
        "commitment_id": payload["commitment_id"],
        "semantic_commitment": deepcopy(payload["semantic_commitment"]),
        "evidence_channel_intended": payload["evidence_channel_intended"],
        "assistance_contract_intended": payload["assistance_contract_intended"],
        "diagnosis_update_eligibility_intended": payload["diagnosis_update_eligibility_intended"],
        "ineligibility_reason_intended": payload["ineligibility_reason_intended"],
        "allowed_update_partitions_intended": sorted(payload["allowed_update_partitions_intended"]),
        "telemetry_event_ids_intended": sorted(payload["telemetry_event_ids_intended"]),
        "decision_traces": normalized_traces,
        "policy_decisions": normalized_decisions,
        "likelihood_sketch": normalized_likelihood,
        "measurement_frame": payload.get("measurement_frame"),
        "measurement_subject": payload.get("measurement_subject"),
        "version_pointers": payload["version_pointers"],
    }


def _precommit_envelope_projection(payload: dict) -> dict:
    return {
        "run_id": payload["run_id"],
        "timeline_id": payload["timeline_id"],
        "session_id": payload["session_id"],
        "attempt_id": payload["attempt_id"],
        "learner_id": payload["learner_id"],
        "precommit_event_id": payload["precommit_event_id"],
        "precommit_hash": payload["precommit_hash"],
        "semantic_commitment": deepcopy(payload["semantic_commitment"]),
        "measurement_frame": payload.get("measurement_frame"),
        "measurement_subject": payload.get("measurement_subject"),
        "telemetry_event_ids_intended": sorted(payload["telemetry_event_ids_intended"]),
    }


def make_attempt(
    manifest: dict,
    attempt_id: str = "att_000001",
    deterministic_policy: bool = True,
    assistance_mode: str = "closed_book",
    evidence_channel: str = "B_measurement",
    diagnosis_update_eligibility: str | None = None,
    ineligibility_reason: str | None = None,
    allowed_update_partitions: list[str] | None = None,
    residual_provenance_overrides: dict | None = None,
    likelihood_sketch_overrides: dict | None = None,
    extra_decision_traces: list[dict] | None = None,
    extra_policy_decisions: list[dict] | None = None,
    measurement_frame: dict | None = None,
    measurement_subject: dict | None = None,
    measurement_adjudication: dict | None = None,
    measurement_execution: dict | None = None,
) -> dict:
    projection = replay_projection_from_manifest(manifest)
    if deterministic_policy:
        candidate_actions = [{"action_id": "MEASURE:pf_0001", "p": 1.0}]
        chosen_probability = 1.0
    else:
        candidate_actions = [
            {"action_id": "MEASURE:pf_0001", "p": 0.7},
            {"action_id": "DISCRIMINATE:pf_0002", "p": 0.3},
        ]
        chosen_probability = 0.7
    (
        default_eligibility,
        default_reason,
        default_allowed_partitions,
    ) = _default_diagnosis_semantics(assistance_mode, evidence_channel)
    provenance = _default_residual_provenance(manifest)
    if residual_provenance_overrides:
        provenance.update(residual_provenance_overrides)
    likelihood_sketch = _default_likelihood_sketch()
    if likelihood_sketch_overrides:
        likelihood_sketch.update(likelihood_sketch_overrides)
    routing_trace = {
        "decision_id": "pol_0001",
        "trace_kind": "routing",
        "candidate_actions": candidate_actions,
        "chosen_action_id": "MEASURE:pf_0001",
        "chosen_action_probability": chosen_probability,
    }
    decision_traces = [routing_trace]
    if extra_decision_traces:
        decision_traces.extend(extra_decision_traces)
    policy_decisions = [
        {
            "decision_id": "pol_0001",
            "policy_domain": "routing",
            "policy_version": manifest["policy_version"],
            "rule_id": "route.default.measure",
            "scope_type": "attempt",
            "scope_id": attempt_id,
            "outcome": "applied",
            "commit_status": "committed",
            "reason_code": "default_measurement_path",
            "decision_ts_utc": "2026-02-27T18:30:00Z",
            "entropy_floor_met": True,
            "min_support_met": True,
            "support_check_status": "pass",
        }
    ]
    if extra_policy_decisions:
        policy_decisions.extend(extra_policy_decisions)
    attempt = {
        "schema_version": "0.1.0",
        "run_id": manifest["run_id"],
        "timeline_id": manifest["timeline_id"],
        "session_id": "session_0001",
        "attempt_id": attempt_id,
        "learner_id": "learner_001",
        "attempt_ts_utc": "2026-02-27T18:30:00Z",
        "item_id": "it_0001",
        "probe_family_id": "pf_0001",
        "commitment_id": "cm_0001",
        "evidence_channel": evidence_channel,
        "evidence_channel_intended": evidence_channel,
        "assistance_mode": assistance_mode,
        "assistance_contract_intended": assistance_mode,
        "assistance_mode_derived": assistance_mode,
        "assistance_derivation_quality": "derived_from_telemetry",
        "diagnosis_update_eligibility": diagnosis_update_eligibility or default_eligibility,
        "diagnosis_update_eligibility_intended": diagnosis_update_eligibility or default_eligibility,
        "ineligibility_reason": ineligibility_reason or default_reason,
        "ineligibility_reason_intended": ineligibility_reason or default_reason,
        "allowed_update_partitions": (
            list(allowed_update_partitions)
            if allowed_update_partitions is not None
            else list(default_allowed_partitions)
        ),
        "allowed_update_partitions_intended": (
            list(allowed_update_partitions)
            if allowed_update_partitions is not None
            else list(default_allowed_partitions)
        ),
        "semantic_commitment": {
            "evidence_channel_intended": evidence_channel,
            "assistance_contract_intended": assistance_mode,
            "diagnosis_update_eligibility_intended": diagnosis_update_eligibility or default_eligibility,
            "ineligibility_reason_intended": ineligibility_reason or default_reason,
            "allowed_update_partitions_intended": sorted(
                list(allowed_update_partitions)
                if allowed_update_partitions is not None
                else list(default_allowed_partitions)
            ),
            "telemetry_event_ids_intended": sorted(
                [f"tel_{attempt_id}_001", f"tel_{attempt_id}_002"]
            ),
        },
        "observation": {
            "slot_pattern": "SLOT(a=pass,b=fail)",
            "latency_sec": 42,
            "hint_level_used": 0,
        },
        "grading_signals": {
            "deterministic_applied": True,
            "llm_used": False,
            "rubric_path_count": 1,
            "schema_valid": True,
            "injection_flags": [],
            "llm_passes": 0,
            "llm_disagreement": None,
        },
        "residual_inputs": {
            "primitive_inputs": {
                "det_vs_llm_disagreement": False,
                "llm_multipass_disagreement": None,
                "schema_invalid": False,
                "rubric_path_count": 1,
                "equivalence_class_size": None,
                "reference_answer_conflict": None,
                "injection_flag_count": 0,
                "parsing_confidence": None,
            },
            "likelihood_sketch": likelihood_sketch,
            "provenance": provenance,
            "derived_inputs": {"max_hypothesis_likelihood": 0.72},
        },
        "decision_traces": decision_traces,
        "policy_decisions": policy_decisions,
        "telemetry_event_ids": [f"tel_{attempt_id}_001", f"tel_{attempt_id}_002"],
        "telemetry_event_ids_intended": [f"tel_{attempt_id}_001", f"tel_{attempt_id}_002"],
        "measurement_frame": deepcopy(measurement_frame) if isinstance(measurement_frame, dict) else None,
        "measurement_subject": deepcopy(measurement_subject) if isinstance(measurement_subject, dict) else None,
        "measurement_adjudication": deepcopy(measurement_adjudication) if isinstance(measurement_adjudication, dict) else None,
        "measurement_execution": deepcopy(measurement_execution) if isinstance(measurement_execution, dict) else None,
        "version_pointers": projection,
        "idempotency": {"sequence_no": 1, "attempt_hash": "att_hash_0001"},
    }
    precommit_event_id = f"pre_{attempt['attempt_id']}"
    precommit_hash = sha256_json(_precommit_projection(attempt))
    precommit_envelope_hash = sha256_json(_precommit_envelope_projection({
        **attempt,
        "precommit_event_id": precommit_event_id,
        "precommit_hash": precommit_hash,
    }))
    attempt["precommit_event_id"] = precommit_event_id
    attempt["precommit_hash"] = precommit_hash
    attempt["precommit_envelope_hash"] = precommit_envelope_hash
    return attempt


def make_attempt_precommit(
    manifest: dict,
    attempt: dict,
    presented_ts_utc: str = "2026-02-27T18:29:59Z",
) -> dict:
    precommit = {
        "schema_version": "0.1.0",
        "run_id": manifest["run_id"],
        "timeline_id": manifest["timeline_id"],
        "session_id": attempt["session_id"],
        "precommit_event_id": attempt["precommit_event_id"],
        "attempt_id": attempt["attempt_id"],
        "learner_id": attempt["learner_id"],
        "presented_ts_utc": presented_ts_utc,
        "item_id": attempt["item_id"],
        "probe_family_id": attempt["probe_family_id"],
        "commitment_id": attempt["commitment_id"],
        "semantic_commitment": deepcopy(attempt["semantic_commitment"]),
        "evidence_channel_intended": attempt["evidence_channel_intended"],
        "assistance_contract_intended": attempt["assistance_contract_intended"],
        "diagnosis_update_eligibility_intended": attempt["diagnosis_update_eligibility_intended"],
        "ineligibility_reason_intended": attempt["ineligibility_reason_intended"],
        "allowed_update_partitions_intended": sorted(
            list(attempt["allowed_update_partitions_intended"])
        ),
        "telemetry_event_ids_intended": sorted(
            list(attempt["telemetry_event_ids_intended"])
        ),
        "decision_traces": deepcopy(attempt["decision_traces"]),
        "policy_decisions": deepcopy(attempt["policy_decisions"]),
        "likelihood_sketch": deepcopy(attempt["residual_inputs"]["likelihood_sketch"]),
        "measurement_frame": deepcopy(attempt.get("measurement_frame")),
        "measurement_subject": deepcopy(attempt.get("measurement_subject")),
        "version_pointers": deepcopy(attempt["version_pointers"]),
        "precommit_hash": attempt["precommit_hash"],
        "precommit_envelope_hash": "",
    }
    precommit["precommit_envelope_hash"] = sha256_json(_precommit_envelope_projection(precommit))
    attempt["precommit_envelope_hash"] = precommit["precommit_envelope_hash"]
    return precommit


def make_attempt_telemetry_events(
    manifest: dict,
    attempt: dict,
) -> list[dict]:
    telemetry_events: list[dict] = []
    for idx, telemetry_event_id in enumerate(attempt.get("telemetry_event_ids", [])):
        telemetry_kind = "response_submitted" if idx == 0 else "ui_mode_toggle"
        telemetry_events.append(
            {
                "schema_version": "0.1.0",
                "run_id": manifest["run_id"],
                "timeline_id": manifest["timeline_id"],
                "session_id": attempt["session_id"],
                "attempt_id": attempt["attempt_id"],
                "learner_id": attempt["learner_id"],
                "telemetry_event_id": telemetry_event_id,
                "telemetry_ts_utc": "2026-02-27T18:29:59Z",
                "telemetry_kind": telemetry_kind,
                "source": "forge_cli",
                "payload_hash": "",
                "mode": attempt["assistance_mode_derived"],
            }
        )
        payload_projection = {k: v for k, v in telemetry_events[-1].items() if k != "payload_hash"}
        telemetry_events[-1]["payload_hash"] = sha256_json(payload_projection)
    return telemetry_events


def make_state_snapshot(manifest: dict, snapshot_id: str = "snap_0008") -> dict:
    state_payload = {"diagnosis_state": {"mastery_score": 0.5}, "learning_retention_state": {}}
    return {
        "schema_version": "0.1.0",
        "run_id": manifest["run_id"],
        "timeline_id": manifest["timeline_id"],
        "session_id": "session_0001",
        "snapshot_id": snapshot_id,
        "learner_id": "learner_001",
        "snapshot_ts_utc": "2026-02-27T18:36:00Z",
        "state_payload": state_payload,
        "state_hash": sha256_json(state_payload),
        "source_attempt_ids": ["att_000001"],
        "version_pointers": replay_projection_from_manifest(manifest),
    }


def make_state_update(
    manifest: dict,
    update_id: str = "upd_000123",
    source_attempt_id: str = "att_000001",
    target_partition: str = "diagnosis_state",
    mutation_outcome: str = "applied",
    diagnosis_log_write_status: str = "committed",
    governor_decision: str = "throttle",
    suppression_reason: str | None = None,
) -> dict:
    base_state = {"diagnosis_state": {}, "learning_retention_state": {}}
    pre_state_hash = sha256_json(base_state)
    applied_state = {"diagnosis_state": {}, "learning_retention_state": {}}
    proposed_state_patch = {
        "op": "set",
        "partition": target_partition,
        "path": "mastery_score" if target_partition == "diagnosis_state" else "exposure_score",
        "value": 1.0 if target_partition == "diagnosis_state" else 0.5,
    }
    base_value_at_proposal = 0.0
    multiplier = 0.00 if governor_decision == "freeze" else 0.50
    applied_value = base_value_at_proposal + multiplier * (
        float(proposed_state_patch["value"]) - base_value_at_proposal
    )
    if target_partition == "diagnosis_state":
        applied_state["diagnosis_state"] = {"mastery_score": applied_value}
        patch_path = "mastery_score"
    else:
        applied_state["learning_retention_state"] = {"exposure_score": proposed_state_patch["value"]}
        patch_path = "exposure_score"
    post_state_hash = pre_state_hash
    state_patch = {
        "op": "set",
        "partition": target_partition,
        "path": patch_path,
        "value": applied_value if target_partition == "diagnosis_state" else proposed_state_patch["value"],
    }
    mutation_attempted = False
    mutation_applied = False
    log_commit_id = None
    integrity_event_id = None

    if mutation_outcome == "applied":
        mutation_attempted = True
        mutation_applied = True
        log_commit_id = "logc_000123"
        suppression_reason = suppression_reason or "none"
        post_state_hash = sha256_json(applied_state)
    elif mutation_outcome == "blocked_by_governor":
        suppression_reason = suppression_reason or "calibration_freeze"
    elif mutation_outcome == "skipped_by_policy":
        suppression_reason = suppression_reason or "policy_skip"
    elif mutation_outcome == "failed_due_to_integrity":
        mutation_attempted = True
        integrity_event_id = "iev_000123"
        suppression_reason = suppression_reason or "none"
    else:
        suppression_reason = suppression_reason or "other"

    if diagnosis_log_write_status in {"failed", "missing"}:
        mutation_attempted = False
        mutation_applied = False
        mutation_outcome = "failed_due_to_integrity"
        log_commit_id = None
        integrity_event_id = integrity_event_id or "iev_000123"
        suppression_reason = "none"
        post_state_hash = pre_state_hash

    return {
        "schema_version": "0.1.0",
        "run_id": manifest["run_id"],
        "timeline_id": manifest["timeline_id"],
        "session_id": "session_0001",
        "snapshot_id": GENESIS_SNAPSHOT_ID,
        "update_id": update_id,
        "learner_id": "learner_001",
        "update_ts_utc": "2026-02-27T18:35:00Z",
        "source_attempt_id": source_attempt_id,
        "stratum_id": "math.linear_algebra.vector_spaces",
        "calibration_status_at_update": "miscalibrated_persistent",
        "governor_decision": governor_decision,
        "governor_reason": "persistent_brier_above_threshold",
        "applied_update_multiplier": multiplier,
        "safe_mode_profile_id": "SG_CALIBRATION_GUARD",
        "governor_transform_version": "governor_transform.v1",
        "state_patch": state_patch,
        "proposed_state_patch": proposed_state_patch,
        "base_value_at_proposal": base_value_at_proposal,
        "pre_state_hash": pre_state_hash,
        "post_state_hash": post_state_hash,
        "diagnosis_log_write_status": diagnosis_log_write_status,
        "mutation_attempted": mutation_attempted,
        "mutation_outcome": mutation_outcome,
        "suppression_reason": suppression_reason,
        "log_commit_id": log_commit_id,
        "mutation_applied": mutation_applied,
        "integrity_event_id": integrity_event_id,
    }


def make_state_migration(manifest: dict) -> dict:
    bootstrap = manifest.get("bootstrap_snapshot_ref") or {
        "source_run_id": "run_prev",
        "source_snapshot_id": "snap_prev",
        "source_state_hash": "sha256:source_state",
        "source_replay_fingerprint": "sha256:replay_prev",
    }
    return {
        "schema_version": "0.1.0",
        "run_id": manifest["run_id"],
        "timeline_id": manifest["timeline_id"],
        "migration_event_id": manifest.get("migration_event_id", "mig_0001"),
        "migration_ts_utc": "2026-02-27T18:20:00Z",
        "source_run_id": bootstrap["source_run_id"],
        "source_snapshot_id": bootstrap["source_snapshot_id"],
        "source_state_hash": bootstrap["source_state_hash"],
        "source_replay_fingerprint": bootstrap["source_replay_fingerprint"],
        "target_manifest_replay_fingerprint": manifest["replay_fingerprint"],
        "migration_rule_set_version": "migration_rules.v0.1.0",
        "migration_rule_ids": ["rule.identity.copy"],
        "pre_migration_state_hash": bootstrap["source_state_hash"],
        "post_migration_state_hash": bootstrap["source_state_hash"],
        "partition_migration_summary": {
            "diagnosis_state": "copied",
            "learning_retention_state": "copied",
        },
        "transform_hash": "sha256:transform_plan_001",
    }


def make_safe_mode_transition_event(
    manifest: dict,
    event_id: str = "evt_safe_mode_0001",
    prior_state: str = "NORMAL",
    trigger_set: list[str] | None = None,
) -> dict:
    resolved_trigger_set = trigger_set or ["TRG-CALIBRATION-ALARM"]
    dominant_trigger = resolved_trigger_set[0]
    next_state = "SAFE_GUARDED"
    profile_id = "SG_CALIBRATION_GUARD"
    if dominant_trigger in {"TRG-MANUAL-PANIC", "TRG-MANIFEST-INVALID", "TRG-FIXTURE-FAIL"}:
        next_state = "SAFE_PANIC"
        profile_id = {
            "TRG-MANUAL-PANIC": "SP_MANUAL_PANIC",
            "TRG-MANIFEST-INVALID": "SP_MANIFEST_INVALID",
            "TRG-FIXTURE-FAIL": "SP_FIXTURE_FAILURE_PANIC",
        }[dominant_trigger]
    if dominant_trigger == "TRG-MANUAL-CLEAR":
        next_state = "SAFE_GUARDED"
        profile_id = "SG_GENERIC_GUARD"
    return {
        "schema_version": "0.1.0",
        "run_id": manifest["run_id"],
        "timeline_id": manifest["timeline_id"],
        "session_id": "session_0001",
        "event_id": event_id,
        "event_ts_utc": "2026-02-27T18:40:00Z",
        "prior_state": prior_state,
        "next_state": next_state,
        "trigger_id": dominant_trigger,
        "trigger_set": list(resolved_trigger_set),
        "dominant_trigger_id": dominant_trigger,
        "trigger_payload_hash": "sha256:trigger_payload_0001",
        "profile_id": profile_id,
        "profile_parent_state": next_state,
        "profile_resolution_version": "safe_mode_profile_resolver.v0.0.0",
        "policy_bundle_hash": SAFE_MODE_POLICY_BUNDLE_HASHES[profile_id],
        "actor_id": None,
        "reason": "deterministic_transition",
        "spec_version": manifest["safe_mode_spec_version"],
    }


def make_quarantine_decision_event(
    manifest: dict,
    event_id: str = "evt_quarantine_0001",
) -> dict:
    return {
        "schema_version": "0.1.0",
        "run_id": manifest["run_id"],
        "timeline_id": manifest["timeline_id"],
        "session_id": "session_0001",
        "event_id": event_id,
        "event_ts_utc": "2026-02-27T18:41:00Z",
        "quarantine_id": "q_0001",
        "metric_id": "invariance.zscore_item_weirdness",
        "scope_type": "item",
        "scope_id": "it_0001",
        "threshold_config_version": "thresholds.v1",
        "threshold_value": 2.5,
        "observed_value": 3.1,
        "threshold_crossed": True,
        "action": "quarantine",
        "reason": "threshold_crossing",
        "spec_version": manifest["invariants_charter_version"],
    }


def make_anchor_audit_event(
    manifest: dict,
    event_id: str = "evt_anchor_audit_0001",
) -> dict:
    return {
        "schema_version": "0.1.0",
        "run_id": manifest["run_id"],
        "timeline_id": manifest["timeline_id"],
        "session_id": "session_0001",
        "event_id": event_id,
        "event_ts_utc": "2026-02-27T18:42:00Z",
        "audit_id": "anc_audit_0001",
        "window_id": "window_2026w09",
        "scope_type": "run",
        "scope_id": manifest["run_id"],
        "quota_min": 3,
        "anchors_sampled": 4,
        "cross_graded_count": 2,
        "cross_grade_disagreement_rate": 0.10,
        "audit_status": "pass",
        "reason": "quota_and_cross_grade_ok",
        "spec_version": manifest["invariants_charter_version"],
    }


def clone(record: dict) -> dict:
    return deepcopy(record)
