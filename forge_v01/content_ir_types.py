"""Typed structures for v0.2 content IR entities."""

from __future__ import annotations

from typing import Any, Literal, NotRequired, TypedDict


class ObservationFeatureSpec(TypedDict):
    feature_id: str
    value_type: Literal["categorical", "number", "boolean", "string"]
    required: bool
    allowed_values: list[Any]
    metadata: NotRequired[dict[str, Any]]


class ObservationSchemaSpec(TypedDict):
    observation_schema_id: str
    schema_version: str
    features: list[ObservationFeatureSpec]
    outcome_surface_feature_ids: list[str]
    auxiliary_feature_ids: list[str]
    metadata: NotRequired[dict[str, Any]]


class CanonicalizationStepSpec(TypedDict):
    step_id: str
    op: Literal["trim", "lowercase", "sort_keys", "normalize_whitespace", "regex_extract", "map_values"]
    params: dict[str, Any]
    metadata: NotRequired[dict[str, Any]]


class ParseIRSpec(TypedDict):
    parse_ir_id: str
    parser_kind: Literal["none", "deterministic", "llm_constrained"]
    output_schema: dict[str, Any]
    uncertainty_fields: list[str]
    metadata: NotRequired[dict[str, Any]]


class ObservationEmissionFieldSpec(TypedDict):
    feature_id: str
    source: Literal["canonical_response", "parse_ir", "grader_output", "constant"]
    source_path: str
    metadata: NotRequired[dict[str, Any]]


class ObservationEmissionSpec(TypedDict):
    emission_id: str
    fields: list[ObservationEmissionFieldSpec]
    metadata: NotRequired[dict[str, Any]]


class ResponseSchemaSpec(TypedDict):
    response_schema_id: str
    response_kind: Literal["slots", "mcq", "numeric", "structured_explanation", "proof_skeleton", "diagram_graph"]
    authoring_status: Literal["active_supported", "reserved"]
    payload_schema: dict[str, Any]
    canonicalization_steps: list[CanonicalizationStepSpec]
    parse_ir: ParseIRSpec
    metadata: NotRequired[dict[str, Any]]


class ScoringRuleSpec(TypedDict):
    rule_id: str
    rule_kind: Literal["exact_match", "choice_lookup", "numeric_tolerance", "field_projection", "parse_ir_assertion"]
    source: Literal["canonical_response", "parse_ir", "constant"]
    source_path: str
    params: dict[str, Any]
    metadata: NotRequired[dict[str, Any]]


class RubricSpec(TypedDict):
    rubric_id: str
    deterministic: bool
    grader_kind: Literal["deterministic", "llm_parser", "hybrid"]
    observation_schema_ref: str
    scoring_rules: list[ScoringRuleSpec]
    observation_emission: ObservationEmissionSpec
    rubric_semantics_version: str
    metadata: NotRequired[dict[str, Any]]


class MeasurementSurfaceObsBindingSpec(TypedDict):
    obs_encoder_version: str
    hypothesis_space_hash: str
    metadata: NotRequired[dict[str, Any]]


class MeasurementSurfaceSpec(TypedDict):
    measurement_surface_id: str
    observation_schema_ref: str
    response_schema_ref: str
    rubric_ref: str
    observation_schema_semantics_hash: str
    canonicalization_hash: str
    parse_ir_hash: str
    rubric_semantics_hash: str
    obs_binding: MeasurementSurfaceObsBindingSpec
    compatibility_class: Literal["safe_minor", "surface_major", "breaking_migration"]
    metadata: NotRequired[dict[str, Any]]


class CalibrationInclusionRulesSpec(TypedDict):
    eligible_channels: list[Literal["A_anchor", "B_measurement", "C_learning", "D_shadow"]]
    eligible_assistance_modes: list[Literal["closed_book", "open_book", "tool_assisted", "mixed"]]
    require_closed_book: bool
    exclude_residual_flags: list[Literal["model_mismatch", "sensor_unreliable", "spec_underdetermined"]]
    metadata: NotRequired[dict[str, Any]]


class CalibrationStrataAxisSpec(TypedDict):
    axis_id: str
    derivation_source: Literal["attempt_field", "telemetry_derived", "ir_tags", "feedback_trace"]
    derivation_path: str
    allowed_values: list[str]
    unknown_value: str
    metadata: NotRequired[dict[str, Any]]


class CalibrationTargetProjectionRuleSpec(TypedDict):
    target: str
    source_features: list[str]
    rule: NotRequired[str]
    metadata: NotRequired[dict[str, Any]]


class CalibrationTargetProjectionSpec(TypedDict):
    projection_id: str
    projection_type: Literal["obs_key", "feature_projection", "named_projection"]
    source_surface: str
    mapping_rules: list[CalibrationTargetProjectionRuleSpec]
    metadata: NotRequired[dict[str, Any]]


class CalibrationContractSpec(TypedDict):
    inclusion_rules: CalibrationInclusionRulesSpec
    strata_axes: list[CalibrationStrataAxisSpec]
    calibration_target_projection: CalibrationTargetProjectionSpec
    calibration_pool_policy: "CalibrationPoolPolicySpec"
    metadata: NotRequired[dict[str, Any]]


class CalibrationPoolPolicySpec(TypedDict):
    baseline_assistance_modes: list[Literal["closed_book", "open_book", "tool_assisted", "mixed"]]
    monitor_only_assistance_modes: list[Literal["closed_book", "open_book", "tool_assisted", "mixed"]]
    stratify_by_assistance_mode: bool
    metadata: NotRequired[dict[str, Any]]


class AssistanceContractSpec(TypedDict):
    allowed_assistance_modes: list[Literal["closed_book", "open_book", "tool_assisted", "mixed"]]
    diagnostic_eligible_assistance_modes: list[Literal["closed_book", "open_book", "tool_assisted", "mixed"]]
    measurement_preserving_assistance_modes: list[Literal["closed_book", "open_book", "tool_assisted", "mixed"]]
    tool_use_allowed: bool
    metadata: NotRequired[dict[str, Any]]


class ChannelConstraintSpec(TypedDict):
    channel: Literal["A_anchor", "B_measurement", "C_learning", "D_shadow"]
    feedback_mode: Literal["none", "minimal", "full", "delayed"]
    hints_allowed: bool
    max_hints: int
    metadata: NotRequired[dict[str, Any]]


class ItemSourceSpec(TypedDict):
    source_kind: Literal["static_bank", "form_bank", "generator_bank"]
    refs: list[str]
    weights: NotRequired[list[float]]
    metadata: NotRequired[dict[str, Any]]


class DeliveryRolePolicySpec(TypedDict):
    allow_dual_use: bool
    metadata: NotRequired[dict[str, Any]]


class DeliveryTagVocabularySpec(TypedDict):
    form_tags: dict[str, list[str]]
    generator_tags: dict[str, list[str]]
    artifact_tags: dict[str, list[str]]
    metadata: NotRequired[dict[str, Any]]


class TagVocabularySpec(TypedDict):
    item_tags: dict[str, list[str]]
    family_tags: dict[str, list[str]]
    commitment_tags: dict[str, list[str]]
    delivery_tags: DeliveryTagVocabularySpec
    metadata: NotRequired[dict[str, Any]]


class InvarianceAxisSpec(TypedDict):
    axis_id: str
    expectation: Literal["must_hold", "may_vary"]
    rationale: str
    metadata: NotRequired[dict[str, Any]]


class InvarianceOperationalConstraintSpec(TypedDict):
    constraint_id: str
    source_path: str
    comparator: Literal["eq", "neq", "lte", "gte", "between", "in_set"]
    value: Any
    tolerance: NotRequired[float]
    metadata: NotRequired[dict[str, Any]]


class InvarianceContractSpec(TypedDict):
    axes: list[InvarianceAxisSpec]
    operational_constraints: NotRequired[list[InvarianceOperationalConstraintSpec]]
    metadata: NotRequired[dict[str, Any]]


class CommitmentSpec(TypedDict):
    commitment_id: str
    display_name: str
    description: str
    lineage_id: str
    status: Literal["active", "deprecated"]
    aliases: list[str]
    supersedes: list[str]
    superseded_by: list[str]
    default_feedback_policy_ref: str | None
    tags: NotRequired[dict[str, str]]
    metadata: NotRequired[dict[str, Any]]


class FactorAppliesToSpec(TypedDict):
    commitment_ids: NotRequired[list[str]]
    probe_family_ids: NotRequired[list[str]]
    domains: NotRequired[list[str]]
    strata: NotRequired[list[str]]


class FactorSpec(TypedDict):
    factor_id: str
    factor_kind: Literal["local_misconception", "relational_confusion", "strategy_process"]
    lineage_id: str
    owner: str
    applies_to: FactorAppliesToSpec
    evidence_channels_allowed: list[Literal["A_anchor", "B_measurement", "C_learning", "D_shadow"]]
    status: Literal["active", "deprecated"]
    aliases: list[str]
    supersedes: list[str]
    superseded_by: list[str]
    metadata: NotRequired[dict[str, Any]]


class EdgeSpec(TypedDict):
    edge_id: str
    src_commitment_id: str
    dst_commitment_id: str
    edge_kind: Literal["hard_prereq", "soft_prereq", "enrichment", "alternative_path"]
    strength_prior: float
    rationale: str
    notes: str
    metadata: NotRequired[dict[str, Any]]


class ProbeFamilySpec(TypedDict):
    probe_family_id: str
    commitment_id: str
    family_kind: Literal["measurement", "teaching", "holdout", "anchor", "shadow", "adversarial"]
    target_factors: list[str]
    measurement_surface_refs: list[str]
    allowed_channels: list[Literal["A_anchor", "B_measurement", "C_learning", "D_shadow"]]
    channel_constraints: list[ChannelConstraintSpec]
    item_source: ItemSourceSpec
    assistance_contract: AssistanceContractSpec
    calibration_contract: CalibrationContractSpec
    default_feedback_policy_ref: str | None
    invariance_contract: NotRequired[InvarianceContractSpec]
    tags: NotRequired[dict[str, str]]
    metadata: NotRequired[dict[str, Any]]


class TargetFactorBindingSpec(TypedDict):
    primary_target_factors: list[str]
    secondary_target_factors: NotRequired[list[str]]
    metadata: NotRequired[dict[str, Any]]


class ItemSignatureSpec(TypedDict):
    prompt_len_tokens: int
    slots_count: int
    binding_ops: int
    step_count_est: int
    metadata: NotRequired[dict[str, Any]]


class ItemParamsSpec(TypedDict):
    difficulty_offset_init: float
    ambiguity_risk_init: float
    signature: ItemSignatureSpec
    metadata: NotRequired[dict[str, Any]]


class ItemGradingMaterialSpec(TypedDict):
    response_kind: Literal["slots", "mcq", "numeric"]
    slot_answer_key: NotRequired[list[str]]
    correct_choice_id: NotRequired[str]
    allowed_choice_ids: NotRequired[list[str]]
    numeric_answer: NotRequired[float]
    metadata: NotRequired[dict[str, Any]]


class ItemSpec(TypedDict):
    item_id: str
    probe_family_id: str
    measurement_surface_ref: str
    response_schema_ref: str
    rubric_ref: str
    target_factor_binding: TargetFactorBindingSpec
    prompt: str
    channel_tags: list[Literal["anchor", "holdout", "shadow", "adversarial", "measurement", "learning"]]
    role_tags: list[Literal["holdout", "adversarial"]]
    form_memberships: list[str]
    item_params: ItemParamsSpec
    grading_material: ItemGradingMaterialSpec
    feedback_policy_ref: str | None
    dual_use_allowed: NotRequired[bool]
    active: bool
    tags: NotRequired[dict[str, str]]
    metadata: NotRequired[dict[str, Any]]


class FormSpec(TypedDict):
    form_id: str
    items: list[str]
    evidence_channel: Literal["A_anchor", "B_measurement", "C_learning", "D_shadow"]
    delivery_role: Literal["regular", "holdout", "anchor", "shadow"]
    fixed_form: bool
    closed_book_only: bool
    max_presented_items: int
    consumption_policy: Literal["none", "retire_on_use", "rotate_forms"]
    feedback_policy_ref: str | None
    form_tags: list[str]
    tags: NotRequired[dict[str, str]]
    active: bool
    metadata: NotRequired[dict[str, Any]]


class GeneratorDeterminismContractSpec(TypedDict):
    mode: Literal["seeded", "deterministic_template"]
    seed_strategy: str
    metadata: NotRequired[dict[str, Any]]


class GeneratorGradingContractSpec(TypedDict):
    measurement_surface_ref: str
    rubric_ref: str
    response_schema_ref: str
    solution_material_contract: "GeneratorSolutionMaterialContractSpec"
    metadata: NotRequired[dict[str, Any]]


class GeneratorSolutionMaterialContractSpec(TypedDict):
    response_kind: Literal["slots", "mcq", "numeric"]
    derivation_source: Literal["generator_params", "rendered_payload", "answer_artifact"]
    source_path: str
    required_fields: list[str]
    metadata: NotRequired[dict[str, Any]]


class GeneratedInstanceBindingContractSpec(TypedDict):
    item_instance_id_required: bool
    generator_id_required: bool
    generator_version_required: bool
    seed_required: bool
    rendered_payload_hash_required: bool
    artifact_pointer_required: bool
    metadata: NotRequired[dict[str, Any]]


class GeneratorPerturbationAxisSpec(TypedDict):
    axis_id: str
    description: str
    allowed_values: list[str]
    metadata: NotRequired[dict[str, Any]]


class AdversarialGeneratorContractSpec(TypedDict):
    generation_mode: Literal["seeded_minimal_pairs"]
    perturbation_axes: list[GeneratorPerturbationAxisSpec]
    max_perturbation_axes_per_instance: int
    metadata: NotRequired[dict[str, Any]]


class GeneratorSpec(TypedDict):
    generator_id: str
    probe_family_id: str
    generator_version: str
    target_factor_binding: TargetFactorBindingSpec
    parameter_schema: dict[str, Any]
    determinism_contract: GeneratorDeterminismContractSpec
    invariance_contract: InvarianceContractSpec
    grading_contract: GeneratorGradingContractSpec
    instance_binding_contract: GeneratedInstanceBindingContractSpec
    adversarial_contract: NotRequired[AdversarialGeneratorContractSpec]
    tags: NotRequired[dict[str, str]]
    active: bool
    metadata: NotRequired[dict[str, Any]]


class FeedbackPolicySpec(TypedDict):
    feedback_policy_id: str
    rules: dict[str, Any]
    active: bool
    metadata: NotRequired[dict[str, Any]]


class ChannelDefaultFeedbackPolicySpec(TypedDict):
    channel: Literal["A_anchor", "B_measurement", "C_learning", "D_shadow"]
    feedback_policy_ref: str
    metadata: NotRequired[dict[str, Any]]


class FeedbackPolicyPrecedenceSpec(TypedDict):
    order: list[Literal["item", "form", "probe_family", "commitment", "channel_default"]]
    metadata: NotRequired[dict[str, Any]]


class ChangeManifestEntrySpec(TypedDict):
    entity_type: Literal[
        "commitment",
        "factor",
        "probe_family",
        "item",
        "measurement_surface",
        "form",
        "generator",
        "fixture",
    ]
    entity_id: str
    change_type: Literal["add", "deprecate", "rename", "split", "merge", "modify"]
    metadata: NotRequired[dict[str, Any]]


class ChangeManifestSpec(TypedDict):
    added: list[ChangeManifestEntrySpec]
    deprecated: list[ChangeManifestEntrySpec]
    modified: list[ChangeManifestEntrySpec]
    metadata: NotRequired[dict[str, Any]]


class MigrationMappingEntrySpec(TypedDict):
    source_ids: list[str]
    target_ids: list[str]
    mode: Literal["rename", "split", "merge", "deprecate"]
    rule: NotRequired[str]
    metadata: NotRequired[dict[str, Any]]


class StateTransformPolicySpec(TypedDict):
    policy_id: str
    uncertainty_mode: Literal["preserve", "widen", "reset"]
    readiness_mode: Literal["preserve", "conservative_recompute", "reset"]
    metadata: NotRequired[dict[str, Any]]


class ContentMigrationSpec(TypedDict):
    migration_id: str
    from_release_hash: str
    to_release_hash: str
    commitment_mapping: list[MigrationMappingEntrySpec]
    factor_mapping: list[MigrationMappingEntrySpec]
    probe_family_mapping: list[MigrationMappingEntrySpec]
    item_mapping: list[MigrationMappingEntrySpec]
    measurement_surface_mapping: list[MigrationMappingEntrySpec]
    state_transform_policy: StateTransformPolicySpec
    transform_hash: str
    metadata: NotRequired[dict[str, Any]]


class FixtureBindingSpec(TypedDict):
    binding_kind: Literal["rubric", "generator", "measurement_surface"]
    ref_id: str
    metadata: NotRequired[dict[str, Any]]


class DeliveryArtifactSpec(TypedDict):
    artifact_id: str
    artifact_kind: Literal["sentinel_fixture", "anchor_bank"]
    bindings: list[FixtureBindingSpec]
    tags: NotRequired[dict[str, str]]
    active: bool
    metadata: NotRequired[dict[str, Any]]


class ContentIRBundle(TypedDict):
    schema_version: str
    release_id: str
    content_ir_version: str
    release_hash: str
    parent_release_hash: NotRequired[str]
    change_manifest: ChangeManifestSpec
    tag_vocab: TagVocabularySpec
    commitments: list[CommitmentSpec]
    factors: list[FactorSpec]
    edges: list[EdgeSpec]
    observation_schemas: list[ObservationSchemaSpec]
    response_schemas: list[ResponseSchemaSpec]
    rubrics: list[RubricSpec]
    measurement_surfaces: list[MeasurementSurfaceSpec]
    probe_families: list[ProbeFamilySpec]
    items: list[ItemSpec]
    forms: list[FormSpec]
    generators: list[GeneratorSpec]
    delivery_artifacts: list[DeliveryArtifactSpec]
    feedback_policies: list[FeedbackPolicySpec]
    feedback_policy_precedence: FeedbackPolicyPrecedenceSpec
    channel_default_feedback_policies: list[ChannelDefaultFeedbackPolicySpec]
    content_migrations: list[ContentMigrationSpec]
    metadata: NotRequired[dict[str, Any]]
