"""Constants for v0.1 contracts and gates."""

MANIFEST_REQUIRED_FIELDS = {
    "schema_version",
    "run_id",
    "timeline_id",
    "epoch_index",
    "predecessor_run_id",
    "bootstrap_snapshot_ref",
    "migration_event_id",
    "run_started_at_utc",
    "content_ir_version",
    "grader_version",
    "sensor_model_version",
    "policy_version",
    "engine_build_version",
    "prompt_bundle_version",
    "residual_formula_version",
    "obs_encoder_version",
    "hypothesis_space_hash",
    "decision_rng_version",
    "json_canonicalization_version",
    "ope_support_level",
    "ope_claim_contract",
    "invariants_charter_version",
    "safe_mode_spec_version",
    "canonical_fingerprint",
    "replay_fingerprint",
    "git_commit_sha",
    "workspace_dirty",
}

CANONICAL_TUPLE_FIELDS = [
    "content_ir_version",
    "grader_version",
    "sensor_model_version",
]

REPLAY_TUPLE_FIELDS = [
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
]

REPLAY_PROJECTION_KEYS = REPLAY_TUPLE_FIELDS + [
    "canonical_fingerprint",
    "replay_fingerprint",
]

ATTEMPT_REQUIRED_FIELDS = {
    "schema_version",
    "run_id",
    "timeline_id",
    "session_id",
    "attempt_id",
    "learner_id",
    "attempt_ts_utc",
    "item_id",
    "probe_family_id",
    "commitment_id",
    "evidence_channel",
    "evidence_channel_intended",
    "assistance_mode",
    "assistance_contract_intended",
    "diagnosis_update_eligibility",
    "diagnosis_update_eligibility_intended",
    "ineligibility_reason",
    "ineligibility_reason_intended",
    "allowed_update_partitions",
    "allowed_update_partitions_intended",
    "observation",
    "grading_signals",
    "residual_inputs",
    "decision_traces",
    "policy_decisions",
    "telemetry_event_ids",
    "telemetry_event_ids_intended",
    "assistance_mode_derived",
    "assistance_derivation_quality",
    "version_pointers",
    "idempotency",
    "precommit_event_id",
    "precommit_hash",
    "precommit_envelope_hash",
    "semantic_commitment",
}

ATTEMPT_PRECOMMIT_REQUIRED_FIELDS = {
    "schema_version",
    "run_id",
    "timeline_id",
    "session_id",
    "precommit_event_id",
    "attempt_id",
    "learner_id",
    "presented_ts_utc",
    "item_id",
    "probe_family_id",
    "commitment_id",
    "evidence_channel_intended",
    "assistance_contract_intended",
    "diagnosis_update_eligibility_intended",
    "ineligibility_reason_intended",
    "allowed_update_partitions_intended",
    "telemetry_event_ids_intended",
    "decision_traces",
    "policy_decisions",
    "likelihood_sketch",
    "version_pointers",
    "precommit_hash",
    "precommit_envelope_hash",
    "semantic_commitment",
}

SEMANTIC_COMMITMENT_REQUIRED_FIELDS = {
    "evidence_channel_intended",
    "assistance_contract_intended",
    "diagnosis_update_eligibility_intended",
    "ineligibility_reason_intended",
    "allowed_update_partitions_intended",
    "telemetry_event_ids_intended",
}

ATTEMPT_TELEMETRY_REQUIRED_FIELDS = {
    "schema_version",
    "run_id",
    "timeline_id",
    "session_id",
    "attempt_id",
    "learner_id",
    "telemetry_event_id",
    "telemetry_ts_utc",
    "telemetry_kind",
    "source",
    "payload_hash",
}

DECISION_TRACE_REQUIRED_FIELDS = {
    "decision_id",
    "trace_kind",
    "candidate_actions",
    "chosen_action_id",
    "chosen_action_probability",
}

TRACE_KINDS = {
    "routing",
    "feedback",
    "holdout",
    "anchor",
    "quarantine",
    "calibration",
    "diagnosis",
    "other",
}

STATE_SNAPSHOT_REQUIRED_FIELDS = {
    "schema_version",
    "run_id",
    "timeline_id",
    "session_id",
    "snapshot_id",
    "learner_id",
    "snapshot_ts_utc",
    "state_payload",
    "state_hash",
    "source_attempt_ids",
    "version_pointers",
}

STATE_UPDATE_REQUIRED_FIELDS = {
    "schema_version",
    "run_id",
    "timeline_id",
    "session_id",
    "snapshot_id",
    "update_id",
    "learner_id",
    "update_ts_utc",
    "source_attempt_id",
    "stratum_id",
    "calibration_status_at_update",
    "governor_decision",
    "governor_reason",
    "applied_update_multiplier",
    "safe_mode_profile_id",
    "governor_transform_version",
    "state_patch",
    "proposed_state_patch",
    "base_value_at_proposal",
    "pre_state_hash",
    "post_state_hash",
    "diagnosis_log_write_status",
    "mutation_attempted",
    "mutation_outcome",
    "suppression_reason",
    "log_commit_id",
    "mutation_applied",
    "integrity_event_id",
}

EVIDENCE_CHANNELS = {"A_anchor", "B_measurement", "C_learning", "D_shadow"}
DIAGNOSTIC_EVIDENCE_CHANNELS = {"A_anchor", "B_measurement", "D_shadow"}
ASSISTANCE_MODES = {"closed_book", "open_book", "tool_assisted", "mixed"}
ASSISTANCE_DERIVATION_QUALITY = {"derived_from_telemetry", "legacy_untrusted"}
DIAGNOSIS_UPDATE_ELIGIBILITY = {"eligible", "ineligible"}
INELIGIBILITY_REASON = {
    "none",
    "assistance_mode_not_closed_book",
    "channel_not_diagnostic",
    "assistance_and_channel",
}
ALLOWED_UPDATE_PARTITIONS = {"diagnosis_state", "learning_retention_state"}
TELEMETRY_KINDS = {
    "tool_call",
    "resource_access",
    "hint_request",
    "ui_mode_toggle",
    "paste",
    "response_submitted",
    "other",
}

POLICY_DOMAINS = {
    "routing",
    "holdout",
    "anchor",
    "invariance",
    "diagnosis",
    "calibration",
    "other",
}
POLICY_SCOPE_TYPES = {"attempt", "item", "family", "stratum", "session", "run", "learner"}
POLICY_OUTCOMES = {"applied", "skipped", "blocked", "noop"}
COMMIT_STATUS = {"committed", "dropped", "failed"}
SUPPORT_CHECK_STATUS = {"pass", "fail", "not_applicable"}

CALIBRATION_STATUS = {"healthy", "warning", "miscalibrated_persistent"}
GOVERNOR_DECISIONS = {"normal", "throttle", "strong_throttle", "freeze"}
DIAGNOSIS_LOG_WRITE_STATUS = {"committed", "failed", "missing"}
MUTATION_OUTCOMES = {
    "applied",
    "blocked_by_governor",
    "skipped_by_policy",
    "failed_due_to_integrity",
}
SUPPRESSION_REASONS = {"none", "calibration_freeze", "policy_skip", "quarantine", "other"}

OPE_SUPPORT_LEVELS = {"none", "propensity_only", "full_support"}

OPE_TARGET_TRACE_KINDS = {"routing", "feedback", "holdout", "anchor", "quarantine", "diagnosis"}
OPE_CONTEXT_AXES = {
    "probe_family_id",
    "assistance_mode_derived",
    "evidence_channel",
    "session_id",
    "learner_id",
}

JSON_CANONICALIZATION_VERSIONS = {"forge_json_c14n_v1"}
GENESIS_SNAPSHOT_ID = "__genesis__"

GOVERNOR_MULTIPLIERS = {
    "normal": 1.00,
    "throttle": 0.50,
    "strong_throttle": 0.20,
    "freeze": 0.00,
}

RESIDUAL_PROVENANCE_PINNED_FIELDS = (
    "sensor_model_version",
    "obs_encoder_version",
    "hypothesis_space_hash",
    "residual_formula_version",
)

EVENT_TYPES = {
    "attempt_precommitted",
    "attempt_telemetry",
    "attempt_observed",
    "state_migration",
    "state_update",
    "safe_mode_transition",
    "quarantine_decision",
    "anchor_audit",
    "snapshot_checkpoint",
}

EVENT_ID_PREFIX_BY_TYPE = {
    "attempt_precommitted": "evt_attempt_precommitted_",
    "attempt_telemetry": "evt_attempt_telemetry_",
    "attempt_observed": "evt_attempt_observed_",
    "state_migration": "evt_state_migration_",
    "state_update": "evt_state_update_",
    "safe_mode_transition": "evt_safe_mode_transition_",
    "quarantine_decision": "evt_quarantine_decision_",
    "anchor_audit": "evt_anchor_audit_",
    "snapshot_checkpoint": "evt_snapshot_checkpoint_",
}

EVENT_PAYLOAD_ID_FIELD_BY_TYPE = {
    "attempt_precommitted": "precommit_event_id",
    "attempt_telemetry": "telemetry_event_id",
    "attempt_observed": "attempt_id",
    "state_migration": "migration_event_id",
    "state_update": "update_id",
    "safe_mode_transition": "event_id",
    "quarantine_decision": "event_id",
    "anchor_audit": "event_id",
    "snapshot_checkpoint": "snapshot_id",
}

# Contract compatibility matrix.
# Validators are schema-version aware by record type, even when multiple versions
# currently share the same validation logic.
SCHEMA_VERSION_COMPATIBILITY: dict[str, set[str]] = {
    "manifest": {"0.0.0", "0.1.0"},
    "attempt": {"0.1.0"},
    "attempt_precommit": {"0.1.0"},
    "attempt_telemetry": {"0.1.0"},
    "state_snapshot": {"0.1.0"},
    "state_update": {"0.1.0"},
    "state_migration": {"0.1.0"},
    "safe_mode_transition": {"0.1.0"},
    "quarantine_decision": {"0.1.0"},
    "anchor_audit": {"0.1.0"},
}

REPLAY_NORMALIZATION_TARGET_SCHEMA_VERSION = "0.1.0"
STATE_MIGRATION_REQUIRED_FIELDS = {
    "schema_version",
    "run_id",
    "timeline_id",
    "migration_event_id",
    "migration_ts_utc",
    "source_run_id",
    "source_snapshot_id",
    "source_state_hash",
    "source_replay_fingerprint",
    "target_manifest_replay_fingerprint",
    "migration_rule_set_version",
    "migration_rule_ids",
    "pre_migration_state_hash",
    "post_migration_state_hash",
    "partition_migration_summary",
    "transform_hash",
}

SAFE_MODE_STATES = {"NORMAL", "SAFE_GUARDED", "SAFE_PANIC"}
SAFE_MODE_TRIGGER_IDS = {
    "TRG-MANUAL-PANIC",
    "TRG-MANIFEST-INVALID",
    "TRG-FIXTURE-FAIL",
    "TRG-CALIBRATION-ALARM",
    "TRG-SENSOR-UNRELIABLE-HIGH",
    "TRG-SPEC-UNDERDETERMINED-HIGH",
    "TRG-MANUAL-CLEAR",
}
SAFE_MODE_PROFILE_IDS = {
    "SG_CALIBRATION_GUARD",
    "SG_SENSOR_UNRELIABLE_GUARD",
    "SG_SPEC_UNDERDETERMINED_GUARD",
    "SG_GENERIC_GUARD",
    "SP_MANUAL_PANIC",
    "SP_MANIFEST_INVALID",
    "SP_FIXTURE_FAILURE_PANIC",
    "SP_GENERIC_PANIC",
}
SAFE_MODE_PROFILE_PARENT_STATES = {
    "SG_CALIBRATION_GUARD": "SAFE_GUARDED",
    "SG_SENSOR_UNRELIABLE_GUARD": "SAFE_GUARDED",
    "SG_SPEC_UNDERDETERMINED_GUARD": "SAFE_GUARDED",
    "SG_GENERIC_GUARD": "SAFE_GUARDED",
    "SP_MANUAL_PANIC": "SAFE_PANIC",
    "SP_MANIFEST_INVALID": "SAFE_PANIC",
    "SP_FIXTURE_FAILURE_PANIC": "SAFE_PANIC",
    "SP_GENERIC_PANIC": "SAFE_PANIC",
}
SAFE_MODE_POLICY_BUNDLE_HASHES = {
    "SG_CALIBRATION_GUARD": "sha256:policy_bundle_sg_calibration_guard_v0_0_0",
    "SG_SENSOR_UNRELIABLE_GUARD": "sha256:policy_bundle_sg_sensor_unreliable_guard_v0_0_0",
    "SG_SPEC_UNDERDETERMINED_GUARD": "sha256:policy_bundle_sg_spec_underdetermined_guard_v0_0_0",
    "SG_GENERIC_GUARD": "sha256:policy_bundle_sg_generic_guard_v0_0_0",
    "SP_MANUAL_PANIC": "sha256:policy_bundle_sp_manual_panic_v0_0_0",
    "SP_MANIFEST_INVALID": "sha256:policy_bundle_sp_manifest_invalid_v0_0_0",
    "SP_FIXTURE_FAILURE_PANIC": "sha256:policy_bundle_sp_fixture_failure_panic_v0_0_0",
    "SP_GENERIC_PANIC": "sha256:policy_bundle_sp_generic_panic_v0_0_0",
}
SAFE_MODE_TRANSITION_REQUIRED_FIELDS = {
    "schema_version",
    "run_id",
    "timeline_id",
    "event_id",
    "event_ts_utc",
    "prior_state",
    "next_state",
    "trigger_id",
    "trigger_set",
    "dominant_trigger_id",
    "trigger_payload_hash",
    "profile_id",
    "profile_parent_state",
    "profile_resolution_version",
    "policy_bundle_hash",
    "reason",
    "spec_version",
}

QUARANTINE_SCOPE_TYPES = {"item", "family", "stratum"}
QUARANTINE_ACTIONS = {"quarantine", "monitor_only", "release"}
QUARANTINE_DECISION_REQUIRED_FIELDS = {
    "schema_version",
    "run_id",
    "timeline_id",
    "event_id",
    "event_ts_utc",
    "quarantine_id",
    "metric_id",
    "scope_type",
    "scope_id",
    "threshold_config_version",
    "threshold_value",
    "observed_value",
    "threshold_crossed",
    "action",
    "reason",
    "spec_version",
}

ANCHOR_AUDIT_STATUSES = {"pass", "fail", "warning"}
ANCHOR_AUDIT_REQUIRED_FIELDS = {
    "schema_version",
    "run_id",
    "timeline_id",
    "event_id",
    "event_ts_utc",
    "audit_id",
    "window_id",
    "scope_type",
    "scope_id",
    "quota_min",
    "anchors_sampled",
    "cross_graded_count",
    "cross_grade_disagreement_rate",
    "audit_status",
    "reason",
    "spec_version",
}
