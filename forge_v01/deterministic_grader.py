"""Deterministic rubric execution for v0.3."""

from __future__ import annotations

from typing import Any

from .grading_types import CanonicalResponse, DeterministicGraderOutput


def run_deterministic_rubric(
    item: dict[str, Any],
    rubric: dict[str, Any],
    canonical_response: CanonicalResponse,
) -> DeterministicGraderOutput:
    rubric_id = str(rubric.get("rubric_id", ""))
    if not rubric.get("deterministic"):
        return DeterministicGraderOutput(
            rubric_id=rubric_id,
            deterministic_applied=False,
            schema_valid=False,
            ambiguous=False,
            rubric_path_count=0,
            scoring_resolution_status="unsupported",
            ambiguity_kind="rubric_not_deterministic",
            candidate_path_count=0,
            accepted_path_count=0,
            grader_output={},
            errors=["rubric_not_deterministic"],
        )

    scoring_rules = rubric.get("scoring_rules")
    if not isinstance(scoring_rules, list) or len(scoring_rules) != 1:
        return DeterministicGraderOutput(
            rubric_id=rubric_id,
            deterministic_applied=True,
            schema_valid=False,
            ambiguous=False,
            rubric_path_count=0,
            scoring_resolution_status="unsupported",
            ambiguity_kind="unsupported_scoring_rule_shape",
            candidate_path_count=0,
            accepted_path_count=0,
            grader_output={},
            errors=["unsupported_scoring_rule_shape"],
        )

    rule = scoring_rules[0]
    params = rule.get("params") if isinstance(rule, dict) else None
    logic = params.get("logic") if isinstance(params, dict) else None

    if logic == "slot_exact_match":
        return _grade_slots(item, rubric_id, canonical_response)
    if logic == "choice_equals_answer_key":
        return _grade_mcq(item, rubric_id, canonical_response)

    return DeterministicGraderOutput(
        rubric_id=rubric_id,
        deterministic_applied=True,
        schema_valid=False,
        ambiguous=False,
        rubric_path_count=0,
        scoring_resolution_status="unsupported",
        ambiguity_kind=f"unsupported_rubric_logic:{logic}",
        candidate_path_count=0,
        accepted_path_count=0,
        grader_output={},
        errors=[f"unsupported_rubric_logic:{logic}"],
    )


def _grade_slots(
    item: dict[str, Any],
    rubric_id: str,
    canonical_response: CanonicalResponse,
) -> DeterministicGraderOutput:
    grading_material = item.get("grading_material", {})
    answer_key = grading_material.get("slot_answer_key") if isinstance(grading_material, dict) else None
    payload = canonical_response.canonical_payload.get("slots", {})
    payload_schema = item.get("_response_schema_payload", {})
    slot_defs = payload_schema.get("slots") if isinstance(payload_schema, dict) else None
    slot_names = [
        str(slot.get("name"))
        for slot in slot_defs
        if isinstance(slot, dict) and isinstance(slot.get("name"), str)
    ] if isinstance(slot_defs, list) else []

    if not isinstance(answer_key, list) or len(answer_key) != len(slot_names):
        return DeterministicGraderOutput(
            rubric_id=rubric_id,
            deterministic_applied=True,
            schema_valid=False,
            ambiguous=False,
            rubric_path_count=0,
            scoring_resolution_status="unsupported",
            ambiguity_kind="slot_answer_key_shape_invalid",
            candidate_path_count=0,
            accepted_path_count=0,
            grader_output={},
            errors=["slot_answer_key_shape_invalid"],
        )

    slot_results: dict[str, str] = {}
    failures: list[str] = []
    schema_valid = canonical_response.schema_valid
    for slot_name, expected in zip(slot_names, answer_key):
        actual = payload.get(slot_name) if isinstance(payload, dict) else None
        if not isinstance(actual, str):
            slot_results[slot_name] = "fail"
            failures.append(slot_name)
            schema_valid = False
            continue
        if actual == expected:
            slot_results[slot_name] = "pass"
        else:
            slot_results[slot_name] = "fail"
            failures.append(slot_name)

    if not failures:
        slot_pattern = "all_correct"
    elif len(failures) == len(slot_names):
        slot_pattern = "all_incorrect"
    else:
        slot_pattern = "partial"

    error_mask = ",".join(f"{name}={slot_results[name]}" for name in slot_names)
    return DeterministicGraderOutput(
        rubric_id=rubric_id,
        deterministic_applied=True,
        schema_valid=schema_valid,
        ambiguous=False,
        rubric_path_count=1 if schema_valid else 0,
        scoring_resolution_status="valid" if schema_valid else "invalid",
        ambiguity_kind=None if schema_valid else "schema_invalid",
        candidate_path_count=1,
        accepted_path_count=1 if schema_valid else 0,
        grader_output={
            "slot_pattern": slot_pattern,
            "slot_error_mask": error_mask,
            "slot_results": slot_results,
        },
        errors=list(canonical_response.errors),
        rule_results=[{"rule_id": "slot_exact_match", "outcome": slot_pattern}],
    )


def _grade_mcq(
    item: dict[str, Any],
    rubric_id: str,
    canonical_response: CanonicalResponse,
) -> DeterministicGraderOutput:
    grading_material = item.get("grading_material", {})
    correct_choice_id = grading_material.get("correct_choice_id") if isinstance(grading_material, dict) else None
    choice = canonical_response.canonical_payload.get("choice")
    if not isinstance(correct_choice_id, str) or correct_choice_id == "":
        return DeterministicGraderOutput(
            rubric_id=rubric_id,
            deterministic_applied=True,
            schema_valid=False,
            ambiguous=False,
            rubric_path_count=0,
            scoring_resolution_status="unsupported",
            ambiguity_kind="correct_choice_id_missing",
            candidate_path_count=0,
            accepted_path_count=0,
            grader_output={},
            errors=["correct_choice_id_missing"],
        )
    schema_valid = canonical_response.schema_valid and isinstance(choice, str) and choice != ""
    outcome = "correct" if choice == correct_choice_id else "incorrect"
    return DeterministicGraderOutput(
        rubric_id=rubric_id,
        deterministic_applied=True,
        schema_valid=schema_valid,
        ambiguous=False,
        rubric_path_count=1 if schema_valid else 0,
        scoring_resolution_status="valid" if schema_valid else "invalid",
        ambiguity_kind=None if schema_valid else "schema_invalid",
        candidate_path_count=1,
        accepted_path_count=1 if schema_valid else 0,
        grader_output={
            "mcq_outcome": outcome,
            "selected_choice_id": choice,
        },
        errors=list(canonical_response.errors),
        rule_results=[{"rule_id": "choice_equals_answer_key", "outcome": outcome}],
    )
