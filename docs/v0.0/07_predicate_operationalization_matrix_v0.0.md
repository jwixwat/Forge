# Predicate Operationalization Matrix v0.0

Version: `0.0.0`  
Effective date: `2026-02-27`  
Depends on: `01_invariants_charter_v0.0.md`, `06_v0.1_interface_preconditions.md`

## 1) Purpose

Provide a deterministic query crosswalk for every invariant predicate so compliance can be computed from logs/manifests rather than human interpretation.

## 2) Matrix

| Invariant ID | Query Sources | Required Fields | Derived Terms | Query Sketch | Activation Stage | Instrumentation Status |
| --- | --- | --- | --- | --- | --- | --- |
| INV-SEM-DET-001 | attempt ledger, content IR | `item_id`, `version_pointers.content_ir_version`, `grading_signals.deterministic_applied` | `deterministic_rubric_exists(attempt)` | For attempts where deterministic rubric resolves true, assert `deterministic_applied=true`. | v0.3 | attempt fields frozen; IR derivation defined |
| INV-SEM-CBG-002 | diagnosis-state updates, attempt metadata | `source_attempt_id`, `assistance_mode`, `evidence_channel`, `state_patch.partition` | `diagnosis_updates` set | For all diagnosis updates, require closed-book and channel in A/B/D. | v2.0 | fields partially frozen; hard gate declared |
| SOFT-SEM-CBG-000 | attempt ledger, telemetry ledger, state updates | `assistance_mode_derived`, `assistance_derivation_quality`, `telemetry_event_ids`, `diagnosis_update_eligibility`, `ineligibility_reason`, `allowed_update_partitions`, `source_attempt_id`, `state_patch.partition` | none | Derive assistance from committed telemetry, require diagnosis semantics from derived mode, and for ineligible attempts assert `diagnosis_state` is not in allowed partitions and updates mutate only source-authorized partitions. | v0.x | soft-enforced now |
| INV-SEM-RES-003 | run manifest, attempt ledger | `residual_formula_version` (manifest + attempt + provenance), `residual_inputs.primitive_inputs`, `residual_inputs.provenance`, `likelihood_sketch` | `recompute_residuals_from_primitives(...)` | Recompute residuals from primitives/provenance and compare with logged residuals. | v0.6 | residual contract frozen |
| INV-EPI-CAL-004 | calibration log | `stratum`, `metric_id`, `metric_value`, `ts_utc`, `trigger_outcome` | `required_strata` | For each required stratum, ensure calibration rows exist over time windows. | v1.1 | declared; log schema required by invariant |
| INV-EPI-CAL-004B | state-update events, calibration alarms, safe-mode events | `calibration_status_at_update`, `applied_update_multiplier`, `governor_decision`, `governor_reason`, `stratum_id`, `safe_mode_profile_id`, `governor_transform_version`, `proposed_state_patch`, `base_value_at_proposal`, `state_patch` | `governor_multiplier`, `governed_transform(proposed,base,m)`, `has_calibration_safe_mode_response` | Persistent miscalibration requires safe-mode response plus bounded diagnosis movement by ladder and deterministic proposed->applied transform checks. | v1.1 | v1.1 contract frozen in v0.1 interfaces |
| INV-EPI-EXP-005A | attempt ledger (`decision_traces`) | `decision_id`, `trace_kind`, `candidate_actions[]`, `chosen_action_id`, `chosen_action_probability` | none | Probabilities normalize to 1.0, chosen probability matches chosen action, and trace kind is in frozen ontology. | v0.1 | logging contract frozen |
| INV-EPI-EXP-005B | policy decision logs, run manifest | `entropy_floor_met`, `min_support_met`, `support_check_status`, `ope_support_level` | `support_constraints_satisfied(decision)` | For active decisions, require entropy/support checks pass before `full_support` classification. | v1.2 | instrumentation frozen; enforcement declared |
| INV-OPS-SEN-006 | fixture reports | `fixture_set_id`, `status`, `report_ts_utc` | `required_fixture_sets` | Latest report for each required fixture set must be `pass`. | v0.8 | declared |
| INV-EPI-HLD-007 | holdout attempts, policy decisions | `holdout_flag`, `holdout_exposure_counter_before/after`, `contamination_index_before/after`, `policy_decisions[]` | `holdout_attempts`, `policy_applied(decision)` | Holdout counters must update monotonically and at least one holdout policy decision is applied. | v2.1 | schema expectations declared |
| INV-EPI-ANC-008 | anchor scheduling log, belief-audit log | `anchors_sampled`, `quota_min`, `window_id`, `belief_audit_record` | `time_windows` | Per time window, sampled anchors meet quota and a belief-audit record exists. | v2.2 | declared |
| INV-EPI-NIV-009 | invariance log, quarantine events | `threshold_crossed`, `metric_id`, `scope_type`, `scope_id`, `threshold_config_version` | `threshold_crossings`, `quarantine_event_emitted(crossing)` | Every threshold crossing must have a matching quarantine event. | v1.3 | declared |
| INV-OPS-VSN-010 | run manifest, attempt ledger, state snapshots | canonical/replay tuple fields, `run_id`, `version_pointers`, `residual_formula_version`, `json_canonicalization_version` | `has_version_tuple`, `has_replay_tuple`, `replay_tuple_projection`, `valid_manifest_ref` | Enforce run-manifest linkage, no mixed semantics, residual version equality, and canonicalization-version equality. | v0.0 | enforced |
| INV-OPS-EPOCH-013 | run manifest, migrations, event ledger, run records | `timeline_id`, `epoch_index`, `predecessor_run_id`, `bootstrap_snapshot_ref`, `migration_event_id`, migration payload ids/hashes, event sequence | `epoch_is_initial`, `migration_precedes_attempts`, `timeline_records_scoped` | Enforce semantic-epoch lineage coherence and explicit migration-first cross-epoch state continuity. | vNext | declared; contracts frozen |
| INV-OPS-LOG-012 | state-update events | `diagnosis_log_write_status`, `log_commit_id`, `mutation_applied`, `integrity_event_id`, `update_id`, `state_patch.partition` | `diagnosis_state_updates` | Diagnosis mutation allowed only when required diagnosis-log write is committed. | v0.1 | contract frozen; gates declared |
| INV-SAF-SFM-011 | safe-mode transition log, spec mapping | `prior_state`, `next_state`, `trigger_set`, `profile_id`, `policy_bundle_hash` | `spec_state`, `spec_profile`, `spec_policy_bundle_hash` | Recompute expected state/profile/bundle and require exact match for each transition. | v0.0 | enforced |

## 3) Operationalization Rule

- If an invariant has no row in this matrix, it is non-compliant with `G-MRG-V00-004`.
- If required fields are missing from contracts at or before activation stage, the corresponding release/merge gate must fail.
