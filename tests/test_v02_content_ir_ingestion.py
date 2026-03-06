"""Tests for v0.2 content IR ingestion contracts."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from forge_v01.content_ir_hashing import (
    compute_content_ir_release_hash,
    fingerprint_observation_schema_semantics,
    fingerprint_rubric_semantics,
)
from forge_v01.content_ir_registry import ContentIRRegistry
from forge_v01.content_ir_validator import validate_content_ir_bundle
from forge_v01.contract_validator import ContractValidator
from tests.fixtures_v02 import clone, load_valid_v02_bundle, v02_bundle_path


class TestV02ContentIRIngestion(unittest.TestCase):
    def setUp(self) -> None:
        self.bundle = load_valid_v02_bundle()

    def test_valid_bundle_passes(self) -> None:
        self.assertEqual(validate_content_ir_bundle(self.bundle), [])

    def test_registry_load_and_resolve(self) -> None:
        registry = ContentIRRegistry()
        registry.register_bundle_from_path(str(v02_bundle_path()))
        version = self.bundle["content_ir_version"]
        item = registry.resolve_item(version, "it_regex_literals_measure_001")
        family = registry.resolve_probe_family(version, item["probe_family_id"])
        self.assertEqual(family["commitment_id"], "cm_regex_literals")

    def test_deterministic_rubric_lookup(self) -> None:
        registry = ContentIRRegistry()
        registry.register_bundle(self.bundle)
        version = self.bundle["content_ir_version"]
        self.assertTrue(registry.deterministic_rubric_exists(version, "it_regex_literals_measure_001"))

        validator = ContractValidator(content_ir_registry=registry)
        self.assertTrue(validator.deterministic_rubric_exists("it_regex_literals_measure_001", version))

    def test_measurement_surface_round_trip(self) -> None:
        registry = ContentIRRegistry()
        registry.register_bundle(self.bundle)
        version = self.bundle["content_ir_version"]
        bundle = registry.get_bundle(version)
        family = registry.resolve_probe_family(version, "pf_regex_literals_measure")
        self.assertTrue(family["measurement_surface_refs"])
        surface_id = family["measurement_surface_refs"][0]
        surface = next(row for row in bundle["measurement_surfaces"] if row["measurement_surface_id"] == surface_id)
        self.assertEqual(surface["observation_schema_ref"], "obs_schema_slots_v1")
        self.assertEqual(surface["rubric_ref"], "rub_slots_regex_v1")
        self.assertIn("obs_encoder_version", surface["obs_binding"])
        self.assertEqual(len(bundle["measurement_surfaces"]), 2)

    def test_observation_schemas_include_richer_auxiliary_features(self) -> None:
        slots_schema = next(
            row for row in self.bundle["observation_schemas"] if row["observation_schema_id"] == "obs_schema_slots_v1"
        )
        mcq_schema = next(
            row for row in self.bundle["observation_schemas"] if row["observation_schema_id"] == "obs_schema_mcq_v1"
        )
        self.assertIn("slot_error_mask", slots_schema["auxiliary_feature_ids"])
        self.assertIn("selected_choice_id", mcq_schema["auxiliary_feature_ids"])

    def test_rubrics_emit_richer_auxiliary_features(self) -> None:
        slots_rubric = next(row for row in self.bundle["rubrics"] if row["rubric_id"] == "rub_slots_regex_v1")
        mcq_rubric = next(row for row in self.bundle["rubrics"] if row["rubric_id"] == "rub_mcq_regex_v1")
        slot_feature_ids = {row["feature_id"] for row in slots_rubric["observation_emission"]["fields"]}
        mcq_feature_ids = {row["feature_id"] for row in mcq_rubric["observation_emission"]["fields"]}
        self.assertIn("slot_error_mask", slot_feature_ids)
        self.assertIn("selected_choice_id", mcq_feature_ids)

    def test_items_and_generators_have_target_factor_bindings(self) -> None:
        self.assertIn("target_factor_binding", self.bundle["items"][0])
        self.assertIn("primary_target_factors", self.bundle["items"][0]["target_factor_binding"])
        self.assertIn("target_factor_binding", self.bundle["generators"][0])
        self.assertIn("primary_target_factors", self.bundle["generators"][0]["target_factor_binding"])

    def test_forms_have_explicit_delivery_contract_fields(self) -> None:
        anchor_form = next(row for row in self.bundle["forms"] if row["form_id"] == "form_anchor_regex_v1")
        shadow_form = next(row for row in self.bundle["forms"] if row["form_id"] == "form_shadow_regex_v1")
        self.assertEqual(anchor_form["delivery_role"], "anchor")
        self.assertTrue(anchor_form["closed_book_only"])
        self.assertEqual(shadow_form["delivery_role"], "shadow")
        self.assertLessEqual(shadow_form["max_presented_items"], 3)

    def test_micro_corpus_has_two_measurement_items_and_one_teaching_item_per_commitment(self) -> None:
        counts = {}
        for item in self.bundle["items"]:
            commitment = item["probe_family_id"].replace("pf_", "").rsplit("_", 1)[0]
            counts.setdefault(commitment, {"measure": 0, "teach": 0})
            if "_measure" in item["probe_family_id"]:
                counts[commitment]["measure"] += 1
            elif "_teach" in item["probe_family_id"]:
                counts[commitment]["teach"] += 1
        for commitment_counts in counts.values():
            self.assertEqual(commitment_counts["measure"], 2)
            self.assertEqual(commitment_counts["teach"], 1)

    def test_micro_corpus_has_parallel_holdout_forms_with_no_overlap(self) -> None:
        holdout_forms = [row for row in self.bundle["forms"] if row["delivery_role"] == "holdout"]
        self.assertEqual(len(holdout_forms), 2)
        first_items = set(holdout_forms[0]["items"])
        second_items = set(holdout_forms[1]["items"])
        self.assertFalse(first_items & second_items)

    def test_micro_corpus_has_sentinel_fixture_for_each_rubric(self) -> None:
        sentinel_refs = {
            binding["ref_id"]
            for artifact in self.bundle["delivery_artifacts"]
            if artifact["artifact_kind"] == "sentinel_fixture"
            for binding in artifact["bindings"]
            if binding["binding_kind"] == "rubric"
        }
        self.assertEqual(sentinel_refs, {"rub_slots_regex_v1", "rub_mcq_regex_v1"})

    def test_missing_measurement_surface_ref_fails(self) -> None:
        broken = clone(self.bundle)
        del broken["probe_families"][0]["measurement_surface_refs"]
        broken["release_hash"] = compute_content_ir_release_hash(broken)
        errors = validate_content_ir_bundle(broken)
        self.assertTrue(any("measurement_surface_refs" in e for e in errors))

    def test_unknown_measurement_surface_ref_fails(self) -> None:
        broken = clone(self.bundle)
        broken["probe_families"][0]["measurement_surface_refs"] = ["missing_surface"]
        broken["release_hash"] = compute_content_ir_release_hash(broken)
        errors = validate_content_ir_bundle(broken)
        self.assertTrue(any("measurement_surface_ref_unknown" in e for e in errors))

    def test_item_requires_explicit_unique_measurement_surface_binding(self) -> None:
        broken = clone(self.bundle)
        broken["items"][0]["measurement_surface_ref"] = "ms_pf_regex_concat_measure_resp_mcq_v1"
        broken["release_hash"] = compute_content_ir_release_hash(broken)
        errors = validate_content_ir_bundle(broken)
        self.assertTrue(any("measurement_surface_ref_not_declared_by_family" in e for e in errors))

    def test_registry_rejects_measurement_surface_repoint(self) -> None:
        first = clone(self.bundle)
        second = clone(self.bundle)
        second["content_ir_version"] = "content.v2026.03.05.regex.v0.2"
        second["observation_schemas"][0]["features"][0]["allowed_values"] = ["all_correct", "partial", "all_incorrect", "new_state"]
        second["measurement_surfaces"][0]["observation_schema_semantics_hash"] = fingerprint_observation_schema_semantics(
            second["observation_schemas"][0]
        )
        second["release_hash"] = compute_content_ir_release_hash(second)

        registry = ContentIRRegistry()
        registry.register_bundle(first)
        with self.assertRaises(ValueError):
            registry.register_bundle(second)

    def test_registry_rejects_measurement_surface_repoint_after_restart(self) -> None:
        first = clone(self.bundle)
        second = clone(self.bundle)
        second["content_ir_version"] = "content.v2026.03.06.regex.v0.2"
        second["rubrics"][0]["scoring_rules"][0]["params"]["logic"] = "slot_exact_match_restart"
        second["rubrics"][0]["rubric_semantics_version"] = fingerprint_rubric_semantics(second["rubrics"][0])
        second["measurement_surfaces"][0]["rubric_semantics_hash"] = second["rubrics"][0]["rubric_semantics_version"]
        second["release_hash"] = compute_content_ir_release_hash(second)

        with tempfile.TemporaryDirectory() as tmpdir:
            index_path = Path(tmpdir) / "measurement_surface_identity_index.json"
            registry_a = ContentIRRegistry(measurement_surface_identity_index_path=index_path)
            registry_a.register_bundle(first)
            registry_b = ContentIRRegistry(measurement_surface_identity_index_path=index_path)
            with self.assertRaises(ValueError):
                registry_b.register_bundle(second)

    def test_anchor_channel_strictness_is_channel_driven(self) -> None:
        broken = clone(self.bundle)
        family = next(row for row in broken["probe_families"] if row["probe_family_id"] == "pf_regex_literals_measure")
        anchor_row = next(row for row in family["channel_constraints"] if row["channel"] == "A_anchor")
        anchor_row["feedback_mode"] = "minimal"
        broken["release_hash"] = compute_content_ir_release_hash(broken)
        errors = validate_content_ir_bundle(broken)
        self.assertTrue(any("strict_measurement_constraint_violation" in e for e in errors))

    def test_missing_generator_instance_binding_contract_fails(self) -> None:
        broken = clone(self.bundle)
        del broken["generators"][0]["instance_binding_contract"]
        broken["release_hash"] = compute_content_ir_release_hash(broken)
        errors = validate_content_ir_bundle(broken)
        self.assertTrue(any("instance_binding_contract" in e for e in errors))

    def test_generator_requires_explicit_unique_measurement_surface_binding(self) -> None:
        broken = clone(self.bundle)
        broken["generators"][0]["grading_contract"]["measurement_surface_ref"] = "ms_pf_regex_concat_measure_resp_mcq_v1"
        broken["release_hash"] = compute_content_ir_release_hash(broken)
        errors = validate_content_ir_bundle(broken)
        self.assertTrue(any("measurement_surface_ref_mismatch_unique_binding" in e for e in errors))

    def test_item_feedback_policy_ref_must_resolve(self) -> None:
        broken = clone(self.bundle)
        broken["items"][0]["feedback_policy_ref"] = "missing_policy"
        broken["release_hash"] = compute_content_ir_release_hash(broken)
        errors = validate_content_ir_bundle(broken)
        self.assertTrue(any("feedback_policy_ref_unknown" in e for e in errors))

    def test_family_default_feedback_policy_ref_must_resolve(self) -> None:
        broken = clone(self.bundle)
        broken["probe_families"][0]["default_feedback_policy_ref"] = "missing_policy"
        broken["release_hash"] = compute_content_ir_release_hash(broken)
        errors = validate_content_ir_bundle(broken)
        self.assertTrue(any("default_feedback_policy_ref_unknown" in e for e in errors))

    def test_commitment_default_feedback_policy_ref_must_resolve(self) -> None:
        broken = clone(self.bundle)
        broken["commitments"][0]["default_feedback_policy_ref"] = "missing_policy"
        broken["release_hash"] = compute_content_ir_release_hash(broken)
        errors = validate_content_ir_bundle(broken)
        self.assertTrue(any("default_feedback_policy_ref_unknown" in e for e in errors))

    def test_item_signature_contract_is_typed(self) -> None:
        broken = clone(self.bundle)
        broken["items"][0]["item_params"]["signature"]["slots_count"] = -1
        broken["release_hash"] = compute_content_ir_release_hash(broken)
        errors = validate_content_ir_bundle(broken)
        self.assertTrue(any("signature_slots_count_invalid" in e for e in errors))

    def test_item_requires_typed_grading_material(self) -> None:
        broken = clone(self.bundle)
        del broken["items"][0]["grading_material"]
        broken["release_hash"] = compute_content_ir_release_hash(broken)
        errors = validate_content_ir_bundle(broken)
        self.assertTrue(any("grading_material" in e for e in errors))

    def test_item_requires_target_factor_binding(self) -> None:
        broken = clone(self.bundle)
        del broken["items"][0]["target_factor_binding"]
        broken["release_hash"] = compute_content_ir_release_hash(broken)
        errors = validate_content_ir_bundle(broken)
        self.assertTrue(any("target_factor_binding" in e for e in errors))

    def test_item_target_factors_must_be_allowed_by_family(self) -> None:
        broken = clone(self.bundle)
        broken["items"][0]["target_factor_binding"]["primary_target_factors"] = ["F_local_star_semantics"]
        broken["release_hash"] = compute_content_ir_release_hash(broken)
        errors = validate_content_ir_bundle(broken)
        self.assertTrue(any("target_factor_not_allowed_by_family" in e for e in errors))

    def test_response_schema_requires_typed_canonicalization_steps(self) -> None:
        broken = clone(self.bundle)
        broken["response_schemas"][0]["canonicalization_steps"] = {}
        broken["release_hash"] = compute_content_ir_release_hash(broken)
        errors = validate_content_ir_bundle(broken)
        self.assertTrue(any("canonicalization_steps_invalid_or_empty" in e for e in errors))

    def test_response_schema_requires_typed_parse_ir(self) -> None:
        broken = clone(self.bundle)
        broken["response_schemas"][0]["parse_ir"] = []
        broken["release_hash"] = compute_content_ir_release_hash(broken)
        errors = validate_content_ir_bundle(broken)
        self.assertTrue(any("parse_ir_not_object" in e for e in errors))

    def test_reserved_response_schema_cannot_be_active_supported(self) -> None:
        broken = clone(self.bundle)
        broken["response_schemas"][0]["response_kind"] = "structured_explanation"
        broken["response_schemas"][0]["authoring_status"] = "active_supported"
        broken["release_hash"] = compute_content_ir_release_hash(broken)
        errors = validate_content_ir_bundle(broken)
        self.assertTrue(any("active_supported_response_kind_not_allowed_in_v0_2" in e for e in errors))

    def test_rubric_requires_typed_scoring_rules(self) -> None:
        broken = clone(self.bundle)
        broken["rubrics"][0]["scoring_rules"] = {}
        broken["release_hash"] = compute_content_ir_release_hash(broken)
        errors = validate_content_ir_bundle(broken)
        self.assertTrue(any("scoring_rules_invalid_or_empty" in e for e in errors))

    def test_delivery_artifact_binding_must_resolve(self) -> None:
        broken = clone(self.bundle)
        broken["delivery_artifacts"][0]["bindings"][0]["ref_id"] = "missing_surface"
        broken["release_hash"] = compute_content_ir_release_hash(broken)
        errors = validate_content_ir_bundle(broken)
        self.assertTrue(any("measurement_surface_ref_unknown" in e for e in errors))

    def test_anchor_form_requires_closed_book_fixed_contract(self) -> None:
        broken = clone(self.bundle)
        anchor_form = next(row for row in broken["forms"] if row["form_id"] == "form_anchor_regex_v1")
        anchor_form["closed_book_only"] = False
        broken["release_hash"] = compute_content_ir_release_hash(broken)
        errors = validate_content_ir_bundle(broken)
        self.assertTrue(any("anchor_delivery_role_requires_closed_book_only" in e for e in errors))

    def test_shadow_form_requires_ultra_short_limit(self) -> None:
        broken = clone(self.bundle)
        shadow_form = next(row for row in broken["forms"] if row["form_id"] == "form_shadow_regex_v1")
        shadow_form["max_presented_items"] = 4
        broken["release_hash"] = compute_content_ir_release_hash(broken)
        errors = validate_content_ir_bundle(broken)
        self.assertTrue(any("shadow_delivery_role_requires_ultra_short_max_items" in e for e in errors))

    def test_adversarial_generator_requires_narrow_contract(self) -> None:
        broken = clone(self.bundle)
        del broken["generators"][0]["adversarial_contract"]
        broken["release_hash"] = compute_content_ir_release_hash(broken)
        errors = validate_content_ir_bundle(broken)
        self.assertTrue(any("adversarial_contract" in e for e in errors))

    def test_holdout_regular_dual_use_forbidden_without_opt_in(self) -> None:
        broken = clone(self.bundle)
        regular_form = {
            "form_id": "form_regular_measure_v1",
            "items": ["it_regex_literals_measure_001"],
            "evidence_channel": "B_measurement",
            "delivery_role": "regular",
            "fixed_form": True,
            "closed_book_only": False,
            "max_presented_items": 1,
            "consumption_policy": "none",
            "feedback_policy_ref": "fb_none_measurement",
            "form_tags": [],
            "active": True,
            "metadata": {},
        }
        broken["forms"].append(regular_form)
        broken["items"][0]["form_memberships"].append("form_regular_measure_v1")
        broken["release_hash"] = compute_content_ir_release_hash(broken)
        errors = validate_content_ir_bundle(broken)
        self.assertTrue(any("dual_use_forbidden" in e for e in errors))

    def test_typed_content_migration_mapping_required(self) -> None:
        broken = clone(self.bundle)
        broken["content_migrations"] = [
            {
                "migration_id": "mig_bad",
                "from_release_hash": "sha256:" + "1" * 64,
                "to_release_hash": "sha256:" + "2" * 64,
                "commitment_mapping": {},
                "factor_mapping": [],
                "probe_family_mapping": [],
                "item_mapping": [],
                "measurement_surface_mapping": [],
                "state_transform_policy": {
                    "policy_id": "p1",
                    "uncertainty_mode": "preserve",
                    "readiness_mode": "preserve",
                    "metadata": {},
                },
                "transform_hash": "sha256:" + "3" * 64,
                "metadata": {},
            }
        ]
        broken["release_hash"] = compute_content_ir_release_hash(broken)
        errors = validate_content_ir_bundle(broken)
        self.assertTrue(any("commitment_mapping_not_array" in e for e in errors))

    def test_measurement_surface_semantic_duplicates_are_rejected(self) -> None:
        broken = clone(self.bundle)
        dup = clone(broken["measurement_surfaces"][0])
        dup["measurement_surface_id"] = "ms_duplicate_slots"
        broken["measurement_surfaces"].append(dup)
        broken["release_hash"] = compute_content_ir_release_hash(broken)
        errors = validate_content_ir_bundle(broken)
        self.assertTrue(any("semantic_duplicate_of_existing_surface" in e for e in errors))

    def test_release_hash_ignores_set_like_nested_order(self) -> None:
        first = clone(self.bundle)
        second = clone(self.bundle)
        second["commitments"][0]["aliases"] = list(reversed(second["commitments"][0]["aliases"]))
        second["probe_families"][0]["allowed_channels"] = list(reversed(second["probe_families"][0]["allowed_channels"]))
        second["items"][0]["form_memberships"] = list(reversed(second["items"][0]["form_memberships"]))
        self.assertEqual(compute_content_ir_release_hash(first), compute_content_ir_release_hash(second))

    def test_release_hash_preserves_truly_ordered_nested_lists(self) -> None:
        first = clone(self.bundle)
        second = clone(self.bundle)
        second["generators"][0]["parameter_schema"]["pair_templates"] = list(
            reversed(second["generators"][0]["parameter_schema"]["pair_templates"])
        )
        self.assertNotEqual(compute_content_ir_release_hash(first), compute_content_ir_release_hash(second))

    def test_release_hash_does_not_apply_set_normalization_inside_opaque_payload_schema(self) -> None:
        first = clone(self.bundle)
        second = clone(self.bundle)
        first["response_schemas"][0]["payload_schema"]["opaque_aliases"] = ["a", "b"]
        second["response_schemas"][0]["payload_schema"]["opaque_aliases"] = ["b", "a"]
        self.assertNotEqual(compute_content_ir_release_hash(first), compute_content_ir_release_hash(second))

    def test_generator_rubric_observation_schema_must_match_family(self) -> None:
        broken = clone(self.bundle)
        broken["generators"][0]["grading_contract"]["rubric_ref"] = "rub_mcq_regex_v1"
        broken["release_hash"] = compute_content_ir_release_hash(broken)
        errors = validate_content_ir_bundle(broken)
        self.assertTrue(any("rubric_observation_schema_mismatch_family" in e for e in errors))

    def test_channel_default_feedback_policy_must_resolve(self) -> None:
        broken = clone(self.bundle)
        broken["channel_default_feedback_policies"][0]["feedback_policy_ref"] = "missing_policy"
        broken["release_hash"] = compute_content_ir_release_hash(broken)
        errors = validate_content_ir_bundle(broken)
        self.assertTrue(any("feedback_policy_ref_unknown" in e for e in errors))

    def test_feedback_policy_precedence_must_match_contract(self) -> None:
        broken = clone(self.bundle)
        broken["feedback_policy_precedence"]["order"] = ["form", "item", "probe_family", "commitment", "channel_default"]
        broken["release_hash"] = compute_content_ir_release_hash(broken)
        errors = validate_content_ir_bundle(broken)
        self.assertTrue(any("feedback_policy_precedence_order_invalid" in e for e in errors))

    def test_measurement_surface_hashes_must_match_recomputed_semantics(self) -> None:
        broken = clone(self.bundle)
        broken["measurement_surfaces"][0]["canonicalization_hash"] = "sha256:" + "0" * 64
        broken["release_hash"] = compute_content_ir_release_hash(broken)
        errors = validate_content_ir_bundle(broken)
        self.assertTrue(any("canonicalization_hash_mismatch_recomputed" in e for e in errors))

    def test_content_migration_cardinality_is_enforced(self) -> None:
        broken = clone(self.bundle)
        broken["parent_release_hash"] = "sha256:" + "1" * 64
        broken["content_migrations"] = [
            {
                "migration_id": "mig_bad_cardinality",
                "from_release_hash": broken["parent_release_hash"],
                "to_release_hash": broken["release_hash"],
                "commitment_mapping": [
                    {
                        "source_ids": ["cm_regex_literals", "cm_regex_concat"],
                        "target_ids": ["cm_regex_literals_v2"],
                        "mode": "rename",
                        "metadata": {},
                    }
                ],
                "factor_mapping": [],
                "probe_family_mapping": [],
                "item_mapping": [],
                "measurement_surface_mapping": [],
                "state_transform_policy": {
                    "policy_id": "p1",
                    "uncertainty_mode": "preserve",
                    "readiness_mode": "preserve",
                    "metadata": {},
                },
                "transform_hash": "sha256:" + "3" * 64,
                "metadata": {},
            }
        ]
        broken["release_hash"] = compute_content_ir_release_hash(broken)
        broken["content_migrations"][0]["to_release_hash"] = broken["release_hash"]
        errors = validate_content_ir_bundle(broken)
        self.assertTrue(any("rename_cardinality_invalid" in e for e in errors))

    def test_calibration_pool_policy_baseline_must_be_closed_book_diagnostic(self) -> None:
        broken = clone(self.bundle)
        broken["probe_families"][0]["calibration_contract"]["calibration_pool_policy"]["baseline_assistance_modes"] = [
            "open_book"
        ]
        broken["release_hash"] = compute_content_ir_release_hash(broken)
        errors = validate_content_ir_bundle(broken)
        self.assertTrue(any("baseline_modes_not_subset_diagnostic_modes" in e for e in errors))

    def test_generator_requires_solution_material_contract(self) -> None:
        broken = clone(self.bundle)
        del broken["generators"][0]["grading_contract"]["solution_material_contract"]
        broken["release_hash"] = compute_content_ir_release_hash(broken)
        errors = validate_content_ir_bundle(broken)
        self.assertTrue(any("solution_material_contract" in e for e in errors))


if __name__ == "__main__":
    unittest.main()
