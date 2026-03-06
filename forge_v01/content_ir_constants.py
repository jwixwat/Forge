"""Constants for v0.2 content IR contracts."""

from __future__ import annotations

CONTENT_IR_SCHEMA_VERSIONS = {"0.2.0"}

TOP_LEVEL_REQUIRED_FIELDS = {
    "schema_version",
    "release_id",
    "content_ir_version",
    "release_hash",
    "change_manifest",
    "tag_vocab",
    "commitments",
    "factors",
    "edges",
    "observation_schemas",
    "response_schemas",
    "rubrics",
    "measurement_surfaces",
    "probe_families",
    "items",
    "forms",
    "generators",
    "delivery_artifacts",
    "feedback_policies",
    "feedback_policy_precedence",
    "channel_default_feedback_policies",
    "content_migrations",
}

TOP_LEVEL_OPTIONAL_FIELDS = {
    "parent_release_hash",
    "metadata",
}

TOP_LEVEL_ALLOWED_FIELDS = TOP_LEVEL_REQUIRED_FIELDS | TOP_LEVEL_OPTIONAL_FIELDS

EVIDENCE_CHANNELS = {"A_anchor", "B_measurement", "C_learning", "D_shadow"}
ASSISTANCE_MODES = {"closed_book", "open_book", "tool_assisted", "mixed"}

COMMITMENT_STATUS = {"active", "deprecated"}
FACTOR_STATUS = {"active", "deprecated"}

FAMILY_KINDS = {"measurement", "teaching", "holdout", "anchor", "shadow", "adversarial"}
EDGE_KINDS = {"hard_prereq", "soft_prereq", "enrichment", "alternative_path"}
FACTOR_KINDS = {"local_misconception", "relational_confusion", "strategy_process"}
DELIVERY_ARTIFACT_KINDS = {"sentinel_fixture", "anchor_bank"}
FIXTURE_BINDING_KINDS = {"rubric", "generator", "measurement_surface"}
FORM_DELIVERY_ROLES = {"regular", "holdout", "anchor", "shadow"}

FEATURE_VALUE_TYPES = {"categorical", "number", "boolean", "string"}
RESPONSE_KINDS = {"slots", "mcq", "numeric", "structured_explanation", "proof_skeleton", "diagram_graph"}
RESPONSE_AUTHORING_STATUS = {"active_supported", "reserved"}
RUBRIC_GRADER_KINDS = {"deterministic", "llm_parser", "hybrid"}
FEEDBACK_MODES = {"none", "minimal", "full", "delayed"}
CONSUMPTION_POLICIES = {"none", "retire_on_use", "rotate_forms"}
ITEM_SOURCE_KINDS = {"static_bank", "form_bank", "generator_bank"}
GENERATOR_DETERMINISM_MODES = {"seeded", "deterministic_template"}
PROJECTION_TYPES = {"obs_key", "feature_projection", "named_projection"}
INVARIANCE_EXPECTATIONS = {"must_hold", "may_vary"}
INVARIANCE_COMPARATORS = {"eq", "neq", "lte", "gte", "between", "in_set"}
CANONICALIZATION_OPS = {"trim", "lowercase", "sort_keys", "normalize_whitespace", "regex_extract", "map_values"}
PARSE_IR_KINDS = {"none", "deterministic", "llm_constrained"}
OBSERVATION_EMISSION_SOURCES = {"canonical_response", "parse_ir", "grader_output", "constant"}
SCORING_RULE_KINDS = {"exact_match", "choice_lookup", "numeric_tolerance", "field_projection", "parse_ir_assertion"}
SCORING_RULE_SOURCES = {"canonical_response", "parse_ir", "constant"}
MEASUREMENT_SURFACE_COMPATIBILITY = {"safe_minor", "surface_major", "breaking_migration"}
MIGRATION_ENTRY_MODES = {"rename", "split", "merge", "deprecate"}
CHANGE_ENTRY_ENTITY_TYPES = {
    "commitment",
    "factor",
    "probe_family",
    "item",
    "measurement_surface",
    "form",
    "generator",
    "fixture",
}
CHANGE_ENTRY_TYPES = {"add", "deprecate", "rename", "split", "merge", "modify"}
STATE_TRANSFORM_UNCERTAINTY_MODES = {"preserve", "widen", "reset"}
STATE_TRANSFORM_READINESS_MODES = {"preserve", "conservative_recompute", "reset"}

CHANNEL_TAGS = {"anchor", "holdout", "shadow", "adversarial", "measurement", "learning"}
CHANNEL_TAG_TO_EVIDENCE_CHANNEL = {
    "anchor": "A_anchor",
    "measurement": "B_measurement",
    "learning": "C_learning",
    "shadow": "D_shadow",
}
CHANNEL_DEFINING_TAGS = set(CHANNEL_TAG_TO_EVIDENCE_CHANNEL.keys())
ROLE_TAGS = {"holdout", "adversarial"}
RESIDUAL_FLAGS = {"model_mismatch", "sensor_unreliable", "spec_underdetermined"}
CALIBRATION_DERIVATION_SOURCES = {"attempt_field", "telemetry_derived", "ir_tags", "feedback_trace"}

BUNDLE_REGISTRY_FIELDS = {
    "commitments",
    "factors",
    "edges",
    "observation_schemas",
    "response_schemas",
    "rubrics",
    "measurement_surfaces",
    "probe_families",
    "items",
    "forms",
    "generators",
    "delivery_artifacts",
    "feedback_policies",
    "channel_default_feedback_policies",
    "content_migrations",
}

COMMITMENT_REQUIRED_FIELDS = {
    "commitment_id",
    "display_name",
    "description",
    "lineage_id",
    "status",
    "aliases",
    "supersedes",
    "superseded_by",
    "default_feedback_policy_ref",
}
COMMITMENT_OPTIONAL_FIELDS = {"tags", "metadata"}
COMMITMENT_ALLOWED_FIELDS = COMMITMENT_REQUIRED_FIELDS | COMMITMENT_OPTIONAL_FIELDS

FACTOR_REQUIRED_FIELDS = {
    "factor_id",
    "factor_kind",
    "lineage_id",
    "owner",
    "applies_to",
    "evidence_channels_allowed",
    "status",
    "aliases",
    "supersedes",
    "superseded_by",
}
FACTOR_OPTIONAL_FIELDS = {"metadata"}
FACTOR_ALLOWED_FIELDS = FACTOR_REQUIRED_FIELDS | FACTOR_OPTIONAL_FIELDS

FACTOR_APPLIES_TO_ALLOWED_FIELDS = {
    "commitment_ids",
    "probe_family_ids",
    "domains",
    "strata",
}

EDGE_REQUIRED_FIELDS = {
    "edge_id",
    "src_commitment_id",
    "dst_commitment_id",
    "edge_kind",
    "strength_prior",
    "rationale",
    "notes",
}
EDGE_OPTIONAL_FIELDS = {"metadata"}
EDGE_ALLOWED_FIELDS = EDGE_REQUIRED_FIELDS | EDGE_OPTIONAL_FIELDS

OBSERVATION_FEATURE_REQUIRED_FIELDS = {
    "feature_id",
    "value_type",
    "required",
    "allowed_values",
}
OBSERVATION_FEATURE_OPTIONAL_FIELDS = {"metadata"}
OBSERVATION_FEATURE_ALLOWED_FIELDS = OBSERVATION_FEATURE_REQUIRED_FIELDS | OBSERVATION_FEATURE_OPTIONAL_FIELDS

OBSERVATION_SCHEMA_REQUIRED_FIELDS = {
    "observation_schema_id",
    "schema_version",
    "features",
    "outcome_surface_feature_ids",
    "auxiliary_feature_ids",
}
OBSERVATION_SCHEMA_OPTIONAL_FIELDS = {"metadata"}
OBSERVATION_SCHEMA_ALLOWED_FIELDS = OBSERVATION_SCHEMA_REQUIRED_FIELDS | OBSERVATION_SCHEMA_OPTIONAL_FIELDS

CANONICALIZATION_STEP_REQUIRED_FIELDS = {"step_id", "op", "params"}
CANONICALIZATION_STEP_OPTIONAL_FIELDS = {"metadata"}
CANONICALIZATION_STEP_ALLOWED_FIELDS = CANONICALIZATION_STEP_REQUIRED_FIELDS | CANONICALIZATION_STEP_OPTIONAL_FIELDS

PARSE_IR_REQUIRED_FIELDS = {"parse_ir_id", "parser_kind", "output_schema", "uncertainty_fields"}
PARSE_IR_OPTIONAL_FIELDS = {"metadata"}
PARSE_IR_ALLOWED_FIELDS = PARSE_IR_REQUIRED_FIELDS | PARSE_IR_OPTIONAL_FIELDS

OBSERVATION_EMISSION_FIELD_REQUIRED_FIELDS = {"feature_id", "source", "source_path"}
OBSERVATION_EMISSION_FIELD_OPTIONAL_FIELDS = {"metadata"}
OBSERVATION_EMISSION_FIELD_ALLOWED_FIELDS = (
    OBSERVATION_EMISSION_FIELD_REQUIRED_FIELDS | OBSERVATION_EMISSION_FIELD_OPTIONAL_FIELDS
)

OBSERVATION_EMISSION_REQUIRED_FIELDS = {"emission_id", "fields"}
OBSERVATION_EMISSION_OPTIONAL_FIELDS = {"metadata"}
OBSERVATION_EMISSION_ALLOWED_FIELDS = OBSERVATION_EMISSION_REQUIRED_FIELDS | OBSERVATION_EMISSION_OPTIONAL_FIELDS

RESPONSE_SCHEMA_REQUIRED_FIELDS = {
    "response_schema_id",
    "response_kind",
    "authoring_status",
    "payload_schema",
    "canonicalization_steps",
    "parse_ir",
}
RESPONSE_SCHEMA_OPTIONAL_FIELDS = {"metadata"}
RESPONSE_SCHEMA_ALLOWED_FIELDS = RESPONSE_SCHEMA_REQUIRED_FIELDS | RESPONSE_SCHEMA_OPTIONAL_FIELDS

SCORING_RULE_REQUIRED_FIELDS = {"rule_id", "rule_kind", "source", "source_path", "params"}
SCORING_RULE_OPTIONAL_FIELDS = {"metadata"}
SCORING_RULE_ALLOWED_FIELDS = SCORING_RULE_REQUIRED_FIELDS | SCORING_RULE_OPTIONAL_FIELDS

RUBRIC_REQUIRED_FIELDS = {
    "rubric_id",
    "deterministic",
    "grader_kind",
    "observation_schema_ref",
    "scoring_rules",
    "observation_emission",
    "rubric_semantics_version",
}
RUBRIC_OPTIONAL_FIELDS = {"metadata"}
RUBRIC_ALLOWED_FIELDS = RUBRIC_REQUIRED_FIELDS | RUBRIC_OPTIONAL_FIELDS

MEASUREMENT_SURFACE_OBS_BINDING_REQUIRED_FIELDS = {"obs_encoder_version", "hypothesis_space_hash"}
MEASUREMENT_SURFACE_OBS_BINDING_OPTIONAL_FIELDS = {"metadata"}
MEASUREMENT_SURFACE_OBS_BINDING_ALLOWED_FIELDS = (
    MEASUREMENT_SURFACE_OBS_BINDING_REQUIRED_FIELDS | MEASUREMENT_SURFACE_OBS_BINDING_OPTIONAL_FIELDS
)

MEASUREMENT_SURFACE_REQUIRED_FIELDS = {
    "measurement_surface_id",
    "observation_schema_ref",
    "response_schema_ref",
    "rubric_ref",
    "observation_schema_semantics_hash",
    "canonicalization_hash",
    "parse_ir_hash",
    "rubric_semantics_hash",
    "obs_binding",
    "compatibility_class",
}
MEASUREMENT_SURFACE_OPTIONAL_FIELDS = {"metadata"}
MEASUREMENT_SURFACE_ALLOWED_FIELDS = MEASUREMENT_SURFACE_REQUIRED_FIELDS | MEASUREMENT_SURFACE_OPTIONAL_FIELDS

CHANNEL_CONSTRAINT_REQUIRED_FIELDS = {"channel", "feedback_mode", "hints_allowed", "max_hints"}
CHANNEL_CONSTRAINT_OPTIONAL_FIELDS = {"metadata"}
CHANNEL_CONSTRAINT_ALLOWED_FIELDS = CHANNEL_CONSTRAINT_REQUIRED_FIELDS | CHANNEL_CONSTRAINT_OPTIONAL_FIELDS

ITEM_SOURCE_REQUIRED_FIELDS = {"source_kind", "refs"}
ITEM_SOURCE_OPTIONAL_FIELDS = {"weights", "metadata"}
ITEM_SOURCE_ALLOWED_FIELDS = ITEM_SOURCE_REQUIRED_FIELDS | ITEM_SOURCE_OPTIONAL_FIELDS

CALIBRATION_INCLUSION_REQUIRED_FIELDS = {
    "eligible_channels",
    "eligible_assistance_modes",
    "require_closed_book",
    "exclude_residual_flags",
}
CALIBRATION_INCLUSION_OPTIONAL_FIELDS = {"metadata"}
CALIBRATION_INCLUSION_ALLOWED_FIELDS = CALIBRATION_INCLUSION_REQUIRED_FIELDS | CALIBRATION_INCLUSION_OPTIONAL_FIELDS

CALIBRATION_AXIS_REQUIRED_FIELDS = {"axis_id", "derivation_source", "derivation_path", "allowed_values", "unknown_value"}
CALIBRATION_AXIS_OPTIONAL_FIELDS = {"metadata"}
CALIBRATION_AXIS_ALLOWED_FIELDS = CALIBRATION_AXIS_REQUIRED_FIELDS | CALIBRATION_AXIS_OPTIONAL_FIELDS

CALIBRATION_TARGET_RULE_REQUIRED_FIELDS = {"target", "source_features"}
CALIBRATION_TARGET_RULE_OPTIONAL_FIELDS = {"rule", "metadata"}
CALIBRATION_TARGET_RULE_ALLOWED_FIELDS = CALIBRATION_TARGET_RULE_REQUIRED_FIELDS | CALIBRATION_TARGET_RULE_OPTIONAL_FIELDS

CALIBRATION_TARGET_REQUIRED_FIELDS = {"projection_id", "projection_type", "source_surface", "mapping_rules"}
CALIBRATION_TARGET_OPTIONAL_FIELDS = {"metadata"}
CALIBRATION_TARGET_ALLOWED_FIELDS = CALIBRATION_TARGET_REQUIRED_FIELDS | CALIBRATION_TARGET_OPTIONAL_FIELDS

CALIBRATION_POOL_POLICY_REQUIRED_FIELDS = {
    "baseline_assistance_modes",
    "monitor_only_assistance_modes",
    "stratify_by_assistance_mode",
}
CALIBRATION_POOL_POLICY_OPTIONAL_FIELDS = {"metadata"}
CALIBRATION_POOL_POLICY_ALLOWED_FIELDS = (
    CALIBRATION_POOL_POLICY_REQUIRED_FIELDS | CALIBRATION_POOL_POLICY_OPTIONAL_FIELDS
)

CALIBRATION_CONTRACT_REQUIRED_FIELDS = {
    "inclusion_rules",
    "strata_axes",
    "calibration_target_projection",
    "calibration_pool_policy",
}
CALIBRATION_CONTRACT_OPTIONAL_FIELDS = {"metadata"}
CALIBRATION_CONTRACT_ALLOWED_FIELDS = CALIBRATION_CONTRACT_REQUIRED_FIELDS | CALIBRATION_CONTRACT_OPTIONAL_FIELDS

ASSISTANCE_CONTRACT_REQUIRED_FIELDS = {
    "allowed_assistance_modes",
    "diagnostic_eligible_assistance_modes",
    "measurement_preserving_assistance_modes",
    "tool_use_allowed",
}
ASSISTANCE_CONTRACT_OPTIONAL_FIELDS = {"metadata"}
ASSISTANCE_CONTRACT_ALLOWED_FIELDS = ASSISTANCE_CONTRACT_REQUIRED_FIELDS | ASSISTANCE_CONTRACT_OPTIONAL_FIELDS

PROBE_FAMILY_REQUIRED_FIELDS = {
    "probe_family_id",
    "commitment_id",
    "family_kind",
    "target_factors",
    "measurement_surface_refs",
    "allowed_channels",
    "channel_constraints",
    "item_source",
    "assistance_contract",
    "calibration_contract",
    "default_feedback_policy_ref",
}
PROBE_FAMILY_OPTIONAL_FIELDS = {"invariance_contract", "tags", "metadata"}
PROBE_FAMILY_ALLOWED_FIELDS = PROBE_FAMILY_REQUIRED_FIELDS | PROBE_FAMILY_OPTIONAL_FIELDS

TARGET_FACTOR_BINDING_REQUIRED_FIELDS = {"primary_target_factors"}
TARGET_FACTOR_BINDING_OPTIONAL_FIELDS = {"secondary_target_factors", "metadata"}
TARGET_FACTOR_BINDING_ALLOWED_FIELDS = (
    TARGET_FACTOR_BINDING_REQUIRED_FIELDS | TARGET_FACTOR_BINDING_OPTIONAL_FIELDS
)

ITEM_SIGNATURE_REQUIRED_FIELDS = {"prompt_len_tokens", "slots_count", "binding_ops", "step_count_est"}
ITEM_SIGNATURE_OPTIONAL_FIELDS = {"metadata"}
ITEM_SIGNATURE_ALLOWED_FIELDS = ITEM_SIGNATURE_REQUIRED_FIELDS | ITEM_SIGNATURE_OPTIONAL_FIELDS

ITEM_PARAMS_REQUIRED_FIELDS = {"difficulty_offset_init", "ambiguity_risk_init", "signature"}
ITEM_PARAMS_OPTIONAL_FIELDS = {"metadata"}
ITEM_PARAMS_ALLOWED_FIELDS = ITEM_PARAMS_REQUIRED_FIELDS | ITEM_PARAMS_OPTIONAL_FIELDS

ITEM_GRADING_MATERIAL_REQUIRED_FIELDS = {"response_kind"}
ITEM_GRADING_MATERIAL_OPTIONAL_FIELDS = {"slot_answer_key", "correct_choice_id", "numeric_answer", "metadata"}
ITEM_GRADING_MATERIAL_ALLOWED_FIELDS = (
    ITEM_GRADING_MATERIAL_REQUIRED_FIELDS | ITEM_GRADING_MATERIAL_OPTIONAL_FIELDS
)

ITEM_REQUIRED_FIELDS = {
    "item_id",
    "probe_family_id",
    "measurement_surface_ref",
    "response_schema_ref",
    "rubric_ref",
    "target_factor_binding",
    "prompt",
    "channel_tags",
    "role_tags",
    "form_memberships",
    "item_params",
    "grading_material",
    "feedback_policy_ref",
    "active",
}
ITEM_OPTIONAL_FIELDS = {"dual_use_allowed", "tags", "metadata"}
ITEM_ALLOWED_FIELDS = ITEM_REQUIRED_FIELDS | ITEM_OPTIONAL_FIELDS

FORM_REQUIRED_FIELDS = {
    "form_id",
    "items",
    "evidence_channel",
    "delivery_role",
    "fixed_form",
    "closed_book_only",
    "max_presented_items",
    "consumption_policy",
    "feedback_policy_ref",
    "form_tags",
    "active",
}
FORM_OPTIONAL_FIELDS = {"tags", "metadata"}
FORM_ALLOWED_FIELDS = FORM_REQUIRED_FIELDS | FORM_OPTIONAL_FIELDS

GENERATOR_REQUIRED_FIELDS = {
    "generator_id",
    "probe_family_id",
    "generator_version",
    "target_factor_binding",
    "parameter_schema",
    "determinism_contract",
    "invariance_contract",
    "grading_contract",
    "instance_binding_contract",
    "active",
}
GENERATOR_OPTIONAL_FIELDS = {"adversarial_contract", "tags", "metadata"}
GENERATOR_ALLOWED_FIELDS = GENERATOR_REQUIRED_FIELDS | GENERATOR_OPTIONAL_FIELDS

GENERATOR_DETERMINISM_REQUIRED_FIELDS = {"mode", "seed_strategy"}
GENERATOR_DETERMINISM_OPTIONAL_FIELDS = {"metadata"}
GENERATOR_DETERMINISM_ALLOWED_FIELDS = (
    GENERATOR_DETERMINISM_REQUIRED_FIELDS | GENERATOR_DETERMINISM_OPTIONAL_FIELDS
)

GENERATOR_SOLUTION_MATERIAL_REQUIRED_FIELDS = {"response_kind", "derivation_source", "source_path", "required_fields"}
GENERATOR_SOLUTION_MATERIAL_OPTIONAL_FIELDS = {"metadata"}
GENERATOR_SOLUTION_MATERIAL_ALLOWED_FIELDS = (
    GENERATOR_SOLUTION_MATERIAL_REQUIRED_FIELDS | GENERATOR_SOLUTION_MATERIAL_OPTIONAL_FIELDS
)

GENERATOR_SOLUTION_DERIVATION_SOURCES = {"generator_params", "rendered_payload", "answer_artifact"}

GENERATOR_GRADING_CONTRACT_REQUIRED_FIELDS = {
    "measurement_surface_ref",
    "rubric_ref",
    "response_schema_ref",
    "solution_material_contract",
}
GENERATOR_GRADING_CONTRACT_OPTIONAL_FIELDS = {"metadata"}
GENERATOR_GRADING_CONTRACT_ALLOWED_FIELDS = (
    GENERATOR_GRADING_CONTRACT_REQUIRED_FIELDS | GENERATOR_GRADING_CONTRACT_OPTIONAL_FIELDS
)

GENERATOR_INSTANCE_BINDING_REQUIRED_FIELDS = {
    "item_instance_id_required",
    "generator_id_required",
    "generator_version_required",
    "seed_required",
    "rendered_payload_hash_required",
    "artifact_pointer_required",
}
GENERATOR_INSTANCE_BINDING_OPTIONAL_FIELDS = {"metadata"}
GENERATOR_INSTANCE_BINDING_ALLOWED_FIELDS = (
    GENERATOR_INSTANCE_BINDING_REQUIRED_FIELDS | GENERATOR_INSTANCE_BINDING_OPTIONAL_FIELDS
)

GENERATOR_PERTURBATION_AXIS_REQUIRED_FIELDS = {"axis_id", "description", "allowed_values"}
GENERATOR_PERTURBATION_AXIS_OPTIONAL_FIELDS = {"metadata"}
GENERATOR_PERTURBATION_AXIS_ALLOWED_FIELDS = (
    GENERATOR_PERTURBATION_AXIS_REQUIRED_FIELDS | GENERATOR_PERTURBATION_AXIS_OPTIONAL_FIELDS
)

ADVERSARIAL_GENERATOR_CONTRACT_REQUIRED_FIELDS = {
    "generation_mode",
    "perturbation_axes",
    "max_perturbation_axes_per_instance",
}
ADVERSARIAL_GENERATOR_CONTRACT_OPTIONAL_FIELDS = {"metadata"}
ADVERSARIAL_GENERATOR_CONTRACT_ALLOWED_FIELDS = (
    ADVERSARIAL_GENERATOR_CONTRACT_REQUIRED_FIELDS | ADVERSARIAL_GENERATOR_CONTRACT_OPTIONAL_FIELDS
)

FEEDBACK_POLICY_REQUIRED_FIELDS = {"feedback_policy_id", "rules", "active"}
FEEDBACK_POLICY_OPTIONAL_FIELDS = {"metadata"}
FEEDBACK_POLICY_ALLOWED_FIELDS = FEEDBACK_POLICY_REQUIRED_FIELDS | FEEDBACK_POLICY_OPTIONAL_FIELDS

CHANNEL_DEFAULT_FEEDBACK_REQUIRED_FIELDS = {"channel", "feedback_policy_ref"}
CHANNEL_DEFAULT_FEEDBACK_OPTIONAL_FIELDS = {"metadata"}
CHANNEL_DEFAULT_FEEDBACK_ALLOWED_FIELDS = (
    CHANNEL_DEFAULT_FEEDBACK_REQUIRED_FIELDS | CHANNEL_DEFAULT_FEEDBACK_OPTIONAL_FIELDS
)

FEEDBACK_POLICY_PRECEDENCE_REQUIRED_FIELDS = {"order"}
FEEDBACK_POLICY_PRECEDENCE_OPTIONAL_FIELDS = {"metadata"}
FEEDBACK_POLICY_PRECEDENCE_ALLOWED_FIELDS = (
    FEEDBACK_POLICY_PRECEDENCE_REQUIRED_FIELDS | FEEDBACK_POLICY_PRECEDENCE_OPTIONAL_FIELDS
)
FEEDBACK_POLICY_PRECEDENCE_ORDER = ["item", "form", "probe_family", "commitment", "channel_default"]

CHANGE_MANIFEST_ENTRY_REQUIRED_FIELDS = {"entity_type", "entity_id", "change_type"}
CHANGE_MANIFEST_ENTRY_OPTIONAL_FIELDS = {"metadata"}
CHANGE_MANIFEST_ENTRY_ALLOWED_FIELDS = CHANGE_MANIFEST_ENTRY_REQUIRED_FIELDS | CHANGE_MANIFEST_ENTRY_OPTIONAL_FIELDS

CHANGE_MANIFEST_REQUIRED_FIELDS = {"added", "deprecated", "modified"}
CHANGE_MANIFEST_OPTIONAL_FIELDS = {"metadata"}
CHANGE_MANIFEST_ALLOWED_FIELDS = CHANGE_MANIFEST_REQUIRED_FIELDS | CHANGE_MANIFEST_OPTIONAL_FIELDS

DELIVERY_TAG_VOCAB_REQUIRED_FIELDS = {"form_tags", "generator_tags", "artifact_tags"}
DELIVERY_TAG_VOCAB_OPTIONAL_FIELDS = {"metadata"}
DELIVERY_TAG_VOCAB_ALLOWED_FIELDS = DELIVERY_TAG_VOCAB_REQUIRED_FIELDS | DELIVERY_TAG_VOCAB_OPTIONAL_FIELDS

TAG_VOCAB_REQUIRED_FIELDS = {"item_tags", "family_tags", "commitment_tags", "delivery_tags"}
TAG_VOCAB_OPTIONAL_FIELDS = {"metadata"}
TAG_VOCAB_ALLOWED_FIELDS = TAG_VOCAB_REQUIRED_FIELDS | TAG_VOCAB_OPTIONAL_FIELDS

INVARIANCE_AXIS_REQUIRED_FIELDS = {"axis_id", "expectation", "rationale"}
INVARIANCE_AXIS_OPTIONAL_FIELDS = {"metadata"}
INVARIANCE_AXIS_ALLOWED_FIELDS = INVARIANCE_AXIS_REQUIRED_FIELDS | INVARIANCE_AXIS_OPTIONAL_FIELDS

INVARIANCE_CONTRACT_REQUIRED_FIELDS = {"axes"}
INVARIANCE_CONTRACT_OPTIONAL_FIELDS = {"operational_constraints", "metadata"}
INVARIANCE_CONTRACT_ALLOWED_FIELDS = INVARIANCE_CONTRACT_REQUIRED_FIELDS | INVARIANCE_CONTRACT_OPTIONAL_FIELDS

INVARIANCE_OPERATIONAL_REQUIRED_FIELDS = {"constraint_id", "source_path", "comparator", "value"}
INVARIANCE_OPERATIONAL_OPTIONAL_FIELDS = {"tolerance", "metadata"}
INVARIANCE_OPERATIONAL_ALLOWED_FIELDS = (
    INVARIANCE_OPERATIONAL_REQUIRED_FIELDS | INVARIANCE_OPERATIONAL_OPTIONAL_FIELDS
)

DELIVERY_ARTIFACT_REQUIRED_FIELDS = {"artifact_id", "artifact_kind", "bindings", "active"}
DELIVERY_ARTIFACT_OPTIONAL_FIELDS = {"tags", "metadata"}
DELIVERY_ARTIFACT_ALLOWED_FIELDS = DELIVERY_ARTIFACT_REQUIRED_FIELDS | DELIVERY_ARTIFACT_OPTIONAL_FIELDS

FIXTURE_BINDING_REQUIRED_FIELDS = {"binding_kind", "ref_id"}
FIXTURE_BINDING_OPTIONAL_FIELDS = {"metadata"}
FIXTURE_BINDING_ALLOWED_FIELDS = FIXTURE_BINDING_REQUIRED_FIELDS | FIXTURE_BINDING_OPTIONAL_FIELDS

MIGRATION_MAPPING_REQUIRED_FIELDS = {"source_ids", "target_ids", "mode"}
MIGRATION_MAPPING_OPTIONAL_FIELDS = {"rule", "metadata"}
MIGRATION_MAPPING_ALLOWED_FIELDS = MIGRATION_MAPPING_REQUIRED_FIELDS | MIGRATION_MAPPING_OPTIONAL_FIELDS

STATE_TRANSFORM_POLICY_REQUIRED_FIELDS = {"policy_id", "uncertainty_mode", "readiness_mode"}
STATE_TRANSFORM_POLICY_OPTIONAL_FIELDS = {"metadata"}
STATE_TRANSFORM_POLICY_ALLOWED_FIELDS = (
    STATE_TRANSFORM_POLICY_REQUIRED_FIELDS | STATE_TRANSFORM_POLICY_OPTIONAL_FIELDS
)

CONTENT_MIGRATION_REQUIRED_FIELDS = {
    "migration_id",
    "from_release_hash",
    "to_release_hash",
    "commitment_mapping",
    "factor_mapping",
    "probe_family_mapping",
    "item_mapping",
    "measurement_surface_mapping",
    "state_transform_policy",
    "transform_hash",
}
CONTENT_MIGRATION_OPTIONAL_FIELDS = {"metadata"}
CONTENT_MIGRATION_ALLOWED_FIELDS = CONTENT_MIGRATION_REQUIRED_FIELDS | CONTENT_MIGRATION_OPTIONAL_FIELDS
