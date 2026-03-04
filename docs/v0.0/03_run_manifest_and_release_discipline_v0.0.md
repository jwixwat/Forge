# Run Manifest and Release Discipline v0.0

Version: `0.0.0`  
Effective date: `2026-02-27`  
Depends on: `01_invariants_charter_v0.0.md`, `02_safe_mode_and_panic_spec_v0.0.md`

## 1) Purpose

Define immutable version-linking for every run and a release process that blocks untraceable builds.

This file operationalizes invariant `INV-OPS-VSN-010`.

## 2) Run Manifest Contract

Each run must have exactly one manifest:

File name convention:

- `run_manifest.<run_id>.json`

Required fields:

- `schema_version` (string)
- `run_id` (string)
- `run_started_at_utc` (RFC3339 timestamp)
- `content_ir_version` (string)
- `grader_version` (string)
- `sensor_model_version` (string)
- `policy_version` (string)
- `engine_build_version` (string)
- `prompt_bundle_version` (string or null)
- `residual_formula_version` (string)
- `obs_encoder_version` (string)
- `hypothesis_space_hash` (string)
- `decision_rng_version` (string)
- `json_canonicalization_version` (`forge_json_c14n_v1`)
- `ope_support_level` (`none` | `propensity_only` | `full_support`)
- `ope_claim_contract` (object; threshold contract for target decision kinds/context overlap)
- `invariants_charter_version` (string)
- `safe_mode_spec_version` (string)
- `canonical_fingerprint` (string)
- `replay_fingerprint` (string)
- `git_commit_sha` (string)
- `workspace_dirty` (boolean)

Field constraint:

- `prompt_bundle_version` must be non-null if any LLM path is enabled for the run.
- `ope_support_level = full_support` is invalid unless `ope_claim_contract` thresholds and policy support checks pass for target decision kinds.

Immutable-after-start fields:

- all fields except `run_ended_at_utc`, `termination_reason`, and `final_status`.

## 3) Canonical Version Tuple

The canonical tuple is:

- `content_ir_version`
- `grader_version`
- `sensor_model_version`

Release and runtime are non-compliant if any tuple component is null, empty, or missing.

Canonical tuple is the minimal identity/compliance basis for semantic validity.

## 4) Replay Tuple (Interpretability Tuple)

The replay tuple is:

- `content_ir_version`
- `grader_version`
- `sensor_model_version`
- `policy_version`
- `engine_build_version`
- `prompt_bundle_version` (nullable when LLM paths are disabled)
- `residual_formula_version`
- `safe_mode_spec_version`
- `invariants_charter_version`
- `obs_encoder_version`
- `hypothesis_space_hash`
- `decision_rng_version`
- `json_canonicalization_version`

Replay tuple is the basis for reconstructing and comparing decision behavior.

## 5) Fingerprints

Required digest fields:

- `canonical_fingerprint = hash(canonical_tuple)`
- `replay_fingerprint = hash(replay_tuple)`

Requirements:

1. Fingerprints must be deterministic and algorithm-labeled in implementation docs.
2. Two runs with equal canonical tuple must have equal `canonical_fingerprint`.
3. Two runs with equal replay tuple must have equal `replay_fingerprint`.
4. If replay tuple differs, `replay_fingerprint` must differ.

## 6) Manifest Referential Integrity

Rules:

1. All attempt records must reference `run_id`.
2. All state snapshots must reference `run_id`.
3. A run id must resolve to exactly one manifest.
4. Manifest `schema_version` must be compatible with contract version pinned by release.
5. For any attempt or state in run `R`, `version_pointers` must exactly match the manifest replay-tuple projection for `R`.
6. `manifest.residual_formula_version` is authoritative; attempt `version_pointers.residual_formula_version` and residual provenance `residual_formula_version` must equal it.
7. Any mismatch under rules 5-6 is `mixed_semantics_within_run` and invalidates the run for release and policy evaluation.
8. `manifest.json_canonicalization_version` is authoritative for hash/replay semantics; attempt/state `version_pointers.json_canonicalization_version` must equal it.

Replay-tuple projection keys for attempt/state `version_pointers`:

- `content_ir_version`
- `grader_version`
- `sensor_model_version`
- `policy_version`
- `engine_build_version`
- `prompt_bundle_version`
- `residual_formula_version`
- `safe_mode_spec_version`
- `invariants_charter_version`
- `obs_encoder_version`
- `hypothesis_space_hash`
- `decision_rng_version`
- `json_canonicalization_version`
- `canonical_fingerprint`
- `replay_fingerprint`

## 7) Comparand Semantics

The system distinguishes:

- `semantic comparand`: same canonical tuple (`canonical_fingerprint` equal)
- `policy/runtime comparand`: same canonical tuple and different replay tuple (`canonical_fingerprint` equal, `replay_fingerprint` different)

Rule:

- Same canonical and different replay is valid and expected for policy iteration and OPE analysis.
- It is not a compliance failure. It is a first-class comparison mode.

## 8) OPE Support Classification

Run-level OPE support classification:

- `none`: policy traces are incomplete for propensity-based evaluation.
- `propensity_only`: action propensities are logged, but support/entropy constraints are not guaranteed; counterfactual OPE may be invalid.
- `full_support`: propensity logging plus support/entropy constraints are enforced and support checks pass.

Classification rules:

1. Deterministic or near-deterministic routing without support constraints must not be labeled `full_support`.
2. Early-stage runs may be valid for auditing and replay while still being `propensity_only`.
3. OPE reports must declare run `ope_support_level` before presenting counterfactual comparisons.

## 9) Release Discipline

### 9.1 Release Artifact Bundle

Required for each release candidate:

- release metadata (`release_id`, target env, timestamp, approver)
- manifest contract version pin
- invariants charter version pin
- safe-mode spec version pin
- v0.0 acceptance report
- panic drill report

### 9.2 Blocking Rules

Release must be blocked if any of the following are true:

- missing run manifest contract pin
- missing canonical version tuple definition
- missing replay tuple definition
- missing fingerprint definitions for canonical/replay tuples
- missing OPE support classification field definition
- mixed semantics detected within run artifacts
- unresolved mismatch between pinned and current invariants/safe-mode versions
- missing or failed v0.0 acceptance report
- missing or failed panic drill report

### 9.3 Promotion Rules

Promotion to higher environment requires:

1. All v0.0 hard gates pass.
2. Manifest contract unchanged or version-bumped with changelog.
3. Approval sign-off from architecture owner.

## 10) Minimal JSON Example

```json
{
  "schema_version": "0.0.0",
  "run_id": "run_2026_02_27_0001",
  "run_started_at_utc": "2026-02-27T18:15:00Z",
  "run_ended_at_utc": null,
  "content_ir_version": "content.v2026.02.27",
  "grader_version": "grader.v0.3.0",
  "sensor_model_version": "sensor.v0.1.0",
  "policy_version": "policy.v0.0.0",
  "engine_build_version": "engine.v0.0.0",
  "residual_formula_version": "residual.v0.6.0",
  "obs_encoder_version": "obsenc.v0.1.0",
  "hypothesis_space_hash": "hyp_hash_001",
  "decision_rng_version": "rng.v0.1.0",
  "json_canonicalization_version": "forge_json_c14n_v1",
  "ope_support_level": "propensity_only",
  "ope_claim_contract": {
    "target_trace_kinds": ["routing"],
    "context_axes": ["probe_family_id", "assistance_mode_derived", "evidence_channel"],
    "min_stochastic_fraction": 0.2,
    "min_candidate_probability": 0.05,
    "min_chosen_probability": 0.05,
    "min_entropy_bits": 0.0,
    "min_context_coverage_fraction": 0.5,
    "min_decisions_per_context": 1
  },
  "invariants_charter_version": "0.0.0",
  "safe_mode_spec_version": "0.0.0",
  "prompt_bundle_version": "prompt.v0.0.0",
  "canonical_fingerprint": "sha256:canon_001",
  "replay_fingerprint": "sha256:replay_001",
  "git_commit_sha": "0123456789abcdef0123456789abcdef01234567",
  "workspace_dirty": false,
  "termination_reason": null,
  "final_status": "running"
}
```

## 11) v0.0 Enforced Checks

- Manifest contract exists with required fields.
- Canonical version tuple is explicitly defined.
- Replay tuple is explicitly defined.
- Canonical/replay fingerprints are explicitly defined.
- OPE support classification is explicitly defined.
- No-mixed-semantics and residual formula pinning rules are explicitly defined.
- Release blocking and promotion rules are explicitly defined.
