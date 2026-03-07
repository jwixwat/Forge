"""v0.3 deterministic grading and observation extraction tests."""

from __future__ import annotations

import unittest
from dataclasses import asdict

from forge_v01.runtime_context import ForgeRuntimeContext
from tests.fixtures import make_attempt, make_attempt_precommit, make_manifest
from tests.fixtures_v02 import load_valid_v02_bundle
from forge_v01.utils import sha256_json


class TestV03DeterministicGrading(unittest.TestCase):
    def setUp(self) -> None:
        self.bundle = load_valid_v02_bundle()
        self.runtime = ForgeRuntimeContext.from_bundle(self.bundle)
        self.registry = self.runtime.content_ir_registry
        self.obs_vocab = self.runtime.obs_vocab_registry
        self.validator = self.runtime.contract_validator

    def test_slots_item_correct_response_materializes_expected_observation(self) -> None:
        result = self.runtime.grade_item_response(
            self.bundle["content_ir_version"],
            "it_regex_literals_measure_001",
            {"slots": {"a": " yes ", "b": "no "}},
            {"latency_sec": 12, "hint_count": 0},
        )
        self.assertTrue(result.grading_signals["schema_valid"])
        self.assertEqual(result.grader_output.grader_output["slot_pattern"], "all_correct")
        self.assertEqual(result.observation_result.obs_key, "slot_pattern=all_correct")
        self.assertEqual(result.observation_result.observation["slot_pattern"], "all_correct")
        self.assertEqual(result.observation_result.observation["latency_bucket"], "fast")
        self.assertFalse(result.observation_result.observation["hint_used"])

    def test_slots_item_partial_response_emits_error_mask(self) -> None:
        result = self.runtime.grade_item_response(
            self.bundle["content_ir_version"],
            "it_regex_literals_teach_001",
            {"slots": {"a": "yes", "b": "yes"}},
            {
                "latency_sec": 75,
                "hint_count": 1,
                "evidence_channel": "C_learning",
                "assistance_mode_derived": "closed_book",
            },
        )
        self.assertTrue(result.grading_signals["schema_valid"])
        self.assertEqual(result.grader_output.grader_output["slot_pattern"], "partial")
        self.assertEqual(result.grader_output.grader_output["slot_error_mask"], "a=pass,b=fail")
        self.assertEqual(result.observation_result.observation["slot_error_mask"], "a=pass,b=fail")
        self.assertEqual(result.observation_result.observation["latency_bucket"], "medium")
        self.assertTrue(result.observation_result.observation["hint_used"])

    def test_slots_item_malformed_response_is_flagged_not_silent(self) -> None:
        result = self.runtime.grade_item_response(
            self.bundle["content_ir_version"],
            "it_regex_literals_measure_001",
            {"slots": {"a": 1, "b": None}},
            {"latency_sec": 120, "hint_count": 0},
        )
        self.assertFalse(result.grading_signals["schema_valid"])
        self.assertEqual(result.grading_signals["rubric_path_count"], 0)
        self.assertFalse(result.grader_output.ambiguous)
        self.assertEqual(result.grading_signals["scoring_resolution_status"], "invalid")
        self.assertEqual(result.grader_output.grader_output["slot_pattern"], "all_incorrect")
        self.assertIsNone(result.observation_result.obs_key)
        self.assertEqual(result.observation_result.observation_status, "invalid")
        self.assertEqual(
            result.observation_result.observation_invalid_reason,
            "schema_invalid",
        )

    def test_mcq_choice_outside_authored_choice_set_is_invalid(self) -> None:
        result = self.runtime.grade_item_response(
            self.bundle["content_ir_version"],
            "it_regex_concat_measure_001",
            {"choice": "choice_z"},
            {"latency_sec": 30, "hint_count": 0},
        )
        self.assertFalse(result.grading_signals["schema_valid"])
        self.assertFalse(result.canonical_response.value_constraints_valid)
        self.assertIn("choice_id_not_in_authored_choice_set", result.canonical_response.errors)
        self.assertEqual(result.grading_signals["scoring_resolution_status"], "invalid")
        self.assertIsNone(result.observation_result.obs_key)

    def test_mcq_item_correct_response_materializes_expected_observation(self) -> None:
        result = self.runtime.grade_item_response(
            self.bundle["content_ir_version"],
            "it_regex_concat_measure_001",
            {"choice": " Choice_B "},
            {"latency_sec": 40, "hint_count": 0},
        )
        self.assertTrue(result.grading_signals["schema_valid"])
        self.assertEqual(result.grader_output.grader_output["mcq_outcome"], "correct")
        self.assertEqual(result.observation_result.obs_key, "mcq_outcome=correct")
        self.assertEqual(result.observation_result.observation["selected_choice_id"], "choice_b")

    def test_mcq_item_incorrect_response_preserves_selected_choice(self) -> None:
        result = self.runtime.grade_item_response(
            self.bundle["content_ir_version"],
            "it_regex_concat_measure_001",
            {"choice": "choice_a"},
            {"latency_sec": 95, "hint_count": 0},
        )
        self.assertTrue(result.grading_signals["schema_valid"])
        self.assertEqual(result.grader_output.grader_output["mcq_outcome"], "incorrect")
        self.assertEqual(result.observation_result.observation["selected_choice_id"], "choice_a")
        self.assertEqual(result.observation_result.observation["latency_bucket"], "slow")

    def test_bundle_active_items_all_grade_to_non_empty_obs_keys(self) -> None:
        for item in self.bundle["items"]:
            if not item["active"]:
                continue
            if item["response_schema_ref"] == "resp_slots_v1":
                raw_response = {"slots": {"a": "yes", "b": "no"}}
            else:
                raw_response = {"choice": "choice_a"}
            result = self.runtime.grade_item_response(
                self.bundle["content_ir_version"],
                item["item_id"],
                raw_response,
                {"latency_sec": 30, "hint_count": 0},
            )
            self.assertIsInstance(result.observation_result.obs_key, str)
            self.assertNotEqual(result.observation_result.obs_key, "")

    def test_sentinel_fixture_cases_execute_for_bound_rubrics(self) -> None:
        rubric_to_item = {}
        for item in self.bundle["items"]:
            rubric_to_item.setdefault(item["rubric_ref"], item["item_id"])
        for artifact in self.bundle["delivery_artifacts"]:
            if artifact["artifact_kind"] != "sentinel_fixture":
                continue
            rubric_ref = artifact["bindings"][0]["ref_id"]
            item_id = rubric_to_item[rubric_ref]
            for case in artifact["metadata"]["cases"]:
                result = self.runtime.grade_item_response(
                    self.bundle["content_ir_version"],
                    item_id,
                    case["response"],
                    {"latency_sec": 20, "hint_count": 0},
                )
                expected_status = case.get("expected_status", "valid")
                self.assertEqual(result.observation_result.observation_status, expected_status)
                if expected_status != "valid":
                    self.assertIsNone(result.observation_result.obs_key)
                    self.assertEqual(
                        result.observation_result.observation_invalid_reason,
                        case.get("expected_invalid_reason"),
                    )
                    continue
                expected_outcome = case["expected_outcome"]
                if rubric_ref == "rub_slots_regex_v1":
                    self.assertEqual(
                        result.grader_output.grader_output["slot_pattern"],
                        expected_outcome,
                    )
                else:
                    self.assertEqual(result.grader_output.grader_output["mcq_outcome"], expected_outcome)

    def test_obs_vocab_registry_registers_surface_vocab_from_bundle(self) -> None:
        slots_vocab = self.obs_vocab.get_vocab(
            "obsenc.v0.2.0",
            "hyp.obs_schema_slots_v1.resp_slots_v1.v0.2",
            calibration_projection_id="proj_slot_pattern",
            measurement_surface_id="ms_pf_regex_literals_measure_resp_slots_v1",
        )
        mcq_vocab = self.obs_vocab.get_vocab(
            "obsenc.v0.2.0",
            "hyp.obs_schema_mcq_v1.resp_mcq_v1.v0.2",
            calibration_projection_id="proj_mcq_outcome",
            measurement_surface_id="ms_pf_regex_concat_measure_resp_mcq_v1",
        )
        self.assertEqual(
            slots_vocab,
            {"slot_pattern=all_correct", "slot_pattern=partial", "slot_pattern=all_incorrect"},
        )
        self.assertEqual(
            mcq_vocab,
            {"mcq_outcome=correct", "mcq_outcome=incorrect"},
        )

    def test_materialized_attempt_observation_validates_against_v01_contract(self) -> None:
        surface = self.registry.resolve_measurement_surface(
            self.bundle["content_ir_version"],
            "ms_pf_regex_literals_measure_resp_slots_v1",
        )
        manifest = make_manifest(run_id="run_v03_smoke")
        manifest["content_ir_version"] = self.bundle["content_ir_version"]
        manifest["obs_encoder_version"] = surface["obs_binding"]["obs_encoder_version"]
        manifest["hypothesis_space_hash"] = surface["obs_binding"]["hypothesis_space_hash"]

        result = self.runtime.grade_item_response(
            self.bundle["content_ir_version"],
            "it_regex_literals_measure_001",
            {"slots": {"a": "yes", "b": "no"}},
            {"latency_sec": 20, "hint_count": 0},
        )

        attempt = make_attempt(
            manifest,
            attempt_id="att_v03_smoke_001",
            measurement_frame=asdict(result.measurement_frame),
            measurement_subject=asdict(result.measurement_subject),
            measurement_execution=asdict(result.measurement_execution),
            measurement_adjudication=asdict(result.measurement_adjudication),
        )
        attempt["item_id"] = "it_regex_literals_measure_001"
        attempt["probe_family_id"] = "pf_regex_literals_measure"
        attempt["commitment_id"] = "cm_regex_literals"
        attempt["observation"] = result.observation_result.observation
        attempt["grading_signals"] = result.grading_signals
        attempt["residual_inputs"]["primitive_inputs"] = result.residual_primitive_inputs
        attempt["residual_inputs"]["likelihood_sketch"]["predicted_observation_distribution"] = [
            {"obs_key": "slot_pattern=all_correct", "p": 0.6},
            {"obs_key": "slot_pattern=partial", "p": 0.25},
            {"obs_key": "slot_pattern=all_incorrect", "p": 0.15},
        ]
        attempt["precommit_hash"] = sha256_json(self.validator.precommit_projection_from_attempt(attempt))
        attempt["precommit_envelope_hash"] = sha256_json(
            self.validator.precommit_envelope_projection_from_attempt(attempt)
        )
        precommit = make_attempt_precommit(manifest, attempt)
        self.assertEqual(self.validator.validate_attempt(attempt, manifest), [])
        self.assertEqual(self.validator.validate_attempt_precommit(precommit, manifest), [])

    def test_measurement_frame_carries_channel_and_eligibility_semantics(self) -> None:
        result = self.runtime.grade_item_response(
            self.bundle["content_ir_version"],
            "it_regex_literals_measure_001",
            {"slots": {"a": "yes", "b": "no"}},
            {
                "latency_sec": 20,
                "hint_count": 0,
                "evidence_channel": "B_measurement",
                "assistance_mode_derived": "closed_book",
            },
        )
        self.assertEqual(result.measurement_frame.evidence_channel, "B_measurement")
        self.assertEqual(result.measurement_frame.assistance_mode, "closed_book")
        self.assertEqual(result.measurement_frame.diagnosis_update_eligibility, "eligible")
        self.assertEqual(result.measurement_frame.ineligibility_reason, "none")
        self.assertTrue(result.measurement_adjudication.calibration_eligible)

    def test_contract_validator_can_derive_vocab_from_content_registry_without_manual_obs_registry(self) -> None:
        validator = self.runtime.contract_validator
        manifest = make_manifest(run_id="run_v03_derived_vocab")
        manifest["content_ir_version"] = self.bundle["content_ir_version"]
        result = self.runtime.grade_item_response(
            self.bundle["content_ir_version"],
            "it_regex_concat_measure_001",
            {"choice": "choice_b"},
            {
                "latency_sec": 20,
                "hint_count": 0,
                "evidence_channel": "B_measurement",
                "assistance_mode_derived": "closed_book",
            },
        )
        frame = asdict(result.measurement_frame)
        manifest["obs_encoder_version"] = frame["obs_encoder_version"]
        manifest["hypothesis_space_hash"] = frame["hypothesis_space_hash"]
        attempt = make_attempt(
            manifest,
            attempt_id="att_v03_smoke_derived_vocab",
            evidence_channel="B_measurement",
            assistance_mode="closed_book",
            measurement_frame=frame,
            measurement_subject=asdict(result.measurement_subject),
            measurement_execution=asdict(result.measurement_execution),
            measurement_adjudication=asdict(result.measurement_adjudication),
        )
        attempt["item_id"] = "it_regex_concat_measure_001"
        attempt["probe_family_id"] = "pf_regex_concat_measure"
        attempt["commitment_id"] = "cm_regex_concat"
        attempt["observation"] = result.observation_result.observation
        attempt["grading_signals"] = result.grading_signals
        attempt["residual_inputs"]["primitive_inputs"] = result.residual_primitive_inputs
        attempt["residual_inputs"]["likelihood_sketch"]["predicted_observation_distribution"] = [
            {"obs_key": "mcq_outcome=correct", "p": 0.6},
            {"obs_key": "mcq_outcome=incorrect", "p": 0.4},
        ]
        attempt["precommit_hash"] = sha256_json(validator.precommit_projection_from_attempt(attempt))
        attempt["precommit_envelope_hash"] = sha256_json(
            validator.precommit_envelope_projection_from_attempt(attempt)
        )
        self.assertEqual(validator.validate_attempt(attempt, manifest), [])

    def test_runtime_validator_rejects_valid_status_observation_missing_required_feature(self) -> None:
        manifest = make_manifest(run_id="run_v03_missing_feature")
        result = self.runtime.grade_item_response(
            self.bundle["content_ir_version"],
            "it_regex_literals_measure_001",
            {"slots": {"a": "yes", "b": "no"}},
            {"latency_sec": 20, "hint_count": 0},
        )
        frame = asdict(result.measurement_frame)
        manifest["content_ir_version"] = frame["content_ir_version"]
        manifest["obs_encoder_version"] = frame["obs_encoder_version"]
        manifest["hypothesis_space_hash"] = frame["hypothesis_space_hash"]
        attempt = make_attempt(
            manifest,
            attempt_id="att_v03_missing_feature_001",
            measurement_frame=frame,
            measurement_subject=asdict(result.measurement_subject),
            measurement_execution=asdict(result.measurement_execution),
            measurement_adjudication=asdict(result.measurement_adjudication),
        )
        attempt["item_id"] = "it_regex_literals_measure_001"
        attempt["probe_family_id"] = "pf_regex_literals_measure"
        attempt["commitment_id"] = "cm_regex_literals"
        observation = dict(result.observation_result.observation)
        del observation["latency_bucket"]
        attempt["observation"] = observation
        attempt["grading_signals"] = result.grading_signals
        attempt["residual_inputs"]["primitive_inputs"] = result.residual_primitive_inputs
        attempt["residual_inputs"]["likelihood_sketch"]["predicted_observation_distribution"] = [
            {"obs_key": "slot_pattern=all_correct", "p": 1.0},
        ]
        attempt["precommit_hash"] = sha256_json(self.validator.precommit_projection_from_attempt(attempt))
        attempt["precommit_envelope_hash"] = sha256_json(
            self.validator.precommit_envelope_projection_from_attempt(attempt)
        )
        errors = self.validator.validate_attempt(attempt, manifest)
        self.assertIn(
            "attempt_runtime_measurement_observation_required_feature_missing:latency_bucket",
            errors,
        )

    def test_runtime_execution_enforces_channel_constraints(self) -> None:
        result = self.runtime.grade_item_response(
            self.bundle["content_ir_version"],
            "it_regex_literals_measure_001",
            {"slots": {"a": "yes", "b": "no"}},
            {"latency_sec": 20, "hint_count": 1, "evidence_channel": "B_measurement"},
        )
        self.assertIn(
            "measurement_execution_hints_used_when_forbidden",
            result.validation_errors,
        )
        manifest = make_manifest(run_id="run_v03_execution_constraints")
        frame = asdict(result.measurement_frame)
        manifest["content_ir_version"] = frame["content_ir_version"]
        manifest["obs_encoder_version"] = frame["obs_encoder_version"]
        manifest["hypothesis_space_hash"] = frame["hypothesis_space_hash"]
        attempt = make_attempt(
            manifest,
            attempt_id="att_v03_execution_constraints_001",
            evidence_channel="B_measurement",
            assistance_mode="closed_book",
            measurement_frame=frame,
            measurement_subject=asdict(result.measurement_subject),
            measurement_execution=asdict(result.measurement_execution),
            measurement_adjudication=asdict(result.measurement_adjudication),
        )
        attempt["item_id"] = "it_regex_literals_measure_001"
        attempt["probe_family_id"] = "pf_regex_literals_measure"
        attempt["commitment_id"] = "cm_regex_literals"
        attempt["observation"] = result.observation_result.observation
        attempt["grading_signals"] = result.grading_signals
        attempt["residual_inputs"]["primitive_inputs"] = result.residual_primitive_inputs
        attempt["residual_inputs"]["likelihood_sketch"]["predicted_observation_distribution"] = [
            {"obs_key": "slot_pattern=all_correct", "p": 1.0},
        ]
        attempt["precommit_hash"] = sha256_json(self.validator.precommit_projection_from_attempt(attempt))
        attempt["precommit_envelope_hash"] = sha256_json(
            self.validator.precommit_envelope_projection_from_attempt(attempt)
        )
        errors = self.validator.validate_attempt(attempt, manifest)
        self.assertIn(
            "attempt_measurement_execution_hints_used_when_forbidden",
            errors,
        )

    def test_runtime_execution_rejects_feedback_trace_when_feedback_forbidden(self) -> None:
        result = self.runtime.grade_item_response(
            self.bundle["content_ir_version"],
            "it_regex_literals_measure_001",
            {"slots": {"a": "yes", "b": "no"}},
            {
                "latency_sec": 20,
                "hint_count": 0,
                "evidence_channel": "D_shadow",
                "assistance_mode_derived": "closed_book",
            },
        )
        manifest = make_manifest(run_id="run_v03_feedback_forbidden")
        frame = asdict(result.measurement_frame)
        manifest["content_ir_version"] = frame["content_ir_version"]
        manifest["obs_encoder_version"] = frame["obs_encoder_version"]
        manifest["hypothesis_space_hash"] = frame["hypothesis_space_hash"]
        feedback_trace = {
            "decision_id": "dec_feedback_001",
            "trace_kind": "feedback",
            "candidate_actions": [{"action_id": "fb_none"}],
            "chosen_action_id": "fb_none",
            "chosen_action_probability": 1.0,
        }
        attempt = make_attempt(
            manifest,
            attempt_id="att_v03_feedback_forbidden_001",
            evidence_channel="D_shadow",
            assistance_mode="closed_book",
            extra_decision_traces=[feedback_trace],
            measurement_frame=frame,
            measurement_subject=asdict(result.measurement_subject),
            measurement_execution=asdict(result.measurement_execution),
            measurement_adjudication=asdict(result.measurement_adjudication),
        )
        attempt["item_id"] = "it_regex_literals_measure_001"
        attempt["probe_family_id"] = "pf_regex_literals_measure"
        attempt["commitment_id"] = "cm_regex_literals"
        attempt["observation"] = result.observation_result.observation
        attempt["grading_signals"] = result.grading_signals
        attempt["residual_inputs"]["primitive_inputs"] = result.residual_primitive_inputs
        attempt["residual_inputs"]["likelihood_sketch"]["predicted_observation_distribution"] = [
            {"obs_key": "slot_pattern=all_correct", "p": 1.0},
        ]
        attempt["precommit_hash"] = sha256_json(self.validator.precommit_projection_from_attempt(attempt))
        attempt["precommit_envelope_hash"] = sha256_json(
            self.validator.precommit_envelope_projection_from_attempt(attempt)
        )
        errors = self.validator.validate_attempt(attempt, manifest)
        self.assertIn(
            "attempt_measurement_execution_feedback_trace_present_when_forbidden",
            errors,
        )

    def test_generated_instance_response_materializes_and_validates(self) -> None:
        generated_instance = {
            "item_instance_id": "geninst_regex_adv_001",
            "generator_version": "1.0.0",
            "generator_seed": "seed_adv_001",
            "rendered_payload_hash": "sha256:generated_payload_hash",
            "solution_material": {"slot_answer_key": ["yes", "no"]},
        }
        result = self.runtime.grade_generated_instance_response(
            self.bundle["content_ir_version"],
            "gen_regex_adversarial_pairs_v1",
            generated_instance,
            {"slots": {"a": "yes", "b": "no"}},
            {
                "latency_sec": 20,
                "hint_count": 0,
                "evidence_channel": "D_shadow",
                "assistance_mode_derived": "closed_book",
            },
        )
        self.assertEqual(result.measurement_subject.subject_kind, "generated_instance")
        self.assertEqual(result.item_id, "geninst_regex_adv_001")
        self.assertEqual(result.measurement_subject.generator_id, "gen_regex_adversarial_pairs_v1")
        self.assertEqual(result.observation_result.observation_status, "valid")
        self.assertEqual(result.observation_result.obs_key, "slot_pattern=all_correct")

        manifest = make_manifest(run_id="run_v03_generated_instance")
        frame = asdict(result.measurement_frame)
        manifest["content_ir_version"] = frame["content_ir_version"]
        manifest["obs_encoder_version"] = frame["obs_encoder_version"]
        manifest["hypothesis_space_hash"] = frame["hypothesis_space_hash"]
        attempt = make_attempt(
            manifest,
            attempt_id="att_v03_generated_instance_001",
            evidence_channel="D_shadow",
            assistance_mode="closed_book",
            measurement_frame=frame,
            measurement_subject=asdict(result.measurement_subject),
            measurement_execution=asdict(result.measurement_execution),
            measurement_adjudication=asdict(result.measurement_adjudication),
        )
        attempt["item_id"] = result.item_id
        attempt["probe_family_id"] = "pf_regex_adversarial_placeholder"
        attempt["commitment_id"] = "cm_regex_literals"
        attempt["observation"] = result.observation_result.observation
        attempt["grading_signals"] = result.grading_signals
        attempt["residual_inputs"]["primitive_inputs"] = result.residual_primitive_inputs
        attempt["residual_inputs"]["likelihood_sketch"]["predicted_observation_distribution"] = [
            {"obs_key": "slot_pattern=all_correct", "p": 0.5},
            {"obs_key": "slot_pattern=partial", "p": 0.3},
            {"obs_key": "slot_pattern=all_incorrect", "p": 0.2},
        ]
        attempt["precommit_hash"] = sha256_json(self.validator.precommit_projection_from_attempt(attempt))
        attempt["precommit_envelope_hash"] = sha256_json(
            self.validator.precommit_envelope_projection_from_attempt(attempt)
        )
        precommit = make_attempt_precommit(manifest, attempt)
        self.assertEqual(self.validator.validate_attempt(attempt, manifest), [])
        self.assertEqual(self.validator.validate_attempt_precommit(precommit, manifest), [])


if __name__ == "__main__":
    unittest.main()
