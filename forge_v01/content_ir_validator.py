"""Compile-time validation for v0.2 content IR bundles."""

from __future__ import annotations

import re
from typing import Any

from .content_ir_constants import (
    ASSISTANCE_MODES,
    ASSISTANCE_CONTRACT_ALLOWED_FIELDS,
    ASSISTANCE_CONTRACT_REQUIRED_FIELDS,
    BUNDLE_REGISTRY_FIELDS,
    CALIBRATION_AXIS_ALLOWED_FIELDS,
    CALIBRATION_AXIS_REQUIRED_FIELDS,
    CALIBRATION_CONTRACT_ALLOWED_FIELDS,
    CALIBRATION_POOL_POLICY_ALLOWED_FIELDS,
    CALIBRATION_POOL_POLICY_REQUIRED_FIELDS,
    CALIBRATION_CONTRACT_REQUIRED_FIELDS,
    CALIBRATION_DERIVATION_SOURCES,
    CALIBRATION_INCLUSION_ALLOWED_FIELDS,
    CALIBRATION_INCLUSION_REQUIRED_FIELDS,
    CALIBRATION_TARGET_ALLOWED_FIELDS,
    CALIBRATION_TARGET_REQUIRED_FIELDS,
    CALIBRATION_TARGET_RULE_ALLOWED_FIELDS,
    CALIBRATION_TARGET_RULE_REQUIRED_FIELDS,
    CANONICALIZATION_OPS,
    CANONICALIZATION_STEP_ALLOWED_FIELDS,
    CANONICALIZATION_STEP_REQUIRED_FIELDS,
    CHANGE_ENTRY_ENTITY_TYPES,
    CHANGE_ENTRY_TYPES,
    CHANGE_MANIFEST_ALLOWED_FIELDS,
    CHANGE_MANIFEST_ENTRY_ALLOWED_FIELDS,
    CHANGE_MANIFEST_ENTRY_REQUIRED_FIELDS,
    CHANGE_MANIFEST_REQUIRED_FIELDS,
    CHANNEL_CONSTRAINT_ALLOWED_FIELDS,
    CHANNEL_CONSTRAINT_REQUIRED_FIELDS,
    CHANNEL_DEFAULT_FEEDBACK_ALLOWED_FIELDS,
    CHANNEL_DEFAULT_FEEDBACK_REQUIRED_FIELDS,
    CHANNEL_DEFINING_TAGS,
    CHANNEL_TAGS,
    CHANNEL_TAG_TO_EVIDENCE_CHANNEL,
    COMMITMENT_ALLOWED_FIELDS,
    COMMITMENT_REQUIRED_FIELDS,
    COMMITMENT_STATUS,
    CONSUMPTION_POLICIES,
    CONTENT_IR_SCHEMA_VERSIONS,
    CONTENT_MIGRATION_ALLOWED_FIELDS,
    CONTENT_MIGRATION_REQUIRED_FIELDS,
    DELIVERY_ARTIFACT_ALLOWED_FIELDS,
    DELIVERY_ARTIFACT_KINDS,
    DELIVERY_ARTIFACT_REQUIRED_FIELDS,
    DELIVERY_TAG_VOCAB_ALLOWED_FIELDS,
    DELIVERY_TAG_VOCAB_REQUIRED_FIELDS,
    FIXTURE_BINDING_ALLOWED_FIELDS,
    FIXTURE_BINDING_KINDS,
    FIXTURE_BINDING_REQUIRED_FIELDS,
    EDGE_ALLOWED_FIELDS,
    EDGE_KINDS,
    EDGE_REQUIRED_FIELDS,
    EVIDENCE_CHANNELS,
    FACTOR_ALLOWED_FIELDS,
    FACTOR_APPLIES_TO_ALLOWED_FIELDS,
    FACTOR_KINDS,
    FACTOR_REQUIRED_FIELDS,
    FACTOR_STATUS,
    FAMILY_KINDS,
    FEATURE_VALUE_TYPES,
    FEEDBACK_POLICY_ALLOWED_FIELDS,
    FEEDBACK_POLICY_PRECEDENCE_ALLOWED_FIELDS,
    FEEDBACK_POLICY_PRECEDENCE_ORDER,
    FEEDBACK_POLICY_PRECEDENCE_REQUIRED_FIELDS,
    FEEDBACK_POLICY_REQUIRED_FIELDS,
    FEEDBACK_MODES,
    FORM_DELIVERY_ROLES,
    FORM_ALLOWED_FIELDS,
    FORM_REQUIRED_FIELDS,
    GENERATOR_ALLOWED_FIELDS,
    ADVERSARIAL_GENERATOR_CONTRACT_ALLOWED_FIELDS,
    ADVERSARIAL_GENERATOR_CONTRACT_REQUIRED_FIELDS,
    GENERATOR_DETERMINISM_ALLOWED_FIELDS,
    GENERATOR_DETERMINISM_MODES,
    GENERATOR_DETERMINISM_REQUIRED_FIELDS,
    GENERATOR_GRADING_CONTRACT_ALLOWED_FIELDS,
    GENERATOR_GRADING_CONTRACT_REQUIRED_FIELDS,
    GENERATOR_INSTANCE_BINDING_ALLOWED_FIELDS,
    GENERATOR_INSTANCE_BINDING_REQUIRED_FIELDS,
    GENERATOR_PERTURBATION_AXIS_ALLOWED_FIELDS,
    GENERATOR_PERTURBATION_AXIS_REQUIRED_FIELDS,
    GENERATOR_SOLUTION_DERIVATION_SOURCES,
    GENERATOR_SOLUTION_MATERIAL_ALLOWED_FIELDS,
    GENERATOR_SOLUTION_MATERIAL_REQUIRED_FIELDS,
    GENERATOR_REQUIRED_FIELDS,
    ITEM_ALLOWED_FIELDS,
    ITEM_REQUIRED_FIELDS,
    ITEM_PARAMS_ALLOWED_FIELDS,
    ITEM_PARAMS_REQUIRED_FIELDS,
    ITEM_GRADING_MATERIAL_ALLOWED_FIELDS,
    ITEM_GRADING_MATERIAL_REQUIRED_FIELDS,
    ITEM_SIGNATURE_ALLOWED_FIELDS,
    ITEM_SIGNATURE_REQUIRED_FIELDS,
    ITEM_SOURCE_ALLOWED_FIELDS,
    ITEM_SOURCE_KINDS,
    ITEM_SOURCE_REQUIRED_FIELDS,
    INVARIANCE_AXIS_ALLOWED_FIELDS,
    INVARIANCE_AXIS_REQUIRED_FIELDS,
    INVARIANCE_COMPARATORS,
    INVARIANCE_CONTRACT_ALLOWED_FIELDS,
    INVARIANCE_CONTRACT_REQUIRED_FIELDS,
    INVARIANCE_OPERATIONAL_ALLOWED_FIELDS,
    INVARIANCE_OPERATIONAL_REQUIRED_FIELDS,
    INVARIANCE_EXPECTATIONS,
    OBSERVATION_FEATURE_ALLOWED_FIELDS,
    OBSERVATION_FEATURE_REQUIRED_FIELDS,
    OBSERVATION_EMISSION_ALLOWED_FIELDS,
    OBSERVATION_EMISSION_FIELD_ALLOWED_FIELDS,
    OBSERVATION_EMISSION_FIELD_REQUIRED_FIELDS,
    OBSERVATION_EMISSION_REQUIRED_FIELDS,
    OBSERVATION_EMISSION_SOURCES,
    OBSERVATION_SCHEMA_ALLOWED_FIELDS,
    OBSERVATION_SCHEMA_REQUIRED_FIELDS,
    MEASUREMENT_SURFACE_ALLOWED_FIELDS,
    MEASUREMENT_SURFACE_COMPATIBILITY,
    MEASUREMENT_SURFACE_OBS_BINDING_ALLOWED_FIELDS,
    MEASUREMENT_SURFACE_OBS_BINDING_REQUIRED_FIELDS,
    MEASUREMENT_SURFACE_REQUIRED_FIELDS,
    MIGRATION_ENTRY_MODES,
    MIGRATION_MAPPING_ALLOWED_FIELDS,
    MIGRATION_MAPPING_REQUIRED_FIELDS,
    PARSE_IR_ALLOWED_FIELDS,
    PARSE_IR_KINDS,
    PARSE_IR_REQUIRED_FIELDS,
    PROBE_FAMILY_ALLOWED_FIELDS,
    PROBE_FAMILY_REQUIRED_FIELDS,
    PROJECTION_TYPES,
    RESIDUAL_FLAGS,
    RESPONSE_KINDS,
    RESPONSE_AUTHORING_STATUS,
    RESPONSE_SCHEMA_ALLOWED_FIELDS,
    RESPONSE_SCHEMA_REQUIRED_FIELDS,
    RUBRIC_ALLOWED_FIELDS,
    RUBRIC_GRADER_KINDS,
    RUBRIC_REQUIRED_FIELDS,
    SCORING_RULE_ALLOWED_FIELDS,
    SCORING_RULE_KINDS,
    SCORING_RULE_REQUIRED_FIELDS,
    SCORING_RULE_SOURCES,
    STATE_TRANSFORM_POLICY_ALLOWED_FIELDS,
    STATE_TRANSFORM_POLICY_REQUIRED_FIELDS,
    STATE_TRANSFORM_READINESS_MODES,
    STATE_TRANSFORM_UNCERTAINTY_MODES,
    TARGET_FACTOR_BINDING_ALLOWED_FIELDS,
    TARGET_FACTOR_BINDING_REQUIRED_FIELDS,
    ROLE_TAGS,
    TAG_VOCAB_ALLOWED_FIELDS,
    TAG_VOCAB_REQUIRED_FIELDS,
    TOP_LEVEL_ALLOWED_FIELDS,
    TOP_LEVEL_REQUIRED_FIELDS,
)
from .content_ir_hashing import compute_content_ir_release_hash
from .content_ir_hashing import (
    fingerprint_observation_schema_semantics,
    fingerprint_response_canonicalization,
    fingerprint_response_parse_ir,
    fingerprint_rubric_semantics,
)


_SHA256_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
_DERIVATION_PATH_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*(\.[A-Za-z_][A-Za-z0-9_]*)+$")
_IR_TAG_PATH_RE = re.compile(r"^(item|family|commitment)\.tags\.([A-Za-z_][A-Za-z0-9_]*)$")

_FAMILY_KIND_CHANNEL_RULES: dict[str, set[str]] = {
    "measurement": {"A_anchor", "B_measurement", "D_shadow"},
    "teaching": {"C_learning"},
    "holdout": {"A_anchor", "B_measurement", "D_shadow"},
    "anchor": {"A_anchor"},
    "shadow": {"D_shadow"},
    "adversarial": {"D_shadow"},
}

_STRICT_CHANNEL_RULES: dict[str, dict[str, Any]] = {
    "A_anchor": {"feedback_mode": "none", "hints_allowed": False, "max_hints": 0},
    "D_shadow": {"feedback_mode": "none", "hints_allowed": False, "max_hints": 0},
}


def validate_content_ir_bundle(bundle: dict[str, Any]) -> list[str]:
    """Return validation errors for a content IR bundle."""
    errors: list[str] = []
    if not isinstance(bundle, dict):
        return ["bundle_not_object"]

    _validate_object_shape(bundle, TOP_LEVEL_REQUIRED_FIELDS, TOP_LEVEL_ALLOWED_FIELDS, "bundle", errors)
    if errors:
        return errors

    _validate_top_level_fields(bundle, errors)
    if errors:
        return errors
    tag_vocab = _validate_tag_vocab(bundle.get("tag_vocab"), errors)
    _validate_feedback_policy_precedence(bundle.get("feedback_policy_precedence"), errors)
    _validate_change_manifest(bundle.get("change_manifest"), errors)
    if errors:
        return errors

    registries: dict[str, list[dict[str, Any]]] = {}
    for field in BUNDLE_REGISTRY_FIELDS:
        value = bundle.get(field)
        if not isinstance(value, list):
            errors.append(f"bundle_{field}_not_array")
            continue
        if not all(isinstance(row, dict) for row in value):
            errors.append(f"bundle_{field}_contains_non_object")
            continue
        registries[field] = value

    if errors:
        return errors

    commitment_ids = _validate_commitments(
        registries["commitments"],
        commitment_tag_vocab=tag_vocab["commitment_tags"],
        errors=errors,
    )
    _validate_commitment_lineage(registries["commitments"], commitment_ids, errors)
    factor_ids = _validate_factors(registries["factors"], errors)
    _validate_factor_lineage(registries["factors"], factor_ids, errors)
    _validate_edges(registries["edges"], commitment_ids, errors)
    observation_schema_ids, outcome_features_by_schema = _validate_observation_schemas(
        registries["observation_schemas"], errors
    )
    observation_schema_by_id = {
        str(row.get("observation_schema_id")): row
        for row in registries["observation_schemas"]
        if _is_non_empty_string(row.get("observation_schema_id"))
    }
    response_schema_ids = _validate_response_schemas(registries["response_schemas"], errors)
    response_schema_by_id = {
        str(row.get("response_schema_id")): row
        for row in registries["response_schemas"]
        if _is_non_empty_string(row.get("response_schema_id"))
    }
    rubric_ids = _validate_rubrics(
        registries["rubrics"],
        observation_schema_ids,
        observation_schema_by_id=observation_schema_by_id,
        response_schema_by_id=response_schema_by_id,
        errors=errors,
    )
    feedback_policy_ids = _validate_feedback_policies(registries["feedback_policies"], errors)
    _validate_commitment_feedback_refs(registries["commitments"], feedback_policy_ids, errors)
    measurement_surface_ids, measurement_surfaces_by_id = _validate_measurement_surfaces(
        registries["measurement_surfaces"],
        observation_schema_ids=observation_schema_ids,
        observation_schema_by_id=observation_schema_by_id,
        response_schema_ids=response_schema_ids,
        response_schema_by_id=response_schema_by_id,
        rubric_ids=rubric_ids,
        rubric_by_id={
            str(row.get("rubric_id")): row
            for row in registries["rubrics"]
            if _is_non_empty_string(row.get("rubric_id"))
        },
        errors=errors,
    )
    _validate_channel_default_feedback_policies(
        registries["channel_default_feedback_policies"],
        feedback_policy_ids,
        errors,
    )
    probe_family_ids = _validate_probe_families(
        registries["probe_families"],
        commitment_ids,
        factor_ids,
        measurement_surfaces_by_id,
        outcome_features_by_schema,
        family_tag_vocab=tag_vocab["family_tags"],
        tag_vocab=tag_vocab,
        feedback_policy_ids=feedback_policy_ids,
        errors=errors,
    )
    probe_family_by_id = {
        str(row.get("probe_family_id")): row
        for row in registries["probe_families"]
        if _is_non_empty_string(row.get("probe_family_id"))
    }
    _validate_factor_applies_to_refs(registries["factors"], commitment_ids, probe_family_ids, errors)
    rubric_by_id = {
        str(row.get("rubric_id")): row
        for row in registries["rubrics"]
        if _is_non_empty_string(row.get("rubric_id"))
    }
    item_ids = _validate_items(
        registries["items"],
        probe_family_ids,
        factor_ids,
        response_schema_ids,
        rubric_ids,
        item_tag_vocab=tag_vocab["item_tags"],
        feedback_policy_ids=feedback_policy_ids,
        errors=errors,
    )
    _validate_item_family_contracts(
        registries["items"],
        probe_family_by_id=probe_family_by_id,
        response_schema_by_id=response_schema_by_id,
        rubric_by_id=rubric_by_id,
        measurement_surfaces_by_id=measurement_surfaces_by_id,
        errors=errors,
    )
    item_by_id = {
        str(row.get("item_id")): row
        for row in registries["items"]
        if _is_non_empty_string(row.get("item_id"))
    }
    form_ids = _validate_forms(
        registries["forms"],
        item_ids,
        item_by_id,
        probe_family_by_id,
        feedback_policy_ids,
        delivery_tag_vocab=tag_vocab["delivery_tags"]["form_tags"],
        errors=errors,
    )
    form_by_id = {
        str(row.get("form_id")): row
        for row in registries["forms"]
        if _is_non_empty_string(row.get("form_id"))
    }
    _validate_items_form_memberships(registries["items"], form_ids, errors)
    _validate_form_item_membership_reciprocity(registries["forms"], item_by_id, errors)
    generator_ids = _validate_generators(
        registries["generators"],
        probe_family_ids,
        factor_ids,
        rubric_ids,
        response_schema_ids,
        probe_family_by_id=probe_family_by_id,
        delivery_tag_vocab=tag_vocab["delivery_tags"]["generator_tags"],
        errors=errors,
    )
    generator_by_id = {
        str(row.get("generator_id")): row
        for row in registries["generators"]
        if _is_non_empty_string(row.get("generator_id"))
    }
    _validate_generator_family_contracts(
        registries["generators"],
        probe_family_by_id=probe_family_by_id,
        response_schema_by_id=response_schema_by_id,
        rubric_by_id=rubric_by_id,
        measurement_surfaces_by_id=measurement_surfaces_by_id,
        errors=errors,
    )
    _validate_probe_family_item_sources(
        registries["probe_families"],
        item_by_id=item_by_id,
        form_by_id=form_by_id,
        generator_by_id=generator_by_id,
        errors=errors,
    )
    _validate_delivery_artifacts(
        registries["delivery_artifacts"],
        measurement_surface_ids=measurement_surface_ids,
        generator_ids=generator_ids,
        rubric_ids=rubric_ids,
        delivery_tag_vocab=tag_vocab["delivery_tags"]["artifact_tags"],
        errors=errors,
    )
    _validate_item_delivery_role_exclusivity(registries["items"], form_by_id, errors)
    _validate_content_migrations(
        registries["content_migrations"],
        bundle=bundle,
        measurement_surfaces=registries["measurement_surfaces"],
        change_manifest=bundle.get("change_manifest"),
        errors=errors,
    )
    _validate_dag_acyclic(registries["edges"], errors)
    _validate_release_hash(bundle, errors)
    return errors


def _validate_tag_vocab(
    value: Any,
    errors: list[str],
) -> dict[str, dict[str, set[str]]]:
    empty = {
        "item_tags": {},
        "family_tags": {},
        "commitment_tags": {},
        "delivery_tags": {"form_tags": {}, "generator_tags": {}, "artifact_tags": {}},
    }
    if not isinstance(value, dict):
        errors.append("bundle_tag_vocab_not_object")
        return empty
    _validate_object_shape(value, TAG_VOCAB_REQUIRED_FIELDS, TAG_VOCAB_ALLOWED_FIELDS, "bundle.tag_vocab", errors)
    if errors:
        return empty
    parsed: dict[str, dict[str, set[str]] | dict[str, dict[str, set[str]]]] = {}
    for scope in ("item_tags", "family_tags", "commitment_tags"):
        raw_scope = value.get(scope)
        if not isinstance(raw_scope, dict):
            errors.append(f"bundle.tag_vocab.{scope}_not_object")
            parsed[scope] = {}
            continue
        parsed_scope: dict[str, set[str]] = {}
        for key, allowed in raw_scope.items():
            if not _is_non_empty_string(key):
                errors.append(f"bundle.tag_vocab.{scope}_key_invalid")
                continue
            if not isinstance(allowed, list) or not allowed:
                errors.append(f"bundle.tag_vocab.{scope}.{key}_allowed_values_invalid")
                continue
            allowed_values: set[str] = set()
            for row in allowed:
                if not _is_non_empty_string(row):
                    errors.append(f"bundle.tag_vocab.{scope}.{key}_allowed_values_invalid")
                    allowed_values = set()
                    break
                allowed_values.add(str(row))
            if not allowed_values:
                continue
            if len(allowed_values) != len(allowed):
                errors.append(f"bundle.tag_vocab.{scope}.{key}_allowed_values_invalid")
                continue
            parsed_scope[str(key)] = allowed_values
        parsed[scope] = parsed_scope
    delivery_scope = value.get("delivery_tags")
    if not isinstance(delivery_scope, dict):
        errors.append("bundle.tag_vocab.delivery_tags_not_object")
        parsed["delivery_tags"] = {"form_tags": {}, "generator_tags": {}, "artifact_tags": {}}
    else:
        _validate_object_shape(
            delivery_scope,
            DELIVERY_TAG_VOCAB_REQUIRED_FIELDS,
            DELIVERY_TAG_VOCAB_ALLOWED_FIELDS,
            "bundle.tag_vocab.delivery_tags",
            errors,
        )
        delivery_parsed: dict[str, dict[str, set[str]]] = {}
        for scope in ("form_tags", "generator_tags", "artifact_tags"):
            raw_scope = delivery_scope.get(scope)
            if not isinstance(raw_scope, dict):
                errors.append(f"bundle.tag_vocab.delivery_tags.{scope}_not_object")
                delivery_parsed[scope] = {}
                continue
            parsed_scope: dict[str, set[str]] = {}
            for key, allowed in raw_scope.items():
                if not _is_non_empty_string(key):
                    errors.append(f"bundle.tag_vocab.delivery_tags.{scope}_key_invalid")
                    continue
                if not isinstance(allowed, list) or not allowed:
                    errors.append(f"bundle.tag_vocab.delivery_tags.{scope}.{key}_allowed_values_invalid")
                    continue
                allowed_values: set[str] = set()
                for row in allowed:
                    if not _is_non_empty_string(row):
                        errors.append(f"bundle.tag_vocab.delivery_tags.{scope}.{key}_allowed_values_invalid")
                        allowed_values = set()
                        break
                    allowed_values.add(str(row))
                if not allowed_values or len(allowed_values) != len(allowed):
                    errors.append(f"bundle.tag_vocab.delivery_tags.{scope}.{key}_allowed_values_invalid")
                    continue
                parsed_scope[str(key)] = allowed_values
            delivery_parsed[scope] = parsed_scope
        metadata = delivery_scope.get("metadata")
        if metadata is not None and not isinstance(metadata, dict):
            errors.append("bundle.tag_vocab.delivery_tags_metadata_not_object")
        parsed["delivery_tags"] = delivery_parsed
    metadata = value.get("metadata")
    if metadata is not None and not isinstance(metadata, dict):
        errors.append("bundle.tag_vocab_metadata_not_object")
    return parsed  # type: ignore[return-value]


def _validate_top_level_fields(bundle: dict[str, Any], errors: list[str]) -> None:
    schema_version = bundle.get("schema_version")
    if schema_version not in CONTENT_IR_SCHEMA_VERSIONS:
        errors.append("bundle_schema_version_unsupported")
    if not _is_non_empty_string(bundle.get("release_id")):
        errors.append("bundle_release_id_invalid")
    if not _is_non_empty_string(bundle.get("content_ir_version")):
        errors.append("bundle_content_ir_version_invalid")
    release_hash = bundle.get("release_hash")
    if not _is_sha256_hash(release_hash):
        errors.append("bundle_release_hash_invalid_format")
    parent_release_hash = bundle.get("parent_release_hash")
    if parent_release_hash is not None and not _is_sha256_hash(parent_release_hash):
        errors.append("bundle_parent_release_hash_invalid_format")
    metadata = bundle.get("metadata")
    if metadata is not None and not isinstance(metadata, dict):
        errors.append("bundle_metadata_not_object")


def _validate_feedback_policy_precedence(value: Any, errors: list[str]) -> None:
    prefix = "bundle.feedback_policy_precedence"
    if not isinstance(value, dict):
        errors.append(f"{prefix}_not_object")
        return
    _validate_object_shape(
        value,
        FEEDBACK_POLICY_PRECEDENCE_REQUIRED_FIELDS,
        FEEDBACK_POLICY_PRECEDENCE_ALLOWED_FIELDS,
        prefix,
        errors,
    )
    if value.get("order") != FEEDBACK_POLICY_PRECEDENCE_ORDER:
        errors.append(f"{prefix}_order_invalid_expected:{','.join(FEEDBACK_POLICY_PRECEDENCE_ORDER)}")
    metadata = value.get("metadata")
    if metadata is not None and not isinstance(metadata, dict):
        errors.append(f"{prefix}_metadata_not_object")


def _validate_change_manifest(value: Any, errors: list[str]) -> None:
    if not isinstance(value, dict):
        errors.append("bundle_change_manifest_not_object")
        return
    _validate_object_shape(value, CHANGE_MANIFEST_REQUIRED_FIELDS, CHANGE_MANIFEST_ALLOWED_FIELDS, "bundle.change_manifest", errors)
    for field_name in ("added", "deprecated", "modified"):
        rows = value.get(field_name)
        if not isinstance(rows, list):
            errors.append(f"bundle.change_manifest_{field_name}_not_array")
            continue
        for idx, row in enumerate(rows):
            prefix = f"bundle.change_manifest.{field_name}[{idx}]"
            if not isinstance(row, dict):
                errors.append(f"{prefix}_not_object")
                continue
            _validate_object_shape(
                row,
                CHANGE_MANIFEST_ENTRY_REQUIRED_FIELDS,
                CHANGE_MANIFEST_ENTRY_ALLOWED_FIELDS,
                prefix,
                errors,
            )
            if row.get("entity_type") not in CHANGE_ENTRY_ENTITY_TYPES:
                errors.append(f"{prefix}_entity_type_invalid")
            if not _is_non_empty_string(row.get("entity_id")):
                errors.append(f"{prefix}_entity_id_invalid")
            if row.get("change_type") not in CHANGE_ENTRY_TYPES:
                errors.append(f"{prefix}_change_type_invalid")
            metadata = row.get("metadata")
            if metadata is not None and not isinstance(metadata, dict):
                errors.append(f"{prefix}_metadata_not_object")
    metadata = value.get("metadata")
    if metadata is not None and not isinstance(metadata, dict):
        errors.append("bundle.change_manifest_metadata_not_object")


def _validate_commitments(
    commitments: list[dict[str, Any]],
    *,
    commitment_tag_vocab: dict[str, set[str]],
    errors: list[str],
) -> set[str]:
    ids = _validate_unique_ids(commitments, "commitment_id", "commitments", errors)
    for idx, commitment in enumerate(commitments):
        prefix = f"commitments[{idx}]"
        _validate_object_shape(commitment, COMMITMENT_REQUIRED_FIELDS, COMMITMENT_ALLOWED_FIELDS, prefix, errors)
        if not _is_non_empty_string(commitment.get("commitment_id")):
            errors.append(f"{prefix}_commitment_id_invalid")
        if not _is_non_empty_string(commitment.get("display_name")):
            errors.append(f"{prefix}_display_name_invalid")
        if not _is_non_empty_string(commitment.get("description")):
            errors.append(f"{prefix}_description_invalid")
        if not _is_non_empty_string(commitment.get("lineage_id")):
            errors.append(f"{prefix}_lineage_id_invalid")
        if commitment.get("status") not in COMMITMENT_STATUS:
            errors.append(f"{prefix}_status_invalid")
        _validate_string_list(commitment.get("aliases"), f"{prefix}_aliases_invalid", errors, unique=True)
        _validate_string_list(commitment.get("supersedes"), f"{prefix}_supersedes_invalid", errors, unique=True)
        _validate_string_list(
            commitment.get("superseded_by"), f"{prefix}_superseded_by_invalid", errors, unique=True
        )
        _validate_entity_tags(
            commitment.get("tags"),
            allowed_vocab=commitment_tag_vocab,
            prefix=f"{prefix}.tags",
            errors=errors,
        )
        metadata = commitment.get("metadata")
        if metadata is not None and not isinstance(metadata, dict):
            errors.append(f"{prefix}_metadata_not_object")
    return ids


def _validate_commitment_lineage(
    commitments: list[dict[str, Any]],
    commitment_ids: set[str],
    errors: list[str],
) -> None:
    by_id = {
        str(row.get("commitment_id")): row
        for row in commitments
        if _is_non_empty_string(row.get("commitment_id"))
    }
    adjacency: dict[str, set[str]] = {}
    for commitment in commitments:
        commitment_id = commitment.get("commitment_id")
        if not _is_non_empty_string(commitment_id):
            continue
        commitment_id = str(commitment_id)
        supersedes = commitment.get("supersedes")
        superseded_by = commitment.get("superseded_by")
        if isinstance(supersedes, list):
            for target in supersedes:
                target_str = str(target)
                if target_str not in commitment_ids:
                    errors.append(f"commitment_lineage_supersedes_unknown:{commitment_id}:{target_str}")
                    continue
                if target_str == commitment_id:
                    errors.append(f"commitment_lineage_self_reference_supersedes:{commitment_id}")
                    continue
                adjacency.setdefault(commitment_id, set()).add(target_str)
                target_row = by_id.get(target_str)
                if isinstance(target_row, dict):
                    target_rev = target_row.get("superseded_by")
                    if not isinstance(target_rev, list) or commitment_id not in {str(v) for v in target_rev}:
                        errors.append(f"commitment_lineage_reciprocity_missing:{commitment_id}:{target_str}")
        if isinstance(superseded_by, list):
            for target in superseded_by:
                target_str = str(target)
                if target_str not in commitment_ids:
                    errors.append(f"commitment_lineage_superseded_by_unknown:{commitment_id}:{target_str}")
                    continue
                if target_str == commitment_id:
                    errors.append(f"commitment_lineage_self_reference_superseded_by:{commitment_id}")
                    continue
                target_row = by_id.get(target_str)
                if isinstance(target_row, dict):
                    target_fwd = target_row.get("supersedes")
                    if not isinstance(target_fwd, list) or commitment_id not in {str(v) for v in target_fwd}:
                        errors.append(f"commitment_lineage_reciprocity_missing:{target_str}:{commitment_id}")

    color: dict[str, int] = {}

    def visit(node: str, stack: list[str]) -> bool:
        mark = color.get(node, 0)
        if mark == 1:
            errors.append(f"commitment_lineage_cycle_detected:{'->'.join(stack + [node])}")
            return True
        if mark == 2:
            return False
        color[node] = 1
        for nxt in adjacency.get(node, set()):
            if visit(nxt, stack + [node]):
                return True
        color[node] = 2
        return False

    for node in adjacency:
        if color.get(node, 0) == 0 and visit(node, []):
            return


def _validate_factors(factors: list[dict[str, Any]], errors: list[str]) -> set[str]:
    ids = _validate_unique_ids(factors, "factor_id", "factors", errors)
    for idx, factor in enumerate(factors):
        prefix = f"factors[{idx}]"
        _validate_object_shape(factor, FACTOR_REQUIRED_FIELDS, FACTOR_ALLOWED_FIELDS, prefix, errors)
        if not _is_non_empty_string(factor.get("factor_id")):
            errors.append(f"{prefix}_factor_id_invalid")
        if factor.get("factor_kind") not in FACTOR_KINDS:
            errors.append(f"{prefix}_factor_kind_invalid")
        if not _is_non_empty_string(factor.get("lineage_id")):
            errors.append(f"{prefix}_lineage_id_invalid")
        if not _is_non_empty_string(factor.get("owner")):
            errors.append(f"{prefix}_owner_invalid")
        if factor.get("status") not in FACTOR_STATUS:
            errors.append(f"{prefix}_status_invalid")
        _validate_string_list(
            factor.get("evidence_channels_allowed"),
            f"{prefix}_evidence_channels_allowed_invalid",
            errors,
            unique=True,
            allowed_values=EVIDENCE_CHANNELS,
            non_empty=True,
        )
        _validate_string_list(factor.get("aliases"), f"{prefix}_aliases_invalid", errors, unique=True)
        _validate_string_list(factor.get("supersedes"), f"{prefix}_supersedes_invalid", errors, unique=True)
        _validate_string_list(
            factor.get("superseded_by"),
            f"{prefix}_superseded_by_invalid",
            errors,
            unique=True,
        )

        applies_to = factor.get("applies_to")
        if not isinstance(applies_to, dict):
            errors.append(f"{prefix}_applies_to_not_object")
        else:
            unknown_applies_to = set(applies_to.keys()) - FACTOR_APPLIES_TO_ALLOWED_FIELDS
            if unknown_applies_to:
                errors.append(f"{prefix}_unknown_applies_to_fields:{','.join(sorted(unknown_applies_to))}")
            for applies_key in ("commitment_ids", "probe_family_ids", "domains", "strata"):
                if applies_key in applies_to:
                    _validate_string_list(
                        applies_to.get(applies_key),
                        f"{prefix}_applies_to_{applies_key}_invalid",
                        errors,
                        unique=True,
                    )
        metadata = factor.get("metadata")
        if metadata is not None and not isinstance(metadata, dict):
            errors.append(f"{prefix}_metadata_not_object")
    return ids


def _validate_factor_lineage(
    factors: list[dict[str, Any]],
    factor_ids: set[str],
    errors: list[str],
) -> None:
    by_id = {
        str(row.get("factor_id")): row
        for row in factors
        if _is_non_empty_string(row.get("factor_id"))
    }
    adjacency: dict[str, set[str]] = {}
    for factor in factors:
        factor_id = factor.get("factor_id")
        if not _is_non_empty_string(factor_id):
            continue
        factor_id = str(factor_id)
        supersedes = factor.get("supersedes")
        superseded_by = factor.get("superseded_by")
        if isinstance(supersedes, list):
            for target in supersedes:
                target_str = str(target)
                if target_str not in factor_ids:
                    errors.append(f"factor_lineage_supersedes_unknown:{factor_id}:{target_str}")
                    continue
                if target_str == factor_id:
                    errors.append(f"factor_lineage_self_reference_supersedes:{factor_id}")
                    continue
                adjacency.setdefault(factor_id, set()).add(target_str)
                target_row = by_id.get(target_str)
                if isinstance(target_row, dict):
                    target_rev = target_row.get("superseded_by")
                    if not isinstance(target_rev, list) or factor_id not in {str(v) for v in target_rev}:
                        errors.append(f"factor_lineage_reciprocity_missing:{factor_id}:{target_str}")
        if isinstance(superseded_by, list):
            for target in superseded_by:
                target_str = str(target)
                if target_str not in factor_ids:
                    errors.append(f"factor_lineage_superseded_by_unknown:{factor_id}:{target_str}")
                    continue
                if target_str == factor_id:
                    errors.append(f"factor_lineage_self_reference_superseded_by:{factor_id}")
                    continue
                target_row = by_id.get(target_str)
                if isinstance(target_row, dict):
                    target_fwd = target_row.get("supersedes")
                    if not isinstance(target_fwd, list) or factor_id not in {str(v) for v in target_fwd}:
                        errors.append(f"factor_lineage_reciprocity_missing:{target_str}:{factor_id}")

    color: dict[str, int] = {}

    def visit(node: str, stack: list[str]) -> bool:
        mark = color.get(node, 0)
        if mark == 1:
            errors.append(f"factor_lineage_cycle_detected:{'->'.join(stack + [node])}")
            return True
        if mark == 2:
            return False
        color[node] = 1
        for nxt in adjacency.get(node, set()):
            if visit(nxt, stack + [node]):
                return True
        color[node] = 2
        return False

    for node in adjacency:
        if color.get(node, 0) == 0 and visit(node, []):
            return


def _validate_factor_applies_to_refs(
    factors: list[dict[str, Any]],
    commitment_ids: set[str],
    probe_family_ids: set[str],
    errors: list[str],
) -> None:
    for idx, factor in enumerate(factors):
        applies_to = factor.get("applies_to")
        if not isinstance(applies_to, dict):
            continue
        commitment_refs = applies_to.get("commitment_ids")
        if isinstance(commitment_refs, list):
            unknown = {str(v) for v in commitment_refs if str(v) not in commitment_ids}
            if unknown:
                errors.append(f"factors[{idx}]_applies_to_commitment_unknown:{','.join(sorted(unknown))}")
        family_refs = applies_to.get("probe_family_ids")
        if isinstance(family_refs, list):
            unknown = {str(v) for v in family_refs if str(v) not in probe_family_ids}
            if unknown:
                errors.append(f"factors[{idx}]_applies_to_probe_family_unknown:{','.join(sorted(unknown))}")


def _validate_edges(edges: list[dict[str, Any]], commitment_ids: set[str], errors: list[str]) -> set[str]:
    ids = _validate_unique_ids(edges, "edge_id", "edges", errors)
    for idx, edge in enumerate(edges):
        prefix = f"edges[{idx}]"
        _validate_object_shape(edge, EDGE_REQUIRED_FIELDS, EDGE_ALLOWED_FIELDS, prefix, errors)
        edge_id = edge.get("edge_id")
        if not _is_non_empty_string(edge_id):
            errors.append(f"{prefix}_edge_id_invalid")
        src = edge.get("src_commitment_id")
        dst = edge.get("dst_commitment_id")
        if not _is_non_empty_string(src):
            errors.append(f"{prefix}_src_commitment_id_invalid")
        elif src not in commitment_ids:
            errors.append(f"{prefix}_src_commitment_unknown")
        if not _is_non_empty_string(dst):
            errors.append(f"{prefix}_dst_commitment_id_invalid")
        elif dst not in commitment_ids:
            errors.append(f"{prefix}_dst_commitment_unknown")
        if edge.get("edge_kind") not in EDGE_KINDS:
            errors.append(f"{prefix}_edge_kind_invalid")
        strength = edge.get("strength_prior")
        if not isinstance(strength, (int, float)):
            errors.append(f"{prefix}_strength_prior_not_numeric")
        elif float(strength) < 0.0 or float(strength) > 1.0:
            errors.append(f"{prefix}_strength_prior_out_of_range")
        if not _is_non_empty_string(edge.get("rationale")):
            errors.append(f"{prefix}_rationale_invalid")
        if not _is_non_empty_string(edge.get("notes")):
            errors.append(f"{prefix}_notes_invalid")
        metadata = edge.get("metadata")
        if metadata is not None and not isinstance(metadata, dict):
            errors.append(f"{prefix}_metadata_not_object")
    return ids


def _validate_observation_schemas(
    schemas: list[dict[str, Any]],
    errors: list[str],
) -> tuple[set[str], dict[str, set[str]]]:
    ids = _validate_unique_ids(schemas, "observation_schema_id", "observation_schemas", errors)
    outcome_features_by_schema: dict[str, set[str]] = {}
    for idx, schema in enumerate(schemas):
        prefix = f"observation_schemas[{idx}]"
        _validate_object_shape(
            schema,
            OBSERVATION_SCHEMA_REQUIRED_FIELDS,
            OBSERVATION_SCHEMA_ALLOWED_FIELDS,
            prefix,
            errors,
        )
        schema_id = schema.get("observation_schema_id")
        if not _is_non_empty_string(schema_id):
            errors.append(f"{prefix}_observation_schema_id_invalid")
            schema_id = f"__invalid_schema_{idx}"
        if not _is_non_empty_string(schema.get("schema_version")):
            errors.append(f"{prefix}_schema_version_invalid")

        features = schema.get("features")
        if not isinstance(features, list) or not features:
            errors.append(f"{prefix}_features_invalid_or_empty")
            continue
        feature_ids: set[str] = set()
        for feature_idx, feature in enumerate(features):
            f_prefix = f"{prefix}.features[{feature_idx}]"
            if not isinstance(feature, dict):
                errors.append(f"{f_prefix}_not_object")
                continue
            _validate_object_shape(
                feature,
                OBSERVATION_FEATURE_REQUIRED_FIELDS,
                OBSERVATION_FEATURE_ALLOWED_FIELDS,
                f_prefix,
                errors,
            )
            feature_id = feature.get("feature_id")
            if not _is_non_empty_string(feature_id):
                errors.append(f"{f_prefix}_feature_id_invalid")
                continue
            if feature_id in feature_ids:
                errors.append(f"{prefix}_duplicate_feature_id:{feature_id}")
            feature_ids.add(feature_id)
            if feature.get("value_type") not in FEATURE_VALUE_TYPES:
                errors.append(f"{f_prefix}_value_type_invalid")
            if not isinstance(feature.get("required"), bool):
                errors.append(f"{f_prefix}_required_not_bool")
            if not isinstance(feature.get("allowed_values"), list):
                errors.append(f"{f_prefix}_allowed_values_not_array")
            metadata = feature.get("metadata")
            if metadata is not None and not isinstance(metadata, dict):
                errors.append(f"{f_prefix}_metadata_not_object")

        outcome_surface = schema.get("outcome_surface_feature_ids")
        auxiliary = schema.get("auxiliary_feature_ids")
        if not isinstance(outcome_surface, list) or not outcome_surface:
            errors.append(f"{prefix}_outcome_surface_feature_ids_invalid_or_empty")
            outcome_ids: set[str] = set()
        else:
            outcome_ids = set()
            for feature_id in outcome_surface:
                if not _is_non_empty_string(feature_id):
                    errors.append(f"{prefix}_outcome_surface_feature_id_invalid")
                    continue
                outcome_ids.add(feature_id)
            unknown = outcome_ids - feature_ids
            if unknown:
                errors.append(f"{prefix}_outcome_surface_feature_unknown:{','.join(sorted(unknown))}")
        if not isinstance(auxiliary, list):
            errors.append(f"{prefix}_auxiliary_feature_ids_not_array")
            auxiliary_ids: set[str] = set()
        else:
            auxiliary_ids = set()
            for feature_id in auxiliary:
                if not _is_non_empty_string(feature_id):
                    errors.append(f"{prefix}_auxiliary_feature_id_invalid")
                    continue
                auxiliary_ids.add(feature_id)
            unknown_aux = auxiliary_ids - feature_ids
            if unknown_aux:
                errors.append(f"{prefix}_auxiliary_feature_unknown:{','.join(sorted(unknown_aux))}")
        overlap = outcome_ids & auxiliary_ids
        if overlap:
            errors.append(f"{prefix}_outcome_aux_overlap:{','.join(sorted(overlap))}")
        outcome_features_by_schema[str(schema_id)] = outcome_ids
        metadata = schema.get("metadata")
        if metadata is not None and not isinstance(metadata, dict):
            errors.append(f"{prefix}_metadata_not_object")
    return ids, outcome_features_by_schema


def _validate_response_schemas(schemas: list[dict[str, Any]], errors: list[str]) -> set[str]:
    ids = _validate_unique_ids(schemas, "response_schema_id", "response_schemas", errors)
    for idx, schema in enumerate(schemas):
        prefix = f"response_schemas[{idx}]"
        _validate_object_shape(schema, RESPONSE_SCHEMA_REQUIRED_FIELDS, RESPONSE_SCHEMA_ALLOWED_FIELDS, prefix, errors)
        if not _is_non_empty_string(schema.get("response_schema_id")):
            errors.append(f"{prefix}_response_schema_id_invalid")
        if schema.get("response_kind") not in RESPONSE_KINDS:
            errors.append(f"{prefix}_response_kind_invalid")
        if schema.get("authoring_status") not in RESPONSE_AUTHORING_STATUS:
            errors.append(f"{prefix}_authoring_status_invalid")
        elif schema.get("authoring_status") == "active_supported" and schema.get("response_kind") not in {"slots", "mcq"}:
            errors.append(f"{prefix}_active_supported_response_kind_not_allowed_in_v0_2")
        if not isinstance(schema.get("payload_schema"), dict):
            errors.append(f"{prefix}_payload_schema_not_object")
        _validate_canonicalization_steps(schema.get("canonicalization_steps"), prefix, errors)
        _validate_parse_ir(schema.get("parse_ir"), prefix, errors)
        metadata = schema.get("metadata")
        if metadata is not None and not isinstance(metadata, dict):
            errors.append(f"{prefix}_metadata_not_object")
    return ids


def _validate_rubrics(
    rubrics: list[dict[str, Any]],
    observation_schema_ids: set[str],
    *,
    observation_schema_by_id: dict[str, dict[str, Any]],
    response_schema_by_id: dict[str, dict[str, Any]],
    errors: list[str],
) -> set[str]:
    ids = _validate_unique_ids(rubrics, "rubric_id", "rubrics", errors)
    for idx, rubric in enumerate(rubrics):
        prefix = f"rubrics[{idx}]"
        _validate_object_shape(rubric, RUBRIC_REQUIRED_FIELDS, RUBRIC_ALLOWED_FIELDS, prefix, errors)
        if not _is_non_empty_string(rubric.get("rubric_id")):
            errors.append(f"{prefix}_rubric_id_invalid")
        if not isinstance(rubric.get("deterministic"), bool):
            errors.append(f"{prefix}_deterministic_not_bool")
        if rubric.get("grader_kind") not in RUBRIC_GRADER_KINDS:
            errors.append(f"{prefix}_grader_kind_invalid")
        deterministic_flag = rubric.get("deterministic")
        grader_kind = rubric.get("grader_kind")
        if isinstance(deterministic_flag, bool):
            if grader_kind == "deterministic" and deterministic_flag is not True:
                errors.append(f"{prefix}_deterministic_flag_mismatch_grader_kind")
            if grader_kind == "llm_parser" and deterministic_flag is not False:
                errors.append(f"{prefix}_deterministic_flag_mismatch_grader_kind")
        observation_ref = rubric.get("observation_schema_ref")
        if not _is_non_empty_string(observation_ref):
            errors.append(f"{prefix}_observation_schema_ref_invalid")
        elif observation_ref not in observation_schema_ids:
            errors.append(f"{prefix}_observation_schema_ref_unknown")
        observation_schema = (
            observation_schema_by_id.get(str(observation_ref)) if _is_non_empty_string(observation_ref) else None
        )
        _validate_scoring_rules(
            rubric.get("scoring_rules"),
            prefix,
            response_schema_by_id=response_schema_by_id,
            errors=errors,
        )
        _validate_observation_emission(
            rubric.get("observation_emission"),
            prefix,
            observation_schema=observation_schema,
            errors=errors,
        )
        if not _is_non_empty_string(rubric.get("rubric_semantics_version")):
            errors.append(f"{prefix}_rubric_semantics_version_invalid")
        elif rubric.get("rubric_semantics_version") != fingerprint_rubric_semantics(rubric):
            errors.append(f"{prefix}_rubric_semantics_version_mismatch_recomputed")
        metadata = rubric.get("metadata")
        if metadata is not None and not isinstance(metadata, dict):
            errors.append(f"{prefix}_metadata_not_object")
    return ids


def _validate_measurement_surfaces(
    surfaces: list[dict[str, Any]],
    *,
    observation_schema_ids: set[str],
    observation_schema_by_id: dict[str, dict[str, Any]],
    response_schema_ids: set[str],
    response_schema_by_id: dict[str, dict[str, Any]],
    rubric_ids: set[str],
    rubric_by_id: dict[str, dict[str, Any]],
    errors: list[str],
) -> tuple[set[str], dict[str, dict[str, Any]]]:
    ids = _validate_unique_ids(surfaces, "measurement_surface_id", "measurement_surfaces", errors)
    by_id: dict[str, dict[str, Any]] = {}
    semantic_ids_by_tuple: dict[tuple[str, ...], str] = {}
    for idx, surface in enumerate(surfaces):
        prefix = f"measurement_surfaces[{idx}]"
        _validate_object_shape(
            surface,
            MEASUREMENT_SURFACE_REQUIRED_FIELDS,
            MEASUREMENT_SURFACE_ALLOWED_FIELDS,
            prefix,
            errors,
        )
        surface_id = surface.get("measurement_surface_id")
        if not _is_non_empty_string(surface_id):
            errors.append(f"{prefix}_measurement_surface_id_invalid")
        else:
            by_id[str(surface_id)] = surface
        observation_ref = surface.get("observation_schema_ref")
        if not _is_non_empty_string(observation_ref):
            errors.append(f"{prefix}_observation_schema_ref_invalid")
        elif observation_ref not in observation_schema_ids:
            errors.append(f"{prefix}_observation_schema_ref_unknown")
        response_ref = surface.get("response_schema_ref")
        if not _is_non_empty_string(response_ref):
            errors.append(f"{prefix}_response_schema_ref_invalid")
        elif response_ref not in response_schema_ids:
            errors.append(f"{prefix}_response_schema_ref_unknown")
        rubric_ref = surface.get("rubric_ref")
        if not _is_non_empty_string(rubric_ref):
            errors.append(f"{prefix}_rubric_ref_invalid")
        elif rubric_ref not in rubric_ids:
            errors.append(f"{prefix}_rubric_ref_unknown")
        for field_name in (
            "observation_schema_semantics_hash",
            "canonicalization_hash",
            "parse_ir_hash",
            "rubric_semantics_hash",
        ):
            if not _is_non_empty_string(surface.get(field_name)):
                errors.append(f"{prefix}_{field_name}_invalid")
        if surface.get("compatibility_class") not in MEASUREMENT_SURFACE_COMPATIBILITY:
            errors.append(f"{prefix}_compatibility_class_invalid")
        obs_binding = surface.get("obs_binding")
        o_prefix = f"{prefix}.obs_binding"
        if not isinstance(obs_binding, dict):
            errors.append(f"{o_prefix}_not_object")
        else:
            _validate_object_shape(
                obs_binding,
                MEASUREMENT_SURFACE_OBS_BINDING_REQUIRED_FIELDS,
                MEASUREMENT_SURFACE_OBS_BINDING_ALLOWED_FIELDS,
                o_prefix,
                errors,
            )
            if not _is_non_empty_string(obs_binding.get("obs_encoder_version")):
                errors.append(f"{o_prefix}_obs_encoder_version_invalid")
            if not _is_non_empty_string(obs_binding.get("hypothesis_space_hash")):
                errors.append(f"{o_prefix}_hypothesis_space_hash_invalid")
            metadata = obs_binding.get("metadata")
            if metadata is not None and not isinstance(metadata, dict):
                errors.append(f"{o_prefix}_metadata_not_object")
        metadata = surface.get("metadata")
        if metadata is not None and not isinstance(metadata, dict):
            errors.append(f"{prefix}_metadata_not_object")
        semantic_tuple = (
            str(surface.get("observation_schema_ref")),
            str(surface.get("response_schema_ref")),
            str(surface.get("rubric_ref")),
            str(surface.get("observation_schema_semantics_hash")),
            str(surface.get("canonicalization_hash")),
            str(surface.get("parse_ir_hash")),
            str(surface.get("rubric_semantics_hash")),
            str(obs_binding.get("obs_encoder_version")) if isinstance(obs_binding, dict) else "",
            str(obs_binding.get("hypothesis_space_hash")) if isinstance(obs_binding, dict) else "",
        )
        if _is_non_empty_string(surface_id):
            prior_surface = semantic_ids_by_tuple.get(semantic_tuple)
            if prior_surface is None:
                semantic_ids_by_tuple[semantic_tuple] = str(surface_id)
            elif prior_surface != str(surface_id):
                errors.append(f"{prefix}_semantic_duplicate_of_existing_surface:{prior_surface}")
        if (
            _is_non_empty_string(observation_ref)
            and observation_ref in observation_schema_by_id
            and surface.get("observation_schema_semantics_hash")
            != fingerprint_observation_schema_semantics(observation_schema_by_id[str(observation_ref)])
        ):
            errors.append(f"{prefix}_observation_schema_semantics_hash_mismatch_recomputed")
        if (
            _is_non_empty_string(response_ref)
            and response_ref in response_schema_by_id
            and surface.get("canonicalization_hash")
            != fingerprint_response_canonicalization(response_schema_by_id[str(response_ref)])
        ):
            errors.append(f"{prefix}_canonicalization_hash_mismatch_recomputed")
        if (
            _is_non_empty_string(response_ref)
            and response_ref in response_schema_by_id
            and surface.get("parse_ir_hash") != fingerprint_response_parse_ir(response_schema_by_id[str(response_ref)])
        ):
            errors.append(f"{prefix}_parse_ir_hash_mismatch_recomputed")
        if (
            _is_non_empty_string(rubric_ref)
            and rubric_ref in rubric_by_id
            and surface.get("rubric_semantics_hash") != fingerprint_rubric_semantics(rubric_by_id[str(rubric_ref)])
        ):
            errors.append(f"{prefix}_rubric_semantics_hash_mismatch_recomputed")
        if (
            _is_non_empty_string(rubric_ref)
            and rubric_ref in rubric_by_id
            and _is_non_empty_string(observation_ref)
            and rubric_by_id[str(rubric_ref)].get("observation_schema_ref") != observation_ref
        ):
            errors.append(f"{prefix}_rubric_observation_schema_ref_mismatch")
        if (
            _is_non_empty_string(rubric_ref)
            and rubric_ref in rubric_by_id
            and _is_non_empty_string(response_ref)
            and not _rubric_is_compatible_with_response_schema(
                rubric_by_id[str(rubric_ref)],
                response_schema_by_id.get(str(response_ref)),
            )
        ):
            errors.append(f"{prefix}_rubric_response_schema_contract_mismatch")
        if (
            _is_non_empty_string(observation_ref)
            and observation_ref in observation_schema_by_id
            and _is_non_empty_string(response_ref)
            and response_ref in response_schema_by_id
            and _is_non_empty_string(rubric_ref)
            and rubric_ref in rubric_by_id
        ):
            _validate_measurement_surface_closed_contract(
                surface=surface,
                observation_schema=observation_schema_by_id[str(observation_ref)],
                response_schema=response_schema_by_id[str(response_ref)],
                rubric=rubric_by_id[str(rubric_ref)],
                prefix=prefix,
                errors=errors,
            )
    return ids, by_id


def _validate_feedback_policies(policies: list[dict[str, Any]], errors: list[str]) -> set[str]:
    ids = _validate_unique_ids(policies, "feedback_policy_id", "feedback_policies", errors)
    for idx, policy in enumerate(policies):
        prefix = f"feedback_policies[{idx}]"
        _validate_object_shape(
            policy,
            FEEDBACK_POLICY_REQUIRED_FIELDS,
            FEEDBACK_POLICY_ALLOWED_FIELDS,
            prefix,
            errors,
        )
        if not _is_non_empty_string(policy.get("feedback_policy_id")):
            errors.append(f"{prefix}_feedback_policy_id_invalid")
        if not isinstance(policy.get("rules"), dict):
            errors.append(f"{prefix}_rules_not_object")
        if not isinstance(policy.get("active"), bool):
            errors.append(f"{prefix}_active_not_bool")
        metadata = policy.get("metadata")
        if metadata is not None and not isinstance(metadata, dict):
            errors.append(f"{prefix}_metadata_not_object")
    return ids


def _validate_channel_default_feedback_policies(
    rows: list[dict[str, Any]],
    feedback_policy_ids: set[str],
    errors: list[str],
) -> None:
    seen_channels: set[str] = set()
    for idx, row in enumerate(rows):
        prefix = f"channel_default_feedback_policies[{idx}]"
        _validate_object_shape(
            row,
            CHANNEL_DEFAULT_FEEDBACK_REQUIRED_FIELDS,
            CHANNEL_DEFAULT_FEEDBACK_ALLOWED_FIELDS,
            prefix,
            errors,
        )
        channel = row.get("channel")
        if channel not in EVIDENCE_CHANNELS:
            errors.append(f"{prefix}_channel_invalid")
        else:
            channel_str = str(channel)
            if channel_str in seen_channels:
                errors.append(f"channel_default_feedback_policies_duplicate_channel:{channel_str}")
            seen_channels.add(channel_str)
        ref = row.get("feedback_policy_ref")
        if not _is_non_empty_string(ref):
            errors.append(f"{prefix}_feedback_policy_ref_invalid")
        elif ref not in feedback_policy_ids:
            errors.append(f"{prefix}_feedback_policy_ref_unknown")
        metadata = row.get("metadata")
        if metadata is not None and not isinstance(metadata, dict):
            errors.append(f"{prefix}_metadata_not_object")


def _validate_commitment_feedback_refs(
    commitments: list[dict[str, Any]],
    feedback_policy_ids: set[str],
    errors: list[str],
) -> None:
    for idx, commitment in enumerate(commitments):
        ref = commitment.get("default_feedback_policy_ref")
        if ref is None or ref == "":
            continue
        prefix = f"commitments[{idx}]"
        if not _is_non_empty_string(ref):
            errors.append(f"{prefix}_default_feedback_policy_ref_invalid")
        elif ref not in feedback_policy_ids:
            errors.append(f"{prefix}_default_feedback_policy_ref_unknown")


def _validate_probe_families(
    families: list[dict[str, Any]],
    commitment_ids: set[str],
    factor_ids: set[str],
    measurement_surfaces_by_id: dict[str, dict[str, Any]],
    outcome_features_by_schema: dict[str, set[str]],
    *,
    family_tag_vocab: dict[str, set[str]],
    tag_vocab: dict[str, dict[str, set[str]]],
    feedback_policy_ids: set[str],
    errors: list[str],
) -> set[str]:
    ids = _validate_unique_ids(families, "probe_family_id", "probe_families", errors)
    for idx, family in enumerate(families):
        prefix = f"probe_families[{idx}]"
        _validate_object_shape(family, PROBE_FAMILY_REQUIRED_FIELDS, PROBE_FAMILY_ALLOWED_FIELDS, prefix, errors)
        if not _is_non_empty_string(family.get("probe_family_id")):
            errors.append(f"{prefix}_probe_family_id_invalid")
        commitment_ref = family.get("commitment_id")
        if not _is_non_empty_string(commitment_ref):
            errors.append(f"{prefix}_commitment_id_invalid")
        elif commitment_ref not in commitment_ids:
            errors.append(f"{prefix}_commitment_id_unknown")
        family_kind = family.get("family_kind")
        if family_kind not in FAMILY_KINDS:
            errors.append(f"{prefix}_family_kind_invalid")

        _validate_string_list(
            family.get("target_factors"),
            f"{prefix}_target_factors_invalid",
            errors,
            unique=True,
        )
        target_factors = family.get("target_factors")
        if isinstance(target_factors, list):
            unknown_factors = {str(row) for row in target_factors if str(row) not in factor_ids}
            if unknown_factors:
                errors.append(f"{prefix}_target_factor_unknown:{','.join(sorted(unknown_factors))}")

        _validate_string_list(
            family.get("measurement_surface_refs"),
            f"{prefix}_measurement_surface_refs_invalid",
            errors,
            unique=True,
            non_empty=True,
        )
        surface_refs = family.get("measurement_surface_refs")
        outcome_features: set[str] = set()
        if isinstance(surface_refs, list):
            unknown_surfaces = {str(row) for row in surface_refs if str(row) not in measurement_surfaces_by_id}
            if unknown_surfaces:
                errors.append(f"{prefix}_measurement_surface_ref_unknown:{','.join(sorted(unknown_surfaces))}")
            if surface_refs and not unknown_surfaces:
                surface_observation_refs: set[str] = set()
                for surface_id in surface_refs:
                    surface_row = measurement_surfaces_by_id.get(str(surface_id))
                    if surface_row is not None:
                        obs_ref = surface_row.get("observation_schema_ref")
                        if _is_non_empty_string(obs_ref):
                            surface_observation_refs.add(str(obs_ref))
                            outcome_features |= outcome_features_by_schema.get(str(obs_ref), set())
                if len(surface_observation_refs) > 1:
                    errors.append(f"{prefix}_measurement_surfaces_observation_schema_mismatch")

        _validate_string_list(
            family.get("allowed_channels"),
            f"{prefix}_allowed_channels_invalid",
            errors,
            unique=True,
            non_empty=True,
            allowed_values=EVIDENCE_CHANNELS,
        )
        allowed_channels = (
            set(family.get("allowed_channels", []))
            if isinstance(family.get("allowed_channels"), list)
            else set()
        )
        _validate_family_kind_channel_coherence(
            family_kind=str(family_kind),
            allowed_channels=allowed_channels,
            prefix=prefix,
            errors=errors,
        )

        _validate_channel_constraints(
            family.get("channel_constraints"),
            allowed_channels=allowed_channels,
            family_kind=str(family_kind),
            prefix=prefix,
            errors=errors,
        )
        _validate_item_source(family.get("item_source"), prefix=prefix, errors=errors)
        item_source = family.get("item_source")
        if family_kind == "adversarial" and isinstance(item_source, dict):
            if item_source.get("source_kind") != "generator_bank":
                errors.append(f"{prefix}_adversarial_family_requires_generator_bank")
        _validate_assistance_contract(
            family.get("assistance_contract"),
            family_kind=str(family_kind),
            prefix=prefix,
            errors=errors,
        )
        _validate_calibration_contract(
            family.get("calibration_contract"),
            allowed_channels=allowed_channels,
            assistance_contract=family.get("assistance_contract"),
            measurement_surface_refs={str(v) for v in surface_refs} if isinstance(surface_refs, list) else set(),
            outcome_features=outcome_features,
            tag_vocab=tag_vocab,
            prefix=prefix,
            errors=errors,
        )
        if family_kind == "measurement" and not isinstance(family.get("calibration_contract"), dict):
            errors.append(f"{prefix}_measurement_family_missing_calibration_contract")

        default_feedback_policy_ref = family.get("default_feedback_policy_ref")
        if default_feedback_policy_ref is not None and default_feedback_policy_ref != "":
            if not _is_non_empty_string(default_feedback_policy_ref):
                errors.append(f"{prefix}_default_feedback_policy_ref_invalid")
            elif default_feedback_policy_ref not in feedback_policy_ids:
                errors.append(f"{prefix}_default_feedback_policy_ref_unknown")

        invariance_contract = family.get("invariance_contract")
        if family_kind == "measurement":
            if not isinstance(invariance_contract, dict):
                errors.append(f"{prefix}_measurement_family_missing_invariance_contract")
            else:
                _validate_invariance_contract(
                    invariance_contract,
                    field_prefix=f"{prefix}.invariance_contract",
                    errors=errors,
                )
        elif invariance_contract is not None:
            if not isinstance(invariance_contract, dict):
                errors.append(f"{prefix}.invariance_contract_not_object")
            else:
                _validate_invariance_contract(
                    invariance_contract,
                    field_prefix=f"{prefix}.invariance_contract",
                    errors=errors,
                )

        _validate_entity_tags(
            family.get("tags"),
            allowed_vocab=family_tag_vocab,
            prefix=f"{prefix}.tags",
            errors=errors,
        )
        metadata = family.get("metadata")
        if metadata is not None and not isinstance(metadata, dict):
            errors.append(f"{prefix}_metadata_not_object")
    return ids


def _validate_family_kind_channel_coherence(
    *,
    family_kind: str,
    allowed_channels: set[str],
    prefix: str,
    errors: list[str],
) -> None:
    expected = _FAMILY_KIND_CHANNEL_RULES.get(family_kind)
    if expected is None or not allowed_channels:
        return
    if not allowed_channels.issubset(expected):
        errors.append(
            f"{prefix}_family_kind_allowed_channels_mismatch:{family_kind}:{','.join(sorted(allowed_channels))}"
        )


def _validate_channel_constraints(
    constraints: Any,
    allowed_channels: set[str],
    family_kind: str,
    prefix: str,
    errors: list[str],
) -> None:
    if not isinstance(constraints, list) or not constraints:
        errors.append(f"{prefix}_channel_constraints_invalid_or_empty")
        return
    seen_channels: set[str] = set()
    for idx, constraint in enumerate(constraints):
        c_prefix = f"{prefix}.channel_constraints[{idx}]"
        if not isinstance(constraint, dict):
            errors.append(f"{c_prefix}_not_object")
            continue
        _validate_object_shape(
            constraint,
            CHANNEL_CONSTRAINT_REQUIRED_FIELDS,
            CHANNEL_CONSTRAINT_ALLOWED_FIELDS,
            c_prefix,
            errors,
        )
        channel = constraint.get("channel")
        if channel not in EVIDENCE_CHANNELS:
            errors.append(f"{c_prefix}_channel_invalid")
        else:
            if channel in seen_channels:
                errors.append(f"{prefix}_duplicate_channel_constraint:{channel}")
            seen_channels.add(str(channel))
            if allowed_channels and channel not in allowed_channels:
                errors.append(f"{c_prefix}_channel_not_allowed_by_family")
        if constraint.get("feedback_mode") not in FEEDBACK_MODES:
            errors.append(f"{c_prefix}_feedback_mode_invalid")
        feedback_mode = constraint.get("feedback_mode")
        if not isinstance(constraint.get("hints_allowed"), bool):
            errors.append(f"{c_prefix}_hints_allowed_not_bool")
        hints_allowed = constraint.get("hints_allowed")
        max_hints = constraint.get("max_hints")
        if not isinstance(max_hints, int) or max_hints < 0:
            errors.append(f"{c_prefix}_max_hints_invalid")
        strict_rule = _STRICT_CHANNEL_RULES.get(str(channel))
        if strict_rule is not None:
            if (
                feedback_mode != strict_rule["feedback_mode"]
                or hints_allowed is not strict_rule["hints_allowed"]
                or max_hints != strict_rule["max_hints"]
            ):
                errors.append(f"{c_prefix}_strict_measurement_constraint_violation")
        if family_kind == "adversarial" and feedback_mode == "full":
            errors.append(f"{c_prefix}_adversarial_feedback_mode_invalid")
        if family_kind == "teaching" and feedback_mode == "none":
            errors.append(f"{c_prefix}_teaching_feedback_mode_invalid")
        metadata = constraint.get("metadata")
        if metadata is not None and not isinstance(metadata, dict):
            errors.append(f"{c_prefix}_metadata_not_object")
    if allowed_channels:
        missing = sorted(allowed_channels - seen_channels)
        if missing:
            errors.append(f"{prefix}_channel_constraints_missing_for_allowed_channels:{','.join(missing)}")


def _validate_assistance_contract(
    value: Any,
    *,
    family_kind: str,
    prefix: str,
    errors: list[str],
) -> None:
    field_prefix = f"{prefix}.assistance_contract"
    if not isinstance(value, dict):
        errors.append(f"{field_prefix}_not_object")
        return
    _validate_object_shape(
        value,
        ASSISTANCE_CONTRACT_REQUIRED_FIELDS,
        ASSISTANCE_CONTRACT_ALLOWED_FIELDS,
        field_prefix,
        errors,
    )
    for field_name in (
        "allowed_assistance_modes",
        "diagnostic_eligible_assistance_modes",
        "measurement_preserving_assistance_modes",
    ):
        _validate_string_list(
            value.get(field_name),
            f"{field_prefix}_{field_name}_invalid",
            errors,
            unique=True,
            non_empty=True,
            allowed_values=ASSISTANCE_MODES,
        )
    if not isinstance(value.get("tool_use_allowed"), bool):
        errors.append(f"{field_prefix}_tool_use_allowed_not_bool")
    allowed = set(value.get("allowed_assistance_modes", [])) if isinstance(value.get("allowed_assistance_modes"), list) else set()
    diagnostic = set(value.get("diagnostic_eligible_assistance_modes", [])) if isinstance(value.get("diagnostic_eligible_assistance_modes"), list) else set()
    preserving = set(value.get("measurement_preserving_assistance_modes", [])) if isinstance(value.get("measurement_preserving_assistance_modes"), list) else set()
    if diagnostic and not diagnostic.issubset(allowed):
        errors.append(f"{field_prefix}_diagnostic_modes_not_subset_allowed")
    if preserving and not preserving.issubset(allowed):
        errors.append(f"{field_prefix}_measurement_preserving_modes_not_subset_allowed")
    if value.get("tool_use_allowed") is False and any(mode in {"tool_assisted", "mixed"} for mode in allowed):
        errors.append(f"{field_prefix}_tool_use_disallows_allowed_modes")
    if family_kind == "teaching" and "closed_book" not in allowed:
        errors.append(f"{field_prefix}_teaching_family_missing_closed_book_mode")
    metadata = value.get("metadata")
    if metadata is not None and not isinstance(metadata, dict):
        errors.append(f"{field_prefix}_metadata_not_object")


def _validate_item_source(item_source: Any, prefix: str, errors: list[str]) -> None:
    field_prefix = f"{prefix}.item_source"
    if not isinstance(item_source, dict):
        errors.append(f"{field_prefix}_not_object")
        return
    _validate_object_shape(item_source, ITEM_SOURCE_REQUIRED_FIELDS, ITEM_SOURCE_ALLOWED_FIELDS, field_prefix, errors)
    source_kind = item_source.get("source_kind")
    if source_kind not in ITEM_SOURCE_KINDS:
        errors.append(f"{field_prefix}_source_kind_invalid")
    refs = item_source.get("refs")
    _validate_string_list(refs, f"{field_prefix}_refs_invalid", errors, unique=True, non_empty=True)
    weights = item_source.get("weights")
    if weights is not None:
        if not isinstance(weights, list) or not weights:
            errors.append(f"{field_prefix}_weights_invalid")
        else:
            if not all(isinstance(row, (int, float)) and float(row) > 0.0 for row in weights):
                errors.append(f"{field_prefix}_weights_value_invalid")
            if isinstance(refs, list) and len(refs) != len(weights):
                errors.append(f"{field_prefix}_weights_length_mismatch_refs")
    metadata = item_source.get("metadata")
    if metadata is not None and not isinstance(metadata, dict):
        errors.append(f"{field_prefix}_metadata_not_object")


def _validate_invariance_contract(
    contract: Any,
    *,
    field_prefix: str,
    errors: list[str],
) -> None:
    if not isinstance(contract, dict):
        errors.append(f"{field_prefix}_not_object")
        return
    _validate_object_shape(
        contract,
        INVARIANCE_CONTRACT_REQUIRED_FIELDS,
        INVARIANCE_CONTRACT_ALLOWED_FIELDS,
        field_prefix,
        errors,
    )
    axes = contract.get("axes")
    if not isinstance(axes, list) or not axes:
        errors.append(f"{field_prefix}_axes_invalid_or_empty")
    else:
        seen_axes: set[str] = set()
        for axis_idx, axis in enumerate(axes):
            a_prefix = f"{field_prefix}.axes[{axis_idx}]"
            if not isinstance(axis, dict):
                errors.append(f"{a_prefix}_not_object")
                continue
            _validate_object_shape(
                axis,
                INVARIANCE_AXIS_REQUIRED_FIELDS,
                INVARIANCE_AXIS_ALLOWED_FIELDS,
                a_prefix,
                errors,
            )
            axis_id = axis.get("axis_id")
            if not _is_non_empty_string(axis_id):
                errors.append(f"{a_prefix}_axis_id_invalid")
            else:
                axis_id_str = str(axis_id)
                if axis_id_str in seen_axes:
                    errors.append(f"{field_prefix}_duplicate_axis_id:{axis_id_str}")
                seen_axes.add(axis_id_str)
            if axis.get("expectation") not in INVARIANCE_EXPECTATIONS:
                errors.append(f"{a_prefix}_expectation_invalid")
            if not _is_non_empty_string(axis.get("rationale")):
                errors.append(f"{a_prefix}_rationale_invalid")
            metadata = axis.get("metadata")
            if metadata is not None and not isinstance(metadata, dict):
                errors.append(f"{a_prefix}_metadata_not_object")
    operational_constraints = contract.get("operational_constraints")
    if operational_constraints is not None:
        if not isinstance(operational_constraints, list):
            errors.append(f"{field_prefix}_operational_constraints_not_array")
        else:
            seen_constraints: set[str] = set()
            for idx, constraint in enumerate(operational_constraints):
                c_prefix = f"{field_prefix}.operational_constraints[{idx}]"
                if not isinstance(constraint, dict):
                    errors.append(f"{c_prefix}_not_object")
                    continue
                _validate_object_shape(
                    constraint,
                    INVARIANCE_OPERATIONAL_REQUIRED_FIELDS,
                    INVARIANCE_OPERATIONAL_ALLOWED_FIELDS,
                    c_prefix,
                    errors,
                )
                constraint_id = constraint.get("constraint_id")
                if not _is_non_empty_string(constraint_id):
                    errors.append(f"{c_prefix}_constraint_id_invalid")
                else:
                    cid = str(constraint_id)
                    if cid in seen_constraints:
                        errors.append(f"{field_prefix}_duplicate_constraint_id:{cid}")
                    seen_constraints.add(cid)
                source_path = constraint.get("source_path")
                if not _is_non_empty_string(source_path):
                    errors.append(f"{c_prefix}_source_path_invalid")
                elif not _is_valid_invariance_source_path(str(source_path)):
                    errors.append(f"{c_prefix}_source_path_syntax_invalid")
                if constraint.get("comparator") not in INVARIANCE_COMPARATORS:
                    errors.append(f"{c_prefix}_comparator_invalid")
                if "value" not in constraint:
                    errors.append(f"{c_prefix}_value_missing")
                tolerance = constraint.get("tolerance")
                if tolerance is not None and not isinstance(tolerance, (int, float)):
                    errors.append(f"{c_prefix}_tolerance_invalid")
                metadata = constraint.get("metadata")
                if metadata is not None and not isinstance(metadata, dict):
                    errors.append(f"{c_prefix}_metadata_not_object")
    metadata = contract.get("metadata")
    if metadata is not None and not isinstance(metadata, dict):
        errors.append(f"{field_prefix}_metadata_not_object")


def _validate_calibration_contract(
    contract: Any,
    allowed_channels: set[str],
    assistance_contract: Any,
    measurement_surface_refs: set[str],
    outcome_features: set[str],
    tag_vocab: dict[str, dict[str, set[str]]],
    prefix: str,
    errors: list[str],
) -> None:
    field_prefix = f"{prefix}.calibration_contract"
    if not isinstance(contract, dict):
        errors.append(f"{field_prefix}_not_object")
        return
    _validate_object_shape(
        contract,
        CALIBRATION_CONTRACT_REQUIRED_FIELDS,
        CALIBRATION_CONTRACT_ALLOWED_FIELDS,
        field_prefix,
        errors,
    )
    inclusion = contract.get("inclusion_rules")
    if not isinstance(inclusion, dict):
        errors.append(f"{field_prefix}.inclusion_rules_not_object")
    else:
        i_prefix = f"{field_prefix}.inclusion_rules"
        _validate_object_shape(
            inclusion,
            CALIBRATION_INCLUSION_REQUIRED_FIELDS,
            CALIBRATION_INCLUSION_ALLOWED_FIELDS,
            i_prefix,
            errors,
        )
        _validate_string_list(
            inclusion.get("eligible_channels"),
            f"{i_prefix}_eligible_channels_invalid",
            errors,
            unique=True,
            non_empty=True,
            allowed_values=EVIDENCE_CHANNELS,
        )
        eligible_channels = (
            set(inclusion.get("eligible_channels", []))
            if isinstance(inclusion.get("eligible_channels"), list)
            else set()
        )
        if allowed_channels and not eligible_channels.issubset(allowed_channels):
            errors.append(f"{i_prefix}_eligible_channels_not_subset_allowed_channels")
        _validate_string_list(
            inclusion.get("eligible_assistance_modes"),
            f"{i_prefix}_eligible_assistance_modes_invalid",
            errors,
            unique=True,
            non_empty=True,
            allowed_values=ASSISTANCE_MODES,
        )
        eligible_modes = (
            {str(v) for v in inclusion.get("eligible_assistance_modes", [])}
            if isinstance(inclusion.get("eligible_assistance_modes"), list)
            else set()
        )
        assistance_allowed_modes = (
            {str(v) for v in assistance_contract.get("allowed_assistance_modes", [])}
            if isinstance(assistance_contract, dict)
            and isinstance(assistance_contract.get("allowed_assistance_modes"), list)
            else set()
        )
        if assistance_allowed_modes and not eligible_modes.issubset(assistance_allowed_modes):
            errors.append(f"{i_prefix}_eligible_assistance_modes_not_subset_assistance_contract")
        if not isinstance(inclusion.get("require_closed_book"), bool):
            errors.append(f"{i_prefix}_require_closed_book_not_bool")
        elif inclusion.get("require_closed_book") and eligible_modes != {"closed_book"}:
            errors.append(f"{i_prefix}_require_closed_book_modes_mismatch")
        _validate_string_list(
            inclusion.get("exclude_residual_flags"),
            f"{i_prefix}_exclude_residual_flags_invalid",
            errors,
            unique=True,
            allowed_values=RESIDUAL_FLAGS,
        )
        metadata = inclusion.get("metadata")
        if metadata is not None and not isinstance(metadata, dict):
            errors.append(f"{i_prefix}_metadata_not_object")

    strata_axes = contract.get("strata_axes")
    if not isinstance(strata_axes, list) or not strata_axes:
        errors.append(f"{field_prefix}.strata_axes_invalid_or_empty")
    else:
        seen_axis_ids: set[str] = set()
        for axis_idx, axis in enumerate(strata_axes):
            a_prefix = f"{field_prefix}.strata_axes[{axis_idx}]"
            if not isinstance(axis, dict):
                errors.append(f"{a_prefix}_not_object")
                continue
            _validate_object_shape(
                axis,
                CALIBRATION_AXIS_REQUIRED_FIELDS,
                CALIBRATION_AXIS_ALLOWED_FIELDS,
                a_prefix,
                errors,
            )
            axis_id = axis.get("axis_id")
            if not _is_non_empty_string(axis_id):
                errors.append(f"{a_prefix}_axis_id_invalid")
            else:
                if axis_id in seen_axis_ids:
                    errors.append(f"{field_prefix}_duplicate_axis_id:{axis_id}")
                seen_axis_ids.add(axis_id)
            if axis.get("derivation_source") not in CALIBRATION_DERIVATION_SOURCES:
                errors.append(f"{a_prefix}_derivation_source_invalid")
            derivation_path = axis.get("derivation_path")
            if not _is_non_empty_string(derivation_path):
                errors.append(f"{a_prefix}_derivation_path_invalid")
            elif not _is_valid_derivation_path(str(axis.get("derivation_source")), str(derivation_path)):
                errors.append(f"{a_prefix}_derivation_path_syntax_invalid")
            elif axis.get("derivation_source") == "ir_tags":
                parsed = _parse_ir_tag_path(str(derivation_path))
                if parsed is None:
                    errors.append(f"{a_prefix}_ir_tags_path_invalid")
                else:
                    scope, tag_key = parsed
                    scope_key = f"{scope}_tags"
                    scope_vocab = tag_vocab.get(scope_key, {})
                    if tag_key not in scope_vocab:
                        errors.append(f"{a_prefix}_ir_tags_key_not_declared:{scope}.{tag_key}")
            _validate_string_list(
                axis.get("allowed_values"),
                f"{a_prefix}_allowed_values_invalid",
                errors,
                unique=True,
                non_empty=True,
            )
            if not _is_non_empty_string(axis.get("unknown_value")):
                errors.append(f"{a_prefix}_unknown_value_invalid")
            metadata = axis.get("metadata")
            if metadata is not None and not isinstance(metadata, dict):
                errors.append(f"{a_prefix}_metadata_not_object")

    projection = contract.get("calibration_target_projection")
    if not isinstance(projection, dict):
        errors.append(f"{field_prefix}.calibration_target_projection_not_object")
        return
    p_prefix = f"{field_prefix}.calibration_target_projection"
    _validate_object_shape(
        projection,
        CALIBRATION_TARGET_REQUIRED_FIELDS,
        CALIBRATION_TARGET_ALLOWED_FIELDS,
        p_prefix,
        errors,
    )
    if not _is_non_empty_string(projection.get("projection_id")):
        errors.append(f"{p_prefix}_projection_id_invalid")
    if projection.get("projection_type") not in PROJECTION_TYPES:
        errors.append(f"{p_prefix}_projection_type_invalid")
    source_surface = projection.get("source_surface")
    if not _is_non_empty_string(source_surface):
        errors.append(f"{p_prefix}_source_surface_invalid")
    elif measurement_surface_refs and source_surface not in measurement_surface_refs:
        errors.append(f"{p_prefix}_source_surface_invalid")
    mapping_rules = projection.get("mapping_rules")
    if not isinstance(mapping_rules, list) or not mapping_rules:
        errors.append(f"{p_prefix}_mapping_rules_invalid_or_empty")
    else:
        for rule_idx, rule in enumerate(mapping_rules):
            r_prefix = f"{p_prefix}.mapping_rules[{rule_idx}]"
            if not isinstance(rule, dict):
                errors.append(f"{r_prefix}_not_object")
                continue
            _validate_object_shape(
                rule,
                CALIBRATION_TARGET_RULE_REQUIRED_FIELDS,
                CALIBRATION_TARGET_RULE_ALLOWED_FIELDS,
                r_prefix,
                errors,
            )
            if not _is_non_empty_string(rule.get("target")):
                errors.append(f"{r_prefix}_target_invalid")
            _validate_string_list(
                rule.get("source_features"),
                f"{r_prefix}_source_features_invalid",
                errors,
                unique=True,
                non_empty=True,
            )
            source_features = (
                set(rule.get("source_features"))
                if isinstance(rule.get("source_features"), list)
                else set()
            )
            unknown_source_features = {str(row) for row in source_features if str(row) not in outcome_features}
            if unknown_source_features:
                errors.append(
                    f"{r_prefix}_source_feature_not_in_outcome_surface:{','.join(sorted(unknown_source_features))}"
                )
            if "rule" in rule and rule.get("rule") is not None and not _is_non_empty_string(rule.get("rule")):
                errors.append(f"{r_prefix}_rule_invalid")
            metadata = rule.get("metadata")
            if metadata is not None and not isinstance(metadata, dict):
                errors.append(f"{r_prefix}_metadata_not_object")
    metadata = projection.get("metadata")
    if metadata is not None and not isinstance(metadata, dict):
        errors.append(f"{p_prefix}_metadata_not_object")
    pool_policy = contract.get("calibration_pool_policy")
    pool_prefix = f"{field_prefix}.calibration_pool_policy"
    if not isinstance(pool_policy, dict):
        errors.append(f"{pool_prefix}_not_object")
        return
    _validate_object_shape(
        pool_policy,
        CALIBRATION_POOL_POLICY_REQUIRED_FIELDS,
        CALIBRATION_POOL_POLICY_ALLOWED_FIELDS,
        pool_prefix,
        errors,
    )
    _validate_string_list(
        pool_policy.get("baseline_assistance_modes"),
        f"{pool_prefix}_baseline_assistance_modes_invalid",
        errors,
        unique=True,
        non_empty=True,
        allowed_values=ASSISTANCE_MODES,
    )
    _validate_string_list(
        pool_policy.get("monitor_only_assistance_modes"),
        f"{pool_prefix}_monitor_only_assistance_modes_invalid",
        errors,
        unique=True,
        allowed_values=ASSISTANCE_MODES,
    )
    if not isinstance(pool_policy.get("stratify_by_assistance_mode"), bool):
        errors.append(f"{pool_prefix}_stratify_by_assistance_mode_not_bool")
    baseline_modes = (
        {str(v) for v in pool_policy.get("baseline_assistance_modes", [])}
        if isinstance(pool_policy.get("baseline_assistance_modes"), list)
        else set()
    )
    monitor_modes = (
        {str(v) for v in pool_policy.get("monitor_only_assistance_modes", [])}
        if isinstance(pool_policy.get("monitor_only_assistance_modes"), list)
        else set()
    )
    if baseline_modes & monitor_modes:
        errors.append(f"{pool_prefix}_baseline_monitor_overlap")
    if eligible_modes and not baseline_modes.issubset(eligible_modes):
        errors.append(f"{pool_prefix}_baseline_modes_not_subset_inclusion_modes")
    if eligible_modes and not monitor_modes.issubset(eligible_modes):
        errors.append(f"{pool_prefix}_monitor_modes_not_subset_inclusion_modes")
    assistance_diagnostic_modes = (
        {str(v) for v in assistance_contract.get("diagnostic_eligible_assistance_modes", [])}
        if isinstance(assistance_contract, dict)
        and isinstance(assistance_contract.get("diagnostic_eligible_assistance_modes"), list)
        else set()
    )
    assistance_preserving_modes = (
        {str(v) for v in assistance_contract.get("measurement_preserving_assistance_modes", [])}
        if isinstance(assistance_contract, dict)
        and isinstance(assistance_contract.get("measurement_preserving_assistance_modes"), list)
        else set()
    )
    if baseline_modes and not baseline_modes.issubset(assistance_diagnostic_modes):
        errors.append(f"{pool_prefix}_baseline_modes_not_subset_diagnostic_modes")
    if baseline_modes and not baseline_modes.issubset(assistance_preserving_modes):
        errors.append(f"{pool_prefix}_baseline_modes_not_subset_measurement_preserving_modes")
    pool_metadata = pool_policy.get("metadata")
    if pool_metadata is not None and not isinstance(pool_metadata, dict):
        errors.append(f"{pool_prefix}_metadata_not_object")


def _validate_items(
    items: list[dict[str, Any]],
    probe_family_ids: set[str],
    factor_ids: set[str],
    response_schema_ids: set[str],
    rubric_ids: set[str],
    *,
    item_tag_vocab: dict[str, set[str]],
    feedback_policy_ids: set[str],
    errors: list[str],
) -> set[str]:
    ids = _validate_unique_ids(items, "item_id", "items", errors)
    for idx, item in enumerate(items):
        prefix = f"items[{idx}]"
        _validate_object_shape(item, ITEM_REQUIRED_FIELDS, ITEM_ALLOWED_FIELDS, prefix, errors)
        if not _is_non_empty_string(item.get("item_id")):
            errors.append(f"{prefix}_item_id_invalid")
        probe_family_ref = item.get("probe_family_id")
        if not _is_non_empty_string(probe_family_ref):
            errors.append(f"{prefix}_probe_family_id_invalid")
        elif probe_family_ref not in probe_family_ids:
            errors.append(f"{prefix}_probe_family_unknown")
        response_ref = item.get("response_schema_ref")
        if not _is_non_empty_string(response_ref):
            errors.append(f"{prefix}_response_schema_ref_invalid")
        elif response_ref not in response_schema_ids:
            errors.append(f"{prefix}_response_schema_unknown")
        rubric_ref = item.get("rubric_ref")
        if not _is_non_empty_string(rubric_ref):
            errors.append(f"{prefix}_rubric_ref_invalid")
        elif rubric_ref not in rubric_ids:
            errors.append(f"{prefix}_rubric_ref_unknown")
        _validate_target_factor_binding(
            item.get("target_factor_binding"),
            factor_ids=factor_ids,
            prefix=f"{prefix}.target_factor_binding",
            errors=errors,
        )
        if not _is_non_empty_string(item.get("prompt")):
            errors.append(f"{prefix}_prompt_invalid")
        _validate_string_list(
            item.get("channel_tags"),
            f"{prefix}_channel_tags_invalid",
            errors,
            unique=True,
            allowed_values=CHANNEL_TAGS,
        )
        _validate_string_list(
            item.get("role_tags"),
            f"{prefix}_role_tags_invalid",
            errors,
            unique=True,
            allowed_values=ROLE_TAGS,
        )
        _validate_string_list(item.get("form_memberships"), f"{prefix}_form_memberships_invalid", errors, unique=True)
        _validate_item_params(item.get("item_params"), prefix, errors)
        _validate_item_grading_material(item.get("grading_material"), prefix, errors)
        feedback_policy_ref = item.get("feedback_policy_ref")
        if feedback_policy_ref is not None and feedback_policy_ref != "":
            if not _is_non_empty_string(feedback_policy_ref):
                errors.append(f"{prefix}_feedback_policy_ref_invalid")
            elif feedback_policy_ref not in feedback_policy_ids:
                errors.append(f"{prefix}_feedback_policy_ref_unknown")
        dual_use_allowed = item.get("dual_use_allowed")
        if dual_use_allowed is not None and not isinstance(dual_use_allowed, bool):
            errors.append(f"{prefix}_dual_use_allowed_not_bool")
        if not isinstance(item.get("active"), bool):
            errors.append(f"{prefix}_active_not_bool")
        _validate_entity_tags(
            item.get("tags"),
            allowed_vocab=item_tag_vocab,
            prefix=f"{prefix}.tags",
            errors=errors,
        )
        metadata = item.get("metadata")
        if metadata is not None and not isinstance(metadata, dict):
            errors.append(f"{prefix}_metadata_not_object")
    return ids


def _validate_item_family_contracts(
    items: list[dict[str, Any]],
    probe_family_by_id: dict[str, dict[str, Any]],
    response_schema_by_id: dict[str, dict[str, Any]],
    rubric_by_id: dict[str, dict[str, Any]],
    measurement_surfaces_by_id: dict[str, dict[str, Any]],
    errors: list[str],
) -> None:
    for idx, item in enumerate(items):
        item_id = item.get("item_id")
        if not _is_non_empty_string(item_id):
            continue
        prefix = f"items[{idx}]"
        family_id = item.get("probe_family_id")
        if not _is_non_empty_string(family_id):
            continue
        family = probe_family_by_id.get(str(family_id))
        if family is None:
            continue
        family_target_factors = {
            str(v) for v in family.get("target_factors", []) if _is_non_empty_string(v)
        }
        target_binding = item.get("target_factor_binding")
        if isinstance(target_binding, dict) and family_target_factors:
            item_targets = {
                str(v)
                for field_name in ("primary_target_factors", "secondary_target_factors")
                for v in target_binding.get(field_name, [])
                if _is_non_empty_string(v)
            }
            invalid_targets = sorted(item_targets - family_target_factors)
            if invalid_targets:
                errors.append(f"{prefix}_target_factor_not_allowed_by_family:{','.join(invalid_targets)}")
        surface_rows: list[dict[str, Any]] = []
        surface_refs = family.get("measurement_surface_refs")
        if isinstance(surface_refs, list):
            surface_rows = [
                measurement_surfaces_by_id[str(ref)]
                for ref in surface_refs
                if isinstance(ref, str) and str(ref) in measurement_surfaces_by_id
            ]
        response_ref = item.get("response_schema_ref")
        response_schema = response_schema_by_id.get(str(response_ref)) if _is_non_empty_string(response_ref) else None
        grading_material = item.get("grading_material")
        allowed_responses = {
            str(row.get("response_schema_ref"))
            for row in surface_rows
            if _is_non_empty_string(row.get("response_schema_ref"))
        }
        if allowed_responses and _is_non_empty_string(response_ref):
            if str(response_ref) not in allowed_responses:
                errors.append(f"{prefix}_response_schema_not_allowed_by_family")
        if isinstance(response_schema, dict):
            if response_schema.get("authoring_status") != "active_supported":
                errors.append(f"{prefix}_response_schema_not_active_supported")
            if isinstance(grading_material, dict) and grading_material.get("response_kind") != response_schema.get("response_kind"):
                errors.append(f"{prefix}_grading_material_response_kind_mismatch_response_schema")

        rubric_ref = item.get("rubric_ref")
        rubric = rubric_by_id.get(str(rubric_ref)) if _is_non_empty_string(rubric_ref) else None
        measurement_surface_ref = item.get("measurement_surface_ref")
        selected_surface = (
            measurement_surfaces_by_id.get(str(measurement_surface_ref))
            if _is_non_empty_string(measurement_surface_ref)
            else None
        )
        if not _is_non_empty_string(measurement_surface_ref):
            errors.append(f"{prefix}_measurement_surface_ref_invalid")
        elif not isinstance(surface_refs, list) or str(measurement_surface_ref) not in {str(v) for v in surface_refs}:
            errors.append(f"{prefix}_measurement_surface_ref_not_declared_by_family")
        if isinstance(rubric, dict):
            if isinstance(grading_material, dict):
                _validate_item_grading_material_compatibility(
                    grading_material=grading_material,
                    rubric=rubric,
                    prefix=prefix,
                    errors=errors,
                )
            family_obs_refs = {
                str(row.get("observation_schema_ref"))
                for row in surface_rows
                if _is_non_empty_string(row.get("observation_schema_ref"))
            }
            rubric_obs = rubric.get("observation_schema_ref")
            if family_obs_refs and _is_non_empty_string(rubric_obs):
                if str(rubric_obs) not in family_obs_refs:
                    errors.append(f"{prefix}_rubric_observation_schema_mismatch_family")
            if isinstance(response_schema, dict) and _is_non_empty_string(rubric_obs):
                matching_surface_ids = _matching_measurement_surface_ids(
                    surface_rows=surface_rows,
                    response_ref=str(response_ref) if _is_non_empty_string(response_ref) else None,
                    response_schema=response_schema,
                    rubric_ref=str(rubric_ref) if _is_non_empty_string(rubric_ref) else None,
                    rubric=rubric,
                )
                if not matching_surface_ids:
                    errors.append(f"{prefix}_measurement_surface_binding_missing_or_mismatched")
                elif len(matching_surface_ids) > 1:
                    errors.append(f"{prefix}_measurement_surface_binding_ambiguous:{','.join(sorted(matching_surface_ids))}")
                elif selected_surface is None or str(selected_surface.get("measurement_surface_id")) != next(iter(matching_surface_ids)):
                    errors.append(f"{prefix}_measurement_surface_ref_mismatch_unique_binding")

        tags = item.get("channel_tags")
        if isinstance(tags, list):
            tag_set = {str(v) for v in tags}
            channel_tags = sorted(tag_set & CHANNEL_DEFINING_TAGS)
            if len(channel_tags) != 1:
                errors.append(f"{prefix}_channel_tag_count_invalid_expected_exactly_one")
            else:
                mapped_channel = CHANNEL_TAG_TO_EVIDENCE_CHANNEL[channel_tags[0]]
                allowed_channels = family.get("allowed_channels")
                if isinstance(allowed_channels, list):
                    if mapped_channel not in {str(v) for v in allowed_channels}:
                        errors.append(f"{prefix}_channel_tag_not_allowed_by_family")
                role_tags = item.get("role_tags")
                role_tag_set = {str(v) for v in role_tags} if isinstance(role_tags, list) else set()
                if "holdout" in role_tag_set and mapped_channel == "C_learning":
                    errors.append(f"{prefix}_holdout_role_channel_mismatch")
                if "adversarial" in role_tag_set and mapped_channel == "C_learning":
                    errors.append(f"{prefix}_adversarial_role_channel_mismatch")
            family_kind = family.get("family_kind")
            role_tags = item.get("role_tags")
            role_tag_set = {str(v) for v in role_tags} if isinstance(role_tags, list) else set()
            if family_kind == "adversarial" and "adversarial" not in role_tag_set:
                errors.append(f"{prefix}_adversarial_family_missing_role_tag")


def _validate_forms(
    forms: list[dict[str, Any]],
    item_ids: set[str],
    item_by_id: dict[str, dict[str, Any]],
    probe_family_by_id: dict[str, dict[str, Any]],
    feedback_policy_ids: set[str],
    *,
    delivery_tag_vocab: dict[str, set[str]],
    errors: list[str],
) -> set[str]:
    ids = _validate_unique_ids(forms, "form_id", "forms", errors)
    for idx, form in enumerate(forms):
        prefix = f"forms[{idx}]"
        _validate_object_shape(form, FORM_REQUIRED_FIELDS, FORM_ALLOWED_FIELDS, prefix, errors)
        if not _is_non_empty_string(form.get("form_id")):
            errors.append(f"{prefix}_form_id_invalid")
        _validate_string_list(form.get("items"), f"{prefix}_items_invalid", errors, unique=True, non_empty=True)
        item_refs = form.get("items")
        if isinstance(item_refs, list):
            unknown_items = {str(row) for row in item_refs if str(row) not in item_ids}
            if unknown_items:
                errors.append(f"{prefix}_item_ref_unknown:{','.join(sorted(unknown_items))}")
        evidence_channel = form.get("evidence_channel")
        if evidence_channel not in EVIDENCE_CHANNELS:
            errors.append(f"{prefix}_evidence_channel_invalid")
            evidence_channel = None
        delivery_role = form.get("delivery_role")
        if delivery_role not in FORM_DELIVERY_ROLES:
            errors.append(f"{prefix}_delivery_role_invalid")
            delivery_role = None
        if not isinstance(form.get("fixed_form"), bool):
            errors.append(f"{prefix}_fixed_form_not_bool")
        if not isinstance(form.get("closed_book_only"), bool):
            errors.append(f"{prefix}_closed_book_only_not_bool")
        max_presented_items = form.get("max_presented_items")
        if not isinstance(max_presented_items, int) or max_presented_items <= 0:
            errors.append(f"{prefix}_max_presented_items_invalid")
        if form.get("consumption_policy") not in CONSUMPTION_POLICIES:
            errors.append(f"{prefix}_consumption_policy_invalid")
        feedback_policy_ref = form.get("feedback_policy_ref")
        if feedback_policy_ref is not None and feedback_policy_ref != "":
            if not _is_non_empty_string(feedback_policy_ref):
                errors.append(f"{prefix}_feedback_policy_ref_invalid")
            elif feedback_policy_ref not in feedback_policy_ids:
                errors.append(f"{prefix}_feedback_policy_ref_unknown")
        _validate_string_list(form.get("form_tags"), f"{prefix}_form_tags_invalid", errors, unique=True)
        _validate_entity_tags(
            form.get("tags"),
            allowed_vocab=delivery_tag_vocab,
            prefix=f"{prefix}.tags",
            errors=errors,
        )
        form_tags = form.get("form_tags")
        if isinstance(form_tags, list):
            form_tag_set = {str(v) for v in form_tags}
            form_channel_tags = sorted(form_tag_set & CHANNEL_DEFINING_TAGS)
            if len(form_channel_tags) > 1:
                errors.append(f"{prefix}_form_channel_tag_count_invalid_max_one")
            elif len(form_channel_tags) == 1 and evidence_channel is not None:
                mapped_channel = CHANNEL_TAG_TO_EVIDENCE_CHANNEL[form_channel_tags[0]]
                if mapped_channel != evidence_channel:
                    errors.append(f"{prefix}_form_channel_tag_mismatch_evidence_channel")
            if "anchor" in form_tag_set and evidence_channel != "A_anchor":
                errors.append(f"{prefix}_anchor_form_channel_mismatch")
            if "shadow" in form_tag_set and evidence_channel != "D_shadow":
                errors.append(f"{prefix}_shadow_form_channel_mismatch")
            if "holdout" in form_tag_set:
                if evidence_channel == "C_learning":
                    errors.append(f"{prefix}_holdout_form_channel_mismatch")
                if form.get("consumption_policy") not in {"retire_on_use", "rotate_forms"}:
                    errors.append(f"{prefix}_holdout_consumption_policy_invalid")
            if "adversarial" in form_tag_set and evidence_channel != "D_shadow":
                errors.append(f"{prefix}_adversarial_form_channel_mismatch")
            _validate_form_delivery_role_coherence(
                form_tag_set=form_tag_set,
                evidence_channel=evidence_channel,
                delivery_role=str(delivery_role) if delivery_role is not None else None,
                fixed_form=form.get("fixed_form"),
                closed_book_only=form.get("closed_book_only"),
                max_presented_items=max_presented_items,
                consumption_policy=form.get("consumption_policy"),
                prefix=prefix,
                errors=errors,
            )

        if evidence_channel is not None and isinstance(item_refs, list):
            for ref in item_refs:
                item_id = str(ref)
                item = item_by_id.get(item_id)
                if item is None:
                    continue
                item_tags = item.get("channel_tags")
                if not isinstance(item_tags, list):
                    errors.append(f"{prefix}_item_channel_underdetermined:{item_id}")
                    continue
                item_channel_tags = sorted({str(v) for v in item_tags} & CHANNEL_DEFINING_TAGS)
                if len(item_channel_tags) != 1:
                    errors.append(f"{prefix}_item_channel_underdetermined:{item_id}")
                    continue
                mapped_item_channel = CHANNEL_TAG_TO_EVIDENCE_CHANNEL[item_channel_tags[0]]
                if mapped_item_channel != evidence_channel:
                    errors.append(
                        f"{prefix}_item_channel_mismatch_form:{item_id}:{mapped_item_channel}:{evidence_channel}"
                    )
                family_id = item.get("probe_family_id")
                family = probe_family_by_id.get(str(family_id)) if _is_non_empty_string(family_id) else None
                if (
                    delivery_role == "anchor"
                    and form.get("closed_book_only") is True
                    and isinstance(family, dict)
                    and not _family_supports_closed_book_only_measurement(family)
                ):
                    errors.append(f"{prefix}_anchor_family_not_closed_book_measurement_preserving:{item_id}")
        if not isinstance(form.get("active"), bool):
            errors.append(f"{prefix}_active_not_bool")
        metadata = form.get("metadata")
        if metadata is not None and not isinstance(metadata, dict):
            errors.append(f"{prefix}_metadata_not_object")
    return ids


def _validate_form_delivery_role_coherence(
    *,
    form_tag_set: set[str],
    evidence_channel: Any,
    delivery_role: str | None,
    fixed_form: Any,
    closed_book_only: Any,
    max_presented_items: Any,
    consumption_policy: Any,
    prefix: str,
    errors: list[str],
) -> None:
    role_tag_set = form_tag_set & {"holdout", "anchor", "shadow", "adversarial"}
    if len(role_tag_set) > 1:
        errors.append(f"{prefix}_multiple_delivery_role_tags_forbidden")
    expected_role_by_tag = {
        "holdout": "holdout",
        "anchor": "anchor",
        "shadow": "shadow",
    }
    if delivery_role in {"holdout", "anchor", "shadow"}:
        expected_tag = next((tag for tag, role in expected_role_by_tag.items() if role == delivery_role), None)
        if expected_tag is not None and expected_tag not in form_tag_set:
            errors.append(f"{prefix}_delivery_role_missing_matching_form_tag")
    if delivery_role == "regular" and role_tag_set:
        errors.append(f"{prefix}_regular_delivery_role_cannot_have_special_role_tag")
    if delivery_role == "anchor":
        if evidence_channel != "A_anchor":
            errors.append(f"{prefix}_anchor_delivery_role_channel_mismatch")
        if fixed_form is not True:
            errors.append(f"{prefix}_anchor_delivery_role_requires_fixed_form")
        if closed_book_only is not True:
            errors.append(f"{prefix}_anchor_delivery_role_requires_closed_book_only")
        if consumption_policy != "none":
            errors.append(f"{prefix}_anchor_delivery_role_consumption_policy_invalid")
    elif delivery_role == "shadow":
        if evidence_channel != "D_shadow":
            errors.append(f"{prefix}_shadow_delivery_role_channel_mismatch")
        if fixed_form is not True:
            errors.append(f"{prefix}_shadow_delivery_role_requires_fixed_form")
        if not isinstance(max_presented_items, int) or max_presented_items > 3:
            errors.append(f"{prefix}_shadow_delivery_role_requires_ultra_short_max_items")
        if consumption_policy != "none":
            errors.append(f"{prefix}_shadow_delivery_role_consumption_policy_invalid")
    elif delivery_role == "holdout":
        if evidence_channel == "C_learning":
            errors.append(f"{prefix}_holdout_delivery_role_channel_mismatch")
        if consumption_policy not in {"retire_on_use", "rotate_forms"}:
            errors.append(f"{prefix}_holdout_delivery_role_consumption_policy_invalid")
    elif delivery_role == "regular":
        if evidence_channel == "A_anchor" or evidence_channel == "D_shadow":
            errors.append(f"{prefix}_regular_delivery_role_channel_invalid")


def _family_supports_closed_book_only_measurement(family: dict[str, Any]) -> bool:
    assistance_contract = family.get("assistance_contract")
    if not isinstance(assistance_contract, dict):
        return False
    diagnostic = assistance_contract.get("diagnostic_eligible_assistance_modes")
    preserving = assistance_contract.get("measurement_preserving_assistance_modes")
    diagnostic_set = {str(v) for v in diagnostic} if isinstance(diagnostic, list) else set()
    preserving_set = {str(v) for v in preserving} if isinstance(preserving, list) else set()
    return diagnostic_set == {"closed_book"} and preserving_set == {"closed_book"}


def _validate_items_form_memberships(items: list[dict[str, Any]], form_ids: set[str], errors: list[str]) -> None:
    for idx, item in enumerate(items):
        form_memberships = item.get("form_memberships")
        if not isinstance(form_memberships, list):
            continue
        unknown_forms = {str(row) for row in form_memberships if str(row) not in form_ids}
        if unknown_forms:
            errors.append(f"items[{idx}]_form_membership_unknown:{','.join(sorted(unknown_forms))}")


def _validate_form_item_membership_reciprocity(
    forms: list[dict[str, Any]],
    item_by_id: dict[str, dict[str, Any]],
    errors: list[str],
) -> None:
    for form_idx, form in enumerate(forms):
        form_id = form.get("form_id")
        if not _is_non_empty_string(form_id):
            continue
        form_id_str = str(form_id)
        form_items = form.get("items")
        if not isinstance(form_items, list):
            continue
        for item_id in form_items:
            item = item_by_id.get(str(item_id))
            if item is None:
                continue
            memberships = item.get("form_memberships")
            if not isinstance(memberships, list) or form_id_str not in {str(v) for v in memberships}:
                errors.append(f"forms[{form_idx}]_item_membership_missing_reciprocity:{item_id}")

    for item_id, item in item_by_id.items():
        memberships = item.get("form_memberships")
        if not isinstance(memberships, list):
            continue
        for form_id in memberships:
            form_id_str = str(form_id)
            form = next(
                (
                    row
                    for row in forms
                    if _is_non_empty_string(row.get("form_id")) and str(row.get("form_id")) == form_id_str
                ),
                None,
            )
            if not isinstance(form, dict):
                continue
            form_items = form.get("items")
            if not isinstance(form_items, list) or item_id not in {str(v) for v in form_items}:
                errors.append(f"items_form_membership_missing_reciprocity:{item_id}:{form_id_str}")


def _validate_generators(
    generators: list[dict[str, Any]],
    probe_family_ids: set[str],
    factor_ids: set[str],
    rubric_ids: set[str],
    response_schema_ids: set[str],
    *,
    probe_family_by_id: dict[str, dict[str, Any]],
    delivery_tag_vocab: dict[str, set[str]],
    errors: list[str],
) -> set[str]:
    ids = _validate_unique_ids(generators, "generator_id", "generators", errors)
    for idx, generator in enumerate(generators):
        prefix = f"generators[{idx}]"
        _validate_object_shape(generator, GENERATOR_REQUIRED_FIELDS, GENERATOR_ALLOWED_FIELDS, prefix, errors)
        if not _is_non_empty_string(generator.get("generator_id")):
            errors.append(f"{prefix}_generator_id_invalid")
        family_ref = generator.get("probe_family_id")
        if not _is_non_empty_string(family_ref):
            errors.append(f"{prefix}_probe_family_id_invalid")
        elif family_ref not in probe_family_ids:
            errors.append(f"{prefix}_probe_family_unknown")
        _validate_target_factor_binding(
            generator.get("target_factor_binding"),
            factor_ids=factor_ids,
            prefix=f"{prefix}.target_factor_binding",
            errors=errors,
        )
        if not _is_non_empty_string(generator.get("generator_version")):
            errors.append(f"{prefix}_generator_version_invalid")
        if not isinstance(generator.get("parameter_schema"), dict):
            errors.append(f"{prefix}_parameter_schema_not_object")
        _validate_invariance_contract(
            generator.get("invariance_contract"),
            field_prefix=f"{prefix}.invariance_contract",
            errors=errors,
        )
        _validate_entity_tags(
            generator.get("tags"),
            allowed_vocab=delivery_tag_vocab,
            prefix=f"{prefix}.tags",
            errors=errors,
        )
        if not isinstance(generator.get("active"), bool):
            errors.append(f"{prefix}_active_not_bool")

        determinism_contract = generator.get("determinism_contract")
        d_prefix = f"{prefix}.determinism_contract"
        if not isinstance(determinism_contract, dict):
            errors.append(f"{d_prefix}_not_object")
        else:
            _validate_object_shape(
                determinism_contract,
                GENERATOR_DETERMINISM_REQUIRED_FIELDS,
                GENERATOR_DETERMINISM_ALLOWED_FIELDS,
                d_prefix,
                errors,
            )
            if determinism_contract.get("mode") not in GENERATOR_DETERMINISM_MODES:
                errors.append(f"{d_prefix}_mode_invalid")
            if not _is_non_empty_string(determinism_contract.get("seed_strategy")):
                errors.append(f"{d_prefix}_seed_strategy_invalid")
            metadata = determinism_contract.get("metadata")
            if metadata is not None and not isinstance(metadata, dict):
                errors.append(f"{d_prefix}_metadata_not_object")

        grading_contract = generator.get("grading_contract")
        g_prefix = f"{prefix}.grading_contract"
        if not isinstance(grading_contract, dict):
            errors.append(f"{g_prefix}_not_object")
        else:
            _validate_object_shape(
                grading_contract,
                GENERATOR_GRADING_CONTRACT_REQUIRED_FIELDS,
                GENERATOR_GRADING_CONTRACT_ALLOWED_FIELDS,
                g_prefix,
                errors,
            )
            rubric_ref = grading_contract.get("rubric_ref")
            if not _is_non_empty_string(rubric_ref):
                errors.append(f"{g_prefix}_rubric_ref_invalid")
            elif rubric_ref not in rubric_ids:
                errors.append(f"{g_prefix}_rubric_ref_unknown")
            response_schema_ref = grading_contract.get("response_schema_ref")
            if not _is_non_empty_string(response_schema_ref):
                errors.append(f"{g_prefix}_response_schema_ref_invalid")
            elif response_schema_ref not in response_schema_ids:
                errors.append(f"{g_prefix}_response_schema_ref_unknown")
            _validate_generator_solution_material_contract(grading_contract.get("solution_material_contract"), g_prefix, errors)
            metadata = grading_contract.get("metadata")
            if metadata is not None and not isinstance(metadata, dict):
                errors.append(f"{g_prefix}_metadata_not_object")
        binding_contract = generator.get("instance_binding_contract")
        b_prefix = f"{prefix}.instance_binding_contract"
        if not isinstance(binding_contract, dict):
            errors.append(f"{b_prefix}_not_object")
        else:
            _validate_object_shape(
                binding_contract,
                GENERATOR_INSTANCE_BINDING_REQUIRED_FIELDS,
                GENERATOR_INSTANCE_BINDING_ALLOWED_FIELDS,
                b_prefix,
                errors,
            )
            for field_name in GENERATOR_INSTANCE_BINDING_REQUIRED_FIELDS:
                if not isinstance(binding_contract.get(field_name), bool):
                    errors.append(f"{b_prefix}_{field_name}_not_bool")
            metadata = binding_contract.get("metadata")
            if metadata is not None and not isinstance(metadata, dict):
                errors.append(f"{b_prefix}_metadata_not_object")
        family = probe_family_by_id.get(str(family_ref)) if _is_non_empty_string(family_ref) else None
        _validate_adversarial_generator_contract(
            generator.get("adversarial_contract"),
            family=family,
            determinism_contract=determinism_contract if isinstance(determinism_contract, dict) else None,
            prefix=prefix,
            errors=errors,
        )
        metadata = generator.get("metadata")
        if metadata is not None and not isinstance(metadata, dict):
            errors.append(f"{prefix}_metadata_not_object")
    return ids


def _validate_generator_family_contracts(
    generators: list[dict[str, Any]],
    *,
    probe_family_by_id: dict[str, dict[str, Any]],
    response_schema_by_id: dict[str, dict[str, Any]],
    rubric_by_id: dict[str, dict[str, Any]],
    measurement_surfaces_by_id: dict[str, dict[str, Any]],
    errors: list[str],
) -> None:
    for idx, generator in enumerate(generators):
        family_id = generator.get("probe_family_id")
        if not _is_non_empty_string(family_id):
            continue
        family = probe_family_by_id.get(str(family_id))
        if family is None:
            continue
        family_target_factors = {
            str(v) for v in family.get("target_factors", []) if _is_non_empty_string(v)
        }
        target_binding = generator.get("target_factor_binding")
        if isinstance(target_binding, dict) and family_target_factors:
            generator_targets = {
                str(v)
                for field_name in ("primary_target_factors", "secondary_target_factors")
                for v in target_binding.get(field_name, [])
                if _is_non_empty_string(v)
            }
            invalid_targets = sorted(generator_targets - family_target_factors)
            if invalid_targets:
                errors.append(f"generators[{idx}]_target_factor_not_allowed_by_family:{','.join(invalid_targets)}")
        grading_contract = generator.get("grading_contract")
        if not isinstance(grading_contract, dict):
            continue
        measurement_surface_ref = grading_contract.get("measurement_surface_ref")
        rubric_ref = grading_contract.get("rubric_ref")
        if not _is_non_empty_string(rubric_ref):
            continue
        rubric = rubric_by_id.get(str(rubric_ref))
        if rubric is None:
            continue
        family_surface_rows = []
        surface_refs = family.get("measurement_surface_refs")
        if isinstance(surface_refs, list):
            family_surface_rows = [
                measurement_surfaces_by_id[str(ref)]
                for ref in surface_refs
                if isinstance(ref, str) and str(ref) in measurement_surfaces_by_id
            ]
        family_obs_refs = {
            str(row.get("observation_schema_ref"))
            for row in family_surface_rows
            if _is_non_empty_string(row.get("observation_schema_ref"))
        }
        family_response_refs = {
            str(row.get("response_schema_ref"))
            for row in family_surface_rows
            if _is_non_empty_string(row.get("response_schema_ref"))
        }
        rubric_obs = rubric.get("observation_schema_ref")
        if family_obs_refs and _is_non_empty_string(rubric_obs):
            if str(rubric_obs) not in family_obs_refs:
                errors.append(f"generators[{idx}]_rubric_observation_schema_mismatch_family")
        response_ref = grading_contract.get("response_schema_ref")
        if family_response_refs and _is_non_empty_string(response_ref):
            if str(response_ref) not in family_response_refs:
                errors.append(f"generators[{idx}]_response_schema_not_allowed_by_family")
        response_schema = response_schema_by_id.get(str(response_ref)) if _is_non_empty_string(response_ref) else None
        solution_contract = grading_contract.get("solution_material_contract")
        if isinstance(response_schema, dict) and _is_non_empty_string(rubric_obs):
            if isinstance(solution_contract, dict):
                _validate_generator_solution_contract_compatibility(
                    solution_contract=solution_contract,
                    rubric=rubric,
                    prefix=f"generators[{idx}]",
                    errors=errors,
                )
            if response_schema.get("authoring_status") != "active_supported":
                errors.append(f"generators[{idx}]_response_schema_not_active_supported")
            if isinstance(solution_contract, dict) and solution_contract.get("response_kind") != response_schema.get("response_kind"):
                errors.append(f"generators[{idx}]_solution_material_response_kind_mismatch_response_schema")
            matching_surface_ids = _matching_measurement_surface_ids(
                surface_rows=family_surface_rows,
                response_ref=str(response_ref) if _is_non_empty_string(response_ref) else None,
                response_schema=response_schema,
                rubric_ref=str(rubric_ref),
                rubric=rubric,
            )
            if not matching_surface_ids:
                errors.append(f"generators[{idx}]_measurement_surface_binding_missing_or_mismatched")
            elif len(matching_surface_ids) > 1:
                errors.append(
                    f"generators[{idx}]_measurement_surface_binding_ambiguous:{','.join(sorted(matching_surface_ids))}"
                )
            elif (
                not _is_non_empty_string(measurement_surface_ref)
                or str(measurement_surface_ref) not in matching_surface_ids
            ):
                errors.append(f"generators[{idx}]_measurement_surface_ref_mismatch_unique_binding")


def _validate_probe_family_item_sources(
    families: list[dict[str, Any]],
    item_by_id: dict[str, dict[str, Any]],
    form_by_id: dict[str, dict[str, Any]],
    generator_by_id: dict[str, dict[str, Any]],
    errors: list[str],
) -> None:
    for idx, family in enumerate(families):
        item_source = family.get("item_source")
        if not isinstance(item_source, dict):
            continue
        family_id = family.get("probe_family_id")
        family_id_str = str(family_id) if _is_non_empty_string(family_id) else ""
        source_kind = item_source.get("source_kind")
        refs = item_source.get("refs")
        if not isinstance(refs, list):
            continue
        prefix = f"probe_families[{idx}].item_source"
        if source_kind == "static_bank":
            for ref in refs:
                ref_str = str(ref)
                item = item_by_id.get(ref_str)
                if item is None:
                    errors.append(f"{prefix}_static_ref_unknown:{ref_str}")
                    continue
                item_family = item.get("probe_family_id")
                if family_id_str and str(item_family) != family_id_str:
                    errors.append(f"{prefix}_static_item_family_mismatch:{ref_str}")
        elif source_kind == "form_bank":
            for ref in refs:
                ref_str = str(ref)
                form = form_by_id.get(ref_str)
                if form is None:
                    errors.append(f"{prefix}_form_ref_unknown:{ref_str}")
                    continue
                form_items = form.get("items")
                if not isinstance(form_items, list):
                    continue
                for form_item_id in form_items:
                    item = item_by_id.get(str(form_item_id))
                    if item is None:
                        continue
                    item_family = item.get("probe_family_id")
                    if family_id_str and str(item_family) != family_id_str:
                        errors.append(f"{prefix}_form_item_family_mismatch:{ref_str}:{form_item_id}")
        elif source_kind == "generator_bank":
            for ref in refs:
                ref_str = str(ref)
                generator = generator_by_id.get(ref_str)
                if generator is None:
                    errors.append(f"{prefix}_generator_ref_unknown:{ref_str}")
                    continue
                generator_family = generator.get("probe_family_id")
                if family_id_str and str(generator_family) != family_id_str:
                    errors.append(f"{prefix}_generator_family_mismatch:{ref_str}")


def _validate_delivery_artifacts(
    artifacts: list[dict[str, Any]],
    *,
    measurement_surface_ids: set[str],
    generator_ids: set[str],
    rubric_ids: set[str],
    delivery_tag_vocab: dict[str, set[str]],
    errors: list[str],
) -> None:
    _validate_unique_ids(artifacts, "artifact_id", "delivery_artifacts", errors)
    for idx, artifact in enumerate(artifacts):
        prefix = f"delivery_artifacts[{idx}]"
        _validate_object_shape(
            artifact,
            DELIVERY_ARTIFACT_REQUIRED_FIELDS,
            DELIVERY_ARTIFACT_ALLOWED_FIELDS,
            prefix,
            errors,
        )
        if not _is_non_empty_string(artifact.get("artifact_id")):
            errors.append(f"{prefix}_artifact_id_invalid")
        if artifact.get("artifact_kind") not in DELIVERY_ARTIFACT_KINDS:
            errors.append(f"{prefix}_artifact_kind_invalid")
        bindings = artifact.get("bindings")
        if not isinstance(bindings, list) or not bindings:
            errors.append(f"{prefix}_bindings_invalid_or_empty")
        else:
            for binding_idx, binding in enumerate(bindings):
                b_prefix = f"{prefix}.bindings[{binding_idx}]"
                if not isinstance(binding, dict):
                    errors.append(f"{b_prefix}_not_object")
                    continue
                _validate_object_shape(
                    binding,
                    FIXTURE_BINDING_REQUIRED_FIELDS,
                    FIXTURE_BINDING_ALLOWED_FIELDS,
                    b_prefix,
                    errors,
                )
                binding_kind = binding.get("binding_kind")
                if binding_kind not in FIXTURE_BINDING_KINDS:
                    errors.append(f"{b_prefix}_binding_kind_invalid")
                ref_id = binding.get("ref_id")
                if not _is_non_empty_string(ref_id):
                    errors.append(f"{b_prefix}_ref_id_invalid")
                else:
                    if binding_kind == "measurement_surface" and ref_id not in measurement_surface_ids:
                        errors.append(f"{b_prefix}_measurement_surface_ref_unknown")
                    if binding_kind == "generator" and ref_id not in generator_ids:
                        errors.append(f"{b_prefix}_generator_ref_unknown")
                    if binding_kind == "rubric" and ref_id not in rubric_ids:
                        errors.append(f"{b_prefix}_rubric_ref_unknown")
                metadata = binding.get("metadata")
                if metadata is not None and not isinstance(metadata, dict):
                    errors.append(f"{b_prefix}_metadata_not_object")
        _validate_entity_tags(
            artifact.get("tags"),
            allowed_vocab=delivery_tag_vocab,
            prefix=f"{prefix}.tags",
            errors=errors,
        )
        if not isinstance(artifact.get("active"), bool):
            errors.append(f"{prefix}_active_not_bool")
        metadata = artifact.get("metadata")
        if metadata is not None and not isinstance(metadata, dict):
            errors.append(f"{prefix}_metadata_not_object")


def _validate_item_delivery_role_exclusivity(
    items: list[dict[str, Any]],
    form_by_id: dict[str, dict[str, Any]],
    errors: list[str],
) -> None:
    for idx, item in enumerate(items):
        form_memberships = item.get("form_memberships")
        if not isinstance(form_memberships, list):
            continue
        role_counts = {"regular": 0, "holdout": 0, "anchor": 0, "shadow": 0, "adversarial": 0}
        for form_id in form_memberships:
            form = form_by_id.get(str(form_id))
            if form is None:
                continue
            delivery_role = form.get("delivery_role")
            if delivery_role in role_counts:
                role_counts[str(delivery_role)] += 1
        active_roles = sorted(role for role, count in role_counts.items() if count)
        if len(active_roles) > 1 and item.get("dual_use_allowed") is not True:
            errors.append(f"items[{idx}]_cross_role_form_dual_use_forbidden:{','.join(active_roles)}")


def _validate_content_migrations(
    migrations: list[dict[str, Any]],
    *,
    bundle: dict[str, Any],
    measurement_surfaces: list[dict[str, Any]],
    change_manifest: Any,
    errors: list[str],
) -> None:
    _validate_unique_ids(migrations, "migration_id", "content_migrations", errors)
    bundle_parent = bundle.get("parent_release_hash")
    bundle_release = bundle.get("release_hash")
    compatibility_classes = {
        str(row.get("measurement_surface_id")): str(row.get("compatibility_class"))
        for row in measurement_surfaces
        if isinstance(row, dict)
        and _is_non_empty_string(row.get("measurement_surface_id"))
        and row.get("compatibility_class") in MEASUREMENT_SURFACE_COMPATIBILITY
    }
    manifest_entries: dict[str, set[str]] = {"rename": set(), "split": set(), "merge": set(), "deprecate": set()}
    if isinstance(change_manifest, dict):
        for bucket in ("added", "deprecated", "modified"):
            rows = change_manifest.get(bucket)
            if not isinstance(rows, list):
                continue
            for row in rows:
                if not isinstance(row, dict):
                    continue
                change_type = row.get("change_type")
                entity_id = row.get("entity_id")
                if change_type in manifest_entries and _is_non_empty_string(entity_id):
                    manifest_entries[str(change_type)].add(str(entity_id))
    for idx, migration in enumerate(migrations):
        prefix = f"content_migrations[{idx}]"
        _validate_object_shape(
            migration,
            CONTENT_MIGRATION_REQUIRED_FIELDS,
            CONTENT_MIGRATION_ALLOWED_FIELDS,
            prefix,
            errors,
        )
        if not _is_non_empty_string(migration.get("migration_id")):
            errors.append(f"{prefix}_migration_id_invalid")
        if not _is_sha256_hash(migration.get("from_release_hash")):
            errors.append(f"{prefix}_from_release_hash_invalid")
        if not _is_sha256_hash(migration.get("to_release_hash")):
            errors.append(f"{prefix}_to_release_hash_invalid")
        if _is_sha256_hash(bundle_parent) and migration.get("from_release_hash") != bundle_parent:
            errors.append(f"{prefix}_from_release_hash_mismatch_bundle_parent")
        if _is_sha256_hash(bundle_release) and migration.get("to_release_hash") != bundle_release:
            errors.append(f"{prefix}_to_release_hash_mismatch_bundle_release")
        migration_present = False
        for field_name in (
            "commitment_mapping",
            "factor_mapping",
            "probe_family_mapping",
            "item_mapping",
            "measurement_surface_mapping",
        ):
            rows = migration.get(field_name)
            if not isinstance(rows, list):
                errors.append(f"{prefix}_{field_name}_not_array")
                continue
            for entry_idx, entry in enumerate(rows):
                e_prefix = f"{prefix}.{field_name}[{entry_idx}]"
                if not isinstance(entry, dict):
                    errors.append(f"{e_prefix}_not_object")
                    continue
                _validate_object_shape(
                    entry,
                    MIGRATION_MAPPING_REQUIRED_FIELDS,
                    MIGRATION_MAPPING_ALLOWED_FIELDS,
                    e_prefix,
                    errors,
                )
                _validate_string_list(entry.get("source_ids"), f"{e_prefix}_source_ids_invalid", errors, unique=True, non_empty=True)
                _validate_string_list(entry.get("target_ids"), f"{e_prefix}_target_ids_invalid", errors, unique=True)
                if entry.get("mode") not in MIGRATION_ENTRY_MODES:
                    errors.append(f"{e_prefix}_mode_invalid")
                else:
                    migration_present = True
                    source_ids = entry.get("source_ids")
                    target_ids = entry.get("target_ids")
                    if isinstance(source_ids, list) and isinstance(target_ids, list):
                        _validate_migration_cardinality(
                            mode=str(entry.get("mode")),
                            source_ids=source_ids,
                            target_ids=target_ids,
                            prefix=e_prefix,
                            errors=errors,
                        )
                        if str(entry.get("mode")) in manifest_entries:
                            for entity_id in source_ids + target_ids:
                                if _is_non_empty_string(entity_id) and str(entity_id) not in manifest_entries[str(entry.get("mode"))]:
                                    errors.append(f"{e_prefix}_change_manifest_missing_entity:{entity_id}")
                if "rule" in entry and entry.get("rule") is not None and not _is_non_empty_string(entry.get("rule")):
                    errors.append(f"{e_prefix}_rule_invalid")
                metadata = entry.get("metadata")
                if metadata is not None and not isinstance(metadata, dict):
                    errors.append(f"{e_prefix}_metadata_not_object")
        policy = migration.get("state_transform_policy")
        p_prefix = f"{prefix}.state_transform_policy"
        if not isinstance(policy, dict):
            errors.append(f"{p_prefix}_not_object")
        else:
            _validate_object_shape(
                policy,
                STATE_TRANSFORM_POLICY_REQUIRED_FIELDS,
                STATE_TRANSFORM_POLICY_ALLOWED_FIELDS,
                p_prefix,
                errors,
            )
            if not _is_non_empty_string(policy.get("policy_id")):
                errors.append(f"{p_prefix}_policy_id_invalid")
            if policy.get("uncertainty_mode") not in STATE_TRANSFORM_UNCERTAINTY_MODES:
                errors.append(f"{p_prefix}_uncertainty_mode_invalid")
            if policy.get("readiness_mode") not in STATE_TRANSFORM_READINESS_MODES:
                errors.append(f"{p_prefix}_readiness_mode_invalid")
            metadata = policy.get("metadata")
            if metadata is not None and not isinstance(metadata, dict):
                errors.append(f"{p_prefix}_metadata_not_object")
        if not _is_sha256_hash(migration.get("transform_hash")):
            errors.append(f"{prefix}_transform_hash_invalid")
        metadata = migration.get("metadata")
        if metadata is not None and not isinstance(metadata, dict):
            errors.append(f"{prefix}_metadata_not_object")
        if not migration_present:
            errors.append(f"{prefix}_has_no_mapping_entries")

    classes = set(compatibility_classes.values())
    if "breaking_migration" in classes and not migrations:
        errors.append("measurement_surfaces_breaking_migration_requires_content_migration")
    if "surface_major" in classes:
        has_surface_mapping = any(
            isinstance(migration, dict)
            and isinstance(migration.get("measurement_surface_mapping"), list)
            and len(migration.get("measurement_surface_mapping", [])) > 0
            for migration in migrations
        )
        if not has_surface_mapping:
            errors.append("measurement_surfaces_surface_major_requires_surface_mapping")
    if migrations and "safe_minor" in classes and classes == {"safe_minor"}:
        errors.append("content_migrations_present_but_all_surfaces_safe_minor")


def _validate_migration_cardinality(
    *,
    mode: str,
    source_ids: list[Any],
    target_ids: list[Any],
    prefix: str,
    errors: list[str],
) -> None:
    source_count = len(source_ids)
    target_count = len(target_ids)
    if mode == "rename" and not (source_count == 1 and target_count == 1):
        errors.append(f"{prefix}_rename_cardinality_invalid")
    if mode == "split" and not (source_count == 1 and target_count > 1):
        errors.append(f"{prefix}_split_cardinality_invalid")
    if mode == "merge" and not (source_count > 1 and target_count == 1):
        errors.append(f"{prefix}_merge_cardinality_invalid")
    if mode == "deprecate" and not (source_count == 1 and target_count == 0):
        errors.append(f"{prefix}_deprecate_cardinality_invalid")


def _validate_dag_acyclic(edges: list[dict[str, Any]], errors: list[str]) -> None:
    adjacency: dict[str, set[str]] = {}
    for edge in edges:
        src = edge.get("src_commitment_id")
        dst = edge.get("dst_commitment_id")
        if not _is_non_empty_string(src) or not _is_non_empty_string(dst):
            continue
        adjacency.setdefault(str(src), set()).add(str(dst))

    color: dict[str, int] = {}

    def visit(node: str, stack: list[str]) -> bool:
        mark = color.get(node, 0)
        if mark == 1:
            cycle_path = "->".join(stack + [node])
            errors.append(f"edges_cycle_detected:{cycle_path}")
            return True
        if mark == 2:
            return False
        color[node] = 1
        for nxt in adjacency.get(node, set()):
            if visit(nxt, stack + [node]):
                return True
        color[node] = 2
        return False

    for node in adjacency:
        if color.get(node, 0) == 0 and visit(node, []):
            return


def _validate_release_hash(bundle: dict[str, Any], errors: list[str]) -> None:
    if "release_hash" not in bundle:
        return
    declared = bundle.get("release_hash")
    if not _is_sha256_hash(declared):
        return
    recomputed = compute_content_ir_release_hash(bundle)
    if declared != recomputed:
        errors.append("bundle_release_hash_mismatch_recomputed")


def _validate_canonicalization_steps(value: Any, prefix: str, errors: list[str]) -> None:
    field_prefix = f"{prefix}.canonicalization_steps"
    if not isinstance(value, list) or not value:
        errors.append(f"{field_prefix}_invalid_or_empty")
        return
    seen_ids: set[str] = set()
    for idx, row in enumerate(value):
        c_prefix = f"{field_prefix}[{idx}]"
        if not isinstance(row, dict):
            errors.append(f"{c_prefix}_not_object")
            continue
        _validate_object_shape(
            row,
            CANONICALIZATION_STEP_REQUIRED_FIELDS,
            CANONICALIZATION_STEP_ALLOWED_FIELDS,
            c_prefix,
            errors,
        )
        step_id = row.get("step_id")
        if not _is_non_empty_string(step_id):
            errors.append(f"{c_prefix}_step_id_invalid")
        else:
            step_id_str = str(step_id)
            if step_id_str in seen_ids:
                errors.append(f"{field_prefix}_duplicate_step_id:{step_id_str}")
            seen_ids.add(step_id_str)
        if row.get("op") not in CANONICALIZATION_OPS:
            errors.append(f"{c_prefix}_op_invalid")
        if not isinstance(row.get("params"), dict):
            errors.append(f"{c_prefix}_params_not_object")
        metadata = row.get("metadata")
        if metadata is not None and not isinstance(metadata, dict):
            errors.append(f"{c_prefix}_metadata_not_object")


def _validate_parse_ir(value: Any, prefix: str, errors: list[str]) -> None:
    field_prefix = f"{prefix}.parse_ir"
    if not isinstance(value, dict):
        errors.append(f"{field_prefix}_not_object")
        return
    _validate_object_shape(value, PARSE_IR_REQUIRED_FIELDS, PARSE_IR_ALLOWED_FIELDS, field_prefix, errors)
    if not _is_non_empty_string(value.get("parse_ir_id")):
        errors.append(f"{field_prefix}_parse_ir_id_invalid")
    if value.get("parser_kind") not in PARSE_IR_KINDS:
        errors.append(f"{field_prefix}_parser_kind_invalid")
    if not isinstance(value.get("output_schema"), dict):
        errors.append(f"{field_prefix}_output_schema_not_object")
    _validate_string_list(value.get("uncertainty_fields"), f"{field_prefix}_uncertainty_fields_invalid", errors, unique=True)
    output_schema = value.get("output_schema")
    uncertainty_fields = value.get("uncertainty_fields")
    if isinstance(output_schema, dict) and isinstance(uncertainty_fields, list):
        output_paths = _schema_paths(output_schema, "parse_ir")
        for field in uncertainty_fields:
            if not _is_non_empty_string(field):
                continue
            candidate = f"parse_ir.{field}"
            if candidate not in output_paths:
                errors.append(f"{field_prefix}_uncertainty_field_unknown:{field}")
    metadata = value.get("metadata")
    if metadata is not None and not isinstance(metadata, dict):
        errors.append(f"{field_prefix}_metadata_not_object")


def _validate_scoring_rules(
    value: Any,
    prefix: str,
    *,
    response_schema_by_id: dict[str, dict[str, Any]],
    errors: list[str],
) -> None:
    field_prefix = f"{prefix}.scoring_rules"
    if not isinstance(value, list) or not value:
        errors.append(f"{field_prefix}_invalid_or_empty")
        return
    seen_ids: set[str] = set()
    for idx, row in enumerate(value):
        s_prefix = f"{field_prefix}[{idx}]"
        if not isinstance(row, dict):
            errors.append(f"{s_prefix}_not_object")
            continue
        _validate_object_shape(row, SCORING_RULE_REQUIRED_FIELDS, SCORING_RULE_ALLOWED_FIELDS, s_prefix, errors)
        rule_id = row.get("rule_id")
        if not _is_non_empty_string(rule_id):
            errors.append(f"{s_prefix}_rule_id_invalid")
        else:
            rule_id_str = str(rule_id)
            if rule_id_str in seen_ids:
                errors.append(f"{field_prefix}_duplicate_rule_id:{rule_id_str}")
            seen_ids.add(rule_id_str)
        if row.get("rule_kind") not in SCORING_RULE_KINDS:
            errors.append(f"{s_prefix}_rule_kind_invalid")
        if row.get("source") not in SCORING_RULE_SOURCES:
            errors.append(f"{s_prefix}_source_invalid")
        if not _is_non_empty_string(row.get("source_path")):
            errors.append(f"{s_prefix}_source_path_invalid")
        if not isinstance(row.get("params"), dict):
            errors.append(f"{s_prefix}_params_not_object")
        else:
            _validate_scoring_rule_params(row.get("rule_kind"), row.get("params"), s_prefix, errors)
        metadata = row.get("metadata")
        if metadata is not None and not isinstance(metadata, dict):
            errors.append(f"{s_prefix}_metadata_not_object")


def _validate_observation_emission(
    value: Any,
    prefix: str,
    *,
    observation_schema: dict[str, Any] | None,
    errors: list[str],
) -> None:
    field_prefix = f"{prefix}.observation_emission"
    if not isinstance(value, dict):
        errors.append(f"{field_prefix}_not_object")
        return
    _validate_object_shape(
        value,
        OBSERVATION_EMISSION_REQUIRED_FIELDS,
        OBSERVATION_EMISSION_ALLOWED_FIELDS,
        field_prefix,
        errors,
    )
    if not _is_non_empty_string(value.get("emission_id")):
        errors.append(f"{field_prefix}_emission_id_invalid")
    fields = value.get("fields")
    if not isinstance(fields, list) or not fields:
        errors.append(f"{field_prefix}_fields_invalid_or_empty")
    else:
        seen_features: set[str] = set()
        declared_features = _observation_schema_feature_map(observation_schema)
        for idx, row in enumerate(fields):
            e_prefix = f"{field_prefix}.fields[{idx}]"
            if not isinstance(row, dict):
                errors.append(f"{e_prefix}_not_object")
                continue
            _validate_object_shape(
                row,
                OBSERVATION_EMISSION_FIELD_REQUIRED_FIELDS,
                OBSERVATION_EMISSION_FIELD_ALLOWED_FIELDS,
                e_prefix,
                errors,
            )
            feature_id = row.get("feature_id")
            if not _is_non_empty_string(feature_id):
                errors.append(f"{e_prefix}_feature_id_invalid")
            else:
                feature_id_str = str(feature_id)
                if feature_id_str in seen_features:
                    errors.append(f"{field_prefix}_duplicate_feature_id:{feature_id_str}")
                seen_features.add(feature_id_str)
                if declared_features and feature_id_str not in declared_features:
                    errors.append(f"{e_prefix}_feature_id_unknown_in_observation_schema")
            if row.get("source") not in OBSERVATION_EMISSION_SOURCES:
                errors.append(f"{e_prefix}_source_invalid")
            if not _is_non_empty_string(row.get("source_path")):
                errors.append(f"{e_prefix}_source_path_invalid")
            metadata = row.get("metadata")
            if metadata is not None and not isinstance(metadata, dict):
                errors.append(f"{e_prefix}_metadata_not_object")
    metadata = value.get("metadata")
    if metadata is not None and not isinstance(metadata, dict):
        errors.append(f"{field_prefix}_metadata_not_object")
    if isinstance(observation_schema, dict) and isinstance(fields, list):
        emitted = {str(row.get("feature_id")) for row in fields if isinstance(row, dict) and _is_non_empty_string(row.get("feature_id"))}
        required_features = {
            feature_id
            for feature_id, feature in _observation_schema_feature_map(observation_schema).items()
            if feature.get("required") is True
        }
        outcome_features = {
            str(v)
            for v in observation_schema.get("outcome_surface_feature_ids", [])
            if _is_non_empty_string(v)
        }
        missing_required = sorted(required_features - emitted)
        if missing_required:
            errors.append(f"{field_prefix}_missing_required_features:{','.join(missing_required)}")
        missing_outcome = sorted(outcome_features - emitted)
        if missing_outcome:
            errors.append(f"{field_prefix}_missing_outcome_surface_features:{','.join(missing_outcome)}")


def _validate_item_params(value: Any, prefix: str, errors: list[str]) -> None:
    field_prefix = f"{prefix}.item_params"
    if not isinstance(value, dict):
        errors.append(f"{field_prefix}_not_object")
        return
    _validate_object_shape(value, ITEM_PARAMS_REQUIRED_FIELDS, ITEM_PARAMS_ALLOWED_FIELDS, field_prefix, errors)
    for field_name in ("difficulty_offset_init", "ambiguity_risk_init"):
        if not isinstance(value.get(field_name), (int, float)):
            errors.append(f"{field_prefix}_{field_name}_invalid")
    signature = value.get("signature")
    s_prefix = f"{field_prefix}.signature"
    if not isinstance(signature, dict):
        errors.append(f"{s_prefix}_not_object")
    else:
        _validate_object_shape(signature, ITEM_SIGNATURE_REQUIRED_FIELDS, ITEM_SIGNATURE_ALLOWED_FIELDS, s_prefix, errors)
        for field_name in ("prompt_len_tokens", "slots_count", "binding_ops", "step_count_est"):
            field_value = signature.get(field_name)
            if not isinstance(field_value, int) or field_value < 0:
                errors.append(f"{s_prefix}_{field_name}_invalid")
        metadata = signature.get("metadata")
        if metadata is not None and not isinstance(metadata, dict):
            errors.append(f"{s_prefix}_metadata_not_object")
    metadata = value.get("metadata")
    if metadata is not None and not isinstance(metadata, dict):
        errors.append(f"{field_prefix}_metadata_not_object")


def _validate_target_factor_binding(
    value: Any,
    *,
    factor_ids: set[str],
    prefix: str,
    errors: list[str],
) -> None:
    if not isinstance(value, dict):
        errors.append(f"{prefix}_not_object")
        return
    _validate_object_shape(
        value,
        TARGET_FACTOR_BINDING_REQUIRED_FIELDS,
        TARGET_FACTOR_BINDING_ALLOWED_FIELDS,
        prefix,
        errors,
    )
    _validate_string_list(
        value.get("primary_target_factors"),
        f"{prefix}_primary_target_factors_invalid",
        errors,
        unique=True,
        non_empty=True,
    )
    primary = value.get("primary_target_factors")
    primary_set = {str(v) for v in primary} if isinstance(primary, list) else set()
    unknown_primary = sorted(f for f in primary_set if f not in factor_ids)
    if unknown_primary:
        errors.append(f"{prefix}_primary_target_factor_unknown:{','.join(unknown_primary)}")
    secondary = value.get("secondary_target_factors")
    if secondary is not None:
        _validate_string_list(
            secondary,
            f"{prefix}_secondary_target_factors_invalid",
            errors,
            unique=True,
        )
        if isinstance(secondary, list):
            secondary_set = {str(v) for v in secondary}
            unknown_secondary = sorted(f for f in secondary_set if f not in factor_ids)
            if unknown_secondary:
                errors.append(f"{prefix}_secondary_target_factor_unknown:{','.join(unknown_secondary)}")
            overlap = sorted(primary_set & secondary_set)
            if overlap:
                errors.append(f"{prefix}_target_factor_overlap:{','.join(overlap)}")
    metadata = value.get("metadata")
    if metadata is not None and not isinstance(metadata, dict):
        errors.append(f"{prefix}_metadata_not_object")


def _validate_item_grading_material(value: Any, prefix: str, errors: list[str]) -> None:
    field_prefix = f"{prefix}.grading_material"
    if not isinstance(value, dict):
        errors.append(f"{field_prefix}_not_object")
        return
    _validate_object_shape(
        value,
        ITEM_GRADING_MATERIAL_REQUIRED_FIELDS,
        ITEM_GRADING_MATERIAL_ALLOWED_FIELDS,
        field_prefix,
        errors,
    )
    response_kind = value.get("response_kind")
    if response_kind not in {"slots", "mcq", "numeric"}:
        errors.append(f"{field_prefix}_response_kind_invalid")
    if response_kind == "slots":
        _validate_string_list(value.get("slot_answer_key"), f"{field_prefix}_slot_answer_key_invalid", errors, non_empty=True)
    elif response_kind == "mcq":
        if not _is_non_empty_string(value.get("correct_choice_id")):
            errors.append(f"{field_prefix}_correct_choice_id_invalid")
    elif response_kind == "numeric":
        if not isinstance(value.get("numeric_answer"), (int, float)):
            errors.append(f"{field_prefix}_numeric_answer_invalid")
    metadata = value.get("metadata")
    if metadata is not None and not isinstance(metadata, dict):
        errors.append(f"{field_prefix}_metadata_not_object")


def _validate_generator_solution_material_contract(value: Any, prefix: str, errors: list[str]) -> None:
    field_prefix = f"{prefix}.solution_material_contract"
    if not isinstance(value, dict):
        errors.append(f"{field_prefix}_not_object")
        return
    _validate_object_shape(
        value,
        GENERATOR_SOLUTION_MATERIAL_REQUIRED_FIELDS,
        GENERATOR_SOLUTION_MATERIAL_ALLOWED_FIELDS,
        field_prefix,
        errors,
    )
    if value.get("response_kind") not in {"slots", "mcq", "numeric"}:
        errors.append(f"{field_prefix}_response_kind_invalid")
    if value.get("derivation_source") not in GENERATOR_SOLUTION_DERIVATION_SOURCES:
        errors.append(f"{field_prefix}_derivation_source_invalid")
    if not _is_non_empty_string(value.get("source_path")):
        errors.append(f"{field_prefix}_source_path_invalid")
    _validate_string_list(value.get("required_fields"), f"{field_prefix}_required_fields_invalid", errors, unique=True, non_empty=True)
    metadata = value.get("metadata")
    if metadata is not None and not isinstance(metadata, dict):
        errors.append(f"{field_prefix}_metadata_not_object")


def _validate_adversarial_generator_contract(
    value: Any,
    *,
    family: dict[str, Any] | None,
    determinism_contract: dict[str, Any] | None,
    prefix: str,
    errors: list[str],
) -> None:
    is_adversarial_family = isinstance(family, dict) and family.get("family_kind") == "adversarial"
    field_prefix = f"{prefix}.adversarial_contract"
    if not is_adversarial_family:
        if value is not None:
            errors.append(f"{field_prefix}_not_allowed_for_non_adversarial_family")
        return
    if not isinstance(value, dict):
        errors.append(f"{field_prefix}_not_object")
        return
    _validate_object_shape(
        value,
        ADVERSARIAL_GENERATOR_CONTRACT_REQUIRED_FIELDS,
        ADVERSARIAL_GENERATOR_CONTRACT_ALLOWED_FIELDS,
        field_prefix,
        errors,
    )
    if value.get("generation_mode") != "seeded_minimal_pairs":
        errors.append(f"{field_prefix}_generation_mode_invalid")
    if not isinstance(determinism_contract, dict) or determinism_contract.get("mode") != "seeded":
        errors.append(f"{field_prefix}_requires_seeded_determinism_contract")
    axes = value.get("perturbation_axes")
    if not isinstance(axes, list) or not axes:
        errors.append(f"{field_prefix}_perturbation_axes_invalid_or_empty")
    else:
        seen_axes: set[str] = set()
        for idx, axis in enumerate(axes):
            a_prefix = f"{field_prefix}.perturbation_axes[{idx}]"
            if not isinstance(axis, dict):
                errors.append(f"{a_prefix}_not_object")
                continue
            _validate_object_shape(
                axis,
                GENERATOR_PERTURBATION_AXIS_REQUIRED_FIELDS,
                GENERATOR_PERTURBATION_AXIS_ALLOWED_FIELDS,
                a_prefix,
                errors,
            )
            axis_id = axis.get("axis_id")
            if not _is_non_empty_string(axis_id):
                errors.append(f"{a_prefix}_axis_id_invalid")
            else:
                axis_id_str = str(axis_id)
                if axis_id_str in seen_axes:
                    errors.append(f"{field_prefix}_duplicate_perturbation_axis:{axis_id_str}")
                seen_axes.add(axis_id_str)
            if not _is_non_empty_string(axis.get("description")):
                errors.append(f"{a_prefix}_description_invalid")
            _validate_string_list(axis.get("allowed_values"), f"{a_prefix}_allowed_values_invalid", errors, unique=True, non_empty=True)
            metadata = axis.get("metadata")
            if metadata is not None and not isinstance(metadata, dict):
                errors.append(f"{a_prefix}_metadata_not_object")
    max_axes = value.get("max_perturbation_axes_per_instance")
    if not isinstance(max_axes, int) or max_axes <= 0:
        errors.append(f"{field_prefix}_max_perturbation_axes_per_instance_invalid")
    elif isinstance(axes, list) and axes and max_axes > len(axes):
        errors.append(f"{field_prefix}_max_perturbation_axes_per_instance_exceeds_axes")
    metadata = value.get("metadata")
    if metadata is not None and not isinstance(metadata, dict):
        errors.append(f"{field_prefix}_metadata_not_object")


def _validate_item_grading_material_compatibility(
    *,
    grading_material: dict[str, Any],
    rubric: dict[str, Any],
    prefix: str,
    errors: list[str],
) -> None:
    for idx, rule in enumerate(rubric.get("scoring_rules", [])):
        if not isinstance(rule, dict):
            continue
        rule_kind = rule.get("rule_kind")
        if rule_kind == "exact_match" and grading_material.get("response_kind") == "slots":
            if not isinstance(grading_material.get("slot_answer_key"), list):
                errors.append(f"{prefix}_grading_material_missing_slot_answer_key_for_rule:{idx}")
        if rule_kind in {"exact_match", "choice_lookup"} and grading_material.get("response_kind") == "mcq":
            if not _is_non_empty_string(grading_material.get("correct_choice_id")):
                errors.append(f"{prefix}_grading_material_missing_correct_choice_id_for_rule:{idx}")
        if rule_kind == "numeric_tolerance" and grading_material.get("response_kind") == "numeric":
            if not isinstance(grading_material.get("numeric_answer"), (int, float)):
                errors.append(f"{prefix}_grading_material_missing_numeric_answer_for_rule:{idx}")


def _validate_generator_solution_contract_compatibility(
    *,
    solution_contract: dict[str, Any],
    rubric: dict[str, Any],
    prefix: str,
    errors: list[str],
) -> None:
    required_fields = (
        {str(v) for v in solution_contract.get("required_fields", [])}
        if isinstance(solution_contract.get("required_fields"), list)
        else set()
    )
    for idx, rule in enumerate(rubric.get("scoring_rules", [])):
        if not isinstance(rule, dict):
            continue
        rule_kind = rule.get("rule_kind")
        if rule_kind == "exact_match" and solution_contract.get("response_kind") == "slots":
            if "slot_answer_key" not in required_fields:
                errors.append(f"{prefix}_solution_material_missing_slot_answer_key_for_rule:{idx}")
        if rule_kind in {"exact_match", "choice_lookup"} and solution_contract.get("response_kind") == "mcq":
            if "correct_choice_id" not in required_fields:
                errors.append(f"{prefix}_solution_material_missing_correct_choice_id_for_rule:{idx}")
        if rule_kind == "numeric_tolerance" and solution_contract.get("response_kind") == "numeric":
            if "numeric_answer" not in required_fields:
                errors.append(f"{prefix}_solution_material_missing_numeric_answer_for_rule:{idx}")


def _matching_measurement_surface_ids(
    *,
    surface_rows: list[dict[str, Any]],
    response_ref: str | None,
    response_schema: dict[str, Any] | None,
    rubric_ref: str | None,
    rubric: dict[str, Any] | None,
) -> set[str]:
    if response_ref is None or not isinstance(response_schema, dict) or rubric_ref is None or not isinstance(rubric, dict):
        return set()
    expected_observation_hash = None
    rubric_observation_ref = rubric.get("observation_schema_ref")
    if _is_non_empty_string(rubric_observation_ref):
        expected_observation_hash = str(rubric_observation_ref)
    expected_canon = fingerprint_response_canonicalization(response_schema)
    expected_parse = fingerprint_response_parse_ir(response_schema)
    expected_rubric = fingerprint_rubric_semantics(rubric)
    matches: set[str] = set()
    for surface_row in surface_rows:
        if (
            surface_row.get("response_schema_ref") == response_ref
            and surface_row.get("rubric_ref") == rubric_ref
            and surface_row.get("canonicalization_hash") == expected_canon
            and surface_row.get("parse_ir_hash") == expected_parse
            and surface_row.get("rubric_semantics_hash") == expected_rubric
            and surface_row.get("observation_schema_ref") == expected_observation_hash
        ):
            surface_id = surface_row.get("measurement_surface_id")
            if _is_non_empty_string(surface_id):
                matches.add(str(surface_id))
    return matches


def _observation_schema_feature_map(schema: dict[str, Any] | None) -> dict[str, dict[str, Any]]:
    if not isinstance(schema, dict):
        return {}
    return {
        str(feature.get("feature_id")): feature
        for feature in schema.get("features", [])
        if isinstance(feature, dict) and _is_non_empty_string(feature.get("feature_id"))
    }


def _schema_paths(schema: dict[str, Any], root_name: str) -> set[str]:
    paths = {root_name}

    def visit(node: Any, prefix: str) -> None:
        if not isinstance(node, dict):
            return
        properties = node.get("properties")
        if isinstance(properties, dict):
            for key, child in properties.items():
                if not _is_non_empty_string(key):
                    continue
                child_prefix = f"{prefix}.{key}"
                paths.add(child_prefix)
                visit(child, child_prefix)
            return
        for key, child in node.items():
            if key in {"type", "required", "items", "enum", "description", "metadata"}:
                continue
            if not _is_non_empty_string(key):
                continue
            child_prefix = f"{prefix}.{key}"
            paths.add(child_prefix)
            visit(child, child_prefix)

    visit(schema, root_name)
    return paths


def _path_is_valid_for_source(source: str, source_path: str, response_schema: dict[str, Any] | None) -> bool:
    if not _is_non_empty_string(source_path):
        return False
    if source in {"constant", "grader_output"}:
        return True
    if source == "canonical_response":
        if source_path == "canonical_response":
            return True
        if not isinstance(response_schema, dict):
            return False
        return source_path in _schema_paths(response_schema.get("payload_schema", {}), "canonical_response")
    if source == "parse_ir":
        if not isinstance(response_schema, dict):
            return False
        parse_ir = response_schema.get("parse_ir")
        if not isinstance(parse_ir, dict):
            return False
        return source_path in _schema_paths(parse_ir.get("output_schema", {}), "parse_ir")
    return False


def _validate_scoring_rule_params(rule_kind: Any, params: Any, prefix: str, errors: list[str]) -> None:
    if not isinstance(params, dict):
        return
    if rule_kind == "exact_match":
        if not _is_non_empty_string(params.get("logic")):
            errors.append(f"{prefix}_exact_match_logic_invalid")
        _validate_string_list(params.get("outcomes"), f"{prefix}_exact_match_outcomes_invalid", errors, unique=True, non_empty=True)
    elif rule_kind == "choice_lookup":
        if not isinstance(params.get("choices"), dict):
            errors.append(f"{prefix}_choice_lookup_choices_invalid")
    elif rule_kind == "numeric_tolerance":
        if not isinstance(params.get("tolerance"), (int, float)) or float(params.get("tolerance")) < 0:
            errors.append(f"{prefix}_numeric_tolerance_invalid")
    elif rule_kind == "field_projection":
        if not _is_non_empty_string(params.get("target_field")):
            errors.append(f"{prefix}_field_projection_target_field_invalid")
    elif rule_kind == "parse_ir_assertion":
        if not _is_non_empty_string(params.get("assertion")):
            errors.append(f"{prefix}_parse_ir_assertion_invalid")


def _rubric_is_compatible_with_response_schema(
    rubric: dict[str, Any],
    response_schema: dict[str, Any] | None,
) -> bool:
    if response_schema is None:
        return False
    scoring_rules = rubric.get("scoring_rules")
    if isinstance(scoring_rules, list):
        for row in scoring_rules:
            if not isinstance(row, dict):
                return False
            source = row.get("source")
            source_path = row.get("source_path")
            if source in {"canonical_response", "parse_ir"} and not _path_is_valid_for_source(str(source), str(source_path), response_schema):
                return False
    emission = rubric.get("observation_emission")
    if isinstance(emission, dict):
        fields = emission.get("fields")
        if isinstance(fields, list):
            for row in fields:
                if not isinstance(row, dict):
                    return False
                source = row.get("source")
                source_path = row.get("source_path")
                if source in {"canonical_response", "parse_ir"} and not _path_is_valid_for_source(str(source), str(source_path), response_schema):
                    return False
    return True


def _validate_measurement_surface_closed_contract(
    *,
    surface: dict[str, Any],
    observation_schema: dict[str, Any],
    response_schema: dict[str, Any],
    rubric: dict[str, Any],
    prefix: str,
    errors: list[str],
) -> None:
    scoring_rules = rubric.get("scoring_rules")
    if isinstance(scoring_rules, list):
        for idx, row in enumerate(scoring_rules):
            if not isinstance(row, dict):
                continue
            source = row.get("source")
            source_path = row.get("source_path")
            if not _path_is_valid_for_source(str(source), str(source_path), response_schema):
                errors.append(f"{prefix}_scoring_rule_source_path_invalid:{idx}")
    emission = rubric.get("observation_emission")
    if isinstance(emission, dict):
        fields = emission.get("fields")
        if isinstance(fields, list):
            for idx, row in enumerate(fields):
                if not isinstance(row, dict):
                    continue
                source = row.get("source")
                source_path = row.get("source_path")
                if source in {"canonical_response", "parse_ir"} and not _path_is_valid_for_source(
                    str(source),
                    str(source_path),
                    response_schema,
                ):
                    errors.append(f"{prefix}_observation_emission_source_path_invalid:{idx}")


def _validate_entity_tags(
    value: Any,
    *,
    allowed_vocab: dict[str, set[str]],
    prefix: str,
    errors: list[str],
) -> None:
    if value is None:
        return
    if not isinstance(value, dict):
        errors.append(f"{prefix}_not_object")
        return
    for key, row in value.items():
        if not _is_non_empty_string(key):
            errors.append(f"{prefix}_key_invalid")
            continue
        key_str = str(key)
        if key_str not in allowed_vocab:
            errors.append(f"{prefix}_unknown_key:{key_str}")
            continue
        if not _is_non_empty_string(row):
            errors.append(f"{prefix}_value_invalid:{key_str}")
            continue
        row_str = str(row)
        if row_str not in allowed_vocab[key_str]:
            errors.append(f"{prefix}_value_not_allowed:{key_str}:{row_str}")


def _parse_ir_tag_path(derivation_path: str) -> tuple[str, str] | None:
    m = _IR_TAG_PATH_RE.match(derivation_path)
    if m is None:
        return None
    return m.group(1), m.group(2)


def _validate_object_shape(
    row: dict[str, Any],
    required_fields: set[str],
    allowed_fields: set[str],
    prefix: str,
    errors: list[str],
) -> None:
    missing = sorted(required_fields - set(row.keys()))
    if missing:
        errors.append(f"{prefix}_missing_required_fields:{','.join(missing)}")
    unknown = sorted(set(row.keys()) - allowed_fields)
    if unknown:
        errors.append(f"{prefix}_unknown_fields:{','.join(unknown)}")


def _validate_unique_ids(
    rows: list[dict[str, Any]],
    id_field: str,
    registry_name: str,
    errors: list[str],
) -> set[str]:
    ids: set[str] = set()
    for idx, row in enumerate(rows):
        value = row.get(id_field)
        if not _is_non_empty_string(value):
            errors.append(f"{registry_name}[{idx}]_{id_field}_invalid")
            continue
        value_str = str(value)
        if value_str in ids:
            errors.append(f"{registry_name}_duplicate_id:{value_str}")
        ids.add(value_str)
    return ids


def _validate_string_list(
    value: Any,
    error_code: str,
    errors: list[str],
    *,
    unique: bool = False,
    non_empty: bool = False,
    allowed_values: set[str] | None = None,
) -> None:
    if not isinstance(value, list):
        errors.append(error_code)
        return
    if non_empty and not value:
        errors.append(error_code)
        return
    seen: set[str] = set()
    for row in value:
        if not _is_non_empty_string(row):
            errors.append(error_code)
            return
        row_str = str(row)
        if unique and row_str in seen:
            errors.append(error_code)
            return
        seen.add(row_str)
        if allowed_values is not None and row_str not in allowed_values:
            errors.append(error_code)
            return


def _is_valid_derivation_path(derivation_source: str, derivation_path: str) -> bool:
    if _DERIVATION_PATH_RE.match(derivation_path) is None:
        return False
    if derivation_source == "attempt_field":
        return derivation_path.startswith("attempt.")
    if derivation_source == "telemetry_derived":
        return derivation_path.startswith("attempt.") or derivation_path.startswith("telemetry.")
    if derivation_source == "ir_tags":
        return _IR_TAG_PATH_RE.match(derivation_path) is not None
    if derivation_source == "feedback_trace":
        return derivation_path.startswith("feedback.")
    return False


def _is_valid_invariance_source_path(source_path: str) -> bool:
    if _DERIVATION_PATH_RE.match(source_path) is None:
        return False
    return (
        source_path.startswith("item.item_params.signature.")
        or source_path.startswith("item.tags.")
        or source_path.startswith("generator.parameter_schema.")
        or source_path.startswith("generator.tags.")
    )


def _is_non_empty_string(value: Any) -> bool:
    return isinstance(value, str) and value != ""


def _is_sha256_hash(value: Any) -> bool:
    return isinstance(value, str) and _SHA256_RE.match(value) is not None
