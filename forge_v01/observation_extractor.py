"""Observation extraction from canonical responses and grader outputs."""

from __future__ import annotations

from typing import Any

from .grading_types import (
    CanonicalResponse,
    DeterministicGraderOutput,
    MeasurementFrameBinding,
    ObservationExtractionResult,
)
from .measurement_frame import derive_obs_key_from_projection


def emit_observation(
    measurement_frame: MeasurementFrameBinding,
    measurement_surface: dict[str, Any],
    observation_schema: dict[str, Any],
    rubric: dict[str, Any],
    calibration_projection: dict[str, Any],
    canonical_response: CanonicalResponse,
    grader_output: DeterministicGraderOutput,
    runtime_context: dict[str, Any] | None,
) -> ObservationExtractionResult:
    runtime_context = runtime_context or {}
    errors: list[str] = []
    observation_features: dict[str, Any] = {}
    feature_map = _observation_feature_map(observation_schema)
    outcome_surface_feature_ids = {
        str(v)
        for v in observation_schema.get("outcome_surface_feature_ids", [])
        if isinstance(v, str) and v
    }
    fields = rubric.get("observation_emission", {}).get("fields", [])
    for field in fields:
        if not isinstance(field, dict):
            continue
        feature_id = field.get("feature_id")
        source = field.get("source")
        source_path = field.get("source_path")
        if not isinstance(feature_id, str) or not feature_id:
            continue
        value = _resolve_emission_value(
            source=source,
            source_path=source_path,
            canonical_response=canonical_response,
            grader_output=grader_output,
            runtime_context=runtime_context,
        )
        if feature_id not in feature_map:
            errors.append(f"emitted_feature_unknown:{feature_id}")
            continue
        if value is None:
            continue
        if feature_id in outcome_surface_feature_ids and grader_output.scoring_resolution_status != "valid":
            continue
        observation_features[feature_id] = value

    required_feature_ids = {
        feature_id
        for feature_id, feature in feature_map.items()
        if feature.get("required") is True
    }
    always_required = required_feature_ids - outcome_surface_feature_ids
    for feature_id in sorted(always_required):
        if feature_id not in observation_features:
            errors.append(f"required_feature_missing:{feature_id}")
    if grader_output.scoring_resolution_status == "valid":
        for feature_id in sorted(outcome_surface_feature_ids):
            if feature_id not in observation_features:
                errors.append(f"outcome_surface_feature_missing:{feature_id}")

    if grader_output.scoring_resolution_status == "valid":
        obs_key = derive_obs_key_from_projection(
            calibration_projection,
            observation_features,
            observation_status="valid",
        )
        observation_status = "valid"
        observation_invalid_reason = None
        if obs_key is None:
            observation_status = "invalid"
            observation_invalid_reason = "obs_key_not_derivable_from_projection"
            errors.append("obs_key_not_derivable_from_projection")
    else:
        obs_key = None
        observation_status = grader_output.scoring_resolution_status
        observation_invalid_reason = grader_output.ambiguity_kind or grader_output.scoring_resolution_status

    if errors and observation_status == "valid":
        observation_status = "invalid"
        observation_invalid_reason = "runtime_emission_validation_failed"
        obs_key = None

    observation = {
        "observation_status": observation_status,
        "observation_invalid_reason": observation_invalid_reason,
    }
    if obs_key is not None:
        observation["obs_key"] = obs_key
    if "slot_pattern" in observation_features:
        observation["slot_pattern"] = observation_features["slot_pattern"]
    observation.update(observation_features)
    return ObservationExtractionResult(
        measurement_surface_id=measurement_frame.measurement_surface_id,
        calibration_projection_id=measurement_frame.calibration_projection_id,
        observation=observation,
        outcome_surface={
            k: observation_features[k]
            for k in observation_schema.get("outcome_surface_feature_ids", [])
            if k in observation_features
        },
        observation_features=observation_features,
        obs_key=obs_key,
        observation_status=observation_status,
        observation_invalid_reason=observation_invalid_reason,
        errors=errors,
    )


def _resolve_emission_value(
    *,
    source: Any,
    source_path: Any,
    canonical_response: CanonicalResponse,
    grader_output: DeterministicGraderOutput,
    runtime_context: dict[str, Any],
) -> Any:
    if not isinstance(source, str) or not isinstance(source_path, str):
        return None
    if source == "canonical_response":
        return _lookup_path(canonical_response.canonical_payload, source_path.removeprefix("canonical_response."))
    if source == "grader_output":
        if source_path == "grader_output.latency_bucket":
            return _latency_bucket(runtime_context.get("latency_sec"))
        if source_path == "grader_output.hint_used":
            return _hint_used(runtime_context)
        return _lookup_path(grader_output.grader_output, source_path.removeprefix("grader_output."))
    if source == "constant":
        return source_path
    if source == "parse_ir":
        return None
    return None


def _lookup_path(payload: Any, path: str) -> Any:
    if path == "" or path == "canonical_response" or path == "grader_output":
        return payload
    node = payload
    for part in path.split("."):
        if not isinstance(node, dict) or part not in node:
            return None
        node = node.get(part)
    return node


def _latency_bucket(latency_sec: Any) -> str:
    if not isinstance(latency_sec, (int, float)):
        return "medium"
    if latency_sec <= 30:
        return "fast"
    if latency_sec <= 90:
        return "medium"
    return "slow"


def _hint_used(runtime_context: dict[str, Any]) -> bool:
    hint_count = runtime_context.get("hint_count")
    hint_level = runtime_context.get("hint_level_used")
    if isinstance(hint_count, int):
        return hint_count > 0
    if isinstance(hint_level, int):
        return hint_level > 0
    return False


def _observation_feature_map(observation_schema: dict[str, Any]) -> dict[str, dict[str, Any]]:
    features = observation_schema.get("features")
    if not isinstance(features, list):
        return {}
    feature_map: dict[str, dict[str, Any]] = {}
    for feature in features:
        if not isinstance(feature, dict):
            continue
        feature_id = feature.get("feature_id")
        if isinstance(feature_id, str) and feature_id:
            feature_map[feature_id] = feature
    return feature_map
