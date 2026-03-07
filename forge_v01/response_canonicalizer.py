"""Canonicalize raw responses according to v0.2 response schemas."""

from __future__ import annotations

import re
from typing import Any

from .grading_types import CanonicalResponse


_WHITESPACE_RE = re.compile(r"\s+")


def canonicalize_response(
    response_schema: dict[str, Any],
    raw_response: dict[str, Any],
    item: dict[str, Any] | None = None,
) -> CanonicalResponse:
    response_schema_id = str(response_schema.get("response_schema_id", ""))
    response_kind = str(response_schema.get("response_kind", ""))
    applied_steps: list[str] = []
    errors: list[str] = []

    if not isinstance(raw_response, dict):
        return CanonicalResponse(
            response_schema_id=response_schema_id,
            response_kind=response_kind,
            canonical_payload={},
            payload_shape_valid=False,
            canonicalization_succeeded=False,
            value_constraints_valid=False,
            schema_valid=False,
            errors=["raw_response_not_object"],
        )

    if response_kind == "slots":
        payload_schema = response_schema.get("payload_schema", {})
        slot_defs = payload_schema.get("slots") if isinstance(payload_schema, dict) else None
        slot_names = [
            str(slot.get("name"))
            for slot in slot_defs
            if isinstance(slot, dict) and isinstance(slot.get("name"), str)
        ] if isinstance(slot_defs, list) else []
        raw_slots = raw_response.get("slots")
        if not isinstance(raw_slots, dict):
            return CanonicalResponse(
                response_schema_id=response_schema_id,
                response_kind=response_kind,
                canonical_payload={"slots": {}},
                payload_shape_valid=False,
                canonicalization_succeeded=False,
                value_constraints_valid=False,
                schema_valid=False,
                errors=["slots_payload_not_object"],
            )
        canonical_slots: dict[str, Any] = {}
        payload_shape_valid = True
        canonicalization_succeeded = True
        value_constraints_valid = True
        schema_valid = True
        raw_slot_keys = set(raw_slots.keys())
        expected_slot_keys = set(slot_names)
        missing_slot_keys = sorted(expected_slot_keys - raw_slot_keys)
        unexpected_slot_keys = sorted(raw_slot_keys - expected_slot_keys)
        if missing_slot_keys:
            errors.append("missing_slot_keys:" + ",".join(missing_slot_keys))
            payload_shape_valid = False
            schema_valid = False
        if unexpected_slot_keys:
            errors.append("unexpected_slot_keys:" + ",".join(unexpected_slot_keys))
            payload_shape_valid = False
            schema_valid = False
        for slot_name in slot_names:
            value = raw_slots.get(slot_name)
            if not isinstance(value, str):
                errors.append(f"slot_value_not_string:{slot_name}")
                schema_valid = False
                canonicalization_succeeded = False
                value_constraints_valid = False
                canonical_slots[slot_name] = None
                continue
            canonical_value, step_errors, step_success = _apply_string_steps(
                value,
                response_schema.get("canonicalization_steps"),
                applied_steps,
            )
            canonical_slots[slot_name] = canonical_value
            errors.extend(f"{slot_name}:{error}" for error in step_errors)
            if not step_success:
                canonicalization_succeeded = False
                schema_valid = False
        return CanonicalResponse(
            response_schema_id=response_schema_id,
            response_kind=response_kind,
            canonical_payload={"slots": canonical_slots},
            payload_shape_valid=payload_shape_valid,
            canonicalization_succeeded=canonicalization_succeeded,
            value_constraints_valid=value_constraints_valid,
            schema_valid=schema_valid,
            errors=errors,
            applied_steps=applied_steps,
        )

    if response_kind == "mcq":
        choice = raw_response.get("choice")
        if not isinstance(choice, str):
            return CanonicalResponse(
                response_schema_id=response_schema_id,
                response_kind=response_kind,
                canonical_payload={"choice": None},
                payload_shape_valid=False,
                canonicalization_succeeded=False,
                value_constraints_valid=False,
                schema_valid=False,
                errors=["choice_not_string"],
            )
        canonical_choice, step_errors, step_success = _apply_string_steps(
            choice,
            response_schema.get("canonicalization_steps"),
            applied_steps,
        )
        errors.extend(step_errors)
        payload_shape_valid = True
        canonicalization_succeeded = step_success
        value_constraints_valid = True
        allowed_choice_ids = _allowed_choice_ids(item)
        schema_valid = step_success and canonical_choice != ""
        if canonical_choice == "":
            errors.append("choice_empty_after_canonicalization")
            value_constraints_valid = False
        if canonical_choice != "" and allowed_choice_ids is not None and canonical_choice not in allowed_choice_ids:
            errors.append("choice_id_not_in_authored_choice_set")
            value_constraints_valid = False
        schema_valid = schema_valid and value_constraints_valid
        return CanonicalResponse(
            response_schema_id=response_schema_id,
            response_kind=response_kind,
            canonical_payload={"choice": canonical_choice},
            payload_shape_valid=payload_shape_valid,
            canonicalization_succeeded=canonicalization_succeeded,
            value_constraints_valid=value_constraints_valid,
            schema_valid=schema_valid,
            errors=errors,
            applied_steps=applied_steps,
        )

    return CanonicalResponse(
        response_schema_id=response_schema_id,
        response_kind=response_kind,
        canonical_payload={},
        payload_shape_valid=False,
        canonicalization_succeeded=False,
        value_constraints_valid=False,
        schema_valid=False,
        errors=[f"unsupported_response_kind:{response_kind}"],
    )


def _apply_string_steps(value: str, steps: Any, applied_steps: list[str]) -> tuple[str, list[str], bool]:
    result = value
    errors: list[str] = []
    succeeded = True
    if not isinstance(steps, list):
        return (result, errors, succeeded)
    for step in steps:
        if not isinstance(step, dict):
            continue
        op = step.get("op")
        step_id = step.get("step_id")
        if isinstance(step_id, str) and step_id:
            applied_steps.append(step_id)
        if op == "trim":
            result = result.strip()
        elif op == "lowercase":
            result = result.lower()
        elif op == "normalize_whitespace":
            result = _WHITESPACE_RE.sub(" ", result).strip()
        elif op == "map_values":
            params = step.get("params")
            mapping = params.get("mapping") if isinstance(params, dict) else None
            if isinstance(mapping, dict) and result in mapping:
                mapped = mapping[result]
                if isinstance(mapped, str):
                    result = mapped
        elif op == "regex_extract":
            params = step.get("params")
            pattern = params.get("pattern") if isinstance(params, dict) else None
            group = params.get("group", 0) if isinstance(params, dict) else 0
            if isinstance(pattern, str):
                match = re.search(pattern, result)
                if match is not None:
                    result = match.group(group)
                else:
                    errors.append(f"regex_extract_no_match:{step_id or 'unknown'}")
                    succeeded = False
        elif op == "sort_keys":
            # No-op for current flat string payloads.
            continue
    return (result, errors, succeeded)
def _allowed_choice_ids(item: dict[str, Any] | None) -> set[str] | None:
    if not isinstance(item, dict):
        return None
    grading_material = item.get("grading_material")
    if not isinstance(grading_material, dict):
        return None
    raw = grading_material.get("allowed_choice_ids")
    if not isinstance(raw, list):
        return None
    normalized = {value for value in raw if isinstance(value, str) and value}
    return normalized or None
