"""Canonical hashing helpers for v0.2 content IR bundles and components."""

from __future__ import annotations

import hashlib
import json
from typing import Any

from .content_ir_constants import BUNDLE_REGISTRY_FIELDS


_REGISTRY_ID_FIELDS = {
    "commitments": "commitment_id",
    "factors": "factor_id",
    "edges": "edge_id",
    "observation_schemas": "observation_schema_id",
    "response_schemas": "response_schema_id",
    "rubrics": "rubric_id",
    "measurement_surfaces": "measurement_surface_id",
    "probe_families": "probe_family_id",
    "items": "item_id",
    "forms": "form_id",
    "generators": "generator_id",
    "delivery_artifacts": "artifact_id",
    "feedback_policies": "feedback_policy_id",
    "channel_default_feedback_policies": "channel",
    "content_migrations": "migration_id",
}

_SET_LIKE_PATHS = {
    ("commitments", "*", "aliases"),
    ("commitments", "*", "supersedes"),
    ("commitments", "*", "superseded_by"),
    ("factors", "*", "aliases"),
    ("factors", "*", "supersedes"),
    ("factors", "*", "superseded_by"),
    ("observation_schemas", "*", "outcome_surface_feature_ids"),
    ("observation_schemas", "*", "auxiliary_feature_ids"),
    ("observation_schemas", "*", "features", "*", "allowed_values"),
    ("response_schemas", "*", "parse_ir", "uncertainty_fields"),
    ("measurement_surfaces", "*", "metadata", "surface_tags"),
    ("probe_families", "*", "allowed_channels"),
    ("probe_families", "*", "measurement_surface_refs"),
    ("probe_families", "*", "target_factors"),
    ("items", "*", "target_factor_binding", "primary_target_factors"),
    ("items", "*", "target_factor_binding", "secondary_target_factors"),
    ("probe_families", "*", "assistance_contract", "allowed_assistance_modes"),
    ("probe_families", "*", "assistance_contract", "diagnostic_eligible_assistance_modes"),
    ("probe_families", "*", "assistance_contract", "measurement_preserving_assistance_modes"),
    ("probe_families", "*", "calibration_contract", "inclusion_rules", "eligible_channels"),
    ("probe_families", "*", "calibration_contract", "inclusion_rules", "eligible_assistance_modes"),
    ("probe_families", "*", "calibration_contract", "inclusion_rules", "exclude_residual_flags"),
    ("probe_families", "*", "calibration_contract", "strata_axes", "*", "allowed_values"),
    ("probe_families", "*", "calibration_contract", "calibration_target_projection", "mapping_rules", "*", "source_features"),
    ("items", "*", "channel_tags"),
    ("items", "*", "role_tags"),
    ("items", "*", "form_memberships"),
    ("forms", "*", "form_tags"),
    ("generators", "*", "target_factor_binding", "primary_target_factors"),
    ("generators", "*", "target_factor_binding", "secondary_target_factors"),
    ("generators", "*", "adversarial_contract", "perturbation_axes", "*", "allowed_values"),
    ("content_migrations", "*", "commitment_mapping", "*", "source_ids"),
    ("content_migrations", "*", "commitment_mapping", "*", "target_ids"),
    ("content_migrations", "*", "factor_mapping", "*", "source_ids"),
    ("content_migrations", "*", "factor_mapping", "*", "target_ids"),
    ("content_migrations", "*", "probe_family_mapping", "*", "source_ids"),
    ("content_migrations", "*", "probe_family_mapping", "*", "target_ids"),
    ("content_migrations", "*", "item_mapping", "*", "source_ids"),
    ("content_migrations", "*", "item_mapping", "*", "target_ids"),
    ("content_migrations", "*", "measurement_surface_mapping", "*", "source_ids"),
    ("content_migrations", "*", "measurement_surface_mapping", "*", "target_ids"),
}

_OBJECT_LIST_SORT_RULES: dict[tuple[str, ...], tuple[str, ...]] = {
    ("observation_schemas", "*", "features"): ("feature_id",),
    ("probe_families", "*", "channel_constraints"): ("channel",),
    ("probe_families", "*", "calibration_contract", "strata_axes"): ("axis_id",),
    ("probe_families", "*", "calibration_contract", "calibration_target_projection", "mapping_rules"): ("target",),
    ("probe_families", "*", "invariance_contract", "axes"): ("axis_id",),
    ("probe_families", "*", "invariance_contract", "operational_constraints"): ("constraint_id",),
    ("generators", "*", "invariance_contract", "axes"): ("axis_id",),
    ("generators", "*", "invariance_contract", "operational_constraints"): ("constraint_id",),
    ("change_manifest", "added"): ("entity_type", "entity_id", "change_type"),
    ("change_manifest", "deprecated"): ("entity_type", "entity_id", "change_type"),
    ("change_manifest", "modified"): ("entity_type", "entity_id", "change_type"),
    ("content_migrations", "*", "commitment_mapping"): ("mode", "source_ids", "target_ids"),
    ("content_migrations", "*", "factor_mapping"): ("mode", "source_ids", "target_ids"),
    ("content_migrations", "*", "probe_family_mapping"): ("mode", "source_ids", "target_ids"),
    ("content_migrations", "*", "item_mapping"): ("mode", "source_ids", "target_ids"),
    ("content_migrations", "*", "measurement_surface_mapping"): ("mode", "source_ids", "target_ids"),
}


def _json_bytes(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")


def _sha256(value: Any) -> str:
    return "sha256:" + hashlib.sha256(_json_bytes(value)).hexdigest()


def _path_matches(path: tuple[str, ...], pattern: tuple[str, ...]) -> bool:
    if len(path) != len(pattern):
        return False
    return all(p == "*" or p == x for x, p in zip(path, pattern))


def _object_sort_keys_for_path(path: tuple[str, ...]) -> tuple[str, ...] | None:
    for pattern, sort_keys in _OBJECT_LIST_SORT_RULES.items():
        if _path_matches(path, pattern):
            return sort_keys
    return None


def _is_set_like_path(path: tuple[str, ...]) -> bool:
    return any(_path_matches(path, pattern) for pattern in _SET_LIKE_PATHS)


def _sort_key_for_value(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _row_sort_key(row: dict[str, Any], sort_keys: tuple[str, ...]) -> tuple[str, ...]:
    key_parts: list[str] = []
    for key in sort_keys:
        value = row.get(key)
        if isinstance(value, list):
            key_parts.append(_sort_key_for_value(value))
        else:
            key_parts.append(str(value))
    return tuple(key_parts)


def _canonicalize_value(value: Any, path: tuple[str, ...]) -> Any:
    if isinstance(value, dict):
        return {key: _canonicalize_value(child, path + (key,)) for key, child in value.items()}
    if isinstance(value, list):
        canonical_list = [_canonicalize_value(child, path + ("*",)) for child in value]
        sort_keys = _object_sort_keys_for_path(path)
        if sort_keys is not None and all(isinstance(row, dict) for row in canonical_list):
            return sorted(canonical_list, key=lambda row: _row_sort_key(row, sort_keys))
        if _is_set_like_path(path):
            return sorted(canonical_list, key=_sort_key_for_value)
        return canonical_list
    return value


def _sorted_registry_rows(rows: list[Any], id_field: str) -> list[Any]:
    return sorted(rows, key=lambda row: str(row.get(id_field, "")) if isinstance(row, dict) else "")


def _canonicalize_for_hash(bundle: dict[str, Any]) -> dict[str, Any]:
    canonical = dict(bundle)
    canonical.pop("release_hash", None)
    for registry in BUNDLE_REGISTRY_FIELDS:
        id_field = _REGISTRY_ID_FIELDS.get(registry)
        rows = canonical.get(registry)
        if id_field is None or not isinstance(rows, list):
            continue
        canonical[registry] = [_canonicalize_value(row, (registry, "*")) for row in _sorted_registry_rows(rows, id_field)]
    for key, value in list(canonical.items()):
        if key not in BUNDLE_REGISTRY_FIELDS:
            canonical[key] = _canonicalize_value(value, (key,))
    return canonical


def canonical_content_ir_json(bundle: dict[str, Any]) -> str:
    canonical = _canonicalize_for_hash(bundle)
    return json.dumps(canonical, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def compute_content_ir_release_hash(bundle: dict[str, Any]) -> str:
    return _sha256(_canonicalize_for_hash(bundle))


def fingerprint_observation_schema_semantics(schema: dict[str, Any]) -> str:
    payload = {
        "features": sorted(
            [
                {
                    "feature_id": feature.get("feature_id"),
                    "value_type": feature.get("value_type"),
                    "required": feature.get("required"),
                    "allowed_values": sorted(feature.get("allowed_values", []), key=_sort_key_for_value)
                    if isinstance(feature.get("allowed_values"), list)
                    else feature.get("allowed_values"),
                }
                for feature in schema.get("features", [])
                if isinstance(feature, dict)
            ],
            key=lambda feature: str(feature.get("feature_id", "")),
        ),
        "outcome_surface_feature_ids": sorted(
            [str(v) for v in schema.get("outcome_surface_feature_ids", [])] if isinstance(schema.get("outcome_surface_feature_ids"), list) else []
        ),
        "auxiliary_feature_ids": sorted(
            [str(v) for v in schema.get("auxiliary_feature_ids", [])] if isinstance(schema.get("auxiliary_feature_ids"), list) else []
        ),
    }
    return _sha256(payload)


def fingerprint_response_canonicalization(schema: dict[str, Any]) -> str:
    payload = {
        "response_kind": schema.get("response_kind"),
        "canonicalization_steps": schema.get("canonicalization_steps"),
    }
    return _sha256(payload)


def fingerprint_response_parse_ir(schema: dict[str, Any]) -> str:
    payload = {
        "parse_ir": schema.get("parse_ir"),
    }
    return _sha256(payload)


def fingerprint_rubric_semantics(rubric: dict[str, Any]) -> str:
    scoring_rules = rubric.get("scoring_rules", [])
    if isinstance(scoring_rules, list):
        scoring_rules = sorted(
            [row for row in scoring_rules if isinstance(row, dict)],
            key=lambda row: str(row.get("rule_id", "")),
        )
    emission = rubric.get("observation_emission", {})
    if isinstance(emission, dict):
        emission = dict(emission)
        fields = emission.get("fields", [])
        if isinstance(fields, list):
            emission["fields"] = sorted(
                [row for row in fields if isinstance(row, dict)],
                key=lambda row: str(row.get("feature_id", "")),
            )
    payload = {
        "deterministic": rubric.get("deterministic"),
        "grader_kind": rubric.get("grader_kind"),
        "observation_schema_ref": rubric.get("observation_schema_ref"),
        "scoring_rules": scoring_rules,
        "observation_emission": emission,
    }
    return _sha256(payload)
