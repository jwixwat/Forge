"""Contract validation for v0.1 records."""

from __future__ import annotations

from typing import Any

from .obs_vocab_registry import ObservationVocabularyRegistry
from . import audit_queries
from .constants import (
    ALLOWED_UPDATE_PARTITIONS,
    ASSISTANCE_MODES,
    ASSISTANCE_DERIVATION_QUALITY,
    ANCHOR_AUDIT_REQUIRED_FIELDS,
    ANCHOR_AUDIT_STATUSES,
    ATTEMPT_PRECOMMIT_REQUIRED_FIELDS,
    ATTEMPT_REQUIRED_FIELDS,
    ATTEMPT_TELEMETRY_REQUIRED_FIELDS,
    CALIBRATION_STATUS,
    CANONICAL_TUPLE_FIELDS,
    COMMIT_STATUS,
    DECISION_TRACE_REQUIRED_FIELDS,
    DIAGNOSIS_UPDATE_ELIGIBILITY,
    DIAGNOSTIC_EVIDENCE_CHANNELS,
    DIAGNOSIS_LOG_WRITE_STATUS,
    EVIDENCE_CHANNELS,
    GOVERNOR_DECISIONS,
    GOVERNOR_MULTIPLIERS,
    INELIGIBILITY_REASON,
    MANIFEST_REQUIRED_FIELDS,
    MUTATION_OUTCOMES,
    JSON_CANONICALIZATION_VERSIONS,
    OPE_SUPPORT_LEVELS,
    OPE_CONTEXT_AXES,
    OPE_TARGET_TRACE_KINDS,
    POLICY_DOMAINS,
    POLICY_OUTCOMES,
    POLICY_SCOPE_TYPES,
    QUARANTINE_ACTIONS,
    QUARANTINE_DECISION_REQUIRED_FIELDS,
    QUARANTINE_SCOPE_TYPES,
    REPLAY_PROJECTION_KEYS,
    REPLAY_TUPLE_FIELDS,
    RESIDUAL_PROVENANCE_PINNED_FIELDS,
    SAFE_MODE_POLICY_BUNDLE_HASHES,
    SAFE_MODE_PROFILE_IDS,
    SAFE_MODE_PROFILE_PARENT_STATES,
    SAFE_MODE_STATES,
    SAFE_MODE_TRANSITION_REQUIRED_FIELDS,
    SAFE_MODE_TRIGGER_IDS,
    SCHEMA_VERSION_COMPATIBILITY,
    SEMANTIC_COMMITMENT_REQUIRED_FIELDS,
    STATE_MIGRATION_REQUIRED_FIELDS,
    STATE_SNAPSHOT_REQUIRED_FIELDS,
    STATE_UPDATE_REQUIRED_FIELDS,
    SUPPRESSION_REASONS,
    SUPPORT_CHECK_STATUS,
    TELEMETRY_KINDS,
    TRACE_KINDS,
)
from .utils import (
    float_equal,
    is_probability,
    is_strict_int,
    is_strict_number,
    is_non_empty_string,
    is_rfc3339_utc,
    missing_required_fields,
    sha256_json,
)


class ValidationError(ValueError):
    """Raised when a record violates contract constraints."""


class ContractValidator:
    """Validator for manifests, attempts, snapshots, and update events."""

    def __init__(self, obs_vocab_registry: ObservationVocabularyRegistry | None = None) -> None:
        self._obs_vocab_registry = obs_vocab_registry or ObservationVocabularyRegistry()

    def replay_projection(self, manifest: dict[str, Any]) -> dict[str, Any]:
        projection: dict[str, Any] = {}
        for key in REPLAY_PROJECTION_KEYS:
            projection[key] = manifest.get(key)
        return projection

    def precommit_projection_from_attempt(self, attempt: dict[str, Any]) -> dict[str, Any]:
        residual_inputs = attempt.get("residual_inputs", {})
        if not isinstance(residual_inputs, dict):
            residual_inputs = {}
        likelihood_sketch = residual_inputs.get("likelihood_sketch")
        return {
            "run_id": attempt.get("run_id"),
            "timeline_id": attempt.get("timeline_id"),
            "session_id": attempt.get("session_id"),
            "attempt_id": attempt.get("attempt_id"),
            "learner_id": attempt.get("learner_id"),
            "item_id": attempt.get("item_id"),
            "probe_family_id": attempt.get("probe_family_id"),
            "commitment_id": attempt.get("commitment_id"),
            "semantic_commitment": self._canonicalize_semantic_commitment(
                attempt.get("semantic_commitment")
            ),
            "evidence_channel_intended": attempt.get("evidence_channel_intended"),
            "assistance_contract_intended": attempt.get("assistance_contract_intended"),
            "diagnosis_update_eligibility_intended": attempt.get(
                "diagnosis_update_eligibility_intended"
            ),
            "ineligibility_reason_intended": attempt.get("ineligibility_reason_intended"),
            "allowed_update_partitions_intended": self._canonicalize_allowed_update_partitions(
                attempt.get("allowed_update_partitions_intended")
            ),
            "telemetry_event_ids_intended": self._canonicalize_telemetry_event_ids(
                attempt.get("telemetry_event_ids_intended")
            ),
            "decision_traces": self._canonicalize_decision_traces(attempt.get("decision_traces")),
            "policy_decisions": self._canonicalize_policy_decisions(attempt.get("policy_decisions")),
            "likelihood_sketch": self._canonicalize_likelihood_sketch(likelihood_sketch),
            "version_pointers": attempt.get("version_pointers"),
        }

    def precommit_projection_from_record(self, precommit: dict[str, Any]) -> dict[str, Any]:
        return {
            "run_id": precommit.get("run_id"),
            "timeline_id": precommit.get("timeline_id"),
            "session_id": precommit.get("session_id"),
            "attempt_id": precommit.get("attempt_id"),
            "learner_id": precommit.get("learner_id"),
            "item_id": precommit.get("item_id"),
            "probe_family_id": precommit.get("probe_family_id"),
            "commitment_id": precommit.get("commitment_id"),
            "semantic_commitment": self._canonicalize_semantic_commitment(
                precommit.get("semantic_commitment")
            ),
            "evidence_channel_intended": precommit.get("evidence_channel_intended"),
            "assistance_contract_intended": precommit.get("assistance_contract_intended"),
            "diagnosis_update_eligibility_intended": precommit.get(
                "diagnosis_update_eligibility_intended"
            ),
            "ineligibility_reason_intended": precommit.get("ineligibility_reason_intended"),
            "allowed_update_partitions_intended": self._canonicalize_allowed_update_partitions(
                precommit.get("allowed_update_partitions_intended")
            ),
            "telemetry_event_ids_intended": self._canonicalize_telemetry_event_ids(
                precommit.get("telemetry_event_ids_intended")
            ),
            "decision_traces": self._canonicalize_decision_traces(precommit.get("decision_traces")),
            "policy_decisions": self._canonicalize_policy_decisions(precommit.get("policy_decisions")),
            "likelihood_sketch": self._canonicalize_likelihood_sketch(precommit.get("likelihood_sketch")),
            "version_pointers": precommit.get("version_pointers"),
        }

    def precommit_envelope_projection_from_attempt(self, attempt: dict[str, Any]) -> dict[str, Any]:
        return {
            "run_id": attempt.get("run_id"),
            "timeline_id": attempt.get("timeline_id"),
            "session_id": attempt.get("session_id"),
            "attempt_id": attempt.get("attempt_id"),
            "learner_id": attempt.get("learner_id"),
            "precommit_event_id": attempt.get("precommit_event_id"),
            "precommit_hash": attempt.get("precommit_hash"),
            "semantic_commitment": self._canonicalize_semantic_commitment(
                attempt.get("semantic_commitment")
            ),
            "telemetry_event_ids_intended": self._canonicalize_telemetry_event_ids(
                attempt.get("telemetry_event_ids_intended")
            ),
        }

    def precommit_envelope_projection_from_record(self, precommit: dict[str, Any]) -> dict[str, Any]:
        return {
            "run_id": precommit.get("run_id"),
            "timeline_id": precommit.get("timeline_id"),
            "session_id": precommit.get("session_id"),
            "attempt_id": precommit.get("attempt_id"),
            "learner_id": precommit.get("learner_id"),
            "precommit_event_id": precommit.get("precommit_event_id"),
            "precommit_hash": precommit.get("precommit_hash"),
            "semantic_commitment": self._canonicalize_semantic_commitment(
                precommit.get("semantic_commitment")
            ),
            "telemetry_event_ids_intended": self._canonicalize_telemetry_event_ids(
                precommit.get("telemetry_event_ids_intended")
            ),
        }

    def _canonicalize_allowed_update_partitions(self, partitions: Any) -> Any:
        if not isinstance(partitions, list):
            return partitions
        return sorted(partitions)

    def _canonicalize_telemetry_event_ids(self, telemetry_event_ids: Any) -> Any:
        if not isinstance(telemetry_event_ids, list):
            return telemetry_event_ids
        return sorted(telemetry_event_ids)

    def _canonicalize_decision_traces(self, traces: Any) -> Any:
        if not isinstance(traces, list):
            return traces
        normalized: list[dict[str, Any]] = []
        for trace in traces:
            if not isinstance(trace, dict):
                normalized.append(trace)
                continue
            trace_copy = dict(trace)
            candidates = trace_copy.get("candidate_actions")
            if isinstance(candidates, list):
                trace_copy["candidate_actions"] = sorted(
                    candidates,
                    key=lambda c: str(c.get("action_id", "")) if isinstance(c, dict) else "",
                )
            normalized.append(trace_copy)
        return sorted(
            normalized,
            key=lambda t: str(t.get("decision_id", "")) if isinstance(t, dict) else "",
        )

    def _canonicalize_policy_decisions(self, decisions: Any) -> Any:
        if not isinstance(decisions, list):
            return decisions
        return sorted(
            decisions,
            key=lambda d: str(d.get("decision_id", "")) if isinstance(d, dict) else "",
        )

    def _canonicalize_likelihood_sketch(self, sketch: Any) -> Any:
        if not isinstance(sketch, dict):
            return sketch
        sketch_copy = dict(sketch)
        top_hypotheses = sketch_copy.get("top_hypotheses")
        if isinstance(top_hypotheses, list):
            sketch_copy["top_hypotheses"] = sorted(
                top_hypotheses,
                key=lambda row: str(row.get("hypothesis_id", "")) if isinstance(row, dict) else "",
            )
        distribution = sketch_copy.get("predicted_observation_distribution")
        if isinstance(distribution, list):
            sketch_copy["predicted_observation_distribution"] = sorted(
                distribution,
                key=lambda row: str(row.get("obs_key", "")) if isinstance(row, dict) else "",
            )
        return sketch_copy

    def _semantic_commitment_from_intended_fields(self, record: dict[str, Any]) -> dict[str, Any]:
        return {
            "evidence_channel_intended": record.get("evidence_channel_intended"),
            "assistance_contract_intended": record.get("assistance_contract_intended"),
            "diagnosis_update_eligibility_intended": record.get(
                "diagnosis_update_eligibility_intended"
            ),
            "ineligibility_reason_intended": record.get("ineligibility_reason_intended"),
            "allowed_update_partitions_intended": self._canonicalize_allowed_update_partitions(
                record.get("allowed_update_partitions_intended")
            ),
            "telemetry_event_ids_intended": self._canonicalize_telemetry_event_ids(
                record.get("telemetry_event_ids_intended")
            ),
        }

    def _canonicalize_semantic_commitment(self, commitment: Any) -> Any:
        if not isinstance(commitment, dict):
            return commitment
        canonical: dict[str, Any] = dict(commitment)
        if "allowed_update_partitions_intended" in canonical:
            canonical["allowed_update_partitions_intended"] = self._canonicalize_allowed_update_partitions(
                canonical.get("allowed_update_partitions_intended")
            )
        if "telemetry_event_ids_intended" in canonical:
            canonical["telemetry_event_ids_intended"] = self._canonicalize_telemetry_event_ids(
                canonical.get("telemetry_event_ids_intended")
            )
        return canonical

    def _validate_semantic_commitment(
        self,
        record: dict[str, Any],
        prefix: str,
    ) -> list[str]:
        errors: list[str] = []
        commitment_raw = record.get("semantic_commitment")
        if not isinstance(commitment_raw, dict):
            return [f"{prefix}_semantic_commitment_not_object"]
        missing = missing_required_fields(commitment_raw, SEMANTIC_COMMITMENT_REQUIRED_FIELDS)
        if missing:
            errors.append(f"{prefix}_semantic_commitment_missing:" + ",".join(missing))
            return errors

        commitment = self._canonicalize_semantic_commitment(commitment_raw)
        field_projection = self._semantic_commitment_from_intended_fields(record)
        if commitment != field_projection:
            errors.append(f"{prefix}_semantic_commitment_mismatch_intended_fields")
            return errors

        channel = commitment.get("evidence_channel_intended")
        assistance = commitment.get("assistance_contract_intended")
        eligibility = commitment.get("diagnosis_update_eligibility_intended")
        reason = commitment.get("ineligibility_reason_intended")
        partitions = commitment.get("allowed_update_partitions_intended")
        if channel not in EVIDENCE_CHANNELS:
            errors.append(f"{prefix}_semantic_commitment_evidence_channel_invalid")
        if assistance not in ASSISTANCE_MODES:
            errors.append(f"{prefix}_semantic_commitment_assistance_contract_invalid")
        if eligibility not in DIAGNOSIS_UPDATE_ELIGIBILITY:
            errors.append(f"{prefix}_semantic_commitment_eligibility_invalid")
        if reason not in INELIGIBILITY_REASON:
            errors.append(f"{prefix}_semantic_commitment_reason_invalid")
        if not isinstance(partitions, list):
            errors.append(f"{prefix}_semantic_commitment_allowed_partitions_not_array")
        return errors

    def _telemetry_payload_projection(self, telemetry_event: dict[str, Any]) -> dict[str, Any]:
        return {
            key: value
            for key, value in telemetry_event.items()
            if key != "payload_hash"
        }

    def _validate_required_non_empty_strings(
        self,
        record: dict[str, Any],
        fields: tuple[str, ...],
        prefix: str,
    ) -> list[str]:
        errors: list[str] = []
        for field in fields:
            if not is_non_empty_string(record.get(field)):
                errors.append(f"{prefix}_{field}_invalid")
        return errors

    def _validate_schema_version_support(
        self,
        record: dict[str, Any],
        record_type: str,
    ) -> list[str]:
        schema_version = record.get("schema_version")
        if not is_non_empty_string(schema_version):
            return [f"{record_type}_schema_version_invalid"]
        supported = SCHEMA_VERSION_COMPATIBILITY.get(record_type, set())
        if schema_version not in supported:
            return [f"{record_type}_schema_version_unsupported:{schema_version}"]
        return []

    def _trace_kind_policy_domain_compatible(
        self,
        trace_kind: Any,
        policy_domain: Any,
    ) -> bool:
        if not isinstance(trace_kind, str) or not isinstance(policy_domain, str):
            return False
        if trace_kind in {"routing", "holdout", "anchor", "diagnosis", "calibration"}:
            return policy_domain == trace_kind
        if trace_kind == "feedback":
            return policy_domain == "other"
        if trace_kind == "quarantine":
            return policy_domain in {"invariance", "other"}
        if trace_kind == "other":
            return policy_domain == "other"
        return False

    def normalize_record_for_replay(
        self,
        record_type: str,
        record: dict[str, Any],
        target_schema_version: str = "0.1.0",
    ) -> tuple[dict[str, Any] | None, list[str]]:
        if not isinstance(record, dict):
            return (None, [f"{record_type}_record_not_object"])
        errors = self._validate_schema_version_support(record, record_type)
        if errors:
            return (None, errors)
        schema_version = record.get("schema_version")
        normalized = dict(record)
        # v0.0 manifest is replay-compatible with v0.1 target; upgrade tag only.
        if record_type == "manifest" and schema_version == "0.0.0" and target_schema_version == "0.1.0":
            normalized["schema_version"] = "0.1.0"
        return (normalized, [])

    def _validate_ope_claim_contract(
        self,
        contract: Any,
        prefix: str = "manifest_ope_claim_contract",
    ) -> list[str]:
        if not isinstance(contract, dict):
            return [f"{prefix}_not_object"]

        errors: list[str] = []
        required = {
            "target_trace_kinds",
            "context_axes",
            "min_stochastic_fraction",
            "min_candidate_probability",
            "min_chosen_probability",
            "min_entropy_bits",
            "min_context_coverage_fraction",
            "min_decisions_per_context",
        }
        missing = missing_required_fields(contract, required)
        if missing:
            errors.append(f"{prefix}_missing:" + ",".join(missing))
            return errors

        target_trace_kinds = contract.get("target_trace_kinds")
        if not isinstance(target_trace_kinds, list) or not target_trace_kinds:
            errors.append(f"{prefix}_target_trace_kinds_invalid")
        else:
            seen_kinds: set[str] = set()
            for idx, trace_kind in enumerate(target_trace_kinds):
                if not is_non_empty_string(trace_kind):
                    errors.append(f"{prefix}_target_trace_kind_invalid[{idx}]")
                    continue
                if trace_kind not in OPE_TARGET_TRACE_KINDS:
                    errors.append(f"{prefix}_target_trace_kind_unknown:{trace_kind}")
                    continue
                if trace_kind in seen_kinds:
                    errors.append(f"{prefix}_target_trace_kind_duplicate:{trace_kind}")
                    continue
                seen_kinds.add(trace_kind)

        context_axes = contract.get("context_axes")
        if not isinstance(context_axes, list) or not context_axes:
            errors.append(f"{prefix}_context_axes_invalid")
        else:
            seen_axes: set[str] = set()
            for idx, axis in enumerate(context_axes):
                if not is_non_empty_string(axis):
                    errors.append(f"{prefix}_context_axis_invalid[{idx}]")
                    continue
                if axis not in OPE_CONTEXT_AXES:
                    errors.append(f"{prefix}_context_axis_unknown:{axis}")
                    continue
                if axis in seen_axes:
                    errors.append(f"{prefix}_context_axis_duplicate:{axis}")
                    continue
                seen_axes.add(axis)

        def _validate_fraction(value: Any, field: str) -> None:
            if not is_probability(value):
                errors.append(f"{prefix}_{field}_not_numeric")
                return

        _validate_fraction(contract.get("min_stochastic_fraction"), "min_stochastic_fraction")
        _validate_fraction(contract.get("min_context_coverage_fraction"), "min_context_coverage_fraction")

        min_entropy_bits = contract.get("min_entropy_bits")
        if not is_strict_number(min_entropy_bits):
            errors.append(f"{prefix}_min_entropy_bits_not_numeric")
        elif float(min_entropy_bits) < 0.0:
            errors.append(f"{prefix}_min_entropy_bits_out_of_range")

        min_candidate_probability = contract.get("min_candidate_probability")
        if not is_probability(min_candidate_probability):
            errors.append(f"{prefix}_min_candidate_probability_not_numeric")
        elif float(min_candidate_probability) <= 0.0:
            errors.append(f"{prefix}_min_candidate_probability_out_of_range")

        min_chosen_probability = contract.get("min_chosen_probability")
        if not is_probability(min_chosen_probability):
            errors.append(f"{prefix}_min_chosen_probability_not_numeric")
        elif float(min_chosen_probability) <= 0.0:
            errors.append(f"{prefix}_min_chosen_probability_out_of_range")

        min_decisions_per_context = contract.get("min_decisions_per_context")
        if not is_strict_int(min_decisions_per_context):
            errors.append(f"{prefix}_min_decisions_per_context_invalid")
        elif min_decisions_per_context <= 0:
            errors.append(f"{prefix}_min_decisions_per_context_invalid")
        return errors

    def _safe_mode_trigger_severity(self, trigger_id: str) -> int | None:
        severity_map = {
            "TRG-MANUAL-PANIC": 0,
            "TRG-MANIFEST-INVALID": 0,
            "TRG-FIXTURE-FAIL": 0,
            "TRG-SENSOR-UNRELIABLE-HIGH": 1,
            "TRG-CALIBRATION-ALARM": 1,
            "TRG-SPEC-UNDERDETERMINED-HIGH": 2,
            "TRG-MANUAL-CLEAR": 3,
        }
        return severity_map.get(trigger_id)

    def _safe_mode_trigger_precedence(self, trigger_id: str) -> int | None:
        precedence = [
            "TRG-MANUAL-PANIC",
            "TRG-MANIFEST-INVALID",
            "TRG-FIXTURE-FAIL",
            "TRG-SENSOR-UNRELIABLE-HIGH",
            "TRG-CALIBRATION-ALARM",
            "TRG-SPEC-UNDERDETERMINED-HIGH",
            "TRG-MANUAL-CLEAR",
        ]
        if trigger_id not in precedence:
            return None
        return precedence.index(trigger_id)

    def _expected_safe_mode_next_state(
        self,
        prior_state: str,
        trigger_set: list[str],
    ) -> str | None:
        if prior_state not in SAFE_MODE_STATES:
            return None
        if not trigger_set:
            return None
        if any(trigger_id in {"TRG-MANUAL-PANIC", "TRG-MANIFEST-INVALID", "TRG-FIXTURE-FAIL"} for trigger_id in trigger_set):
            return "SAFE_PANIC"
        if trigger_set == ["TRG-MANUAL-CLEAR"]:
            if prior_state != "SAFE_PANIC":
                return None
            return "SAFE_GUARDED"
        if prior_state == "SAFE_PANIC":
            return "SAFE_PANIC"
        if any(trigger_id in {"TRG-SENSOR-UNRELIABLE-HIGH", "TRG-CALIBRATION-ALARM", "TRG-SPEC-UNDERDETERMINED-HIGH"} for trigger_id in trigger_set):
            return "SAFE_GUARDED"
        return None

    def _expected_dominant_trigger_id(self, trigger_set: list[str]) -> str | None:
        if not trigger_set:
            return None
        known = [t for t in trigger_set if t in SAFE_MODE_TRIGGER_IDS]
        if len(known) != len(trigger_set):
            return None
        sorted_candidates = sorted(
            known,
            key=lambda t: (self._safe_mode_trigger_precedence(t), t),
        )
        return sorted_candidates[0] if sorted_candidates else None

    def _expected_profile_id(
        self,
        dominant_trigger_id: str,
        next_state: str,
    ) -> str | None:
        direct = {
            "TRG-MANUAL-PANIC": "SP_MANUAL_PANIC",
            "TRG-MANIFEST-INVALID": "SP_MANIFEST_INVALID",
            "TRG-FIXTURE-FAIL": "SP_FIXTURE_FAILURE_PANIC",
            "TRG-CALIBRATION-ALARM": "SG_CALIBRATION_GUARD",
            "TRG-SENSOR-UNRELIABLE-HIGH": "SG_SENSOR_UNRELIABLE_GUARD",
            "TRG-SPEC-UNDERDETERMINED-HIGH": "SG_SPEC_UNDERDETERMINED_GUARD",
            "TRG-MANUAL-CLEAR": "SG_GENERIC_GUARD",
        }
        if dominant_trigger_id in direct:
            return direct[dominant_trigger_id]
        if next_state == "SAFE_GUARDED":
            return "SG_GENERIC_GUARD"
        if next_state == "SAFE_PANIC":
            return "SP_GENERIC_PANIC"
        return None

    def _expected_diagnosis_multiplier_for_profile(
        self,
        safe_mode_profile_id: Any,
        governor_decision: Any,
    ) -> float | None:
        if not isinstance(safe_mode_profile_id, str):
            return None
        if safe_mode_profile_id == "SG_CALIBRATION_GUARD":
            if governor_decision not in GOVERNOR_MULTIPLIERS:
                return None
            return float(GOVERNOR_MULTIPLIERS[governor_decision])
        if safe_mode_profile_id == "SG_SENSOR_UNRELIABLE_GUARD":
            return 0.10
        if safe_mode_profile_id.startswith("SP_"):
            return 0.00
        return None

    def validate_manifest(self, manifest: dict[str, Any]) -> list[str]:
        if not isinstance(manifest, dict):
            return ["manifest_record_not_object"]
        try:
            errors: list[str] = []
            missing = missing_required_fields(manifest, MANIFEST_REQUIRED_FIELDS)
            if missing:
                errors.append("manifest_missing:" + ",".join(missing))
                return errors
            schema_errors = self._validate_schema_version_support(manifest, "manifest")
            if schema_errors:
                errors.extend(schema_errors)
                return errors

            errors.extend(
                self._validate_required_non_empty_strings(
                    manifest,
                    (
                        "schema_version",
                        "run_id",
                        "timeline_id",
                        "run_started_at_utc",
                        "content_ir_version",
                        "grader_version",
                        "sensor_model_version",
                        "policy_version",
                        "engine_build_version",
                        "residual_formula_version",
                        "obs_encoder_version",
                        "hypothesis_space_hash",
                        "decision_rng_version",
                        "json_canonicalization_version",
                        "invariants_charter_version",
                        "safe_mode_spec_version",
                    ),
                    "manifest",
                )
            )
            if not is_rfc3339_utc(manifest.get("run_started_at_utc")):
                errors.append("manifest_run_started_at_utc_invalid")
            epoch_index = manifest.get("epoch_index")
            if not is_strict_int(epoch_index) or epoch_index <= 0:
                errors.append("manifest_epoch_index_invalid")

            predecessor_run_id = manifest.get("predecessor_run_id")
            bootstrap_snapshot_ref = manifest.get("bootstrap_snapshot_ref")
            migration_event_id = manifest.get("migration_event_id")

            if epoch_index == 1:
                if predecessor_run_id is not None:
                    errors.append("manifest_epoch1_predecessor_run_id_must_be_null")
                if bootstrap_snapshot_ref is not None:
                    errors.append("manifest_epoch1_bootstrap_snapshot_ref_must_be_null")
                if migration_event_id is not None:
                    errors.append("manifest_epoch1_migration_event_id_must_be_null")
            elif is_strict_int(epoch_index) and epoch_index > 1:
                if not is_non_empty_string(predecessor_run_id):
                    errors.append("manifest_non_initial_predecessor_run_id_invalid")
                if not isinstance(bootstrap_snapshot_ref, dict):
                    errors.append("manifest_non_initial_bootstrap_snapshot_ref_invalid")
                if not is_non_empty_string(migration_event_id):
                    errors.append("manifest_non_initial_migration_event_id_invalid")
                if predecessor_run_id == manifest.get("run_id"):
                    errors.append("manifest_predecessor_run_id_self_reference")
                if isinstance(bootstrap_snapshot_ref, dict):
                    required_bootstrap = {
                        "source_run_id",
                        "source_snapshot_id",
                        "source_state_hash",
                        "source_replay_fingerprint",
                    }
                    missing_bootstrap = missing_required_fields(bootstrap_snapshot_ref, required_bootstrap)
                    if missing_bootstrap:
                        errors.append(
                            "manifest_bootstrap_snapshot_ref_missing:" + ",".join(missing_bootstrap)
                        )
                    else:
                        for key in required_bootstrap:
                            if not is_non_empty_string(bootstrap_snapshot_ref.get(key)):
                                errors.append(f"manifest_bootstrap_snapshot_ref_{key}_invalid")
                        if bootstrap_snapshot_ref.get("source_run_id") != predecessor_run_id:
                            errors.append("manifest_bootstrap_source_run_id_mismatch_predecessor")

            for key in CANONICAL_TUPLE_FIELDS:
                if not is_non_empty_string(manifest.get(key)):
                    errors.append(f"manifest_canonical_invalid:{key}")

            for key in REPLAY_TUPLE_FIELDS:
                value = manifest.get(key)
                if key == "prompt_bundle_version":
                    continue
                if not is_non_empty_string(value):
                    errors.append(f"manifest_replay_invalid:{key}")

            if manifest.get("ope_support_level") not in OPE_SUPPORT_LEVELS:
                errors.append("manifest_ope_support_level_invalid")
            contract_errors = self._validate_ope_claim_contract(manifest.get("ope_claim_contract"))
            errors.extend(contract_errors)
            ope_level = manifest.get("ope_support_level")
            ope_claim_contract = manifest.get("ope_claim_contract")
            if (
                ope_level == "full_support"
                and isinstance(ope_claim_contract, dict)
                and "routing" not in ope_claim_contract.get("target_trace_kinds", [])
            ):
                errors.append("manifest_full_support_requires_routing_target")
            if manifest.get("json_canonicalization_version") not in JSON_CANONICALIZATION_VERSIONS:
                errors.append("manifest_json_canonicalization_version_invalid")

            llm_paths_enabled = manifest.get("llm_paths_enabled")
            if llm_paths_enabled is True and manifest.get("prompt_bundle_version") is None:
                errors.append("manifest_prompt_bundle_required_for_llm")

            for key in ("canonical_fingerprint", "replay_fingerprint", "git_commit_sha"):
                if not is_non_empty_string(manifest.get(key)):
                    errors.append(f"manifest_string_invalid:{key}")

            if not isinstance(manifest.get("workspace_dirty"), bool):
                errors.append("manifest_workspace_dirty_not_bool")
            return errors
        except Exception as exc:
            return [f"manifest_validator_internal_exception:{type(exc).__name__}"]

    def validate_attempt(self, attempt: dict[str, Any], manifest: dict[str, Any]) -> list[str]:
        if not isinstance(attempt, dict):
            return ["attempt_record_not_object"]
        if not isinstance(manifest, dict):
            return ["attempt_manifest_not_object"]
        try:
            errors: list[str] = []
            missing = missing_required_fields(attempt, ATTEMPT_REQUIRED_FIELDS)
            if missing:
                errors.append("attempt_missing:" + ",".join(missing))
                return errors
            schema_errors = self._validate_schema_version_support(attempt, "attempt")
            if schema_errors:
                errors.extend(schema_errors)
                return errors

            errors.extend(
                self._validate_required_non_empty_strings(
                    attempt,
                    (
                        "schema_version",
                        "run_id",
                        "timeline_id",
                        "session_id",
                        "attempt_id",
                        "learner_id",
                        "item_id",
                        "probe_family_id",
                        "commitment_id",
                        "evidence_channel_intended",
                        "assistance_contract_intended",
                        "diagnosis_update_eligibility_intended",
                        "ineligibility_reason_intended",
                    ),
                    "attempt",
                )
            )
            errors.extend(self._validate_semantic_commitment(attempt, "attempt"))
            if attempt.get("run_id") != manifest.get("run_id"):
                errors.append("attempt_run_id_mismatch_manifest")
            if attempt.get("timeline_id") != manifest.get("timeline_id"):
                errors.append("attempt_timeline_id_mismatch_manifest")
            if not is_rfc3339_utc(attempt.get("attempt_ts_utc")):
                errors.append("attempt_attempt_ts_utc_invalid")

            if attempt["evidence_channel"] not in EVIDENCE_CHANNELS:
                errors.append("attempt_evidence_channel_invalid")
            if attempt["assistance_mode"] not in ASSISTANCE_MODES:
                errors.append("attempt_assistance_mode_invalid")
            if attempt.get("assistance_mode_derived") not in ASSISTANCE_MODES:
                errors.append("attempt_assistance_mode_derived_invalid")
            if attempt.get("assistance_derivation_quality") not in ASSISTANCE_DERIVATION_QUALITY:
                errors.append("attempt_assistance_derivation_quality_invalid")
            if attempt.get("assistance_mode") != attempt.get("assistance_mode_derived"):
                errors.append("attempt_assistance_mode_claimed_mismatch_derived")
            if attempt["diagnosis_update_eligibility"] not in DIAGNOSIS_UPDATE_ELIGIBILITY:
                errors.append("attempt_diagnosis_update_eligibility_invalid")
            if attempt["ineligibility_reason"] not in INELIGIBILITY_REASON:
                errors.append("attempt_ineligibility_reason_invalid")
            if attempt.get("evidence_channel_intended") not in EVIDENCE_CHANNELS:
                errors.append("attempt_evidence_channel_intended_invalid")
            if attempt.get("assistance_contract_intended") not in ASSISTANCE_MODES:
                errors.append("attempt_assistance_contract_intended_invalid")
            if attempt.get("diagnosis_update_eligibility_intended") not in DIAGNOSIS_UPDATE_ELIGIBILITY:
                errors.append("attempt_diagnosis_update_eligibility_intended_invalid")
            if attempt.get("ineligibility_reason_intended") not in INELIGIBILITY_REASON:
                errors.append("attempt_ineligibility_reason_intended_invalid")
            allowed_partitions_raw = attempt["allowed_update_partitions"]
            if not isinstance(allowed_partitions_raw, list):
                errors.append("attempt_allowed_update_partitions_not_array")
                allowed_partitions = []
            else:
                allowed_partitions = allowed_partitions_raw
                seen_allowed: set[str] = set()
                for idx, partition in enumerate(allowed_partitions):
                    if partition not in ALLOWED_UPDATE_PARTITIONS:
                        errors.append(f"attempt_allowed_update_partition_invalid[{idx}]")
                        continue
                    if partition in seen_allowed:
                        errors.append(f"attempt_allowed_update_partition_duplicate:{partition}")
                        continue
                    seen_allowed.add(partition)
            allowed_partitions_intended_raw = attempt.get("allowed_update_partitions_intended")
            if not isinstance(allowed_partitions_intended_raw, list):
                errors.append("attempt_allowed_update_partitions_intended_not_array")
            else:
                seen_allowed_intended: set[str] = set()
                for idx, partition in enumerate(allowed_partitions_intended_raw):
                    if partition not in ALLOWED_UPDATE_PARTITIONS:
                        errors.append(f"attempt_allowed_update_partitions_intended_invalid[{idx}]")
                        continue
                    if partition in seen_allowed_intended:
                        errors.append(
                            f"attempt_allowed_update_partitions_intended_duplicate:{partition}"
                        )
                        continue
                    seen_allowed_intended.add(partition)
            telemetry_event_ids = attempt.get("telemetry_event_ids")
            if not isinstance(telemetry_event_ids, list) or not telemetry_event_ids:
                errors.append("attempt_telemetry_event_ids_invalid")
            else:
                seen_telemetry_ids: set[str] = set()
                for idx, telemetry_event_id in enumerate(telemetry_event_ids):
                    if not is_non_empty_string(telemetry_event_id):
                        errors.append(f"attempt_telemetry_event_id_invalid[{idx}]")
                        continue
                    if telemetry_event_id in seen_telemetry_ids:
                        errors.append(f"attempt_telemetry_event_id_duplicate:{telemetry_event_id}")
                        continue
                    seen_telemetry_ids.add(telemetry_event_id)
            telemetry_event_ids_intended = attempt.get("telemetry_event_ids_intended")
            if not isinstance(telemetry_event_ids_intended, list) or not telemetry_event_ids_intended:
                errors.append("attempt_telemetry_event_ids_intended_invalid")
            else:
                seen_telemetry_ids_intended: set[str] = set()
                for idx, telemetry_event_id in enumerate(telemetry_event_ids_intended):
                    if not is_non_empty_string(telemetry_event_id):
                        errors.append(f"attempt_telemetry_event_id_intended_invalid[{idx}]")
                        continue
                    if telemetry_event_id in seen_telemetry_ids_intended:
                        errors.append(
                            f"attempt_telemetry_event_id_intended_duplicate:{telemetry_event_id}"
                        )
                        continue
                    seen_telemetry_ids_intended.add(telemetry_event_id)
            errors.extend(
                self._validate_precommit_intended_diagnosis_semantics(
                    attempt.get("evidence_channel_intended"),
                    attempt.get("assistance_contract_intended"),
                    attempt.get("diagnosis_update_eligibility_intended"),
                    attempt.get("ineligibility_reason_intended"),
                    attempt.get("allowed_update_partitions_intended"),
                )
            )
            errors.extend(self._validate_diagnosis_update_semantics(attempt))
            errors.extend(self._validate_observation(attempt.get("observation")))

            errors.extend(self._validate_grading_signals(attempt.get("grading_signals", {})))
            errors.extend(
                self._validate_residual_inputs(
                    attempt.get("residual_inputs", {}),
                    manifest,
                    attempt.get("version_pointers", {}),
                    attempt.get("observation", {}),
                )
            )
            decision_traces = attempt.get("decision_traces", [])
            errors.extend(self._validate_decision_traces(decision_traces))
            policy_decisions_raw = attempt.get("policy_decisions", [])
            errors.extend(self._validate_policy_decisions(policy_decisions_raw, manifest))
            decision_ids = set()
            if isinstance(policy_decisions_raw, list):
                for decision in policy_decisions_raw:
                    if isinstance(decision, dict):
                        decision_ids.add(decision.get("decision_id"))
            traces_for_join = decision_traces if isinstance(decision_traces, list) else []
            for trace in traces_for_join:
                if isinstance(trace, dict):
                    trace_id = trace.get("decision_id")
                    if trace_id not in decision_ids:
                        errors.append(
                            "attempt_decision_trace_decision_id_missing_from_policy_decisions"
                        )
                        continue
                    matching_decisions = [
                        d
                        for d in policy_decisions_raw
                        if isinstance(d, dict) and d.get("decision_id") == trace_id
                    ]
                    trace_kind = trace.get("trace_kind")
                    for decision in matching_decisions:
                        policy_domain = decision.get("policy_domain")
                        if not self._trace_kind_policy_domain_compatible(
                            trace_kind,
                            policy_domain,
                        ):
                            errors.append(
                                f"attempt_decision_trace_policy_domain_mismatch:{trace_id}"
                            )
                            break

            ope_claim_contract = manifest.get("ope_claim_contract")
            if isinstance(ope_claim_contract, dict):
                target_trace_kinds = ope_claim_contract.get("target_trace_kinds")
                min_candidate_probability = ope_claim_contract.get("min_candidate_probability")
                min_chosen_probability = ope_claim_contract.get("min_chosen_probability")
                min_entropy_bits = ope_claim_contract.get("min_entropy_bits")
                if (
                    isinstance(target_trace_kinds, list)
                    and all(is_non_empty_string(kind) for kind in target_trace_kinds)
                    and is_strict_number(min_candidate_probability)
                    and is_strict_number(min_chosen_probability)
                    and is_strict_number(min_entropy_bits)
                    and isinstance(policy_decisions_raw, list)
                ):
                    target_kinds = set(target_trace_kinds)
                    for trace in traces_for_join:
                        if not isinstance(trace, dict):
                            continue
                        trace_kind = trace.get("trace_kind")
                        if trace_kind not in target_kinds:
                            continue
                        trace_id = trace.get("decision_id")
                        matching_decisions = [
                            d
                            for d in policy_decisions_raw
                            if isinstance(d, dict) and d.get("decision_id") == trace_id
                        ]
                        for decision in matching_decisions:
                            recomputed = audit_queries.recompute_support_claim_for_trace(
                                trace,
                                min_candidate_probability=float(min_candidate_probability),
                                min_chosen_probability=float(min_chosen_probability),
                                min_entropy_bits=float(min_entropy_bits),
                            )
                            if not recomputed.get("valid"):
                                errors.append(f"attempt_policy_decision_support_recompute_invalid:{trace_id}")
                                continue
                            if decision.get("entropy_floor_met") is not bool(
                                recomputed.get("entropy_floor_expected", False)
                            ):
                                errors.append(
                                    f"attempt_policy_decision_entropy_floor_claim_mismatch:{trace_id}"
                                )
                            if decision.get("min_support_met") is not bool(
                                recomputed.get("min_support_expected", False)
                            ):
                                errors.append(
                                    f"attempt_policy_decision_min_support_claim_mismatch:{trace_id}"
                                )
                            if decision.get("support_check_status") != str(
                                recomputed.get("status_expected", "fail")
                            ):
                                errors.append(
                                    f"attempt_policy_decision_support_status_claim_mismatch:{trace_id}"
                                )

            expected_projection = self.replay_projection(manifest)
            if attempt.get("version_pointers") != expected_projection:
                errors.append("attempt_version_pointers_mismatch_manifest_projection")

            idempotency = attempt.get("idempotency", {})
            if not isinstance(idempotency, dict):
                errors.append("attempt_idempotency_not_object")
            elif "sequence_no" not in idempotency or "attempt_hash" not in idempotency:
                errors.append("attempt_idempotency_missing")
            else:
                sequence_no = idempotency.get("sequence_no")
                attempt_hash = idempotency.get("attempt_hash")
                if not is_strict_int(sequence_no) or sequence_no <= 0:
                    errors.append("attempt_idempotency_sequence_no_invalid")
                if not is_non_empty_string(attempt_hash):
                    errors.append("attempt_idempotency_attempt_hash_invalid")

            if not is_non_empty_string(attempt.get("precommit_event_id")):
                errors.append("attempt_precommit_event_id_invalid")
            if not is_non_empty_string(attempt.get("precommit_hash")):
                errors.append("attempt_precommit_hash_invalid")
            else:
                expected_precommit_hash = sha256_json(self.precommit_projection_from_attempt(attempt))
                if attempt.get("precommit_hash") != expected_precommit_hash:
                    errors.append("attempt_precommit_hash_mismatch_projection")
            if not is_non_empty_string(attempt.get("precommit_envelope_hash")):
                errors.append("attempt_precommit_envelope_hash_invalid")
            else:
                expected_envelope_hash = sha256_json(
                    self.precommit_envelope_projection_from_attempt(attempt)
                )
                if attempt.get("precommit_envelope_hash") != expected_envelope_hash:
                    errors.append("attempt_precommit_envelope_hash_mismatch_projection")

            return errors
        except Exception as exc:
            return [f"attempt_validator_internal_exception:{type(exc).__name__}"]

    def validate_attempt_precommit(self, precommit: dict[str, Any], manifest: dict[str, Any]) -> list[str]:
        if not isinstance(precommit, dict):
            return ["attempt_precommit_record_not_object"]
        if not isinstance(manifest, dict):
            return ["attempt_precommit_manifest_not_object"]
        try:
            errors: list[str] = []
            missing = missing_required_fields(precommit, ATTEMPT_PRECOMMIT_REQUIRED_FIELDS)
            if missing:
                errors.append("attempt_precommit_missing:" + ",".join(missing))
                return errors
            schema_errors = self._validate_schema_version_support(precommit, "attempt_precommit")
            if schema_errors:
                errors.extend(schema_errors)
                return errors

            errors.extend(
                self._validate_required_non_empty_strings(
                    precommit,
                    (
                        "schema_version",
                        "run_id",
                        "timeline_id",
                        "session_id",
                        "precommit_event_id",
                        "attempt_id",
                        "learner_id",
                        "item_id",
                        "probe_family_id",
                        "commitment_id",
                        "evidence_channel_intended",
                        "assistance_contract_intended",
                        "diagnosis_update_eligibility_intended",
                        "ineligibility_reason_intended",
                    ),
                    "attempt_precommit",
                )
            )
            errors.extend(self._validate_semantic_commitment(precommit, "attempt_precommit"))
            if precommit.get("run_id") != manifest.get("run_id"):
                errors.append("attempt_precommit_run_id_mismatch_manifest")
            if precommit.get("timeline_id") != manifest.get("timeline_id"):
                errors.append("attempt_precommit_timeline_id_mismatch_manifest")
            if not is_rfc3339_utc(precommit.get("presented_ts_utc")):
                errors.append("attempt_precommit_presented_ts_utc_invalid")
            evidence_channel_intended = precommit.get("evidence_channel_intended")
            assistance_contract_intended = precommit.get("assistance_contract_intended")
            eligibility_intended = precommit.get("diagnosis_update_eligibility_intended")
            reason_intended = precommit.get("ineligibility_reason_intended")
            allowed_partitions_intended_raw = precommit.get("allowed_update_partitions_intended")

            if evidence_channel_intended not in EVIDENCE_CHANNELS:
                errors.append("attempt_precommit_evidence_channel_intended_invalid")
            if assistance_contract_intended not in ASSISTANCE_MODES:
                errors.append("attempt_precommit_assistance_contract_intended_invalid")
            if eligibility_intended not in DIAGNOSIS_UPDATE_ELIGIBILITY:
                errors.append("attempt_precommit_diagnosis_update_eligibility_intended_invalid")
            if reason_intended not in INELIGIBILITY_REASON:
                errors.append("attempt_precommit_ineligibility_reason_intended_invalid")
            if not isinstance(allowed_partitions_intended_raw, list):
                errors.append("attempt_precommit_allowed_update_partitions_intended_not_array")
                allowed_partitions_intended = []
            else:
                allowed_partitions_intended = allowed_partitions_intended_raw
                seen_allowed: set[str] = set()
                for idx, partition in enumerate(allowed_partitions_intended):
                    if partition not in ALLOWED_UPDATE_PARTITIONS:
                        errors.append(
                            f"attempt_precommit_allowed_update_partitions_intended_invalid[{idx}]"
                        )
                        continue
                    if partition in seen_allowed:
                        errors.append(
                            f"attempt_precommit_allowed_update_partitions_intended_duplicate:{partition}"
                        )
                        continue
                    seen_allowed.add(partition)
            telemetry_event_ids_intended = precommit.get("telemetry_event_ids_intended")
            if not isinstance(telemetry_event_ids_intended, list) or not telemetry_event_ids_intended:
                errors.append("attempt_precommit_telemetry_event_ids_intended_invalid")
            else:
                seen_telemetry_ids: set[str] = set()
                for idx, telemetry_event_id in enumerate(telemetry_event_ids_intended):
                    if not is_non_empty_string(telemetry_event_id):
                        errors.append(
                            f"attempt_precommit_telemetry_event_id_intended_invalid[{idx}]"
                        )
                        continue
                    if telemetry_event_id in seen_telemetry_ids:
                        errors.append(
                            f"attempt_precommit_telemetry_event_id_intended_duplicate:{telemetry_event_id}"
                        )
                        continue
                    seen_telemetry_ids.add(telemetry_event_id)

            errors.extend(
                self._validate_precommit_intended_diagnosis_semantics(
                    evidence_channel_intended,
                    assistance_contract_intended,
                    eligibility_intended,
                    reason_intended,
                    allowed_partitions_intended_raw,
                )
            )

            if not is_non_empty_string(precommit.get("precommit_event_id")):
                errors.append("attempt_precommit_event_id_invalid")
            if not is_non_empty_string(precommit.get("precommit_hash")):
                errors.append("attempt_precommit_hash_invalid")
            else:
                expected_hash = sha256_json(self.precommit_projection_from_record(precommit))
                if precommit.get("precommit_hash") != expected_hash:
                    errors.append("attempt_precommit_hash_mismatch_projection")
            if not is_non_empty_string(precommit.get("precommit_envelope_hash")):
                errors.append("attempt_precommit_envelope_hash_invalid")
            else:
                expected_envelope_hash = sha256_json(
                    self.precommit_envelope_projection_from_record(precommit)
                )
                if precommit.get("precommit_envelope_hash") != expected_envelope_hash:
                    errors.append("attempt_precommit_envelope_hash_mismatch_projection")

            errors.extend(self._validate_decision_traces(precommit.get("decision_traces", [])))
            policy_decisions = precommit.get("policy_decisions", [])
            errors.extend(self._validate_policy_decisions(policy_decisions, manifest))
            decision_ids = set()
            if isinstance(policy_decisions, list):
                for decision in policy_decisions:
                    if isinstance(decision, dict):
                        decision_ids.add(decision.get("decision_id"))
            precommit_traces = precommit.get("decision_traces", [])
            if isinstance(precommit_traces, list):
                for trace in precommit_traces:
                    if isinstance(trace, dict):
                        trace_id = trace.get("decision_id")
                        if trace_id not in decision_ids:
                            errors.append(
                                "attempt_precommit_decision_trace_decision_id_missing_from_policy_decisions"
                            )
                            continue
                        matching_decisions = [
                            d
                            for d in policy_decisions
                            if isinstance(d, dict) and d.get("decision_id") == trace_id
                        ]
                        trace_kind = trace.get("trace_kind")
                        for decision in matching_decisions:
                            policy_domain = decision.get("policy_domain")
                            if not self._trace_kind_policy_domain_compatible(
                                trace_kind,
                                policy_domain,
                            ):
                                errors.append(
                                    f"attempt_precommit_decision_trace_policy_domain_mismatch:{trace_id}"
                                )
                                break

            likelihood_errors = self._validate_likelihood_sketch(
                precommit.get("likelihood_sketch", {}),
                manifest,
                {"slot_pattern": ""},
            )
            errors.extend(likelihood_errors)

            expected_projection = self.replay_projection(manifest)
            if precommit.get("version_pointers") != expected_projection:
                errors.append("attempt_precommit_version_pointers_mismatch_manifest_projection")
            return errors
        except Exception as exc:
            return [f"attempt_precommit_validator_internal_exception:{type(exc).__name__}"]

    def _expected_diagnosis_semantics(
        self,
        assistance_mode: Any,
        evidence_channel: Any,
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

    def _validate_precommit_intended_diagnosis_semantics(
        self,
        evidence_channel_intended: Any,
        assistance_contract_intended: Any,
        diagnosis_update_eligibility_intended: Any,
        ineligibility_reason_intended: Any,
        allowed_update_partitions_intended: Any,
    ) -> list[str]:
        errors: list[str] = []
        if not isinstance(allowed_update_partitions_intended, list):
            return errors
        expected_eligibility, expected_reason, _ = self._expected_diagnosis_semantics(
            assistance_contract_intended,
            evidence_channel_intended,
        )
        if diagnosis_update_eligibility_intended != expected_eligibility:
            errors.append("attempt_precommit_diagnosis_update_eligibility_intended_mismatch_semantics")
        if ineligibility_reason_intended != expected_reason:
            errors.append("attempt_precommit_ineligibility_reason_intended_mismatch_semantics")
        if expected_eligibility == "eligible":
            if "diagnosis_state" not in allowed_update_partitions_intended:
                errors.append(
                    "attempt_precommit_allowed_update_partitions_intended_missing_diagnosis_state"
                )
        elif "diagnosis_state" in allowed_update_partitions_intended:
            errors.append("attempt_precommit_allowed_update_partitions_intended_allows_diagnosis_state")
        return errors

    def _validate_diagnosis_update_semantics(self, attempt: dict[str, Any]) -> list[str]:
        errors: list[str] = []
        assistance_mode = attempt.get("assistance_mode_derived", attempt.get("assistance_mode"))
        evidence_channel = attempt["evidence_channel"]
        eligibility = attempt["diagnosis_update_eligibility"]
        reason = attempt["ineligibility_reason"]
        derivation_quality = attempt.get("assistance_derivation_quality")
        allowed_partitions_raw = attempt["allowed_update_partitions"]
        allowed_partitions = (
            allowed_partitions_raw if isinstance(allowed_partitions_raw, list) else []
        )

        if derivation_quality != "derived_from_telemetry":
            if eligibility != "ineligible":
                errors.append("attempt_untrusted_assistance_derivation_must_be_ineligible")
            if "diagnosis_state" in allowed_partitions:
                errors.append("attempt_untrusted_assistance_derivation_allows_diagnosis_state")
            return errors

        expected_eligibility, expected_reason, _ = self._expected_diagnosis_semantics(
            assistance_mode,
            evidence_channel,
        )
        should_be_eligible = expected_eligibility == "eligible"

        if should_be_eligible:
            if eligibility != "eligible":
                errors.append("attempt_diagnostic_closed_book_must_be_eligible")
            if reason != "none":
                errors.append("attempt_eligible_ineligibility_reason_must_be_none")
            if "diagnosis_state" not in allowed_partitions:
                errors.append("attempt_eligible_allowed_update_partitions_missing_diagnosis_state")
            return errors

        if eligibility != "ineligible":
            errors.append("attempt_non_diagnostic_or_assisted_must_be_ineligible")
        if "diagnosis_state" in allowed_partitions:
            errors.append("attempt_ineligible_allows_diagnosis_state")
        if reason != expected_reason:
            errors.append("attempt_ineligibility_reason_mismatch_semantics")
        return errors

    def validate_attempt_diagnosis_semantics(self, attempt: dict[str, Any]) -> list[str]:
        """Public single-source check for assistance/channel/eligibility semantics."""
        if not isinstance(attempt, dict):
            return ["attempt_record_not_object"]
        required = {
            "assistance_mode",
            "assistance_mode_derived",
            "assistance_derivation_quality",
            "evidence_channel",
            "diagnosis_update_eligibility",
            "ineligibility_reason",
            "allowed_update_partitions",
        }
        missing = missing_required_fields(attempt, required)
        if missing:
            return ["attempt_missing:" + ",".join(missing)]
        return self._validate_diagnosis_update_semantics(attempt)

    def validate_decision_traces_contract(self, traces: Any) -> list[str]:
        """Public single-source check for decision trace probability contract."""
        return self._validate_decision_traces(traces)

    def validate_attempt_telemetry_event(
        self,
        telemetry_event: dict[str, Any],
        manifest: dict[str, Any],
    ) -> list[str]:
        if not isinstance(telemetry_event, dict):
            return ["attempt_telemetry_record_not_object"]
        if not isinstance(manifest, dict):
            return ["attempt_telemetry_manifest_not_object"]
        try:
            errors: list[str] = []
            missing = missing_required_fields(telemetry_event, ATTEMPT_TELEMETRY_REQUIRED_FIELDS)
            if missing:
                errors.append("attempt_telemetry_missing:" + ",".join(missing))
                return errors
            schema_errors = self._validate_schema_version_support(telemetry_event, "attempt_telemetry")
            if schema_errors:
                errors.extend(schema_errors)
                return errors
            errors.extend(
                self._validate_required_non_empty_strings(
                    telemetry_event,
                    (
                        "schema_version",
                        "run_id",
                        "timeline_id",
                        "session_id",
                        "attempt_id",
                        "learner_id",
                        "telemetry_event_id",
                        "source",
                        "payload_hash",
                    ),
                    "attempt_telemetry",
                )
            )
            if telemetry_event.get("run_id") != manifest.get("run_id"):
                errors.append("attempt_telemetry_run_id_mismatch_manifest")
            if telemetry_event.get("timeline_id") != manifest.get("timeline_id"):
                errors.append("attempt_telemetry_timeline_id_mismatch_manifest")
            if not is_rfc3339_utc(telemetry_event.get("telemetry_ts_utc")):
                errors.append("attempt_telemetry_ts_utc_invalid")
            if telemetry_event.get("telemetry_kind") not in TELEMETRY_KINDS:
                errors.append("attempt_telemetry_kind_invalid")
            expected_payload_hash = sha256_json(self._telemetry_payload_projection(telemetry_event))
            if telemetry_event.get("payload_hash") != expected_payload_hash:
                errors.append("attempt_telemetry_payload_hash_mismatch_projection")
            return errors
        except Exception as exc:
            return [f"attempt_telemetry_validator_internal_exception:{type(exc).__name__}"]

    def validate_state_snapshot(self, snapshot: dict[str, Any], manifest: dict[str, Any]) -> list[str]:
        if not isinstance(snapshot, dict):
            return ["state_snapshot_record_not_object"]
        if not isinstance(manifest, dict):
            return ["state_snapshot_manifest_not_object"]
        try:
            errors: list[str] = []
            missing = missing_required_fields(snapshot, STATE_SNAPSHOT_REQUIRED_FIELDS)
            if missing:
                errors.append("state_snapshot_missing:" + ",".join(missing))
                return errors
            schema_errors = self._validate_schema_version_support(snapshot, "state_snapshot")
            if schema_errors:
                errors.extend(schema_errors)
                return errors

            errors.extend(
                self._validate_required_non_empty_strings(
                    snapshot,
                    (
                        "schema_version",
                        "run_id",
                        "timeline_id",
                        "session_id",
                        "snapshot_id",
                        "learner_id",
                    ),
                    "state_snapshot",
                )
            )
            if snapshot.get("run_id") != manifest.get("run_id"):
                errors.append("state_snapshot_run_id_mismatch_manifest")
            if snapshot.get("timeline_id") != manifest.get("timeline_id"):
                errors.append("state_snapshot_timeline_id_mismatch_manifest")
            if not is_rfc3339_utc(snapshot.get("snapshot_ts_utc")):
                errors.append("state_snapshot_snapshot_ts_utc_invalid")

            source_attempt_ids = snapshot.get("source_attempt_ids")
            if not isinstance(source_attempt_ids, list):
                errors.append("state_snapshot_source_attempt_ids_not_array")
            else:
                seen_source_ids: set[str] = set()
                for idx, source_id in enumerate(source_attempt_ids):
                    if not is_non_empty_string(source_id):
                        errors.append(f"state_snapshot_source_attempt_id_invalid[{idx}]")
                        continue
                    if source_id in seen_source_ids:
                        errors.append(f"state_snapshot_source_attempt_id_duplicate:{source_id}")
                        continue
                    seen_source_ids.add(source_id)

            expected_projection = self.replay_projection(manifest)
            if snapshot.get("version_pointers") != expected_projection:
                errors.append("state_snapshot_version_pointers_mismatch_manifest_projection")

            payload = snapshot.get("state_payload")
            if not isinstance(payload, dict):
                errors.append("state_snapshot_payload_not_object")
            else:
                if "diagnosis_state" not in payload:
                    errors.append("state_snapshot_missing_diagnosis_state_partition")
                if "learning_retention_state" not in payload:
                    errors.append("state_snapshot_missing_learning_retention_state_partition")
                expected_hash = sha256_json(payload)
                if snapshot.get("state_hash") != expected_hash:
                    errors.append("state_snapshot_state_hash_mismatch_payload")
            if not is_non_empty_string(snapshot.get("state_hash")):
                errors.append("state_snapshot_state_hash_invalid")
            return errors
        except Exception as exc:
            return [f"state_snapshot_validator_internal_exception:{type(exc).__name__}"]

    def validate_state_update_event(self, update: dict[str, Any]) -> list[str]:
        if not isinstance(update, dict):
            return ["state_update_record_not_object"]
        try:
            schema_errors = self._validate_schema_version_support(update, "state_update")
            if schema_errors:
                return schema_errors
            return self._validate_state_update_event_impl(update)
        except Exception as exc:
            return [f"state_update_validator_internal_exception:{type(exc).__name__}"]

    def validate_state_migration_event(
        self,
        migration: dict[str, Any],
        manifest: dict[str, Any],
    ) -> list[str]:
        if not isinstance(migration, dict):
            return ["state_migration_record_not_object"]
        if not isinstance(manifest, dict):
            return ["state_migration_manifest_not_object"]
        try:
            errors: list[str] = []
            missing = missing_required_fields(migration, STATE_MIGRATION_REQUIRED_FIELDS)
            if missing:
                errors.append("state_migration_missing:" + ",".join(missing))
                return errors
            schema_errors = self._validate_schema_version_support(migration, "state_migration")
            if schema_errors:
                errors.extend(schema_errors)
                return errors

            errors.extend(
                self._validate_required_non_empty_strings(
                    migration,
                    (
                        "schema_version",
                        "run_id",
                        "timeline_id",
                        "migration_event_id",
                        "source_run_id",
                        "source_snapshot_id",
                        "source_state_hash",
                        "source_replay_fingerprint",
                        "target_manifest_replay_fingerprint",
                        "migration_rule_set_version",
                        "pre_migration_state_hash",
                        "post_migration_state_hash",
                        "transform_hash",
                    ),
                    "state_migration",
                )
            )
            if migration.get("run_id") != manifest.get("run_id"):
                errors.append("state_migration_run_id_mismatch_manifest")
            if migration.get("timeline_id") != manifest.get("timeline_id"):
                errors.append("state_migration_timeline_id_mismatch_manifest")
            if not is_rfc3339_utc(migration.get("migration_ts_utc")):
                errors.append("state_migration_ts_utc_invalid")
            if migration.get("target_manifest_replay_fingerprint") != manifest.get("replay_fingerprint"):
                errors.append("state_migration_target_replay_fingerprint_mismatch_manifest")

            rule_ids = migration.get("migration_rule_ids")
            if not isinstance(rule_ids, list) or not rule_ids:
                errors.append("state_migration_rule_ids_invalid")
            else:
                seen_rule_ids: set[str] = set()
                for idx, rule_id in enumerate(rule_ids):
                    if not is_non_empty_string(rule_id):
                        errors.append(f"state_migration_rule_id_invalid[{idx}]")
                        continue
                    if rule_id in seen_rule_ids:
                        errors.append(f"state_migration_rule_id_duplicate:{rule_id}")
                        continue
                    seen_rule_ids.add(rule_id)

            if not isinstance(migration.get("partition_migration_summary"), dict):
                errors.append("state_migration_partition_migration_summary_not_object")
            return errors
        except Exception as exc:
            return [f"state_migration_validator_internal_exception:{type(exc).__name__}"]

    def validate_safe_mode_transition_event(
        self,
        transition: dict[str, Any],
        manifest: dict[str, Any],
    ) -> list[str]:
        if not isinstance(transition, dict):
            return ["safe_mode_transition_record_not_object"]
        if not isinstance(manifest, dict):
            return ["safe_mode_transition_manifest_not_object"]
        try:
            errors: list[str] = []
            missing = missing_required_fields(transition, SAFE_MODE_TRANSITION_REQUIRED_FIELDS)
            if missing:
                errors.append("safe_mode_transition_missing:" + ",".join(missing))
                return errors
            schema_errors = self._validate_schema_version_support(
                transition, "safe_mode_transition"
            )
            if schema_errors:
                errors.extend(schema_errors)
                return errors

            errors.extend(
                self._validate_required_non_empty_strings(
                    transition,
                    (
                        "schema_version",
                        "run_id",
                        "timeline_id",
                        "event_id",
                        "trigger_id",
                        "dominant_trigger_id",
                        "trigger_payload_hash",
                        "profile_id",
                        "profile_parent_state",
                        "profile_resolution_version",
                        "policy_bundle_hash",
                        "reason",
                        "spec_version",
                    ),
                    "safe_mode_transition",
                )
            )
            session_id = transition.get("session_id")
            if session_id is not None and not is_non_empty_string(session_id):
                errors.append("safe_mode_transition_session_id_invalid")
            actor_id = transition.get("actor_id")
            if actor_id is not None and not is_non_empty_string(actor_id):
                errors.append("safe_mode_transition_actor_id_invalid")
            if transition.get("run_id") != manifest.get("run_id"):
                errors.append("safe_mode_transition_run_id_mismatch_manifest")
            if transition.get("timeline_id") != manifest.get("timeline_id"):
                errors.append("safe_mode_transition_timeline_id_mismatch_manifest")
            if not is_rfc3339_utc(transition.get("event_ts_utc")):
                errors.append("safe_mode_transition_event_ts_utc_invalid")
            if transition.get("spec_version") != manifest.get("safe_mode_spec_version"):
                errors.append("safe_mode_transition_spec_version_mismatch_manifest")

            prior_state = transition.get("prior_state")
            next_state = transition.get("next_state")
            if prior_state not in SAFE_MODE_STATES:
                errors.append("safe_mode_transition_prior_state_invalid")
            if next_state not in SAFE_MODE_STATES:
                errors.append("safe_mode_transition_next_state_invalid")
            trigger_id = transition.get("trigger_id")
            dominant_trigger_id = transition.get("dominant_trigger_id")
            if trigger_id not in SAFE_MODE_TRIGGER_IDS:
                errors.append("safe_mode_transition_trigger_id_invalid")
            if dominant_trigger_id not in SAFE_MODE_TRIGGER_IDS:
                errors.append("safe_mode_transition_dominant_trigger_id_invalid")

            trigger_set_raw = transition.get("trigger_set")
            trigger_set: list[str] = []
            if not isinstance(trigger_set_raw, list) or not trigger_set_raw:
                errors.append("safe_mode_transition_trigger_set_invalid")
            else:
                seen_triggers: set[str] = set()
                for idx, candidate_trigger in enumerate(trigger_set_raw):
                    if candidate_trigger not in SAFE_MODE_TRIGGER_IDS:
                        errors.append(f"safe_mode_transition_trigger_set_member_invalid[{idx}]")
                        continue
                    if candidate_trigger in seen_triggers:
                        errors.append(
                            f"safe_mode_transition_trigger_set_member_duplicate:{candidate_trigger}"
                        )
                        continue
                    seen_triggers.add(candidate_trigger)
                    trigger_set.append(candidate_trigger)
            if isinstance(trigger_id, str) and trigger_set and trigger_id not in trigger_set:
                errors.append("safe_mode_transition_trigger_id_not_in_trigger_set")

            expected_dominant_trigger_id = self._expected_dominant_trigger_id(trigger_set)
            if (
                expected_dominant_trigger_id is not None
                and dominant_trigger_id != expected_dominant_trigger_id
            ):
                errors.append("safe_mode_transition_dominant_trigger_id_mismatch")
            expected_next_state = None
            if isinstance(prior_state, str):
                expected_next_state = self._expected_safe_mode_next_state(prior_state, trigger_set)
            if expected_next_state is None:
                errors.append("safe_mode_transition_next_state_unresolvable")
            elif next_state != expected_next_state:
                errors.append("safe_mode_transition_next_state_mismatch")

            profile_id = transition.get("profile_id")
            if profile_id not in SAFE_MODE_PROFILE_IDS:
                errors.append("safe_mode_transition_profile_id_invalid")
            elif expected_dominant_trigger_id is not None and isinstance(next_state, str):
                expected_profile = self._expected_profile_id(expected_dominant_trigger_id, next_state)
                if expected_profile is None:
                    errors.append("safe_mode_transition_profile_unresolvable")
                elif profile_id != expected_profile:
                    errors.append("safe_mode_transition_profile_id_mismatch")
                expected_parent_state = SAFE_MODE_PROFILE_PARENT_STATES.get(profile_id)
                if transition.get("profile_parent_state") != expected_parent_state:
                    errors.append("safe_mode_transition_profile_parent_state_mismatch")

                expected_policy_bundle_hash = SAFE_MODE_POLICY_BUNDLE_HASHES.get(profile_id)
                if transition.get("policy_bundle_hash") != expected_policy_bundle_hash:
                    errors.append("safe_mode_transition_policy_bundle_hash_mismatch")
            return errors
        except Exception as exc:
            return [f"safe_mode_transition_validator_internal_exception:{type(exc).__name__}"]

    def validate_quarantine_decision_event(
        self,
        decision: dict[str, Any],
        manifest: dict[str, Any],
    ) -> list[str]:
        if not isinstance(decision, dict):
            return ["quarantine_decision_record_not_object"]
        if not isinstance(manifest, dict):
            return ["quarantine_decision_manifest_not_object"]
        try:
            errors: list[str] = []
            missing = missing_required_fields(decision, QUARANTINE_DECISION_REQUIRED_FIELDS)
            if missing:
                errors.append("quarantine_decision_missing:" + ",".join(missing))
                return errors
            schema_errors = self._validate_schema_version_support(
                decision, "quarantine_decision"
            )
            if schema_errors:
                errors.extend(schema_errors)
                return errors
            errors.extend(
                self._validate_required_non_empty_strings(
                    decision,
                    (
                        "schema_version",
                        "run_id",
                        "timeline_id",
                        "event_id",
                        "quarantine_id",
                        "metric_id",
                        "scope_type",
                        "scope_id",
                        "threshold_config_version",
                        "action",
                        "reason",
                        "spec_version",
                    ),
                    "quarantine_decision",
                )
            )
            session_id = decision.get("session_id")
            if session_id is not None and not is_non_empty_string(session_id):
                errors.append("quarantine_decision_session_id_invalid")
            if decision.get("run_id") != manifest.get("run_id"):
                errors.append("quarantine_decision_run_id_mismatch_manifest")
            if decision.get("timeline_id") != manifest.get("timeline_id"):
                errors.append("quarantine_decision_timeline_id_mismatch_manifest")
            if decision.get("spec_version") != manifest.get("invariants_charter_version"):
                errors.append("quarantine_decision_spec_version_mismatch_manifest")
            if not is_rfc3339_utc(decision.get("event_ts_utc")):
                errors.append("quarantine_decision_event_ts_utc_invalid")
            if decision.get("scope_type") not in QUARANTINE_SCOPE_TYPES:
                errors.append("quarantine_decision_scope_type_invalid")
            if decision.get("action") not in QUARANTINE_ACTIONS:
                errors.append("quarantine_decision_action_invalid")
            threshold_value = decision.get("threshold_value")
            observed_value = decision.get("observed_value")
            if not is_strict_number(threshold_value):
                errors.append("quarantine_decision_threshold_value_not_numeric")
            if not is_strict_number(observed_value):
                errors.append("quarantine_decision_observed_value_not_numeric")
            threshold_crossed = decision.get("threshold_crossed")
            if not isinstance(threshold_crossed, bool):
                errors.append("quarantine_decision_threshold_crossed_not_bool")
            elif decision.get("action") == "quarantine" and threshold_crossed is not True:
                errors.append("quarantine_decision_quarantine_action_requires_threshold_crossed")
            elif decision.get("action") == "release" and threshold_crossed is True:
                errors.append("quarantine_decision_release_action_requires_threshold_not_crossed")
            return errors
        except Exception as exc:
            return [f"quarantine_decision_validator_internal_exception:{type(exc).__name__}"]

    def validate_anchor_audit_event(
        self,
        audit_event: dict[str, Any],
        manifest: dict[str, Any],
    ) -> list[str]:
        if not isinstance(audit_event, dict):
            return ["anchor_audit_record_not_object"]
        if not isinstance(manifest, dict):
            return ["anchor_audit_manifest_not_object"]
        try:
            errors: list[str] = []
            missing = missing_required_fields(audit_event, ANCHOR_AUDIT_REQUIRED_FIELDS)
            if missing:
                errors.append("anchor_audit_missing:" + ",".join(missing))
                return errors
            schema_errors = self._validate_schema_version_support(audit_event, "anchor_audit")
            if schema_errors:
                errors.extend(schema_errors)
                return errors
            errors.extend(
                self._validate_required_non_empty_strings(
                    audit_event,
                    (
                        "schema_version",
                        "run_id",
                        "timeline_id",
                        "event_id",
                        "audit_id",
                        "window_id",
                        "scope_type",
                        "scope_id",
                        "audit_status",
                        "reason",
                        "spec_version",
                    ),
                    "anchor_audit",
                )
            )
            session_id = audit_event.get("session_id")
            if session_id is not None and not is_non_empty_string(session_id):
                errors.append("anchor_audit_session_id_invalid")
            if audit_event.get("run_id") != manifest.get("run_id"):
                errors.append("anchor_audit_run_id_mismatch_manifest")
            if audit_event.get("timeline_id") != manifest.get("timeline_id"):
                errors.append("anchor_audit_timeline_id_mismatch_manifest")
            if audit_event.get("spec_version") != manifest.get("invariants_charter_version"):
                errors.append("anchor_audit_spec_version_mismatch_manifest")
            if not is_rfc3339_utc(audit_event.get("event_ts_utc")):
                errors.append("anchor_audit_event_ts_utc_invalid")

            if audit_event.get("scope_type") not in POLICY_SCOPE_TYPES:
                errors.append("anchor_audit_scope_type_invalid")
            if audit_event.get("audit_status") not in ANCHOR_AUDIT_STATUSES:
                errors.append("anchor_audit_status_invalid")

            quota_min = audit_event.get("quota_min")
            anchors_sampled = audit_event.get("anchors_sampled")
            cross_graded_count = audit_event.get("cross_graded_count")
            disagreement_rate = audit_event.get("cross_grade_disagreement_rate")
            for value, code in (
                (quota_min, "anchor_audit_quota_min_invalid"),
                (anchors_sampled, "anchor_audit_anchors_sampled_invalid"),
                (cross_graded_count, "anchor_audit_cross_graded_count_invalid"),
            ):
                if not is_strict_int(value) or value < 0:
                    errors.append(code)
            if is_strict_int(quota_min) and is_strict_int(anchors_sampled):
                if anchors_sampled < quota_min:
                    errors.append("anchor_audit_quota_not_met")
            if is_strict_int(cross_graded_count) and is_strict_int(anchors_sampled):
                if cross_graded_count > anchors_sampled:
                    errors.append("anchor_audit_cross_graded_count_exceeds_sampled")
            if not is_strict_number(disagreement_rate):
                errors.append("anchor_audit_cross_grade_disagreement_rate_not_numeric")
            elif disagreement_rate < 0 or disagreement_rate > 1:
                errors.append("anchor_audit_cross_grade_disagreement_rate_out_of_range")
            return errors
        except Exception as exc:
            return [f"anchor_audit_validator_internal_exception:{type(exc).__name__}"]

    def _validate_state_update_event_impl(self, update: dict[str, Any]) -> list[str]:
        errors: list[str] = []
        missing = missing_required_fields(update, STATE_UPDATE_REQUIRED_FIELDS)
        if missing:
            errors.append("state_update_missing:" + ",".join(missing))
            return errors

        errors.extend(
            self._validate_required_non_empty_strings(
                update,
                (
                    "schema_version",
                    "run_id",
                    "timeline_id",
                    "session_id",
                    "snapshot_id",
                    "update_id",
                    "learner_id",
                    "source_attempt_id",
                    "stratum_id",
                    "governor_reason",
                    "safe_mode_profile_id",
                    "governor_transform_version",
                ),
                "state_update",
            )
        )
        if not is_rfc3339_utc(update.get("update_ts_utc")):
            errors.append("state_update_update_ts_utc_invalid")

        if update["calibration_status_at_update"] not in CALIBRATION_STATUS:
            errors.append("state_update_calibration_status_invalid")
        if update["governor_decision"] not in GOVERNOR_DECISIONS:
            errors.append("state_update_governor_decision_invalid")
        if update["safe_mode_profile_id"] not in SAFE_MODE_PROFILE_IDS:
            errors.append("state_update_safe_mode_profile_id_invalid")
        if update["diagnosis_log_write_status"] not in DIAGNOSIS_LOG_WRITE_STATUS:
            errors.append("state_update_diagnosis_log_write_status_invalid")
        if update["mutation_outcome"] not in MUTATION_OUTCOMES:
            errors.append("state_update_mutation_outcome_invalid")
        if update["suppression_reason"] not in SUPPRESSION_REASONS:
            errors.append("state_update_suppression_reason_invalid")
        if not isinstance(update["mutation_attempted"], bool):
            errors.append("state_update_mutation_attempted_not_bool")
        if not isinstance(update["mutation_applied"], bool):
            errors.append("state_update_mutation_applied_not_bool")
        if not is_non_empty_string(update["pre_state_hash"]):
            errors.append("state_update_pre_state_hash_invalid")
        if not is_non_empty_string(update["post_state_hash"]):
            errors.append("state_update_post_state_hash_invalid")
        patch_errors = self._validate_state_patch(update.get("state_patch"))
        errors.extend(patch_errors)
        proposed_patch_errors = self._validate_state_patch(update.get("proposed_state_patch"))
        errors.extend([e.replace("state_update_state_patch", "state_update_proposed_state_patch") for e in proposed_patch_errors])

        base_value_at_proposal = update.get("base_value_at_proposal")
        if not is_strict_number(base_value_at_proposal):
            errors.append("state_update_base_value_at_proposal_not_numeric")

        patch = update.get("state_patch")
        proposed_patch = update.get("proposed_state_patch")
        if not patch_errors and isinstance(patch, dict):
            patch_partition = patch.get("partition")
            if patch_partition not in {"diagnosis_state", "learning_retention_state"}:
                errors.append("state_update_state_patch_partition_invalid")
            if not proposed_patch_errors and isinstance(proposed_patch, dict):
                if proposed_patch.get("partition") != patch_partition:
                    errors.append("state_update_proposed_patch_partition_mismatch")
                if proposed_patch.get("path") != patch.get("path"):
                    errors.append("state_update_proposed_patch_path_mismatch")
                if proposed_patch.get("op") != patch.get("op"):
                    errors.append("state_update_proposed_patch_op_mismatch")

        # v1.1 frozen contract rules
        if isinstance(patch, dict) and patch.get("partition") == "diagnosis_state":
            applied_multiplier = update.get("applied_update_multiplier")
            if not is_strict_number(applied_multiplier):
                errors.append("state_update_applied_update_multiplier_not_numeric")
            expected_multiplier = self._expected_diagnosis_multiplier_for_profile(
                update.get("safe_mode_profile_id"),
                update.get("governor_decision"),
            )
            if expected_multiplier is not None and is_strict_number(applied_multiplier):
                if not float_equal(float(applied_multiplier), expected_multiplier):
                    errors.append("state_update_profile_multiplier_mismatch")
            if update.get("safe_mode_profile_id") == "SG_CALIBRATION_GUARD":
                governor_decision = update["governor_decision"]
                if governor_decision not in GOVERNOR_MULTIPLIERS:
                    errors.append("state_update_governor_decision_invalid")
                elif is_strict_number(applied_multiplier):
                    expected_from_ladder = GOVERNOR_MULTIPLIERS[governor_decision]
                    if not float_equal(float(applied_multiplier), expected_from_ladder):
                        errors.append("state_update_governor_multiplier_mismatch")

            if update["calibration_status_at_update"] == "miscalibrated_persistent":
                if update["governor_decision"] not in {"throttle", "strong_throttle", "freeze"}:
                    errors.append("state_update_miscalibrated_governor_decision_invalid")

            if update["governor_decision"] == "freeze" and update["mutation_outcome"] == "applied":
                errors.append("state_update_freeze_cannot_apply_diagnosis_mutation")
            if (
                isinstance(update.get("safe_mode_profile_id"), str)
                and str(update.get("safe_mode_profile_id")).startswith("SP_")
                and update.get("mutation_outcome") == "applied"
            ):
                errors.append("state_update_panic_profile_cannot_apply_diagnosis_mutation")

            if not proposed_patch_errors and isinstance(proposed_patch, dict):
                proposed_value = proposed_patch.get("value")
                applied_value = patch.get("value")
                if not is_strict_number(proposed_value):
                    errors.append("state_update_proposed_patch_value_not_numeric_for_diagnosis")
                if not is_strict_number(applied_value):
                    errors.append("state_update_state_patch_value_not_numeric_for_diagnosis")
                if (
                    is_strict_number(proposed_value)
                    and is_strict_number(applied_value)
                    and is_strict_number(base_value_at_proposal)
                ):
                    if not is_strict_number(applied_multiplier):
                        errors.append("state_update_applied_update_multiplier_not_numeric")
                    elif update.get("governor_decision") not in GOVERNOR_MULTIPLIERS:
                        errors.append("state_update_governor_decision_invalid")
                    elif update["mutation_outcome"] == "applied":
                        expected_applied_value = float(base_value_at_proposal) + float(applied_multiplier) * (
                            float(proposed_value) - float(base_value_at_proposal)
                        )
                        if not float_equal(float(applied_value), expected_applied_value, tolerance=1e-8):
                            errors.append("state_update_governed_transform_mismatch")

        ledger_status = update["diagnosis_log_write_status"]
        mutation_outcome = update["mutation_outcome"]
        mutation_attempted = update["mutation_attempted"]
        mutation_applied = update["mutation_applied"]
        suppression_reason = update["suppression_reason"]
        log_commit_id = update["log_commit_id"]
        integrity_event_id = update["integrity_event_id"]

        if ledger_status in {"failed", "missing"}:
            if mutation_outcome != "failed_due_to_integrity":
                errors.append("state_update_failed_or_missing_requires_integrity_outcome")
            if mutation_attempted is not False:
                errors.append("state_update_failed_or_missing_must_not_attempt_mutation")
            if mutation_applied is not False:
                errors.append("state_update_failed_or_missing_must_not_apply_mutation")
            if update["pre_state_hash"] != update["post_state_hash"]:
                errors.append("state_update_failed_or_missing_requires_equal_pre_post_hash")
            if not is_non_empty_string(integrity_event_id):
                errors.append("state_update_failed_or_missing_requires_integrity_event_id")
            if log_commit_id is not None:
                errors.append("state_update_failed_or_missing_log_commit_id_should_be_null")
            return errors

        # From here, ledger append was committed; event-level durability exists.
        if mutation_outcome == "applied":
            if mutation_attempted is not True:
                errors.append("state_update_applied_requires_mutation_attempted")
            if mutation_applied is not True:
                errors.append("state_update_applied_requires_mutation_applied")
            if update["pre_state_hash"] == update["post_state_hash"]:
                errors.append("state_update_applied_requires_state_hash_change")
            if not is_non_empty_string(log_commit_id):
                errors.append("state_update_applied_requires_log_commit_id")
            if integrity_event_id is not None:
                errors.append("state_update_applied_integrity_event_should_be_null")
            if suppression_reason != "none":
                errors.append("state_update_applied_requires_no_suppression_reason")
            return errors

        if mutation_outcome == "blocked_by_governor":
            if mutation_attempted is not False:
                errors.append("state_update_blocked_by_governor_must_not_attempt_mutation")
            if mutation_applied is not False:
                errors.append("state_update_blocked_by_governor_must_not_apply_mutation")
            if update["pre_state_hash"] != update["post_state_hash"]:
                errors.append("state_update_blocked_by_governor_requires_equal_pre_post_hash")
            if log_commit_id is not None:
                errors.append("state_update_blocked_by_governor_log_commit_id_should_be_null")
            if integrity_event_id is not None:
                errors.append("state_update_blocked_by_governor_integrity_event_should_be_null")
            if suppression_reason == "none":
                errors.append("state_update_blocked_by_governor_requires_suppression_reason")
            return errors

        if mutation_outcome == "skipped_by_policy":
            if mutation_attempted is not False:
                errors.append("state_update_skipped_by_policy_must_not_attempt_mutation")
            if mutation_applied is not False:
                errors.append("state_update_skipped_by_policy_must_not_apply_mutation")
            if update["pre_state_hash"] != update["post_state_hash"]:
                errors.append("state_update_skipped_by_policy_requires_equal_pre_post_hash")
            if suppression_reason != "policy_skip":
                errors.append("state_update_skipped_by_policy_requires_policy_skip_reason")
            if log_commit_id is not None:
                errors.append("state_update_skipped_by_policy_log_commit_id_should_be_null")
            if integrity_event_id is not None:
                errors.append("state_update_skipped_by_policy_integrity_event_should_be_null")
            return errors

        if mutation_outcome == "failed_due_to_integrity":
            if mutation_applied is not False:
                errors.append("state_update_integrity_failure_must_not_apply_mutation")
            if mutation_attempted is not True:
                errors.append("state_update_integrity_failure_requires_mutation_attempted")
            if update["pre_state_hash"] != update["post_state_hash"]:
                errors.append("state_update_integrity_failure_requires_equal_pre_post_hash")
            if not is_non_empty_string(integrity_event_id):
                errors.append("state_update_integrity_failure_requires_integrity_event_id")
            if log_commit_id is not None:
                errors.append("state_update_integrity_failure_log_commit_id_should_be_null")
            if suppression_reason != "none":
                errors.append("state_update_integrity_failure_requires_no_suppression_reason")
        return errors

    def _validate_grading_signals(self, grading: dict[str, Any]) -> list[str]:
        required = {
            "deterministic_applied",
            "llm_used",
            "rubric_path_count",
            "schema_valid",
            "injection_flags",
            "llm_passes",
            "llm_disagreement",
        }
        missing = missing_required_fields(grading, required)
        return [("attempt_grading_signals_missing:" + ",".join(missing))] if missing else []

    def _validate_observation(self, observation: Any) -> list[str]:
        if not isinstance(observation, dict):
            return ["attempt_observation_not_object"]
        if not is_non_empty_string(observation.get("slot_pattern")):
            return ["attempt_observation_slot_pattern_invalid"]
        return []

    def _validate_residual_primitive_inputs(self, primitive_inputs: dict[str, Any]) -> list[str]:
        errors: list[str] = []
        required = {
            "det_vs_llm_disagreement",
            "llm_multipass_disagreement",
            "schema_invalid",
            "rubric_path_count",
            "equivalence_class_size",
            "reference_answer_conflict",
            "injection_flag_count",
            "parsing_confidence",
        }
        missing = missing_required_fields(primitive_inputs, required)
        if missing:
            errors.append("attempt_residual_primitive_inputs_missing:" + ",".join(missing))
            return errors

        if not isinstance(primitive_inputs.get("det_vs_llm_disagreement"), bool):
            errors.append("attempt_residual_primitive_det_vs_llm_disagreement_invalid")
        llm_multipass = primitive_inputs.get("llm_multipass_disagreement")
        if llm_multipass is not None and not isinstance(llm_multipass, bool):
            errors.append("attempt_residual_primitive_llm_multipass_disagreement_invalid")
        if not isinstance(primitive_inputs.get("schema_invalid"), bool):
            errors.append("attempt_residual_primitive_schema_invalid_invalid")
        rubric_path_count = primitive_inputs.get("rubric_path_count")
        if not is_strict_int(rubric_path_count):
            errors.append("attempt_residual_primitive_rubric_path_count_invalid")
        equivalence_size = primitive_inputs.get("equivalence_class_size")
        if equivalence_size is not None and not is_strict_int(equivalence_size):
            errors.append("attempt_residual_primitive_equivalence_class_size_invalid")
        reference_conflict = primitive_inputs.get("reference_answer_conflict")
        if reference_conflict is not None and not isinstance(reference_conflict, bool):
            errors.append("attempt_residual_primitive_reference_answer_conflict_invalid")
        injection_count = primitive_inputs.get("injection_flag_count")
        if not is_strict_int(injection_count):
            errors.append("attempt_residual_primitive_injection_flag_count_invalid")
        parsing_confidence = primitive_inputs.get("parsing_confidence")
        if parsing_confidence is not None and not is_probability(parsing_confidence):
            errors.append("attempt_residual_primitive_parsing_confidence_invalid")
        return errors

    def _validate_residual_derived_inputs(self, derived_inputs: dict[str, Any]) -> list[str]:
        errors: list[str] = []
        required = {"max_hypothesis_likelihood"}
        missing = missing_required_fields(derived_inputs, required)
        if missing:
            errors.append("attempt_residual_derived_inputs_missing:" + ",".join(missing))
            return errors
        max_likelihood = derived_inputs.get("max_hypothesis_likelihood")
        if not is_probability(max_likelihood):
            errors.append("attempt_residual_derived_max_hypothesis_likelihood_not_numeric")
        return errors

    def _validate_residual_inputs(
        self,
        residual_inputs: dict[str, Any],
        manifest: dict[str, Any],
        version_pointers: dict[str, Any],
        observation: dict[str, Any],
    ) -> list[str]:
        errors: list[str] = []
        required = {"primitive_inputs", "likelihood_sketch", "provenance", "derived_inputs"}
        missing = missing_required_fields(residual_inputs, required)
        if missing:
            errors.append("attempt_residual_inputs_missing:" + ",".join(missing))
            return errors

        primitive_inputs = residual_inputs.get("primitive_inputs")
        if not isinstance(primitive_inputs, dict):
            errors.append("attempt_residual_primitive_inputs_not_object")
            primitive_inputs = {}
        derived_inputs = residual_inputs.get("derived_inputs")
        if not isinstance(derived_inputs, dict):
            errors.append("attempt_residual_derived_inputs_not_object")
            derived_inputs = {}

        errors.extend(self._validate_residual_primitive_inputs(primitive_inputs))
        errors.extend(self._validate_residual_derived_inputs(derived_inputs))

        provenance = residual_inputs.get("provenance", {})
        if not isinstance(provenance, dict):
            errors.append("attempt_residual_provenance_not_object")
            provenance = {}
        if not isinstance(version_pointers, dict):
            errors.append("attempt_version_pointers_not_object_for_residuals")
            version_pointers = {}
        for field in RESIDUAL_PROVENANCE_PINNED_FIELDS:
            if field not in provenance:
                errors.append(f"attempt_residual_provenance_missing:{field}")
                continue

            value = provenance.get(field)
            if value != manifest.get(field):
                errors.append(f"attempt_residual_provenance_mismatch_manifest:{field}")

            if field in version_pointers and value != version_pointers.get(field):
                errors.append(f"attempt_residual_provenance_mismatch_version_pointers:{field}")

        snapshot_id = provenance.get("state_snapshot_id")
        if not is_non_empty_string(snapshot_id):
            errors.append("attempt_residual_provenance_state_snapshot_id_invalid")

        likelihood_errors = self._validate_likelihood_sketch(
            residual_inputs.get("likelihood_sketch", {}),
            manifest,
            observation,
        )
        errors.extend(likelihood_errors)
        return errors

    def _validate_likelihood_sketch(
        self,
        likelihood_sketch: dict[str, Any],
        manifest: dict[str, Any],
        observation: dict[str, Any],
    ) -> list[str]:
        errors: list[str] = []
        if not isinstance(likelihood_sketch, dict):
            return ["attempt_likelihood_sketch_not_object"]
        required = {"top_hypotheses", "predicted_observation_distribution"}
        missing = missing_required_fields(likelihood_sketch, required)
        if missing:
            errors.append("attempt_likelihood_sketch_missing:" + ",".join(missing))
            return errors

        top_hypotheses = likelihood_sketch.get("top_hypotheses")
        if not isinstance(top_hypotheses, list) or not top_hypotheses:
            errors.append("attempt_likelihood_top_hypotheses_invalid")
        else:
            seen_hypotheses: set[str] = set()
            for idx, row in enumerate(top_hypotheses):
                if not isinstance(row, dict):
                    errors.append(f"attempt_likelihood_top_hypothesis_row_not_object[{idx}]")
                    continue
                if "hypothesis_id" not in row or "likelihood" not in row:
                    errors.append(f"attempt_likelihood_top_hypothesis_missing_fields[{idx}]")
                    continue
                hypothesis_id = row["hypothesis_id"]
                likelihood = row["likelihood"]
                if not isinstance(hypothesis_id, str) or hypothesis_id == "":
                    errors.append(f"attempt_likelihood_top_hypothesis_id_invalid[{idx}]")
                elif hypothesis_id in seen_hypotheses:
                    errors.append(f"attempt_likelihood_top_hypothesis_duplicate:{hypothesis_id}")
                else:
                    seen_hypotheses.add(hypothesis_id)
                if not is_probability(likelihood):
                    errors.append(f"attempt_likelihood_top_hypothesis_probability_invalid[{idx}]")

        distribution = likelihood_sketch.get("predicted_observation_distribution")
        if not isinstance(distribution, list) or not distribution:
            errors.append("attempt_likelihood_distribution_invalid")
            return errors

        obs_encoder_version = manifest.get("obs_encoder_version")
        hypothesis_space_hash = manifest.get("hypothesis_space_hash")
        known_vocab = self._obs_vocab_registry.get_vocab(obs_encoder_version, hypothesis_space_hash)
        if known_vocab is None:
            errors.append("attempt_likelihood_vocab_binding_unknown")
            return errors

        prob_sum = 0.0
        seen_obs_keys: set[str] = set()
        for idx, row in enumerate(distribution):
            if not isinstance(row, dict):
                errors.append(f"attempt_likelihood_distribution_row_not_object[{idx}]")
                continue
            if "obs_key" not in row or "p" not in row:
                errors.append(f"attempt_likelihood_distribution_missing_fields[{idx}]")
                continue
            obs_key = row["obs_key"]
            p = row["p"]
            if not isinstance(obs_key, str) or obs_key == "":
                errors.append(f"attempt_likelihood_distribution_obs_key_invalid[{idx}]")
                continue
            if obs_key in seen_obs_keys:
                errors.append(f"attempt_likelihood_distribution_duplicate_obs_key:{obs_key}")
            else:
                seen_obs_keys.add(obs_key)
            if obs_key not in known_vocab:
                errors.append(f"attempt_likelihood_distribution_obs_key_unknown:{obs_key}")
            if not is_probability(p):
                errors.append(f"attempt_likelihood_distribution_probability_invalid[{idx}]")
                continue
            prob_sum += float(p)

        if not float_equal(prob_sum, 1.0, tolerance=1e-5):
            errors.append("attempt_likelihood_distribution_not_normalized")

        if not isinstance(observation, dict):
            errors.append("attempt_observation_not_object")
            observed_key = None
        else:
            observed_key = observation.get("slot_pattern")
        if isinstance(observed_key, str) and observed_key != "" and observed_key not in known_vocab:
            errors.append("attempt_observation_slot_pattern_unknown")
        return errors

    def _validate_decision_traces(self, traces: Any) -> list[str]:
        if not isinstance(traces, list):
            return ["attempt_decision_traces_not_array"]
        if not traces:
            return ["attempt_decision_traces_empty"]

        errors: list[str] = []
        seen_decision_ids: set[str] = set()
        for idx, trace in enumerate(traces):
            if not isinstance(trace, dict):
                errors.append(f"attempt_decision_trace_row_not_object[{idx}]")
                continue

            missing = missing_required_fields(trace, DECISION_TRACE_REQUIRED_FIELDS)
            if missing:
                errors.append(f"attempt_decision_trace_missing[{idx}]:" + ",".join(missing))
                continue

            decision_id = trace["decision_id"]
            trace_kind = trace["trace_kind"]
            if not is_non_empty_string(decision_id):
                errors.append(f"attempt_decision_trace_decision_id_invalid[{idx}]")
            elif decision_id in seen_decision_ids:
                errors.append(f"attempt_decision_trace_duplicate_decision_id:{decision_id}")
            else:
                seen_decision_ids.add(decision_id)

            if not is_non_empty_string(trace_kind):
                errors.append(f"attempt_decision_trace_trace_kind_invalid[{idx}]")
            elif trace_kind not in TRACE_KINDS:
                errors.append(f"attempt_decision_trace_trace_kind_unknown:{trace_kind}")
            if not is_non_empty_string(trace.get("chosen_action_id")):
                errors.append(f"attempt_decision_trace_chosen_action_id_invalid[{idx}]")

            errors.extend(
                self._validate_candidate_actions(
                    trace["candidate_actions"],
                    trace["chosen_action_id"],
                    trace["chosen_action_probability"],
                    prefix=f"attempt_decision_trace[{idx}]",
                )
            )
        return errors

    def _validate_candidate_actions(
        self,
        candidates: Any,
        chosen_action_id: Any,
        chosen_action_probability: Any,
        prefix: str,
    ) -> list[str]:
        errors: list[str] = []
        if not isinstance(candidates, list) or not candidates:
            errors.append(f"{prefix}_candidates_empty")
            return errors

        prob_sum = 0.0
        chosen_probability = None
        seen_action_ids: set[str] = set()
        for candidate in candidates:
            if not isinstance(candidate, dict):
                errors.append(f"{prefix}_candidate_not_object")
                continue
            if "action_id" not in candidate or "p" not in candidate:
                errors.append(f"{prefix}_candidate_missing_fields")
                continue
            action_id = candidate.get("action_id")
            if not is_non_empty_string(action_id):
                errors.append(f"{prefix}_candidate_action_id_invalid")
                continue
            if action_id in seen_action_ids:
                errors.append(f"{prefix}_candidate_action_id_duplicate:{action_id}")
                continue
            seen_action_ids.add(action_id)
            p = candidate["p"]
            if not is_probability(p):
                errors.append(f"{prefix}_candidate_probability_invalid")
                continue
            prob_sum += float(p)
            if action_id == chosen_action_id:
                chosen_probability = float(p)

        if not float_equal(prob_sum, 1.0, tolerance=1e-5):
            errors.append(f"{prefix}_probabilities_not_normalized")
        if chosen_probability is None:
            errors.append(f"{prefix}_chosen_action_missing_in_candidates")
        elif not is_probability(chosen_action_probability):
            errors.append(f"{prefix}_chosen_probability_not_numeric")
        elif not float_equal(chosen_probability, float(chosen_action_probability)):
            errors.append(f"{prefix}_chosen_probability_mismatch")
        return errors

    def _validate_state_patch(self, patch: Any) -> list[str]:
        if not isinstance(patch, dict):
            return ["state_update_state_patch_not_object"]
        required = {"op", "partition", "path", "value"}
        missing = missing_required_fields(patch, required)
        if missing:
            return ["state_update_state_patch_missing:" + ",".join(missing)]

        errors: list[str] = []
        if patch["op"] != "set":
            errors.append("state_update_state_patch_op_invalid")
        if patch["partition"] not in {"diagnosis_state", "learning_retention_state"}:
            errors.append("state_update_state_patch_partition_invalid")
        path = patch["path"]
        if not isinstance(path, str) or path == "":
            errors.append("state_update_state_patch_path_invalid")
        return errors

    def _validate_policy_decisions(self, decisions: Any, manifest: dict[str, Any]) -> list[str]:
        errors: list[str] = []
        if not isinstance(decisions, list):
            return ["attempt_policy_decisions_not_array"]

        required = {
            "decision_id",
            "policy_domain",
            "policy_version",
            "rule_id",
            "scope_type",
            "scope_id",
            "outcome",
            "commit_status",
            "reason_code",
            "decision_ts_utc",
            "entropy_floor_met",
            "min_support_met",
            "support_check_status",
        }
        for idx, decision in enumerate(decisions):
            if not isinstance(decision, dict):
                errors.append(f"attempt_policy_decision_row_not_object[{idx}]")
                continue
            missing = missing_required_fields(decision, required)
            if missing:
                errors.append(f"attempt_policy_decision_missing[{idx}]:" + ",".join(missing))
                continue
            for field in ("decision_id", "rule_id", "scope_id", "reason_code"):
                if not is_non_empty_string(decision.get(field)):
                    errors.append(f"attempt_policy_decision_{field}_invalid[{idx}]")
            if decision["policy_domain"] not in POLICY_DOMAINS:
                errors.append(f"attempt_policy_decision_domain_invalid[{idx}]")
            if decision["policy_version"] != manifest.get("policy_version"):
                errors.append(f"attempt_policy_decision_policy_version_mismatch_manifest[{idx}]")
            if decision["scope_type"] not in POLICY_SCOPE_TYPES:
                errors.append(f"attempt_policy_decision_scope_type_invalid[{idx}]")
            if decision["outcome"] not in POLICY_OUTCOMES:
                errors.append(f"attempt_policy_decision_outcome_invalid[{idx}]")
            if decision["commit_status"] not in COMMIT_STATUS:
                errors.append(f"attempt_policy_decision_commit_status_invalid[{idx}]")
            if decision["support_check_status"] not in SUPPORT_CHECK_STATUS:
                errors.append(f"attempt_policy_decision_support_check_status_invalid[{idx}]")
            if not is_rfc3339_utc(decision.get("decision_ts_utc")):
                errors.append(f"attempt_policy_decision_decision_ts_utc_invalid[{idx}]")
            entropy_floor_met = decision.get("entropy_floor_met")
            min_support_met = decision.get("min_support_met")
            if entropy_floor_met is not None and not isinstance(entropy_floor_met, bool):
                errors.append(f"attempt_policy_decision_entropy_floor_met_invalid[{idx}]")
            if min_support_met is not None and not isinstance(min_support_met, bool):
                errors.append(f"attempt_policy_decision_min_support_met_invalid[{idx}]")
        return errors
