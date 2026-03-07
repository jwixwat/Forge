"""Runtime result types for v0.3 deterministic grading."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class MeasurementFrameBinding:
    content_ir_version: str
    measurement_surface_id: str
    calibration_projection_id: str
    response_schema_id: str
    rubric_id: str
    observation_schema_id: str
    obs_encoder_version: str
    hypothesis_space_hash: str
    evidence_channel: str
    assistance_mode: str
    diagnosis_update_eligibility: str
    ineligibility_reason: str


@dataclass(frozen=True)
class MeasurementAdjudication:
    calibration_eligible: bool
    calibration_inclusion_reason: str


@dataclass(frozen=True)
class MeasurementExecutionSemantics:
    feedback_mode_applied: str
    hint_count_used: int


@dataclass(frozen=True)
class MeasurementSubjectBinding:
    subject_kind: str
    item_id: str | None = None
    item_instance_id: str | None = None
    generator_id: str | None = None
    generator_version: str | None = None
    generator_seed: str | None = None
    rendered_payload_hash: str | None = None


@dataclass(frozen=True)
class CanonicalResponse:
    response_schema_id: str
    response_kind: str
    canonical_payload: dict[str, Any]
    payload_shape_valid: bool
    canonicalization_succeeded: bool
    value_constraints_valid: bool
    schema_valid: bool
    errors: list[str] = field(default_factory=list)
    applied_steps: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class DeterministicGraderOutput:
    rubric_id: str
    deterministic_applied: bool
    schema_valid: bool
    ambiguous: bool
    rubric_path_count: int
    scoring_resolution_status: str
    ambiguity_kind: str | None
    candidate_path_count: int
    accepted_path_count: int
    grader_output: dict[str, Any]
    errors: list[str] = field(default_factory=list)
    rule_results: list[dict[str, Any]] = field(default_factory=list)


@dataclass(frozen=True)
class ObservationExtractionResult:
    measurement_surface_id: str
    calibration_projection_id: str
    observation: dict[str, Any]
    outcome_surface: dict[str, Any]
    observation_features: dict[str, Any]
    obs_key: str | None
    observation_status: str
    observation_invalid_reason: str | None
    errors: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class AttemptObservationMaterialization:
    item_id: str
    measurement_subject: MeasurementSubjectBinding
    measurement_frame: MeasurementFrameBinding
    measurement_execution: MeasurementExecutionSemantics
    measurement_adjudication: MeasurementAdjudication
    canonical_response: CanonicalResponse
    grader_output: DeterministicGraderOutput
    observation_result: ObservationExtractionResult
    grading_signals: dict[str, Any]
    residual_primitive_inputs: dict[str, Any]
    validation_errors: list[str] = field(default_factory=list)
