# Merge and Release Gate Matrix v0.0

Version: `0.0.0`  
Effective date: `2026-02-27`

## 1) Purpose

Provide explicit hard gates for v0.0 and declared gates for later stages.  
This prevents accidental over-blocking before capabilities exist.

## 2) Gate Modes

- `enforced`: must pass now.
- `declared`: contract frozen now, enforcement starts at activation stage.

## 3) Gate Matrix

| Gate ID | Gate Type | Mode | Activation Stage | Predicate | Failure Action |
| --- | --- | --- | --- | --- | --- |
| G-MRG-V00-001 | merge | enforced | v0.0 | all v0.0 spec artifacts exist | block merge |
| G-MRG-V00-002 | merge | enforced | v0.0 | invariants, safe-mode, and manifest versions are consistent across docs | block merge |
| G-MRG-V00-003 | merge | enforced | v0.0 | v0.0 acceptance plan defines AT-1..AT-11 with expected outcomes | block merge |
| G-MRG-V00-004 | merge | enforced | v0.0 | every invariant predicate term is operationalizable (defined in charter predicate language or operationalization matrix) | block merge |
| G-REL-V00-001 | release | enforced | v0.0 | release candidate includes manifest contract and canonical version tuple | block release |
| G-REL-V00-004 | release | enforced | v0.0 | release candidate includes replay tuple contract and canonical/replay fingerprint definitions | block release |
| G-REL-V00-002 | release | enforced | v0.0 | panic drill report exists and passes | block release |
| G-REL-V00-003 | release | enforced | v0.0 | v0.0 acceptance report exists and passes | block release |
| G-RUN-V00-001 | runtime | enforced | v0.0 | panic trigger maps deterministically to `SAFE_PANIC` state and panic profile id, and `SAFE_PANIC` policy disables all LLM calls | abort run start |
| G-RUN-V00-002 | runtime | enforced | v0.0 | invalid/missing manifest triggers `SAFE_PANIC` | abort run start |
| G-RUN-V01-RPL | runtime | declared | v0.1 | run manifests include complete replay tuple fields and replay fingerprint; missing fields are invalid | abort run start at v0.1 |
| G-RUN-V01-NOMIX | runtime | declared | v0.1 | attempt/state `version_pointers` and residual formula pointers match the run manifest; mixed semantics within a run are invalid | abort run at v0.1 |
| G-RUN-V01-PREQ | runtime | declared | v0.1 | each `attempt_observed` binds to a committed `attempt_precommitted` artifact (`precommit_event_id`, `precommit_hash`) with `presented_ts_utc <= attempt_ts_utc`, identity binding integrity, intended-vs-observed semantics coherence (`evidence_channel`, assistance monotonicity, diagnosis semantics), and complete telemetry-window binding (`telemetry_event_ids` equals full in-window committed telemetry set) | abort run at v0.1 |
| G-RUN-V01-PREQSEQ | runtime | declared | v0.1 | event-ledger sequencing proves prequential authenticity for each attempt: `attempt_precommitted` occurs before `response_submitted` telemetry, which occurs before/equal `attempt_observed`; explicit `events` input is required | abort run at v0.1 |
| G-RUN-V01-EVTBIND | runtime | declared | v0.1 | when both are provided, typed record lists and event ledger must be equivalent views (same ids and payload hashes for attempts/precommits/telemetry/snapshots/updates/migrations); explicit `events` input is required | abort run at v0.1 |
| G-RUN-V01-PROVREF | runtime | declared | v0.1 | attempt provenance `state_snapshot_id` references an existing lineage node (`__genesis__` allowed) and referenced snapshot timestamp is not after attempt timestamp | abort run at v0.1 |
| G-RUN-V01-REFINT | runtime | declared | v0.1 | state updates reference committed/valid source attempts and maintain partition authorization + diagnosis eligibility coherence (`diagnosis_state` updates require eligible closed-book diagnostic source attempts with telemetry-derived assistance) | abort run at v0.1 |
| G-RUN-V01-UPDSNAPREF | runtime | declared | v0.1 | each state update `snapshot_id` references known snapshot lineage (`__genesis__` allowed) | abort run at v0.1 |
| G-RUN-V01-GOVEVENTS | runtime | declared | v0.1 | governance events (`safe_mode_transition`, `quarantine_decision`, `anchor_audit`) satisfy mechanical payload contracts; safe-mode transition sequence is deterministic and state-coherent; each `state_update.safe_mode_profile_id` matches the active safe-mode transition profile in event order; and explicit `events` input is required | abort run at v0.1 |
| G-RUN-V01-EVORD | runtime | declared | v0.1 | event ledger integrity checks pass (`event_id` uniqueness, type-prefix namespace, `event_type` validity, header/payload run binding coherence, unique positive `ledger_sequence_no`, and non-decreasing `event_written_ts_utc` by sequence); replay ordering uses `ledger_sequence_no` + append-time metadata only | abort run at v0.1 |
| G-RUN-V01-REPLAYSTATE | runtime | declared | v0.1 | deterministic replay over canonical event order must produce final state hash equal to the latest committed snapshot checkpoint hash (when checkpoint exists); for non-initial epochs replay requires manifest-declared migration coherence and migration-before-precommit sequencing | abort run at v0.1 |
| G-RUN-V01-LOGATOMIC | runtime | declared | v0.1 | diagnosis-state mutation is allowed only when `diagnosis_log_write_status=committed`; failed/missing required diagnosis-log writes force `mutation_applied=false` and integrity event emission | abort mutation at v0.1 |
| G-MRG-V01-LEDGER | merge | declared | v0.1 | attempt/precommit/telemetry/state contracts include required fields, idempotency keys, canonical/replay version pointers, no-mixed-semantics rules, complete telemetry-window integrity, precommit binding integrity, and epoch lineage/migration coherence for non-initial runs | block merge at v0.1 |
| G-MRG-V01-POLICYDEC | merge | declared | v0.1 | attempt contracts include `policy_decisions[]` with required fields (`decision_id`, `outcome`, `commit_status`, support-check fields), `decision_traces.decision_id` join integrity, and baseline `trace_kind`/`policy_domain` semantic alignment | block merge at v0.1 |
| G-MRG-V01-LOGATOMIC | merge | declared | v0.1 | state-update contracts include log-atomicity fields (`diagnosis_log_write_status`, `log_commit_id`, `mutation_applied`, `integrity_event_id`) and no-unlogged-mutation rules | block merge at v0.1 |
| G-MRG-V01-REFINT | merge | declared | v0.1 | update bundles are referentially integral against validated attempt bundles with partition authorization and diagnosis semantics coherence | block merge at v0.1 |
| G-MRG-V01-CBGSOFT | merge | declared | v0.1 | attempt logs include `diagnosis_update_eligibility`, `ineligibility_reason`, `allowed_update_partitions`; ineligible attempts must not authorize `diagnosis_state` and updates must remain partition-authorized | block merge at v0.1 |
| G-MRG-V01-CALGOVLOG | merge | declared | v0.1 | state-update contracts include calibration-governor fields (`calibration_status_at_update`, `applied_update_multiplier`, `governor_decision`, `governor_reason`, `stratum_id`, `safe_mode_profile_id`, `governor_transform_version`, `proposed_state_patch`, `base_value_at_proposal`) and diagnosis-state governed transform coherence | block merge at v0.1 |
| G-MRG-V01-EXPLOG | merge | declared | v0.1 | every decision logs `decision_traces.trace_kind`, `candidate_actions[]`, and `chosen_action_probability`; candidate `action_id` values are unique per trace; probabilities are normalized; chosen action probability matches logged candidate probability; and `trace_kind` is in the frozen ontology | block merge at v0.1 |
| G-MRG-V01-GOVLOG | merge | declared | v0.1 | governance event logs satisfy deterministic contracts (`safe_mode_transition` state/profile/bundle determinism; quarantine threshold-linkage; anchor-audit quota/cross-grade fields), state-update safe-mode profile binding to the active transition profile, and explicit `events` input is required | block merge at v0.1 |
| G-MRG-V01-EVTBIND | merge | declared | v0.1 | typed record bundles and provided event ledger must be equivalent representations (same ids and payload hashes across typed classes); explicit `events` input is required | block merge at v0.1 |
| G-REL-V01-OPECLASS | release | declared | v0.1 | run manifest includes `ope_support_level` + `ope_claim_contract`; `propensity_only` requires valid propensity logs for each target trace kind; `full_support` requires target-trace threshold pass (`min_stochastic_fraction`, `min_candidate_probability`, `min_chosen_probability`, `min_entropy_bits`, `min_context_coverage_fraction`, `min_decisions_per_context`) plus support-check evidence (`entropy_floor_met=true`, `min_support_met=true`, `support_check_status=pass`) for target decision kinds | block release at v0.1 |
| G-MRG-V03-DET | merge | declared | v0.3 | deterministic-first grading checks pass for deterministic-rubric items | block merge at v0.3 |
| G-MRG-V06-RES | merge | declared | v0.4 | residual recomputation from `primitive_inputs + provenance` equals logged residuals; derived-only recompute is invalid | block merge at v0.4 |
| G-REL-V11-SFBR | release | declared | v1.1 | safe-mode profile branching coverage exists by trigger family and no active trigger is unmapped | block release at v1.1 |
| G-REL-V08-SEN | release | declared | v0.5 | sentinel fixture suite pass in CI and runtime self-test | block release at v0.5 |
| G-REL-V11-CAL | release | declared | v1.1 | calibration checks logged and safe-mode triggers wired | block release at v1.1 |
| G-REL-V11-CALGOV | release | declared | v1.1 | persistent miscalibration triggers both safe-mode/profile action and bounded diagnosis-state movement by stratum (`throttle/strong_throttle/freeze`) with logged governor fields | block release at v1.1 |
| G-REL-V12-EXP | release | declared | v1.2 | entropy/support floor is enforced and run `ope_support_level` qualifies as `full_support` only when support checks pass | block release at v1.2 |
| G-REL-V13-NIV | release | declared | v1.3 | non-invariance metrics and quarantine routing active | block release at v1.3 |
| G-REL-V20-CBG | release | declared | v2.0 | closed-book diagnosis gating enforced and ineligible diagnosis updates applied to `diagnosis_state` are zero | block release at v2.0 |
| G-REL-V21-HLD | release | declared | v2.1 | holdout contamination protocol active | block release at v2.1 |
| G-REL-V22-ANC | release | declared | v2.2 | anchor quotas and belief audits active | block release at v2.2 |

## 4) v0.0 Hard-Block Inputs

- docs/v0.0/README.md
- docs/v0.0/01_invariants_charter_v0.0.md
- docs/v0.0/02_safe_mode_and_panic_spec_v0.0.md
- docs/v0.0/03_run_manifest_and_release_discipline_v0.0.md
- docs/v0.0/04_merge_release_gate_matrix_v0.0.md
- docs/v0.0/05_acceptance_test_plan_v0.0.md
- docs/v0.0/06_v0.1_interface_preconditions.md
- docs/v0.0/07_predicate_operationalization_matrix_v0.0.md

## 5) Verification Notes

- Version consistency means `0.0.0` appears as the active version for all v0.0 spec artifacts.
- "Exists and passes" for reports is satisfied by dry-run sign-off in v0.0, then by automated evidence once implemented.
- For residual gates, recomputability must be demonstrated from auditable primitives, not only summary statistics.
- Canonical tuple gates enforce semantic validity; replay tuple gates enforce interpretability and policy comparability.
- Safe-mode states are severity buckets; profile ids are the deterministic policy surface.
- Pre-v2.0 closed-book diagnosis behavior is debt-prevention by policy default; v2.0 promotes this to hard-zero enforcement for ineligible diagnosis updates.
- Exploration support is staged but claim semantics are strict: `propensity_only` means logs exist; `full_support` means target-kind overlap/support thresholds and support checks pass.
- Canonical event-ledger input is mandatory for v0.1 gate evaluation; typed lists are auxiliary comparands for `G-*-EVTBIND` only.
- Event-dependent gates are non-optional: missing event ledgers produce hard failure (or evaluation refusal), never green defaults.
- Timestamp anti-time-travel checks are v0.1 integrity guards under an honest-clock assumption; stronger trusted-time authority is a future hardening item.
- Version pointers are integrity constraints, not metadata: no mixed semantics are allowed within a run.
- Calibration is a governor, not only observability: persistent miscalibration must throttle/freeze diagnosis authority by stratum.
- In `SG_CALIBRATION_GUARD`, diagnosis update multipliers are governed by the calibration ladder (`0.50`, `0.20`, `0.00`) and must be logged on each diagnosis-state update.
- State mutation requires durable logging: no diagnosis-state update is valid unless required state-update log write is committed.
- Predicate compliance is mechanical: undefined or interpretation-only predicate terms are non-compliant until operationalized in charter/matrix.

