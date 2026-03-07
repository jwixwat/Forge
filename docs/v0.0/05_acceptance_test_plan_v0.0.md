# V0.0 Acceptance Test Plan

Version: `0.0.0`  
Effective date: `2026-02-27`

## 1) Purpose

Define v0.0 acceptance criteria and dry-run runbook before implementation.

This plan covers:

- AT-1 Panic determinism
- AT-2 Panic latency
- AT-3 Version traceability
- AT-4 Release blocking
- AT-5 Invariant policy presence
- AT-6 Safe-mode auditability
- AT-7 Pre-enforcement diagnosis debt prevention
- AT-8 Exploration support staging
- AT-9 Calibration governor authority
- AT-10 No-unlogged-mutation integrity
- AT-11 Predicate operationalizability

## 2) Execution Mode

For v0.0, tests are `tabletop_dry_run`:

- no runtime code required
- expected behavior checked against formal specs
- evidence recorded in acceptance report

## 3) Test Cases

### AT-1 Panic Determinism

- Goal: same prior state plus same trigger set yields same next state/profile, and trigger-family profile branching is deterministic.
- Method: evaluate transition and profile-selection rules in safe-mode spec for repeated identical inputs and cross-trigger comparisons.
- Inputs:
  - case A:
    - prior state: `NORMAL`
    - trigger: `TRG-MANUAL-PANIC`
  - case B:
    - prior state: `NORMAL`
    - triggers:
      - `TRG-CALIBRATION-ALARM`
      - `TRG-SENSOR-UNRELIABLE-HIGH`
      - `TRG-SPEC-UNDERDETERMINED-HIGH`
- Expected:
  - case A:
    - next state always `SAFE_PANIC`
    - profile mapping always `SP_MANUAL_PANIC`
    - `SAFE_PANIC` policy enforces zero LLM calls
  - case B:
    - each trigger maps to `SAFE_GUARDED`
    - each trigger maps to a distinct deterministic profile id:
      - `SG_CALIBRATION_GUARD`
      - `SG_SENSOR_UNRELIABLE_GUARD`
      - `SG_SPEC_UNDERDETERMINED_GUARD`
- Evidence artifact: `acceptance_report.at_1`.

### AT-2 Panic Latency

- Goal: panic state applies before next routing decision.
- Method: sequence walk-through with trigger event inserted between step `n` and selection `n+1`.
- Inputs:
  - running session timeline
  - manual panic activation at `t`
- Expected:
  - first post-trigger routing decision uses `SAFE_PANIC` constraints
- Evidence artifact: `acceptance_report.at_2`.

### AT-3 Version Traceability

- Goal: every run artifact can be traced to canonical and replay tuples with explicit comparand semantics.
- Method: manifest and log contract review.
- Inputs:
  - run manifest contract
  - attempt/state contracts
  - two dry-run manifest examples:
    - M1 and M2 share canonical tuple
    - M1 and M2 differ in replay tuple (for example `policy_version`)
- Expected:
  - canonical tuple is defined
  - replay tuple is defined
  - canonical/replay fingerprints are defined
  - attempt/state records must carry `run_id` reference
  - attempt/state records include version pointers sufficient to resolve replay context
  - attempt/state records in run `R` must have version pointers equal to manifest replay projection for `R`
  - residual formula version is pinned and equal across manifest, attempt version pointers, and residual provenance
  - same-canonical/different-replay is treated as valid and intentional (policy comparand), not compliance failure
- Evidence artifact: `acceptance_report.at_3`.

### AT-4 Release Blocking

- Goal: release is blocked when version contract is incomplete.
- Method: negative-case dry-run using candidate with missing tuple field.
- Inputs:
  - mock release candidate missing `sensor_model_version`
- Expected:
  - gate `G-REL-V00-001` fails
  - release outcome is `blocked`
- Evidence artifact: `acceptance_report.at_4`.

### AT-5 Invariant Policy Presence

- Goal: merge is blocked unless invariants charter and gate matrix are present and coherent.
- Method: document existence and consistency review.
- Inputs:
  - v0.0 spec package
- Expected:
  - all required artifacts present
  - invariant ids and gate ids are consistent
  - residual invariant and v0.4 gate require primitive-input recomputation, not derived-only recomputation
- Evidence artifact: `acceptance_report.at_5`.

### AT-6 Safe-Mode Auditability

- Goal: transitions are auditable with required metadata.
- Method: event schema review against safe-mode logging contract.
- Inputs:
  - safe-mode event field list
- Expected:
  - event contract includes trigger set, dominant trigger id, prior/next state, profile id, profile resolution version, timestamp, reason
- Evidence artifact: `acceptance_report.at_6`.

### AT-7 Pre-Enforcement Diagnosis Debt Prevention

- Goal: ensure pre-v2.0 policy contract exists to avoid contaminated diagnosis-state updates.
- Method: policy/contract dry-run review using eligible and ineligible attempt examples.
- Inputs:
  - invariants charter soft invariant `SOFT-SEM-CBG-000`
  - v0.1 attempt contract for diagnosis-governance fields
  - gate matrix entries for v0.1 soft logging and v2.0 hard enforcement
- Expected:
  - policy default is explicit: ineligible evidence must not authorize `diagnosis_state` in `allowed_update_partitions`
  - required fields exist: `diagnosis_update_eligibility`, `ineligibility_reason`, `allowed_update_partitions`
  - hard v2.0 gate explicitly requires zero ineligible diagnosis updates applied to `diagnosis_state`
- Evidence artifact: `acceptance_report.at_7`.

### AT-8 Exploration Support Staging

- Goal: ensure exploration support is explicitly staged as propensity logging first, entropy/support floor later.
- Method: invariant and gate contract dry-run review.
- Inputs:
  - invariants charter exploration split (`INV-EPI-EXP-005A`, `INV-EPI-EXP-005B`)
  - v0.1 attempt contract `decision_traces` validity rules
  - run manifest OPE support classification contract (`ope_support_level`)
  - gate matrix entries for v0.1 and v1.2 exploration stages
- Expected:
  - propensity logging invariant activates at v0.1 and is decoupled from entropy floor enforcement
  - entropy/support floor invariant activates at v1.2
  - deterministic-policy runs are not labeled `full_support`
  - `full_support` classification requires explicit routing support-check evidence (`entropy_floor_met=true`, `min_support_met=true`, `support_check_status=pass`) in addition to stochastic routing propensities
  - OPE caveat for `propensity_only` runs is explicit
- Evidence artifact: `acceptance_report.at_8`.

### AT-9 Calibration Governor Authority

- Goal: ensure persistent miscalibration deterministically governs diagnosis authority, not only safe-mode visibility.
- Method: simulated persistent-miscalibration dry-run across one stratum with escalating governor decisions.
- Inputs:
  - stratum id example: `math.linear_algebra.vector_spaces`
  - calibration status timeline showing persistent failure across escalation windows
  - state-update event contract and safe-mode profile contract
  - gate matrix entries `G-REL-V11-CAL` and `G-REL-V11-CALGOV`
- Expected:
  - `TRG-CALIBRATION-ALARM` maps to `SAFE_GUARDED` with profile `SG_CALIBRATION_GUARD`
  - diagnosis-state updates include required governor fields:
    - `calibration_status_at_update`
    - `applied_update_multiplier`
    - `governor_decision`
    - `governor_reason`
    - `stratum_id`
    - `safe_mode_profile_id`
  - escalation path is represented as `throttle -> strong_throttle -> freeze`
  - applied multipliers follow the ladder values `0.50 -> 0.20 -> 0.00`
  - once `freeze` is active, diagnosis updates for that stratum stop (`state_patch.partition != diagnosis_state`)
  - anchor/shadow pressure is elevated under calibration guard (3x target by profile contract)
- Evidence artifact: `acceptance_report.at_9`.

### AT-10 No-Unlogged-Mutation Integrity

- Goal: ensure diagnosis-state movement is blocked when required state-update log write is not committed.
- Method: dry-run contract check with committed and failed/missing log-write cases.
- Inputs:
  - state-update event contract (`diagnosis_log_write_status`, `mutation_applied`, `integrity_event_id`)
  - invariant `INV-OPS-LOG-012`
  - gate matrix entries `G-MRG-V01-LOGATOMIC` and `G-RUN-V01-LOGATOMIC`
- Expected:
  - when `state_patch.partition = diagnosis_state` and `diagnosis_log_write_status = committed`, mutation may apply (`mutation_applied = true`)
  - when `state_patch.partition = diagnosis_state` and `diagnosis_log_write_status in {failed, missing}`, mutation is blocked (`mutation_applied = false`)
  - failed/missing diagnosis-state log writes produce an integrity incident id
  - no case exists where `mutation_applied = true` with non-committed log status
- Evidence artifact: `acceptance_report.at_10`.

### AT-11 Predicate Operationalizability

- Goal: ensure every invariant predicate can be evaluated as deterministic queries over manifests/logs without human interpretation.
- Method: charter and operationalization-matrix cross-check.
- Inputs:
  - invariant predicates in `01_invariants_charter_v0.0.md`
  - predicate-language definitions
  - operationalization matrix `07_predicate_operationalization_matrix_v0.0.md`
  - gate `G-MRG-V00-004`
- Expected:
  - every non-primitive predicate term resolves to a charter definition or matrix entry
  - no unresolved symbols remain in predicates
  - ambiguous terms (for example `policy_applied`) are grounded in concrete fields
  - each invariant row has query sources and required fields documented in the matrix
- Evidence artifact: `acceptance_report.at_11`.

## 4) Pass Criteria

All of the following must be true:

- AT-1 through AT-6 each marked `pass`
- AT-7 marked `pass`
- AT-8 marked `pass`
- AT-9 marked `pass`
- AT-10 marked `pass`
- AT-11 marked `pass`
- no unresolved ambiguities in transition or manifest rules
- architecture owner sign-off recorded

## 5) Acceptance Report Template

Use this shape for v0.0 sign-off:

```json
{
  "schema_version": "0.0.0",
  "executed_at_utc": "2026-02-27T00:00:00Z",
  "mode": "tabletop_dry_run",
  "results": {
    "AT-1": "pass",
    "AT-2": "pass",
    "AT-3": "pass",
    "AT-4": "pass",
    "AT-5": "pass",
    "AT-6": "pass",
    "AT-7": "pass",
    "AT-8": "pass",
    "AT-9": "pass",
    "AT-10": "pass",
    "AT-11": "pass"
  },
  "notes": [],
  "approver": "architecture_owner"
}
```

## 6) Exit to v0.1

v0.0 is complete when:

- this test plan is approved
- acceptance report is produced and passed
- gates `G-MRG-V00-001..004`, `G-REL-V00-001..004`, `G-RUN-V00-001..002` are satisfied by policy
