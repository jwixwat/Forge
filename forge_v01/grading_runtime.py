"""Runtime orchestration for v0.3 deterministic grading."""

from __future__ import annotations

from typing import Any

from .content_ir_registry import ContentIRRegistry
from .constants import DIAGNOSTIC_EVIDENCE_CHANNELS
from .deterministic_grader import run_deterministic_rubric
from .grading_types import (
    AttemptObservationMaterialization,
    MeasurementAdjudication,
    MeasurementExecutionSemantics,
    MeasurementFrameBinding,
    MeasurementSubjectBinding,
)
from .observation_extractor import emit_observation
from .response_canonicalizer import canonicalize_response


def grade_item_response(
    content_ir_registry: ContentIRRegistry,
    content_ir_version: str,
    item_id: str,
    raw_response: dict[str, Any],
    runtime_context: dict[str, Any] | None = None,
) -> AttemptObservationMaterialization:
    runtime_context = runtime_context or {}
    item = content_ir_registry.resolve_item(content_ir_version, item_id)
    family = content_ir_registry.resolve_probe_family(content_ir_version, item["probe_family_id"])
    measurement_surface = content_ir_registry.resolve_measurement_surface(
        content_ir_version, item["measurement_surface_ref"]
    )
    response_schema = content_ir_registry.resolve_response_schema(
        content_ir_version, item["response_schema_ref"]
    )
    rubric = content_ir_registry.resolve_rubric(content_ir_version, item["rubric_ref"])
    observation_schema = content_ir_registry.resolve_observation_schema(
        content_ir_version, measurement_surface["observation_schema_ref"]
    )
    calibration_projection = family["calibration_contract"]["calibration_target_projection"]
    evidence_channel = str(runtime_context.get("evidence_channel", "B_measurement"))
    assistance_mode = str(
        runtime_context.get(
            "assistance_mode_derived",
            runtime_context.get("assistance_mode", "closed_book"),
        )
    )
    diagnosis_update_eligibility, ineligibility_reason = _diagnosis_semantics(
        assistance_mode,
        evidence_channel,
    )
    measurement_execution = _measurement_execution_from_runtime_context(
        family,
        evidence_channel=evidence_channel,
        runtime_context=runtime_context,
    )
    measurement_frame = MeasurementFrameBinding(
        content_ir_version=content_ir_version,
        measurement_surface_id=measurement_surface["measurement_surface_id"],
        calibration_projection_id=calibration_projection["projection_id"],
        response_schema_id=response_schema["response_schema_id"],
        rubric_id=rubric["rubric_id"],
        observation_schema_id=observation_schema["observation_schema_id"],
        obs_encoder_version=measurement_surface["obs_binding"]["obs_encoder_version"],
        hypothesis_space_hash=measurement_surface["obs_binding"]["hypothesis_space_hash"],
        evidence_channel=evidence_channel,
        assistance_mode=assistance_mode,
        diagnosis_update_eligibility=diagnosis_update_eligibility,
        ineligibility_reason=ineligibility_reason,
    )
    measurement_subject = MeasurementSubjectBinding(
        subject_kind="static_item",
        item_id=item_id,
    )

    item_for_grading = dict(item)
    item_for_grading["_response_schema_payload"] = response_schema.get("payload_schema", {})

    canonical_response = canonicalize_response(response_schema, raw_response, item=item)
    grader_output = run_deterministic_rubric(item_for_grading, rubric, canonical_response)
    observation_result = emit_observation(
        measurement_frame=measurement_frame,
        measurement_surface=measurement_surface,
        observation_schema=observation_schema,
        rubric=rubric,
        calibration_projection=calibration_projection,
        canonical_response=canonical_response,
        grader_output=grader_output,
        runtime_context=runtime_context,
    )
    validation_errors = _validate_materialized_measurement_frame(
        measurement_frame=measurement_frame,
        item=item,
        generator=None,
        family=family,
        measurement_surface=measurement_surface,
        response_schema=response_schema,
        rubric=rubric,
        observation_schema=observation_schema,
        observation_result=observation_result,
    )
    validation_errors.extend(
        _validate_materialized_measurement_execution(
            family=family,
            measurement_frame=measurement_frame,
            measurement_execution=measurement_execution,
            observation_result=observation_result,
            runtime_context=runtime_context,
        )
    )
    measurement_adjudication = _adjudicate_measurement_inclusion(
        family=family,
        measurement_frame=measurement_frame,
        observation_result=observation_result,
        validation_errors=validation_errors,
    )

    grading_signals = {
        "deterministic_applied": grader_output.deterministic_applied,
        "llm_used": False,
        "rubric_path_count": grader_output.rubric_path_count,
        "schema_valid": (
            canonical_response.payload_shape_valid
            and canonical_response.canonicalization_succeeded
            and canonical_response.value_constraints_valid
            and canonical_response.schema_valid
            and grader_output.schema_valid
            and observation_result.observation_status == "valid"
            and not validation_errors
        ),
        "injection_flags": [],
        "llm_passes": 0,
        "llm_disagreement": None,
        "scoring_resolution_status": grader_output.scoring_resolution_status,
        "ambiguity_kind": grader_output.ambiguity_kind,
        "candidate_path_count": grader_output.candidate_path_count,
        "accepted_path_count": grader_output.accepted_path_count,
        "observation_status": observation_result.observation_status,
        "measurement_execution": {
            "feedback_mode_applied": measurement_execution.feedback_mode_applied,
            "hint_count_used": measurement_execution.hint_count_used,
        },
        "measurement_adjudication": {
            "calibration_eligible": measurement_adjudication.calibration_eligible,
            "calibration_inclusion_reason": measurement_adjudication.calibration_inclusion_reason,
        },
    }
    residual_primitive_inputs = {
        "det_vs_llm_disagreement": False,
        "llm_multipass_disagreement": None,
        "schema_invalid": not grading_signals["schema_valid"],
        "rubric_path_count": grader_output.rubric_path_count,
        "scoring_resolution_status": grader_output.scoring_resolution_status,
        "candidate_path_count": grader_output.candidate_path_count,
        "accepted_path_count": grader_output.accepted_path_count,
        "equivalence_class_size": None,
        "reference_answer_conflict": None,
        "injection_flag_count": 0,
        "parsing_confidence": None,
    }
    return AttemptObservationMaterialization(
        item_id=item_id,
        measurement_subject=measurement_subject,
        measurement_frame=measurement_frame,
        measurement_execution=measurement_execution,
        measurement_adjudication=measurement_adjudication,
        canonical_response=canonical_response,
        grader_output=grader_output,
        observation_result=observation_result,
        grading_signals=grading_signals,
        residual_primitive_inputs=residual_primitive_inputs,
        validation_errors=validation_errors,
    )


def grade_generated_instance_response(
    content_ir_registry: ContentIRRegistry,
    content_ir_version: str,
    generator_id: str,
    generated_instance: dict[str, Any],
    raw_response: dict[str, Any],
    runtime_context: dict[str, Any] | None = None,
) -> AttemptObservationMaterialization:
    runtime_context = runtime_context or {}
    generator = content_ir_registry.resolve_generator(content_ir_version, generator_id)
    family = content_ir_registry.resolve_probe_family(content_ir_version, generator["probe_family_id"])
    grading_contract = generator["grading_contract"]
    measurement_surface = content_ir_registry.resolve_measurement_surface(
        content_ir_version, grading_contract["measurement_surface_ref"]
    )
    response_schema = content_ir_registry.resolve_response_schema(
        content_ir_version, grading_contract["response_schema_ref"]
    )
    rubric = content_ir_registry.resolve_rubric(content_ir_version, grading_contract["rubric_ref"])
    observation_schema = content_ir_registry.resolve_observation_schema(
        content_ir_version, measurement_surface["observation_schema_ref"]
    )
    calibration_projection = family["calibration_contract"]["calibration_target_projection"]
    evidence_channel = str(runtime_context.get("evidence_channel", "B_measurement"))
    assistance_mode = str(
        runtime_context.get(
            "assistance_mode_derived",
            runtime_context.get("assistance_mode", "closed_book"),
        )
    )
    diagnosis_update_eligibility, ineligibility_reason = _diagnosis_semantics(
        assistance_mode,
        evidence_channel,
    )
    measurement_execution = _measurement_execution_from_runtime_context(
        family,
        evidence_channel=evidence_channel,
        runtime_context=runtime_context,
    )
    measurement_frame = MeasurementFrameBinding(
        content_ir_version=content_ir_version,
        measurement_surface_id=measurement_surface["measurement_surface_id"],
        calibration_projection_id=calibration_projection["projection_id"],
        response_schema_id=response_schema["response_schema_id"],
        rubric_id=rubric["rubric_id"],
        observation_schema_id=observation_schema["observation_schema_id"],
        obs_encoder_version=measurement_surface["obs_binding"]["obs_encoder_version"],
        hypothesis_space_hash=measurement_surface["obs_binding"]["hypothesis_space_hash"],
        evidence_channel=evidence_channel,
        assistance_mode=assistance_mode,
        diagnosis_update_eligibility=diagnosis_update_eligibility,
        ineligibility_reason=ineligibility_reason,
    )
    measurement_subject = MeasurementSubjectBinding(
        subject_kind="generated_instance",
        item_instance_id=str(generated_instance.get("item_instance_id", "")),
        generator_id=generator_id,
        generator_version=str(generated_instance.get("generator_version", generator["generator_version"])),
        generator_seed=str(generated_instance.get("generator_seed", "")),
        rendered_payload_hash=str(generated_instance.get("rendered_payload_hash", "")),
    )
    generated_grading_material, generated_binding_errors = _grading_material_from_generated_instance(
        generator,
        generated_instance,
    )
    grading_subject = {
        "grading_material": generated_grading_material,
        "_response_schema_payload": response_schema.get("payload_schema", {}),
    }
    canonical_response = canonicalize_response(response_schema, raw_response, item=grading_subject)
    grader_output = run_deterministic_rubric(grading_subject, rubric, canonical_response)
    observation_result = emit_observation(
        measurement_frame=measurement_frame,
        measurement_surface=measurement_surface,
        observation_schema=observation_schema,
        rubric=rubric,
        calibration_projection=calibration_projection,
        canonical_response=canonical_response,
        grader_output=grader_output,
        runtime_context=runtime_context,
    )
    validation_errors = list(generated_binding_errors)
    validation_errors.extend(
        _validate_generated_instance_contract(
            generator=generator,
            generated_instance=generated_instance,
            measurement_subject=measurement_subject,
        )
    )
    validation_errors.extend(
        _validate_materialized_measurement_frame(
            measurement_frame=measurement_frame,
            item=None,
            generator=generator,
            family=family,
            measurement_surface=measurement_surface,
            response_schema=response_schema,
            rubric=rubric,
            observation_schema=observation_schema,
            observation_result=observation_result,
        )
    )
    validation_errors.extend(
        _validate_materialized_measurement_execution(
            family=family,
            measurement_frame=measurement_frame,
            measurement_execution=measurement_execution,
            observation_result=observation_result,
            runtime_context=runtime_context,
        )
    )
    measurement_adjudication = _adjudicate_measurement_inclusion(
        family=family,
        measurement_frame=measurement_frame,
        observation_result=observation_result,
        validation_errors=validation_errors,
    )
    grading_signals = {
        "deterministic_applied": grader_output.deterministic_applied,
        "llm_used": False,
        "rubric_path_count": grader_output.rubric_path_count,
        "schema_valid": (
            canonical_response.payload_shape_valid
            and canonical_response.canonicalization_succeeded
            and canonical_response.value_constraints_valid
            and canonical_response.schema_valid
            and grader_output.schema_valid
            and observation_result.observation_status == "valid"
            and not validation_errors
        ),
        "injection_flags": [],
        "llm_passes": 0,
        "llm_disagreement": None,
        "scoring_resolution_status": grader_output.scoring_resolution_status,
        "ambiguity_kind": grader_output.ambiguity_kind,
        "candidate_path_count": grader_output.candidate_path_count,
        "accepted_path_count": grader_output.accepted_path_count,
        "observation_status": observation_result.observation_status,
        "measurement_execution": {
            "feedback_mode_applied": measurement_execution.feedback_mode_applied,
            "hint_count_used": measurement_execution.hint_count_used,
        },
        "measurement_adjudication": {
            "calibration_eligible": measurement_adjudication.calibration_eligible,
            "calibration_inclusion_reason": measurement_adjudication.calibration_inclusion_reason,
        },
    }
    residual_primitive_inputs = {
        "det_vs_llm_disagreement": False,
        "llm_multipass_disagreement": None,
        "schema_invalid": not grading_signals["schema_valid"],
        "rubric_path_count": grader_output.rubric_path_count,
        "scoring_resolution_status": grader_output.scoring_resolution_status,
        "candidate_path_count": grader_output.candidate_path_count,
        "accepted_path_count": grader_output.accepted_path_count,
        "equivalence_class_size": None,
        "reference_answer_conflict": None,
        "injection_flag_count": 0,
        "parsing_confidence": None,
    }
    return AttemptObservationMaterialization(
        item_id=measurement_subject.item_instance_id or "",
        measurement_subject=measurement_subject,
        measurement_frame=measurement_frame,
        measurement_execution=measurement_execution,
        measurement_adjudication=measurement_adjudication,
        canonical_response=canonical_response,
        grader_output=grader_output,
        observation_result=observation_result,
        grading_signals=grading_signals,
        residual_primitive_inputs=residual_primitive_inputs,
        validation_errors=validation_errors,
    )


def _validate_materialized_measurement_frame(
    *,
    measurement_frame: MeasurementFrameBinding,
    item: dict[str, Any] | None,
    generator: dict[str, Any] | None,
    family: dict[str, Any],
    measurement_surface: dict[str, Any],
    response_schema: dict[str, Any],
    rubric: dict[str, Any],
    observation_schema: dict[str, Any],
    observation_result: Any,
) -> list[str]:
    errors: list[str] = []
    if item is not None:
        if item.get("measurement_surface_ref") != measurement_frame.measurement_surface_id:
            errors.append("item_measurement_surface_mismatch_materialized_frame")
    elif generator is not None:
        grading_contract = generator.get("grading_contract", {})
        if grading_contract.get("measurement_surface_ref") != measurement_frame.measurement_surface_id:
            errors.append("generator_measurement_surface_mismatch_materialized_frame")
        if grading_contract.get("response_schema_ref") != response_schema.get("response_schema_id"):
            errors.append("generator_response_schema_mismatch_materialized_frame")
        if grading_contract.get("rubric_ref") != rubric.get("rubric_id"):
            errors.append("generator_rubric_mismatch_materialized_frame")
    if measurement_frame.measurement_surface_id not in family.get("measurement_surface_refs", []):
        errors.append("family_measurement_surface_missing_materialized_frame")
    if measurement_surface.get("response_schema_ref") != response_schema.get("response_schema_id"):
        errors.append("response_schema_mismatch_materialized_frame")
    if measurement_surface.get("rubric_ref") != rubric.get("rubric_id"):
        errors.append("rubric_mismatch_materialized_frame")
    if measurement_surface.get("observation_schema_ref") != observation_schema.get("observation_schema_id"):
        errors.append("observation_schema_mismatch_materialized_frame")
    if observation_result.measurement_surface_id != measurement_frame.measurement_surface_id:
        errors.append("observation_measurement_surface_id_mismatch_materialized_frame")
    if observation_result.calibration_projection_id != measurement_frame.calibration_projection_id:
        errors.append("observation_calibration_projection_mismatch_materialized_frame")
    return errors


def _validate_materialized_measurement_execution(
    *,
    family: dict[str, Any],
    measurement_frame: MeasurementFrameBinding,
    measurement_execution: MeasurementExecutionSemantics,
    observation_result: Any,
    runtime_context: dict[str, Any],
) -> list[str]:
    errors: list[str] = []
    constraint = _channel_constraint_for(family, measurement_frame.evidence_channel)
    if constraint is None:
        return ["measurement_execution_channel_constraint_missing"]
    expected_feedback_mode = constraint.get("feedback_mode")
    if measurement_execution.feedback_mode_applied != expected_feedback_mode:
        errors.append("measurement_execution_feedback_mode_mismatch_channel_constraint")
    hints_allowed = constraint.get("hints_allowed")
    max_hints = constraint.get("max_hints")
    if hints_allowed is False and measurement_execution.hint_count_used != 0:
        errors.append("measurement_execution_hints_used_when_forbidden")
    if isinstance(max_hints, int) and measurement_execution.hint_count_used > max_hints:
        errors.append("measurement_execution_hint_count_exceeds_channel_constraint")
    feedback_traces = runtime_context.get("feedback_trace_count")
    if feedback_traces is None:
        feedback_traces = len(
            [
                trace
                for trace in runtime_context.get("decision_traces", [])
                if isinstance(trace, dict) and trace.get("trace_kind") == "feedback"
            ]
        )
    if measurement_execution.feedback_mode_applied == "none" and int(feedback_traces or 0) > 0:
        errors.append("measurement_execution_feedback_trace_present_when_feedback_forbidden")
    hint_used = observation_result.observation.get("hint_used")
    if isinstance(hint_used, bool) and hint_used != (measurement_execution.hint_count_used > 0):
        errors.append("measurement_execution_hint_count_mismatch_observation")
    return errors


def _diagnosis_semantics(assistance_mode: str, evidence_channel: str) -> tuple[str, str]:
    closed_book = assistance_mode == "closed_book"
    diagnostic_channel = evidence_channel in DIAGNOSTIC_EVIDENCE_CHANNELS
    if closed_book and diagnostic_channel:
        return ("eligible", "none")
    if not closed_book and diagnostic_channel:
        return ("ineligible", "assistance_mode_not_closed_book")
    if closed_book and not diagnostic_channel:
        return ("ineligible", "channel_not_diagnostic")
    return ("ineligible", "assistance_and_channel")


def _measurement_execution_from_runtime_context(
    family: dict[str, Any],
    *,
    evidence_channel: str,
    runtime_context: dict[str, Any],
) -> MeasurementExecutionSemantics:
    channel_constraint = _channel_constraint_for(family, evidence_channel) or {}
    feedback_mode = str(runtime_context.get("feedback_mode", channel_constraint.get("feedback_mode", "none")))
    hint_count_raw = runtime_context.get("hint_count", 0)
    try:
        hint_count_used = int(hint_count_raw)
    except (TypeError, ValueError):
        hint_count_used = -1
    return MeasurementExecutionSemantics(
        feedback_mode_applied=feedback_mode,
        hint_count_used=hint_count_used,
    )


def _channel_constraint_for(
    family: dict[str, Any],
    evidence_channel: str,
) -> dict[str, Any] | None:
    constraints = family.get("channel_constraints")
    if not isinstance(constraints, list):
        return None
    for row in constraints:
        if isinstance(row, dict) and row.get("channel") == evidence_channel:
            return row
    return None


def _calibration_eligible(
    family: dict[str, Any],
    *,
    evidence_channel: str,
    assistance_mode: str,
) -> bool:
    calibration_contract = family.get("calibration_contract", {})
    inclusion_rules = (
        calibration_contract.get("inclusion_rules")
        if isinstance(calibration_contract, dict)
        else None
    )
    if not isinstance(inclusion_rules, dict):
        return False
    eligible_channels = inclusion_rules.get("eligible_channels")
    eligible_assistance_modes = inclusion_rules.get("eligible_assistance_modes")
    require_closed_book = inclusion_rules.get("require_closed_book")
    if not isinstance(eligible_channels, list) or evidence_channel not in eligible_channels:
        return False
    if not isinstance(eligible_assistance_modes, list) or assistance_mode not in eligible_assistance_modes:
        return False
    if require_closed_book is True and assistance_mode != "closed_book":
        return False
    return True


def _adjudicate_measurement_inclusion(
    *,
    family: dict[str, Any],
    measurement_frame: MeasurementFrameBinding,
    observation_result: Any,
    validation_errors: list[str],
) -> MeasurementAdjudication:
    structurally_eligible = _calibration_eligible(
        family,
        evidence_channel=measurement_frame.evidence_channel,
        assistance_mode=measurement_frame.assistance_mode,
    )
    if not structurally_eligible:
        return MeasurementAdjudication(
            calibration_eligible=False,
            calibration_inclusion_reason="structurally_ineligible",
        )
    if observation_result.observation_status != "valid":
        return MeasurementAdjudication(
            calibration_eligible=False,
            calibration_inclusion_reason="observation_not_valid",
        )
    if validation_errors:
        return MeasurementAdjudication(
            calibration_eligible=False,
            calibration_inclusion_reason="measurement_frame_validation_failed",
        )
    return MeasurementAdjudication(
        calibration_eligible=True,
        calibration_inclusion_reason="eligible",
    )


def _grading_material_from_generated_instance(
    generator: dict[str, Any],
    generated_instance: dict[str, Any],
) -> tuple[dict[str, Any], list[str]]:
    errors: list[str] = []
    grading_contract = generator.get("grading_contract", {})
    solution_contract = grading_contract.get("solution_material_contract", {})
    response_kind = str(solution_contract.get("response_kind", ""))
    required_fields = (
        [str(v) for v in solution_contract.get("required_fields", []) if isinstance(v, str)]
        if isinstance(solution_contract.get("required_fields"), list)
        else []
    )
    solution_material = generated_instance.get("solution_material")
    if not isinstance(solution_material, dict):
        solution_material = {}
        errors.append("generated_instance_solution_material_missing")
    grading_material: dict[str, Any] = {"response_kind": response_kind}
    for field in required_fields:
        if field not in solution_material:
            errors.append(f"generated_instance_solution_material_missing_field:{field}")
            continue
        grading_material[field] = solution_material[field]
    if response_kind == "mcq" and "allowed_choice_ids" in solution_material:
        grading_material["allowed_choice_ids"] = solution_material["allowed_choice_ids"]
    return grading_material, errors


def _validate_generated_instance_contract(
    *,
    generator: dict[str, Any],
    generated_instance: dict[str, Any],
    measurement_subject: MeasurementSubjectBinding,
) -> list[str]:
    errors: list[str] = []
    contract = generator.get("instance_binding_contract", {})
    if not isinstance(contract, dict):
        return ["generated_instance_binding_contract_missing"]
    required_map = {
        "item_instance_id_required": measurement_subject.item_instance_id,
        "generator_id_required": measurement_subject.generator_id,
        "generator_version_required": measurement_subject.generator_version,
        "seed_required": measurement_subject.generator_seed,
        "rendered_payload_hash_required": measurement_subject.rendered_payload_hash,
    }
    for flag, value in required_map.items():
        if contract.get(flag) is True and not value:
            errors.append(f"generated_instance_binding_missing:{flag}")
    if measurement_subject.generator_version and measurement_subject.generator_version != generator.get("generator_version"):
        errors.append("generated_instance_generator_version_mismatch")
    return errors
