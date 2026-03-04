# Safe Mode and Panic Spec v0.0

Version: `0.0.0`  
Effective date: `2026-02-27`  
Depends on: `01_invariants_charter_v0.0.md`

## 1) Purpose

Define deterministic runtime degradation behavior for integrity and epistemic risk events.  
This document satisfies v0.0 requirement for a panic switch and predictable degraded behavior.

## 2) State Model

Runtime safety state is one of:

- `NORMAL`
- `SAFE_GUARDED`
- `SAFE_PANIC`

State must be logged on each transition and at session start.

State is a coarse severity bucket only.  
Deterministic policy behavior is carried by `profile_id`, not by state alone.

## 3) Trigger Taxonomy

| Trigger ID | Trigger Class | Description | Severity | Target State | v0.0 Availability |
| --- | --- | --- | --- | --- | --- |
| TRG-MANUAL-PANIC | manual_control | Operator/manual panic activation | P0 | SAFE_PANIC | required |
| TRG-MANIFEST-INVALID | manifest_integrity | Run manifest missing or invalid version tuple | P0 | SAFE_PANIC | required |
| TRG-FIXTURE-FAIL | fixture_integrity | Sentinel fixture failure indicates grading stack may be invalid | P0 | SAFE_PANIC | declared |
| TRG-CALIBRATION-ALARM | predictive_calibration | Persistent miscalibration alarm | P1 | SAFE_GUARDED | declared |
| TRG-SENSOR-UNRELIABLE-HIGH | sensor_health | Residual sensor unreliability above threshold | P1 | SAFE_GUARDED | declared |
| TRG-SPEC-UNDERDETERMINED-HIGH | spec_ambiguity | Residual ambiguity above threshold | P2 | SAFE_GUARDED | declared |

Severity ordering: `P0 > P1 > P2`.

## 4) Transition Rules

Transition function is deterministic:

1. If trigger is `TRG-MANUAL-PANIC`, next state is `SAFE_PANIC`.
2. If trigger is `TRG-MANIFEST-INVALID`, next state is `SAFE_PANIC`.
3. If trigger is `TRG-FIXTURE-FAIL`, next state is `SAFE_PANIC`.
4. If current state is `NORMAL` and trigger severity is `P1` or `P2`, next state is `SAFE_GUARDED`.
5. If current state is `SAFE_GUARDED` and trigger severity escalates to `P0`, next state is `SAFE_PANIC`.
6. `SAFE_PANIC` cannot auto-clear.

Exit rules:

- `SAFE_GUARDED -> NORMAL` requires:
  - no active P1/P0 triggers
  - explicit clear event
  - two consecutive healthy checks (where checks exist)
- `SAFE_PANIC -> SAFE_GUARDED` requires manual clear by authorized actor.
- `SAFE_PANIC -> NORMAL` is not allowed directly.

## 5) Deterministic Profile Selection

Profile selection is deterministic and separate from state transition:

- `next_state = spec_state(trigger_set, prior_state)`
- `profile_id = spec_profile(trigger_set, prior_state, next_state)`

### 5.1 Single-trigger profile map

| Trigger ID | Next State | Profile ID |
| --- | --- | --- |
| TRG-MANUAL-PANIC | SAFE_PANIC | SP_MANUAL_PANIC |
| TRG-MANIFEST-INVALID | SAFE_PANIC | SP_MANIFEST_INVALID |
| TRG-FIXTURE-FAIL | SAFE_PANIC | SP_FIXTURE_FAILURE_PANIC |
| TRG-CALIBRATION-ALARM | SAFE_GUARDED | SG_CALIBRATION_GUARD |
| TRG-SENSOR-UNRELIABLE-HIGH | SAFE_GUARDED | SG_SENSOR_UNRELIABLE_GUARD |
| TRG-SPEC-UNDERDETERMINED-HIGH | SAFE_GUARDED | SG_SPEC_UNDERDETERMINED_GUARD |

### 5.2 Multi-trigger profile precedence

When multiple triggers are active:

1. `next_state` is chosen by transition rules and highest severity.
2. `dominant_trigger_id` is selected by this precedence list:
   - `TRG-MANUAL-PANIC`
   - `TRG-MANIFEST-INVALID`
   - `TRG-FIXTURE-FAIL`
   - `TRG-SENSOR-UNRELIABLE-HIGH`
   - `TRG-CALIBRATION-ALARM`
   - `TRG-SPEC-UNDERDETERMINED-HIGH`
3. Ties at equal precedence use lexical order of `trigger_id`.
4. `profile_id` is derived from `dominant_trigger_id` and `next_state`.
5. If a trigger is unknown to this spec version, fallback profiles are:
   - `SG_GENERIC_GUARD` when `next_state = SAFE_GUARDED`
   - `SP_GENERIC_PANIC` when `next_state = SAFE_PANIC`

## 6) Degraded Policy Profiles

Base policy by state:

| Dimension | NORMAL | SAFE_GUARDED | SAFE_PANIC |
| --- | --- | --- | --- |
| Allowed response formats | all enabled by stage | structured only (`mcq`,`slots`,`schema_short`) | structured deterministic only |
| Diagnosis update multiplier | `1.00` | `0.35` (except calibration-governed profiles) | `0.00` |
| LLM policy | allowed under deterministic-first rule | allowed only as parser helper; no standalone grade decision | no LLM calls |
| Routing scope | full stage-enabled actions | conservative actions only, no aggressive reroute | measurement and defer only |
| Anchor/shadow sampling | baseline quotas | 2x target (when channels available) | 3x target (when channels available) |
| Feedback | normal | minimal and structured | minimal, no high-variance feedback |

If a capability is unavailable at current stage, profile behavior is recorded as `declared_noop`.

Profile-specific overrides:

| Profile ID | Parent State | Deterministic Overrides |
| --- | --- | --- |
| SG_CALIBRATION_GUARD | SAFE_GUARDED | Diagnosis update multiplier is governor-controlled per stratum: `throttle=0.50`, `strong_throttle=0.20`, `freeze=0.00`; increase anchor/shadow target to 3x; prefer shortest structured measurement probes |
| SG_SENSOR_UNRELIABLE_GUARD | SAFE_GUARDED | Diagnosis update multiplier `0.10`; require deterministic rubric confirmation path; disable non-essential LLM grading assistance |
| SG_SPEC_UNDERDETERMINED_GUARD | SAFE_GUARDED | Quarantine flagged item/family; learner penalty on flagged attempts set to `0`; open content defect ticket |
| SG_GENERIC_GUARD | SAFE_GUARDED | No additional override beyond guarded baseline |
| SP_MANUAL_PANIC | SAFE_PANIC | Diagnosis updates `0.00`; routing restricted to measure/defer; LLM calls `0`; manual clear required |
| SP_MANIFEST_INVALID | SAFE_PANIC | Abort run start or resume; block learner-facing grading until manifest is valid; LLM calls `0` |
| SP_FIXTURE_FAILURE_PANIC | SAFE_PANIC | Halt learner grading decisions; run fixture diagnostics only until clear; LLM calls `0` |
| SP_GENERIC_PANIC | SAFE_PANIC | No additional override beyond panic baseline; LLM calls `0` |

## 7) Panic Switch Contract

Required control interface semantics:

- `panic_on(reason, actor_id)`:
  - idempotent
  - forces `SAFE_PANIC`
  - sets `profile_id = SP_MANUAL_PANIC`
  - emits transition event
- `panic_off(reason, actor_id)`:
  - only valid from `SAFE_PANIC`
  - transitions to `SAFE_GUARDED`
  - sets `profile_id = SG_GENERIC_GUARD`
  - emits transition event

Authorization policy:

- actor must be in `panic_operators` allow-list.
- unauthorized calls must be logged as denied attempts.

## 8) Event Logging Contract

Each transition must emit:

- `event_id`
- `event_ts_utc`
- `run_id`
- `session_id` (nullable)
- `prior_state`
- `next_state`
- `trigger_id`
- `trigger_set` (array)
- `dominant_trigger_id`
- `trigger_payload_hash`
- `profile_id`
- `profile_parent_state`
- `profile_resolution_version`
- `policy_bundle_hash`
- `actor_id` (nullable for automatic triggers)
- `reason`
- `spec_version`

## 9) Determinism Requirements

- Same prior state and same trigger set/payload class must produce same next state, profile id, and policy bundle hash.
- Transition precedence must not depend on non-deterministic ordering of concurrent triggers.
- When multiple triggers occur simultaneously, highest severity wins. Ties break by trigger id lexical order.
- Profile selection must be branch-deterministic by trigger family. Different trigger families may share a state and still require different profiles.
- Unmapped active triggers are disallowed once branch-coverage gates are enforced.
- In `SAFE_PANIC`, LLM call count must be `0` for learner-facing and control-path operations.
- Under calibration-triggered guarded profiles, governor authority must apply to diagnosis updates by stratum (throttle/strong_throttle/freeze) and may freeze affected diagnosis-update paths.
- For `SG_CALIBRATION_GUARD`, applied diagnosis update multipliers must equal the governor ladder values for the recorded decision.

## 10) v0.0 Enforced Checks

- Panic controls are defined.
- Transition rules and profile mapping are defined, including trigger-family profile branching.
- Transition event contract is defined.
- Acceptance tests AT-1, AT-2, and AT-6 (in `05_acceptance_test_plan_v0.0.md`) must pass in dry-run review.
