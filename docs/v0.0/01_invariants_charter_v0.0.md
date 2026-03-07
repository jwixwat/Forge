# Invariants Charter v0.0

Version: `0.0.0`  
Effective date: `2026-02-27`  
Owner: Forge core architecture

## 1) Purpose

This charter is the normative source for system invariants. Each invariant is defined with:

- invariant id
- activation stage
- formal statement
- evidence contract
- verification predicate
- failure action

The goal is to prevent ambiguous interpretation before implementation begins.

## 2) Predicate Language

Verification predicates in this document use these terms:

- `exists(path)` means the artifact/file exists.
- `field(record, name)` means a required field exists.
- `eq(a,b)` means strict equality.
- `all(records, predicate)` means predicate holds for all records.
- `any(records, predicate)` means predicate holds for at least one record.
- `implies(a,b)` means logical implication.
- `runs` means all run-manifest records.
- `attempts` means all attempt records.
- `states` means all state snapshot records.
- `transitions` means all safe-mode transition event records.
- `primitive_inputs` means first-order logged signals (raw or directly observed), not model summaries.
- `derived_inputs` means deterministic summaries computed from primitives and referenced models/state.
- `run_manifest(run_id)` means the unique manifest associated with `run_id`.
- `recompute_residuals_from_primitives(...)` means deterministic recomputation using `residual_formula_version` from manifest.
- `deterministic_rubric_exists(attempt)` is derived from `attempt.item_id` and `attempt.version_pointers.content_ir_version` by resolving the item in content IR.
- `replay_tuple_projection(manifest)` means the subset of manifest fields required in attempt/state `version_pointers`.
- `has_version_tuple(manifest)` means required canonical tuple fields (`content_ir_version`, `grader_version`, `sensor_model_version`) exist and are non-empty.
- `has_replay_tuple(manifest)` means required replay tuple fields exist and are non-empty except nullable `prompt_bundle_version` when LLM paths are disabled.
- `valid_manifest_ref(run_id)` means `run_manifest(run_id)` exists and is unique.
- `policy_decisions` means persisted policy decision records linked to attempts/snapshots.
- `policy_applied(decision)` means `decision.outcome == "applied"` and `decision.commit_status == "committed"`.
- `support_constraints_satisfied(decision)` means a matching policy decision exists where `policy_decision.decision_id == decision.decision_id` and `entropy_floor_met == true` and `min_support_met == true` and `support_check_status == "pass"`.
- `decisions` means routing decision records resolved from attempt `decision_traces`.
- `candidates(decision)` means `decision.candidate_actions`.
- `action_ids(decision)` means set of `action_id` values in `candidate_actions`.
- `sum_p(decision)` means sum of probabilities `p` across `candidate_actions` for the decision.
- `p(action_id, decision)` means probability `p` of the candidate with `action_id` within `candidate_actions`.
- `entropy(candidates)` means Shannon entropy of candidate action probabilities.
- `entropy_floor` means configured minimum entropy for routing decisions at the active stage.
- `required_strata` means configured calibration strata list.
- `calibration_log` means persisted predictive-calibration metric rows.
- `strata_with_persistent_miscalibration` means strata where calibration log rows satisfy persistence threshold configuration.
- `governor_decision(stratum)` means latest active governor decision for the stratum in calibration/governor logs.
- `required_fixture_sets` means configured sentinel fixture suite ids.
- `latest_report(fixture_set_id)` means most recent fixture report row for that fixture set id.
- `time_windows` means configured audit windows for anchor quotas.
- `belief_audit_records` means persisted belief-audit rows keyed by `window_id`.
- `invariance_log` means persisted invariance metric rows.
- `holdout_attempts` means attempt records where `holdout_flag == true`.
- `diagnosis_updates` means diagnosis-state updates joined with source attempt metadata (`assistance_mode`, `evidence_channel`).
- `threshold_crossings` means invariance log rows where `threshold_crossed == true`.
- `quarantine_event_emitted(crossing)` means a quarantine event exists with matching `metric_id`, `scope_type`, `scope_id`, and `threshold_config_version`.
- `state_update_events` means all persisted state update event records.
- `diagnosis_state_updates` means state update events where `state_patch.partition == "diagnosis_state"`.
- `governor_multiplier(decision)` maps: `normal -> 1.00`, `throttle -> 0.50`, `strong_throttle -> 0.20`, `freeze -> 0.00`.
- `has_calibration_safe_mode_response(stratum)` means persistent miscalibration in the stratum produced `TRG-CALIBRATION-ALARM` with profile `SG_CALIBRATION_GUARD` or stronger panic response.
- `spec_state(trigger_set, prior_state)` means deterministic next-state mapping from `02_safe_mode_and_panic_spec_v0.0.md`.
- `spec_profile(trigger_set, prior_state, next_state)` means deterministic profile mapping from `02_safe_mode_and_panic_spec_v0.0.md`.
- `spec_policy_bundle_hash(profile_id)` means deterministic expected policy bundle hash for the profile under pinned safe-mode spec version.

## 2.1 Operationalizability Requirement

- Every invariant predicate must be evaluable as a deterministic query over manifests and logs.
- Every non-primitive predicate term used in Section 4 must be defined in Section 2 or in `07_predicate_operationalization_matrix_v0.0.md`.
- Undefined symbols or human-interpretation-only predicate terms make an invariant non-operational and fail `G-MRG-V00-004`.

## 3) Invariant Registry

| ID | Invariant Name | Activation Stage | v0.0 Mode |
| --- | --- | --- | --- |
| INV-SEM-DET-001 | Deterministic-first grading | v0.3 | declared |
| INV-SEM-CBG-002 | Closed-book gating for diagnosis | v2.0 | declared |
| SOFT-SEM-CBG-000 | Pre-enforcement diagnosis debt prevention default | v0.x | soft_enforced |
| INV-SEM-RES-003 | Residuals are mechanical | v0.4 | declared |
| INV-EPI-CAL-004 | Posterior predictive checks run and logged | v1.1 | declared |
| INV-EPI-CAL-004B | Calibration governs diagnosis authority | v1.1 | declared |
| INV-EPI-EXP-005A | Propensity logging support exists | v0.1 | declared |
| INV-EPI-EXP-005B | Entropy/support floor enforced | v1.2 | declared |
| INV-OPS-SEN-006 | Sentinel fixtures pass | v0.5 | declared |
| INV-EPI-HLD-007 | Holdout contamination tracked | v2.1 | declared |
| INV-EPI-ANC-008 | Anchor quotas enforced | v2.2 | declared |
| INV-EPI-NIV-009 | Non-invariance guardrails active | v1.3 | declared |
| INV-OPS-VSN-010 | Versioned semantics | v0.0 | enforced |
| INV-OPS-LOG-012 | No unlogged diagnosis-state mutation | v0.1 | declared |
| INV-SAF-SFM-011 | Safe mode degrades predictably | v0.0 | enforced |

`declared` means contract is frozen now and implementation is enforced from activation stage onward.  
`enforced` means compliance is required in v0.0 gates.  
`soft_enforced` means policy default is required and auditable now, but violations are warning-grade until hard gate activation.

## 4) Invariant Definitions

### INV-SEM-DET-001 Deterministic-first grading

- Formal statement: If a deterministic rubric exists for an attempt, deterministic grading must run before any LLM-assisted parsing.
- Evidence contract:
  - attempt record includes `grading_signals.deterministic_applied`, `grading_signals.llm_used`, `item_id`, and `version_pointers.content_ir_version`,
  - deterministic rubric existence is derived from content IR using `(item_id, content_ir_version)`.
- Predicate: `all(attempts, implies(deterministic_rubric_exists(attempt), eq(field(attempt, "grading_signals.deterministic_applied"), true)))`.
- Failure action: block merge for grading pipeline changes; mark release non-compliant.

### INV-SEM-CBG-002 Closed-book gating for diagnosis

- Formal statement: Factor-diagnosis updates are allowed only from channels `A_anchor`, `B_measurement`, `D_shadow` and only when `assistance_mode=closed_book`.
- Evidence contract: state update log includes source attempt ids, evidence channel, assistance mode.
- Predicate: `all(diagnosis_updates, eq(update.assistance_mode, "closed_book") and update.evidence_channel in {"A_anchor","B_measurement","D_shadow"})`.
- Failure action: block release; auto-route runtime to safe mode once implemented.
- Pre-v2.0 behavior is governed by `SOFT-SEM-CBG-000` to reduce semantic debt before hard enforcement.

### SOFT-SEM-CBG-000 Pre-enforcement diagnosis debt prevention default

- Formal statement: Before v2.0 hard gating, diagnosis updates are discouraged by default unless `assistance_mode=closed_book` and evidence channel is in `A_anchor/B_measurement/D_shadow`; ineligible evidence routes to learning/retention updates only.
- Evidence contract:
  - attempt log fields `diagnosis_update_eligibility`, `ineligibility_reason`, `allowed_update_partitions`,
  - state update log fields `state_patch.partition`, `source_attempt_id`.
- Predicate:
  - `all(attempts, field(attempt, "diagnosis_update_eligibility") and field(attempt, "allowed_update_partitions"))`
  - `and all(attempts, implies(eq(attempt.diagnosis_update_eligibility, "ineligible"), not("diagnosis_state" in attempt.allowed_update_partitions)))`.
- Failure action: emit semantic-debt warning and release-risk annotation; does not hard-block until v2.0.

### INV-SEM-RES-003 Residuals are mechanical

- Formal statement: Residual values are computed from auditable primitive inputs using deterministic formulas, never free-form judgment. Derived summaries may be logged for performance but cannot be the sole recomputation substrate.
- Evidence contract:
  - run manifest field `residual_formula_version` (authoritative source of truth),
  - `residual_inputs.primitive_inputs` logged per attempt,
  - `residual_inputs.provenance` logged (state/model/formula pointers),
  - `version_pointers.residual_formula_version` logged per attempt,
  - optional `residual_inputs.derived_inputs`,
  - likelihood evidence sketch logged (`likelihood_sketch`),
  - residual formula version equality across manifest, `version_pointers`, and residual provenance.
- Predicate:
  - `all(attempts, eq(attempt.version_pointers.residual_formula_version, run_manifest(attempt.run_id).residual_formula_version))`
  - `and all(attempts, eq(attempt.residual_inputs.provenance.residual_formula_version, run_manifest(attempt.run_id).residual_formula_version))`
  - `all(attempts, recompute_residuals_from_primitives(attempt.residual_inputs.primitive_inputs, attempt.residual_inputs.provenance, run_manifest(attempt.run_id).residual_formula_version) == attempt.residuals)`
  - `and all(attempts, field(attempt.residual_inputs, "likelihood_sketch"))`.
- Failure action: block merge for residual logic; quarantine affected items; fail v0.4 residual gate if primitive recomputation is not possible.

### INV-EPI-CAL-004 Posterior predictive checks run and logged

- Formal statement: Predictive checks (log score/Brier or equivalent) are continuously computed and logged by defined strata.
- Evidence contract: calibration log with metric values, strata, timestamps, trigger outcomes.
- Predicate: `exists(calibration_log) and all(required_strata, any(calibration_log, row.stratum == required_stratum))`.
- Failure action: block release; enter safe mode on runtime gap once implemented.

### INV-EPI-CAL-004B Calibration governs diagnosis authority

- Formal statement: Persistent miscalibration in a stratum must reduce epistemic authority for diagnosis updates in that stratum via deterministic governor actions (throttle/strong_throttle/freeze), in addition to safe-mode/profile response. This yields bounded diagnosis-state movement under calibration failure.
- Evidence contract:
  - calibration status by stratum, persistence counters, and alarm state,
  - state-update fields `calibration_status_at_update`, `applied_update_multiplier`, `governor_decision`, `governor_reason`, `stratum_id`, `safe_mode_profile_id`,
  - anchor/shadow pressure adjustments when governor escalates.
- Governor escalation ladder (per stratum):
  - `normal`: multiplier `1.00`
  - `throttle`: multiplier `0.50`
  - `strong_throttle`: multiplier `0.20`
  - `freeze`: multiplier `0.00`
- Predicate:
  - `all(diagnosis_state_updates, field(update, "calibration_status_at_update") and field(update, "applied_update_multiplier") and field(update, "governor_decision") and field(update, "governor_reason") and field(update, "stratum_id") and field(update, "safe_mode_profile_id"))`
  - `and all(diagnosis_state_updates, implies(eq(update.safe_mode_profile_id, "SG_CALIBRATION_GUARD"), eq(update.applied_update_multiplier, governor_multiplier(update.governor_decision))))`
  - `and all(strata_with_persistent_miscalibration, has_calibration_safe_mode_response(stratum))`
  - `and all(strata_with_persistent_miscalibration, governor_decision(stratum) in {"throttle","strong_throttle","freeze"})`.
- Failure action: block release at v1.1 and mark diagnosis-state outputs for affected strata as low-authority.

### INV-EPI-EXP-005A Propensity logging support exists

- Formal statement: For each routing decision, candidate actions and their probabilities are logged, and chosen action probability is explicitly recorded.
- Evidence contract: `decision_traces.candidate_actions[]`, `decision_traces.chosen_action_id`, `decision_traces.chosen_action_probability`.
- Predicate: `all(decisions, sum_p(decision)=1 and decision.chosen_action_id in action_ids(decision) and decision.chosen_action_probability == p(decision.chosen_action_id, decision))`.
- Failure action: block policy/OPE logging-related merges once activated.

### INV-EPI-EXP-005B Entropy/support floor enforced

- Formal statement: Routing policy must enforce minimum exploration entropy/support constraints so OPE counterfactual comparisons are structurally viable.
- Evidence contract: entropy floor config, run-level OPE support classification, and per-decision support checks (`entropy_floor_met`, `min_support_met`, `support_check_status`).
- Predicate: `all(decisions, entropy(candidates(decision))>=entropy_floor and support_constraints_satisfied(decision))`.
- Failure action: block policy release and mark OPE outputs as unsupported for counterfactual comparison.

### INV-OPS-SEN-006 Sentinel fixtures pass

- Formal statement: Fixed fixture suite passes in CI and periodic runtime self-test.
- Evidence contract: fixture reports by run/build; drift status.
- Predicate: `all(required_fixture_sets, latest_report(fixture_set).status == "pass")`.
- Failure action: block release; force safe mode at runtime.

### INV-EPI-HLD-007 Holdout contamination tracked

- Formal statement: Holdout exposure, contamination index, and retirement/rotation behavior are tracked and enforced.
- Evidence contract: holdout attempt logs (`holdout_flag`, exposure/contamination before/after counters, `policy_decisions[]`) and policy decision logs.
- Predicate:
  - `all(holdout_attempts, field(attempt, "holdout_exposure_counter_before") and field(attempt, "holdout_exposure_counter_after") and field(attempt, "contamination_index_before") and field(attempt, "contamination_index_after") and field(attempt, "policy_decisions"))`
  - `and all(holdout_attempts, attempt.holdout_exposure_counter_after >= attempt.holdout_exposure_counter_before)`
  - `and all(holdout_attempts, attempt.contamination_index_after >= attempt.contamination_index_before)`
  - `and all(holdout_attempts, any(attempt.policy_decisions, policy_applied(decision)))`.
- Failure action: block holdout-based claims and certification outputs.

### INV-EPI-ANC-008 Anchor quotas enforced

- Formal statement: Anchor sampling minimums and belief-audit discrepancy logging are enforced.
- Evidence contract: anchor scheduling logs; quota config; audit records.
- Predicate: `all(time_windows, window.anchors_sampled >= window.quota_min and any(belief_audit_records, eq(record.window_id, window.window_id)))`.
- Failure action: block release for controller changes.

### INV-EPI-NIV-009 Non-invariance guardrails active

- Formal statement: Item weirdness and family health are computed; quarantine path exists for suspect items/families.
- Evidence contract: invariance metrics log and quarantine events.
- Predicate: `exists(invariance_log) and all(threshold_crossings, quarantine_event_emitted(crossing))`.
- Failure action: block release of affected content/model bundle.

### INV-OPS-VSN-010 Versioned semantics

- Formal statement: Every run and downstream artifact references immutable versions, and no mixed semantics are allowed within a run.
- Evidence contract:
  - run manifest with required canonical and replay tuple fields,
  - attempt/state records reference `run_id` and include `version_pointers`,
  - residual formula version appears in manifest, attempt version pointers, and residual provenance.
- Predicate:
  - `all(runs, has_version_tuple(run) and has_replay_tuple(run))`
  - `and all(attempts, valid_manifest_ref(attempt.run_id))`
  - `and all(attempts, attempt.version_pointers == replay_tuple_projection(run_manifest(attempt.run_id)))`
  - `and all(states, state.version_pointers == replay_tuple_projection(run_manifest(state.run_id)))`
  - `and all(attempts, eq(attempt.version_pointers.residual_formula_version, run_manifest(attempt.run_id).residual_formula_version))`.
- Failure action: hard release block.

### INV-OPS-LOG-012 No unlogged diagnosis-state mutation

- Formal statement: Diagnosis-state mutation is valid only when required state-update logging succeeds and is committed. If required log write fails or is missing, diagnosis-state mutation must not be applied.
- Evidence contract:
  - state-update fields `diagnosis_log_write_status`, `log_commit_id`, `mutation_applied`, `integrity_event_id`,
  - `update_id` persisted for each state update event.
- Predicate:
  - `all(state_update_events, field(update, "diagnosis_log_write_status") and field(update, "mutation_applied") and field(update, "update_id"))`
  - `and all(diagnosis_state_updates, implies(eq(update.diagnosis_log_write_status, "committed"), eq(update.mutation_applied, true)))`
  - `and all(diagnosis_state_updates, implies(update.diagnosis_log_write_status in {"failed","missing"}, eq(update.mutation_applied, false)))`
  - `and all(diagnosis_state_updates, implies(eq(update.mutation_applied, true), eq(update.diagnosis_log_write_status, "committed")))`.
- Failure action: block release at v0.1, emit integrity incident, and invalidate affected diagnosis-state outputs.

### INV-SAF-SFM-011 Safe mode degrades predictably

- Formal statement: Triggered safe mode must apply a deterministic state transition and deterministic profile-specific degraded policy bundle.
- Evidence contract: safe-mode transition logs with trigger set, dominant trigger id, resulting state, resulting profile id, and policy bundle hash.
- Predicate: `all(transitions, transition.next_state == spec_state(transition.trigger_set, transition.prior_state) and transition.profile_id == spec_profile(transition.trigger_set, transition.prior_state, transition.next_state) and transition.policy_bundle_hash == spec_policy_bundle_hash(transition.profile_id))`.
- Failure action: hard release block and panic escalation.

## 5) v0.0 Enforced Subset

The following are enforced in v0.0:

- INV-OPS-VSN-010
- INV-SAF-SFM-011
- SOFT-SEM-CBG-000 (soft_enforced policy default with warning-grade violations)
- Presence and frozen definitions for all remaining invariants in this charter

All other invariants are contract-frozen in v0.0 and become enforceable at their activation stages.

## 6) Change Control

- Any invariant edit requires version bump and change note.
- Removing an invariant requires explicit deprecation rationale and replacement strategy.
- Predicates may be tightened in patch versions; they may not be weakened without major version bump.
