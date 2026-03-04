"""Reusable audit query primitives for gates/invariants."""

from __future__ import annotations

import math
from typing import Any

from .constants import (
    DIAGNOSTIC_EVIDENCE_CHANNELS,
    EVENT_ID_PREFIX_BY_TYPE,
    EVENT_PAYLOAD_ID_FIELD_BY_TYPE,
    EVENT_TYPES,
    GENESIS_SNAPSHOT_ID,
    OPE_CONTEXT_AXES,
    RESIDUAL_PROVENANCE_PINNED_FIELDS,
    SAFE_MODE_PROFILE_IDS,
    SAFE_MODE_PROFILE_PARENT_STATES,
)
from .utils import (
    float_equal,
    is_probability,
    is_strict_int,
    is_strict_number,
    missing_required_fields,
    parse_rfc3339_utc,
    sha256_json,
)


def extract_decision_traces(attempt: dict[str, Any]) -> list[dict[str, Any]]:
    traces = attempt.get("decision_traces")
    if isinstance(traces, list):
        return traces
    return []


def extract_traces_by_kind(attempt: dict[str, Any], trace_kind: str) -> list[dict[str, Any]]:
    return [t for t in extract_decision_traces(attempt) if t.get("trace_kind") == trace_kind]


def _trace_probability_stats(trace: Any) -> dict[str, Any]:
    if not isinstance(trace, dict):
        return {"valid": False}
    candidates = trace.get("candidate_actions")
    chosen_action_id = trace.get("chosen_action_id")
    chosen_action_probability = trace.get("chosen_action_probability")
    if (
        not isinstance(candidates, list)
        or not candidates
        or not isinstance(chosen_action_id, str)
        or chosen_action_id == ""
        or not is_probability(chosen_action_probability)
    ):
        return {"valid": False}

    prob_sum = 0.0
    min_candidate_probability = 1.0
    chosen_probability: float | None = None
    seen_action_ids: set[str] = set()
    for candidate in candidates:
        if not isinstance(candidate, dict):
            return {"valid": False}
        action_id = candidate.get("action_id")
        p = candidate.get("p")
        if (
            not isinstance(action_id, str)
            or action_id == ""
            or not is_probability(p)
        ):
            return {"valid": False}
        if action_id in seen_action_ids:
            return {"valid": False}
        seen_action_ids.add(action_id)
        p_float = float(p)
        prob_sum += p_float
        if p_float < min_candidate_probability:
            min_candidate_probability = p_float
        if action_id == chosen_action_id:
            chosen_probability = p_float

    if not float_equal(prob_sum, 1.0, tolerance=1e-5):
        return {"valid": False}
    if chosen_probability is None:
        return {"valid": False}
    if not float_equal(chosen_probability, float(chosen_action_probability), tolerance=1e-5):
        return {"valid": False}

    deterministic = (
        len(candidates) == 1 and float_equal(float(candidates[0].get("p", 0.0)), 1.0, tolerance=1e-5)
    )
    entropy_bits = 0.0
    for candidate in candidates:
        p = float(candidate.get("p", 0.0))
        if p > 0.0:
            entropy_bits += -p * math.log2(p)
    return {
        "valid": True,
        "deterministic": deterministic,
        "entropy_bits": entropy_bits,
        "min_candidate_probability": min_candidate_probability,
        "chosen_probability": chosen_probability,
    }


def recompute_support_claim_for_trace(
    trace: dict[str, Any],
    min_candidate_probability: float,
    min_chosen_probability: float,
    min_entropy_bits: float,
) -> dict[str, Any]:
    stats = _trace_probability_stats(trace)
    if not stats.get("valid"):
        return {"valid": False}
    entropy_bits = float(stats.get("entropy_bits", 0.0))
    min_support_expected = (
        float(stats.get("min_candidate_probability", 0.0)) >= float(min_candidate_probability)
        and float(stats.get("chosen_probability", 0.0)) >= float(min_chosen_probability)
    )
    entropy_floor_expected = entropy_bits >= float(min_entropy_bits)
    status_expected = "pass" if (entropy_floor_expected and min_support_expected) else "fail"
    return {
        "valid": True,
        "entropy_bits": entropy_bits,
        "min_candidate_probability": float(stats.get("min_candidate_probability", 0.0)),
        "chosen_probability": float(stats.get("chosen_probability", 0.0)),
        "deterministic": bool(stats.get("deterministic", False)),
        "entropy_floor_expected": entropy_floor_expected,
        "min_support_expected": min_support_expected,
        "status_expected": status_expected,
    }


def classify_trace_kind_support(attempts: list[dict[str, Any]], trace_kind: str) -> str:
    matching: list[dict[str, Any]] = []
    for attempt in attempts:
        matching.extend(extract_traces_by_kind(attempt, trace_kind))
    if not matching:
        return "none"

    all_deterministic = True
    for trace in matching:
        stats = _trace_probability_stats(trace)
        if not stats.get("valid"):
            return "none"
        if not stats.get("deterministic", False):
            all_deterministic = False
    return "deterministic_only" if all_deterministic else "stochastic_support"


def support_checks_pass_for_trace_kinds(
    attempts: list[dict[str, Any]],
    trace_kinds: list[str],
    min_candidate_probability: float,
    min_chosen_probability: float,
    min_entropy_bits: float,
) -> bool:
    target_kinds = set(trace_kinds)
    if not target_kinds:
        return False
    for attempt in attempts:
        policy_decisions = attempt.get("policy_decisions")
        if not isinstance(policy_decisions, list):
            return False
        for trace in extract_decision_traces(attempt):
            if not isinstance(trace, dict):
                return False
            trace_kind = trace.get("trace_kind")
            if trace_kind not in target_kinds:
                continue
            decision_id = trace.get("decision_id")
            matches = [
                d
                for d in policy_decisions
                if isinstance(d, dict) and d.get("decision_id") == decision_id
            ]
            if not matches:
                return False
            for match in matches:
                if not trace_kind_policy_domain_compatible(
                    trace_kind,
                    match.get("policy_domain"),
                ):
                    return False
                recomputed = recompute_support_claim_for_trace(
                    trace,
                    min_candidate_probability=min_candidate_probability,
                    min_chosen_probability=min_chosen_probability,
                    min_entropy_bits=min_entropy_bits,
                )
                if not recomputed.get("valid"):
                    return False
                entropy_floor_expected = bool(recomputed.get("entropy_floor_expected", False))
                min_support_expected = bool(recomputed.get("min_support_expected", False))
                expected_status = str(recomputed.get("status_expected", "fail"))
                if match.get("entropy_floor_met") is not entropy_floor_expected:
                    return False
                if match.get("min_support_met") is not min_support_expected:
                    return False
                if match.get("support_check_status") != expected_status:
                    return False
                if expected_status != "pass":
                    return False
    return True


def routing_support_checks_pass(attempts: list[dict[str, Any]]) -> bool:
    return support_checks_pass_for_trace_kinds(
        attempts,
        ["routing"],
        min_candidate_probability=0.0,
        min_chosen_probability=0.0,
        min_entropy_bits=0.0,
    )


def trace_kind_policy_domain_compatible(trace_kind: Any, policy_domain: Any) -> bool:
    if not isinstance(trace_kind, str) or not isinstance(policy_domain, str):
        return False
    if trace_kind in {"routing", "holdout", "anchor", "diagnosis", "calibration"}:
        return policy_domain == trace_kind
    if trace_kind == "feedback":
        return policy_domain == "other"
    if trace_kind == "quarantine":
        return policy_domain in {"invariance", "other"}
    if trace_kind == "other":
        return policy_domain == "other"
    return False


def compute_ope_support_report(
    attempts: list[dict[str, Any]],
    manifest: dict[str, Any],
) -> dict[str, Any]:
    contract = manifest.get("ope_claim_contract")
    if not isinstance(contract, dict):
        return {
            "valid_contract": False,
            "contract_error": "ope_claim_contract_not_object",
        }

    target_trace_kinds_raw = contract.get("target_trace_kinds")
    context_axes_raw = contract.get("context_axes")
    if not isinstance(target_trace_kinds_raw, list) or not target_trace_kinds_raw:
        return {"valid_contract": False, "contract_error": "target_trace_kinds_invalid"}
    if not isinstance(context_axes_raw, list) or not context_axes_raw:
        return {"valid_contract": False, "contract_error": "context_axes_invalid"}

    target_trace_kinds = [
        tk for tk in target_trace_kinds_raw if isinstance(tk, str) and tk != ""
    ]
    context_axes = [
        axis
        for axis in context_axes_raw
        if isinstance(axis, str) and axis in OPE_CONTEXT_AXES
    ]
    if len(target_trace_kinds) != len(target_trace_kinds_raw):
        return {"valid_contract": False, "contract_error": "target_trace_kinds_invalid"}
    if len(context_axes) != len(context_axes_raw):
        return {"valid_contract": False, "contract_error": "context_axes_invalid"}

    min_stochastic_fraction = contract.get("min_stochastic_fraction")
    min_candidate_probability = contract.get("min_candidate_probability")
    min_chosen_probability = contract.get("min_chosen_probability")
    min_entropy_bits = contract.get("min_entropy_bits")
    min_context_coverage_fraction = contract.get("min_context_coverage_fraction")
    min_decisions_per_context = contract.get("min_decisions_per_context")
    numeric_thresholds = (
        min_stochastic_fraction,
        min_candidate_probability,
        min_chosen_probability,
        min_entropy_bits,
        min_context_coverage_fraction,
    )
    if not all(is_strict_number(v) for v in numeric_thresholds):
        return {"valid_contract": False, "contract_error": "threshold_not_numeric"}
    if (
        float(min_stochastic_fraction) < 0.0
        or float(min_stochastic_fraction) > 1.0
        or float(min_context_coverage_fraction) < 0.0
        or float(min_context_coverage_fraction) > 1.0
        or float(min_candidate_probability) <= 0.0
        or float(min_candidate_probability) > 1.0
        or float(min_chosen_probability) <= 0.0
        or float(min_chosen_probability) > 1.0
        or float(min_entropy_bits) < 0.0
        or not is_strict_int(min_decisions_per_context)
        or min_decisions_per_context <= 0
    ):
        return {"valid_contract": False, "contract_error": "threshold_out_of_range"}

    per_kind: dict[str, dict[str, Any]] = {}
    global_valid = True
    global_min_candidate = 1.0
    global_min_chosen = 1.0
    global_min_entropy_bits = float("inf")
    global_min_stochastic_fraction = 1.0
    global_min_context_coverage = 1.0
    global_min_decisions_per_context: int | None = None

    for trace_kind in target_trace_kinds:
        rows: list[tuple[dict[str, Any], dict[str, Any]]] = []
        for attempt in attempts:
            for trace in extract_traces_by_kind(attempt, trace_kind):
                rows.append((attempt, trace))
        decisions_total = len(rows)
        if decisions_total == 0:
            per_kind[trace_kind] = {
                "trace_support": "none",
                "decisions_total": 0,
                "stochastic_fraction": 0.0,
                "min_candidate_probability_observed": 0.0,
                "min_chosen_probability_observed": 0.0,
                "min_entropy_bits_observed": 0.0,
                "context_coverage_fraction": 0.0,
                "min_decisions_per_context_observed": 0,
                "valid": False,
            }
            global_valid = False
            global_min_stochastic_fraction = min(global_min_stochastic_fraction, 0.0)
            global_min_context_coverage = min(global_min_context_coverage, 0.0)
            global_min_candidate = min(global_min_candidate, 0.0)
            global_min_chosen = min(global_min_chosen, 0.0)
            global_min_entropy_bits = min(global_min_entropy_bits, 0.0)
            global_min_decisions_per_context = 0
            continue

        stochastic_count = 0
        has_invalid = False
        min_candidate = 1.0
        min_chosen = 1.0
        min_entropy = float("inf")
        context_counts: dict[tuple[Any, ...], int] = {}
        context_has_stochastic: dict[tuple[Any, ...], bool] = {}
        for attempt, trace in rows:
            stats = _trace_probability_stats(trace)
            if not stats.get("valid"):
                has_invalid = True
                continue
            deterministic = bool(stats.get("deterministic", False))
            if not deterministic:
                stochastic_count += 1
            min_candidate = min(min_candidate, float(stats.get("min_candidate_probability", 1.0)))
            min_chosen = min(min_chosen, float(stats.get("chosen_probability", 1.0)))
            min_entropy = min(min_entropy, float(stats.get("entropy_bits", 0.0)))
            context_key = tuple(attempt.get(axis) for axis in context_axes)
            context_counts[context_key] = context_counts.get(context_key, 0) + 1
            if not deterministic:
                context_has_stochastic[context_key] = True

        trace_support = classify_trace_kind_support(attempts, trace_kind)
        stochastic_fraction = float(stochastic_count) / float(decisions_total)
        contexts_total = len(context_counts)
        contexts_with_stochastic = sum(1 for k in context_counts if context_has_stochastic.get(k, False))
        context_coverage_fraction = (
            float(contexts_with_stochastic) / float(contexts_total) if contexts_total > 0 else 0.0
        )
        min_decisions_observed = min(context_counts.values()) if context_counts else 0
        kind_valid = not has_invalid
        per_kind[trace_kind] = {
            "trace_support": trace_support,
            "decisions_total": decisions_total,
            "stochastic_fraction": stochastic_fraction,
            "min_candidate_probability_observed": min_candidate if kind_valid else 0.0,
            "min_chosen_probability_observed": min_chosen if kind_valid else 0.0,
            "min_entropy_bits_observed": min_entropy if kind_valid else 0.0,
            "context_coverage_fraction": context_coverage_fraction if kind_valid else 0.0,
            "min_decisions_per_context_observed": min_decisions_observed if kind_valid else 0,
            "valid": kind_valid,
        }
        global_valid = global_valid and kind_valid
        global_min_stochastic_fraction = min(global_min_stochastic_fraction, stochastic_fraction)
        global_min_context_coverage = min(global_min_context_coverage, context_coverage_fraction)
        global_min_candidate = min(
            global_min_candidate,
            min_candidate if kind_valid else 0.0,
        )
        global_min_chosen = min(
            global_min_chosen,
            min_chosen if kind_valid else 0.0,
        )
        global_min_entropy_bits = min(
            global_min_entropy_bits,
            min_entropy if kind_valid else 0.0,
        )
        if global_min_decisions_per_context is None:
            global_min_decisions_per_context = min_decisions_observed if kind_valid else 0
        else:
            global_min_decisions_per_context = min(
                global_min_decisions_per_context,
                min_decisions_observed if kind_valid else 0,
            )

    support_checks_pass = support_checks_pass_for_trace_kinds(
        attempts,
        target_trace_kinds,
        min_candidate_probability=float(min_candidate_probability),
        min_chosen_probability=float(min_chosen_probability),
        min_entropy_bits=float(min_entropy_bits),
    )
    thresholds_pass = (
        global_valid
        and global_min_stochastic_fraction >= float(min_stochastic_fraction)
        and global_min_candidate >= float(min_candidate_probability)
        and global_min_chosen >= float(min_chosen_probability)
        and global_min_entropy_bits >= float(min_entropy_bits)
        and global_min_context_coverage >= float(min_context_coverage_fraction)
        and (global_min_decisions_per_context or 0) >= int(min_decisions_per_context)
    )
    full_support_ready = thresholds_pass and support_checks_pass
    return {
        "valid_contract": True,
        "target_trace_kinds": target_trace_kinds,
        "context_axes": context_axes,
        "per_kind": per_kind,
        "global_min_stochastic_fraction": global_min_stochastic_fraction,
        "global_min_candidate_probability": global_min_candidate,
        "global_min_chosen_probability": global_min_chosen,
        "global_min_entropy_bits": global_min_entropy_bits if global_min_entropy_bits != float("inf") else 0.0,
        "global_min_context_coverage_fraction": global_min_context_coverage,
        "global_min_decisions_per_context": global_min_decisions_per_context or 0,
        "support_checks_pass": support_checks_pass,
        "thresholds_pass": thresholds_pass,
        "full_support_ready": full_support_ready,
    }


def propensity_logs_present_for_targets(support_report: dict[str, Any]) -> bool:
    if not isinstance(support_report, dict):
        return False
    if support_report.get("valid_contract") is not True:
        return False
    per_kind = support_report.get("per_kind")
    target_trace_kinds = support_report.get("target_trace_kinds")
    if not isinstance(per_kind, dict):
        return False
    if not isinstance(target_trace_kinds, list) or not target_trace_kinds:
        return False
    for trace_kind in target_trace_kinds:
        row = per_kind.get(trace_kind)
        if not isinstance(row, dict):
            return False
        decisions_total = row.get("decisions_total")
        trace_support = row.get("trace_support")
        valid = row.get("valid")
        if not is_strict_int(decisions_total) or decisions_total <= 0:
            return False
        if trace_support not in {"deterministic_only", "stochastic_support"}:
            return False
        if valid is not True:
            return False
    return True


ASSISTANCE_MODE_ORDER = {
    "closed_book": 0,
    "open_book": 1,
    "tool_assisted": 2,
    "mixed": 3,
}


def _expected_diagnosis_semantics(
    assistance_mode: Any,
    evidence_channel: Any,
) -> tuple[str, str]:
    closed_book = assistance_mode == "closed_book"
    diagnostic_channel = evidence_channel in DIAGNOSTIC_EVIDENCE_CHANNELS
    if closed_book and diagnostic_channel:
        return ("eligible", "none")
    if not closed_book and diagnostic_channel:
        return ("ineligible", "assistance_mode_not_closed_book")
    if closed_book and not diagnostic_channel:
        return ("ineligible", "channel_not_diagnostic")
    return ("ineligible", "assistance_and_channel")


def _assistance_observed_at_least_intended(
    observed: Any,
    intended: Any,
) -> bool:
    observed_rank = ASSISTANCE_MODE_ORDER.get(observed)
    intended_rank = ASSISTANCE_MODE_ORDER.get(intended)
    if observed_rank is None or intended_rank is None:
        return False
    return observed_rank >= intended_rank


def precommit_semantics_binding_consistent(
    attempt: dict[str, Any],
    precommit: dict[str, Any],
) -> bool:
    # Identity-critical bindings should remain explicit, not implied by hash comparison alone.
    identity_pairs = (
        ("run_id", "run_id"),
        ("timeline_id", "timeline_id"),
        ("session_id", "session_id"),
        ("attempt_id", "attempt_id"),
        ("learner_id", "learner_id"),
        ("item_id", "item_id"),
        ("probe_family_id", "probe_family_id"),
        ("commitment_id", "commitment_id"),
    )
    for precommit_key, attempt_key in identity_pairs:
        if precommit.get(precommit_key) != attempt.get(attempt_key):
            return False

    precommit_commitment = precommit.get("semantic_commitment")
    attempt_commitment = attempt.get("semantic_commitment")
    if not isinstance(precommit_commitment, dict) or not isinstance(attempt_commitment, dict):
        return False
    if sha256_json(precommit_commitment) != sha256_json(attempt_commitment):
        return False

    intended_channel = precommit_commitment.get("evidence_channel_intended")
    intended_assistance = precommit_commitment.get("assistance_contract_intended")
    intended_eligibility = precommit_commitment.get("diagnosis_update_eligibility_intended")
    intended_reason = precommit_commitment.get("ineligibility_reason_intended")
    intended_allowed = precommit_commitment.get("allowed_update_partitions_intended")
    intended_telemetry_ids = precommit_commitment.get("telemetry_event_ids_intended")
    if not isinstance(intended_allowed, list):
        return False
    if not isinstance(intended_telemetry_ids, list):
        return False

    # Top-level intended fields must mirror the semantic commitment object.
    if precommit.get("evidence_channel_intended") != intended_channel:
        return False
    if precommit.get("assistance_contract_intended") != intended_assistance:
        return False
    if precommit.get("diagnosis_update_eligibility_intended") != intended_eligibility:
        return False
    if precommit.get("ineligibility_reason_intended") != intended_reason:
        return False
    precommit_allowed = precommit.get("allowed_update_partitions_intended")
    if not isinstance(precommit_allowed, list):
        return False
    if sorted(precommit_allowed) != sorted(intended_allowed):
        return False
    precommit_telemetry_ids = precommit.get("telemetry_event_ids_intended")
    if not isinstance(precommit_telemetry_ids, list):
        return False
    if sorted(precommit_telemetry_ids) != sorted(intended_telemetry_ids):
        return False

    observed_channel = attempt.get("evidence_channel")
    observed_assistance = attempt.get("assistance_mode_derived")
    claimed_assistance = attempt.get("assistance_mode")
    derivation_quality = attempt.get("assistance_derivation_quality")
    observed_eligibility = attempt.get("diagnosis_update_eligibility")
    observed_reason = attempt.get("ineligibility_reason")
    observed_allowed = attempt.get("allowed_update_partitions")
    observed_telemetry_ids = attempt.get("telemetry_event_ids")
    if not isinstance(observed_allowed, list):
        return False
    if not isinstance(observed_telemetry_ids, list):
        return False
    if derivation_quality != "derived_from_telemetry":
        return False

    # Channel intent is precommitted and must not drift.
    if intended_channel != observed_channel:
        return False
    if claimed_assistance != observed_assistance:
        return False
    if sorted(intended_telemetry_ids) != sorted(observed_telemetry_ids):
        return False
    # Assistance can only be observed as equal-or-more-assisted than intended.
    if not _assistance_observed_at_least_intended(observed_assistance, intended_assistance):
        return False

    expected_intended_eligibility, expected_intended_reason = _expected_diagnosis_semantics(
        intended_assistance,
        intended_channel,
    )
    if intended_eligibility != expected_intended_eligibility:
        return False
    if intended_reason != expected_intended_reason:
        return False
    if expected_intended_eligibility == "eligible":
        if "diagnosis_state" not in intended_allowed:
            return False
    elif "diagnosis_state" in intended_allowed:
        return False

    expected_observed_eligibility, expected_observed_reason = _expected_diagnosis_semantics(
        observed_assistance,
        observed_channel,
    )
    if observed_eligibility != expected_observed_eligibility:
        return False
    if observed_reason != expected_observed_reason:
        return False
    if expected_observed_eligibility == "eligible":
        if "diagnosis_state" not in observed_allowed:
            return False
    elif "diagnosis_state" in observed_allowed:
        return False

    return True


def telemetry_window_bindings_consistent(
    attempts: list[dict[str, Any]],
    telemetry_events: list[dict[str, Any]],
    precommits: list[dict[str, Any]],
    events: list[dict[str, Any]] | None = None,
) -> bool:
    telemetry_by_id: dict[str, dict[str, Any]] = {}
    telemetry_ts_by_id: dict[str, Any] = {}
    for telemetry in telemetry_events:
        telemetry_event_id = telemetry.get("telemetry_event_id")
        attempt_id = telemetry.get("attempt_id")
        run_id = telemetry.get("run_id")
        timeline_id = telemetry.get("timeline_id")
        if not isinstance(telemetry_event_id, str) or telemetry_event_id == "":
            return False
        if telemetry_event_id in telemetry_by_id:
            return False
        if not isinstance(attempt_id, str) or attempt_id == "":
            return False
        if not isinstance(run_id, str) or run_id == "":
            return False
        if not isinstance(timeline_id, str) or timeline_id == "":
            return False
        telemetry_ts_raw = telemetry.get("telemetry_ts_utc")
        if not isinstance(telemetry_ts_raw, str) or telemetry_ts_raw == "":
            return False
        try:
            telemetry_ts = parse_rfc3339_utc(telemetry_ts_raw)
        except ValueError:
            return False
        telemetry_by_id[telemetry_event_id] = telemetry
        telemetry_ts_by_id[telemetry_event_id] = telemetry_ts

    if attempts and not telemetry_events:
        return False

    precommit_by_event_id: dict[str, dict[str, Any]] = {}
    precommit_by_attempt_id: dict[str, dict[str, Any]] = {}
    precommit_sequence_by_attempt: dict[str, int] = {}
    observed_sequence_by_attempt: dict[str, int] = {}
    telemetry_sequence_by_id: dict[str, int] = {}
    if events is not None:
        seen_event_seqs: set[int] = set()
        for event in events:
            seq = event.get("ledger_sequence_no")
            if not is_strict_int(seq) or seq <= 0:
                return False
            if seq in seen_event_seqs:
                return False
            seen_event_seqs.add(int(seq))
            event_type = event.get("event_type")
            payload = event.get("payload")
            if not isinstance(payload, dict):
                return False
            if event_type == "attempt_precommitted":
                attempt_id = payload.get("attempt_id")
                if not isinstance(attempt_id, str) or attempt_id == "":
                    return False
                precommit_sequence_by_attempt[attempt_id] = int(seq)
            elif event_type == "attempt_observed":
                attempt_id = payload.get("attempt_id")
                if not isinstance(attempt_id, str) or attempt_id == "":
                    return False
                observed_sequence_by_attempt[attempt_id] = int(seq)
            elif event_type == "attempt_telemetry":
                telemetry_event_id = payload.get("telemetry_event_id")
                if not isinstance(telemetry_event_id, str) or telemetry_event_id == "":
                    return False
                telemetry_sequence_by_id[telemetry_event_id] = int(seq)
    for precommit in precommits:
        precommit_event_id = precommit.get("precommit_event_id")
        attempt_id = precommit.get("attempt_id")
        if not isinstance(precommit_event_id, str) or precommit_event_id == "":
            return False
        if not isinstance(attempt_id, str) or attempt_id == "":
            return False
        if precommit_event_id in precommit_by_event_id:
            return False
        if attempt_id in precommit_by_attempt_id:
            return False
        precommit_by_event_id[precommit_event_id] = precommit
        precommit_by_attempt_id[attempt_id] = precommit

    for attempt in attempts:
        attempt_id = attempt.get("attempt_id")
        precommit_event_id = attempt.get("precommit_event_id")
        run_id = attempt.get("run_id")
        timeline_id = attempt.get("timeline_id")
        learner_id = attempt.get("learner_id")
        telemetry_ids = attempt.get("telemetry_event_ids")
        attempt_ts_raw = attempt.get("attempt_ts_utc")
        if not isinstance(precommit_event_id, str) or precommit_event_id == "":
            return False
        if not isinstance(attempt_ts_raw, str) or attempt_ts_raw == "":
            return False
        try:
            attempt_ts = parse_rfc3339_utc(attempt_ts_raw)
        except ValueError:
            return False

        precommit = precommit_by_event_id.get(precommit_event_id)
        if precommit is None:
            return False
        if precommit_by_attempt_id.get(attempt_id) is not precommit:
            return False
        presented_ts_raw = precommit.get("presented_ts_utc")
        if not isinstance(presented_ts_raw, str) or presented_ts_raw == "":
            return False
        try:
            presented_ts = parse_rfc3339_utc(presented_ts_raw)
        except ValueError:
            return False
        if presented_ts > attempt_ts:
            return False
        precommit_seq = precommit_sequence_by_attempt.get(attempt_id)
        observed_seq = observed_sequence_by_attempt.get(attempt_id)
        if events is not None:
            if precommit_seq is None or observed_seq is None:
                return False
            if precommit_seq >= observed_seq:
                return False

        if not isinstance(telemetry_ids, list) or not telemetry_ids:
            return False
        declared_ids: set[str] = set()
        declared_has_response_submitted = False
        for telemetry_event_id in telemetry_ids:
            if not isinstance(telemetry_event_id, str) or telemetry_event_id == "":
                return False
            if telemetry_event_id in declared_ids:
                return False
            declared_ids.add(telemetry_event_id)
            event = telemetry_by_id.get(telemetry_event_id)
            if event is None:
                return False
            if event.get("attempt_id") != attempt_id:
                return False
            if event.get("run_id") != run_id:
                return False
            if event.get("timeline_id") != timeline_id:
                return False
            if event.get("learner_id") != learner_id:
                return False
            if event.get("telemetry_kind") == "response_submitted":
                declared_has_response_submitted = True
            event_ts = telemetry_ts_by_id.get(telemetry_event_id)
            if event_ts is None:
                return False
            if events is not None:
                event_seq = telemetry_sequence_by_id.get(telemetry_event_id)
                if event_seq is None:
                    return False
                if precommit_seq is None or observed_seq is None:
                    return False
                if not (precommit_seq < event_seq <= observed_seq):
                    return False
                if event_ts < presented_ts:
                    return False
                if event_ts > attempt_ts:
                    return False
            else:
                if event_ts < presented_ts:
                    return False
                if event_ts > attempt_ts:
                    return False
        if not declared_has_response_submitted:
            return False

        derived_ids: set[str] = set()
        derived_has_response_submitted = False
        for telemetry_event_id, event in telemetry_by_id.items():
            if event.get("attempt_id") != attempt_id:
                continue
            if event.get("run_id") != run_id:
                continue
            if event.get("timeline_id") != timeline_id:
                continue
            if event.get("learner_id") != learner_id:
                continue
            event_ts = telemetry_ts_by_id.get(telemetry_event_id)
            if event_ts is None:
                return False
            if events is not None:
                event_seq = telemetry_sequence_by_id.get(telemetry_event_id)
                if event_seq is None:
                    return False
                if precommit_seq is None or observed_seq is None:
                    return False
                if not (precommit_seq < event_seq <= observed_seq):
                    continue
                if event_ts < presented_ts or event_ts > attempt_ts:
                    return False
            else:
                if event_ts < presented_ts or event_ts > attempt_ts:
                    continue
            derived_ids.add(telemetry_event_id)
            if event.get("telemetry_kind") == "response_submitted":
                derived_has_response_submitted = True
        if not derived_has_response_submitted:
            return False
        if declared_ids != derived_ids:
            return False
    return True


def precommit_bindings_consistent(
    attempts: list[dict[str, Any]],
    precommits: list[dict[str, Any]],
) -> bool:
    precommits_by_event_id: dict[str, dict[str, Any]] = {}
    precommits_by_attempt_id: dict[str, dict[str, Any]] = {}
    for precommit in precommits:
        event_id = precommit.get("precommit_event_id")
        attempt_id = precommit.get("attempt_id")
        if not isinstance(event_id, str) or event_id == "":
            return False
        if not isinstance(attempt_id, str) or attempt_id == "":
            return False
        if event_id in precommits_by_event_id:
            return False
        if attempt_id in precommits_by_attempt_id:
            return False
        precommits_by_event_id[event_id] = precommit
        precommits_by_attempt_id[attempt_id] = precommit

    for attempt in attempts:
        precommit_event_id = attempt.get("precommit_event_id")
        attempt_id = attempt.get("attempt_id")
        if not isinstance(precommit_event_id, str) or precommit_event_id == "":
            return False
        if not isinstance(attempt_id, str) or attempt_id == "":
            return False

        precommit = precommits_by_event_id.get(precommit_event_id)
        if precommit is None:
            return False
        if precommits_by_attempt_id.get(attempt_id) is not precommit:
            return False
        if not precommit_semantics_binding_consistent(attempt, precommit):
            return False
        precommit_hash = precommit.get("precommit_hash")
        attempt_hash = attempt.get("precommit_hash")
        if not isinstance(precommit_hash, str) or precommit_hash == "":
            return False
        if not isinstance(attempt_hash, str) or attempt_hash == "":
            return False
        if precommit_hash != attempt_hash:
            return False
        precommit_envelope_hash = precommit.get("precommit_envelope_hash")
        attempt_envelope_hash = attempt.get("precommit_envelope_hash")
        if not isinstance(precommit_envelope_hash, str) or precommit_envelope_hash == "":
            return False
        if not isinstance(attempt_envelope_hash, str) or attempt_envelope_hash == "":
            return False
        if precommit_envelope_hash != attempt_envelope_hash:
            return False

        presented_ts_raw = precommit.get("presented_ts_utc")
        observed_ts_raw = attempt.get("attempt_ts_utc")
        if not isinstance(presented_ts_raw, str) or not isinstance(observed_ts_raw, str):
            return False
        try:
            presented_ts = parse_rfc3339_utc(presented_ts_raw)
            observed_ts = parse_rfc3339_utc(observed_ts_raw)
        except ValueError:
            return False
        if presented_ts > observed_ts:
            return False
    return True


def event_sequence_integrity_valid(events: list[dict[str, Any]]) -> bool:
    seen: set[int] = set()
    for event in events:
        seq = event.get("ledger_sequence_no")
        if not is_strict_int(seq) or seq <= 0:
            return False
        if seq in seen:
            return False
        seen.add(seq)
    return True


def event_ledger_integrity_valid(
    events: list[dict[str, Any]],
    manifest: dict[str, Any] | None = None,
) -> bool:
    if not events:
        return False
    seen_sequences: set[int] = set()
    seen_event_ids: set[str] = set()
    manifest_run_id = manifest.get("run_id") if isinstance(manifest, dict) else None
    manifest_timeline_id = manifest.get("timeline_id") if isinstance(manifest, dict) else None
    written_ts_by_seq: dict[int, Any] = {}
    for event in events:
        event_id = event.get("event_id")
        run_id = event.get("run_id")
        event_type = event.get("event_type")
        seq = event.get("ledger_sequence_no")
        written_ts_raw = event.get("event_written_ts_utc")
        payload = event.get("payload")
        if not isinstance(event_id, str) or event_id == "":
            return False
        if event_id in seen_event_ids:
            return False
        seen_event_ids.add(event_id)
        if not isinstance(run_id, str) or run_id == "":
            return False
        if manifest_run_id is not None and run_id != manifest_run_id:
            return False
        if event_type not in EVENT_TYPES:
            return False
        expected_prefix = EVENT_ID_PREFIX_BY_TYPE.get(event_type)
        if expected_prefix is None or not event_id.startswith(expected_prefix):
            return False
        if not is_strict_int(seq) or seq <= 0:
            return False
        if seq in seen_sequences:
            return False
        seen_sequences.add(seq)
        if not isinstance(written_ts_raw, str) or written_ts_raw == "":
            return False
        try:
            written_ts_by_seq[int(seq)] = parse_rfc3339_utc(written_ts_raw)
        except ValueError:
            return False
        if not isinstance(payload, dict):
            return False
        if payload.get("run_id") != run_id:
            return False
        payload_id_field = EVENT_PAYLOAD_ID_FIELD_BY_TYPE.get(event_type)
        if payload_id_field is None:
            return False
        payload_id = payload.get(payload_id_field)
        if not isinstance(payload_id, str) or payload_id == "":
            return False
        payload_timeline_id = payload.get("timeline_id")
        if manifest_timeline_id is not None and payload_timeline_id is not None:
            if payload_timeline_id != manifest_timeline_id:
                return False
    ordered_sequences = sorted(written_ts_by_seq.keys())
    previous_ts = None
    for seq in ordered_sequences:
        current_ts = written_ts_by_seq[seq]
        if previous_ts is not None and current_ts < previous_ts:
            return False
        previous_ts = current_ts
    return True


def event_payloads_by_type(
    events: list[dict[str, Any]],
    event_type: str,
) -> list[dict[str, Any]]:
    payloads: list[dict[str, Any]] = []
    for event in events:
        if event.get("event_type") != event_type:
            continue
        payload = event.get("payload")
        if isinstance(payload, dict):
            payloads.append(payload)
    return payloads


def safe_mode_transition_sequence_coherent(
    transitions: list[dict[str, Any]],
    events: list[dict[str, Any]] | None = None,
) -> bool:
    if not transitions:
        return True
    ordered: list[dict[str, Any]] = []
    if events is not None:
        transition_events: list[dict[str, Any]] = []
        for event in events:
            if event.get("event_type") != "safe_mode_transition":
                continue
            seq = event.get("ledger_sequence_no")
            payload = event.get("payload")
            if not is_strict_int(seq) or seq <= 0:
                return False
            if not isinstance(payload, dict):
                return False
            transition_events.append({"seq": seq, "payload": payload})
        transition_events.sort(key=lambda row: int(row["seq"]))
        ordered = [row["payload"] for row in transition_events]
    else:
        ordered = sorted(
            transitions,
            key=lambda row: (
                str(row.get("event_ts_utc", "")),
                str(row.get("event_id", "")),
            ),
        )
    current_state = "NORMAL"
    for transition in ordered:
        prior_state = transition.get("prior_state")
        next_state = transition.get("next_state")
        if not isinstance(prior_state, str) or not isinstance(next_state, str):
            return False
        if prior_state != current_state:
            return False
        current_state = next_state
    return True


def precommit_response_sequence_coherent(
    events: list[dict[str, Any]],
) -> bool:
    if not events:
        return False
    precommit_seq_by_attempt: dict[tuple[str, str], int] = {}
    observed_seq_by_attempt: dict[tuple[str, str], int] = {}
    response_seqs_by_attempt: dict[tuple[str, str], list[int]] = {}
    precommit_written_ts_by_attempt: dict[tuple[str, str], Any] = {}
    observed_written_ts_by_attempt: dict[tuple[str, str], Any] = {}
    response_written_ts_by_attempt: dict[tuple[str, str], list[Any]] = {}

    for event in events:
        event_type = event.get("event_type")
        seq = event.get("ledger_sequence_no")
        payload = event.get("payload")
        if not is_strict_int(seq) or seq <= 0 or not isinstance(payload, dict):
            return False
        written_ts_raw = event.get("event_written_ts_utc")
        if not isinstance(written_ts_raw, str) or written_ts_raw == "":
            return False
        try:
            written_ts = parse_rfc3339_utc(written_ts_raw)
        except ValueError:
            return False
        run_id = payload.get("run_id")
        attempt_id: Any = None
        if event_type == "attempt_precommitted":
            attempt_id = payload.get("attempt_id")
        elif event_type == "attempt_observed":
            attempt_id = payload.get("attempt_id")
        elif event_type == "attempt_telemetry":
            attempt_id = payload.get("attempt_id")
        else:
            continue
        if not isinstance(run_id, str) or run_id == "":
            return False
        if not isinstance(attempt_id, str) or attempt_id == "":
            return False
        key = (run_id, attempt_id)
        if event_type == "attempt_precommitted":
            if key in precommit_seq_by_attempt:
                return False
            precommit_seq_by_attempt[key] = int(seq)
            precommit_written_ts_by_attempt[key] = written_ts
        elif event_type == "attempt_observed":
            if key in observed_seq_by_attempt:
                return False
            observed_seq_by_attempt[key] = int(seq)
            observed_written_ts_by_attempt[key] = written_ts
        elif payload.get("telemetry_kind") == "response_submitted":
            response_seqs_by_attempt.setdefault(key, []).append(int(seq))
            response_written_ts_by_attempt.setdefault(key, []).append(written_ts)

    if not observed_seq_by_attempt:
        return False
    for key, observed_seq in observed_seq_by_attempt.items():
        precommit_seq = precommit_seq_by_attempt.get(key)
        response_seqs = response_seqs_by_attempt.get(key, [])
        precommit_written_ts = precommit_written_ts_by_attempt.get(key)
        observed_written_ts = observed_written_ts_by_attempt.get(key)
        response_written_ts = response_written_ts_by_attempt.get(key, [])
        if precommit_seq is None:
            return False
        if not response_seqs:
            return False
        if precommit_written_ts is None or observed_written_ts is None or not response_written_ts:
            return False
        min_response_seq = min(response_seqs)
        min_response_written_ts = min(response_written_ts)
        if not (precommit_seq < min_response_seq <= observed_seq):
            return False
        if not (precommit_written_ts < min_response_written_ts <= observed_written_ts):
            return False
    return True


def safe_mode_update_profile_bindings_consistent(
    events: list[dict[str, Any]],
) -> bool:
    if not events:
        return True
    ordered: list[dict[str, Any]] = []
    for event in events:
        seq = event.get("ledger_sequence_no")
        if not is_strict_int(seq) or seq <= 0:
            return False
        ordered.append(event)
    ordered.sort(key=lambda row: int(row.get("ledger_sequence_no")))

    current_state = "NORMAL"
    current_profile_id: str | None = None
    binding_active = False
    for event in ordered:
        event_type = event.get("event_type")
        payload = event.get("payload")
        if not isinstance(payload, dict):
            continue
        if event_type == "safe_mode_transition":
            prior_state = payload.get("prior_state")
            next_state = payload.get("next_state")
            profile_id = payload.get("profile_id")
            if not isinstance(prior_state, str) or not isinstance(next_state, str):
                return False
            if not isinstance(profile_id, str) or profile_id == "":
                return False
            if prior_state != current_state:
                return False
            if profile_id not in SAFE_MODE_PROFILE_IDS:
                return False
            expected_parent_state = SAFE_MODE_PROFILE_PARENT_STATES.get(profile_id)
            if expected_parent_state != next_state:
                return False
            current_state = next_state
            current_profile_id = profile_id
            binding_active = True
            continue

        if event_type == "state_update":
            profile_id = payload.get("safe_mode_profile_id")
            if not isinstance(profile_id, str) or profile_id == "":
                return False
            if profile_id not in SAFE_MODE_PROFILE_IDS:
                return False
            if binding_active and current_profile_id is not None and profile_id != current_profile_id:
                return False
    return True


def records_unique_by_id(records: list[dict[str, Any]], id_field: str) -> bool:
    seen: set[str] = set()
    for record in records:
        value = record.get(id_field)
        if not isinstance(value, str) or value == "":
            return False
        if value in seen:
            return False
        seen.add(value)
    return True


def duplicate_ids_with_conflicting_payload(
    records: list[dict[str, Any]],
    id_field: str,
) -> bool:
    hashes_by_id: dict[str, str] = {}
    for record in records:
        value = record.get(id_field)
        if not isinstance(value, str) or value == "":
            continue
        current_hash = sha256_json(record)
        prior_hash = hashes_by_id.get(value)
        if prior_hash is None:
            hashes_by_id[value] = current_hash
            continue
        if prior_hash != current_hash:
            return True
    return False


def event_typed_views_consistent(
    events: list[dict[str, Any]],
    attempts: list[dict[str, Any]],
    precommits: list[dict[str, Any]],
    telemetry_events: list[dict[str, Any]],
    snapshots: list[dict[str, Any]],
    updates: list[dict[str, Any]],
    migrations: list[dict[str, Any]],
) -> bool:
    typed_records_by_type: dict[str, tuple[list[dict[str, Any]], str]] = {
        "attempt_observed": (attempts, "attempt_id"),
        "attempt_precommitted": (precommits, "precommit_event_id"),
        "attempt_telemetry": (telemetry_events, "telemetry_event_id"),
        "snapshot_checkpoint": (snapshots, "snapshot_id"),
        "state_update": (updates, "update_id"),
        "state_migration": (migrations, "migration_event_id"),
    }
    events_by_type_and_id: dict[str, dict[str, str]] = {
        key: {} for key in typed_records_by_type.keys()
    }
    for event in events:
        event_type = event.get("event_type")
        if event_type not in events_by_type_and_id:
            continue
        payload = event.get("payload")
        if not isinstance(payload, dict):
            return False
        id_field = typed_records_by_type[event_type][1]
        payload_id = payload.get(id_field)
        if not isinstance(payload_id, str) or payload_id == "":
            return False
        payload_hash = sha256_json(payload)
        prior_hash = events_by_type_and_id[event_type].get(payload_id)
        if prior_hash is not None and prior_hash != payload_hash:
            return False
        events_by_type_and_id[event_type][payload_id] = payload_hash

    for event_type, (records, id_field) in typed_records_by_type.items():
        typed_by_id: dict[str, str] = {}
        for record in records:
            payload_id = record.get(id_field)
            if not isinstance(payload_id, str) or payload_id == "":
                return False
            payload_hash = sha256_json(record)
            prior_hash = typed_by_id.get(payload_id)
            if prior_hash is not None and prior_hash != payload_hash:
                return False
            typed_by_id[payload_id] = payload_hash

        event_view = events_by_type_and_id[event_type]
        if set(typed_by_id.keys()) != set(event_view.keys()):
            return False
        for payload_id, typed_hash in typed_by_id.items():
            if event_view.get(payload_id) != typed_hash:
                return False
    return True


def governor_fields_present(update: dict[str, Any]) -> bool:
    fields = {
        "calibration_status_at_update",
        "applied_update_multiplier",
        "governor_decision",
        "governor_reason",
        "stratum_id",
        "safe_mode_profile_id",
        "governor_transform_version",
        "proposed_state_patch",
        "base_value_at_proposal",
    }
    return all(field in update for field in fields)


def provenance_snapshot_ref_integrity(
    attempts: list[dict[str, Any]],
    snapshots: list[dict[str, Any]],
) -> bool:
    snapshot_ts_by_id: dict[str, Any] = {GENESIS_SNAPSHOT_ID: parse_rfc3339_utc("1970-01-01T00:00:00Z")}
    for snapshot in snapshots:
        snapshot_id = snapshot.get("snapshot_id")
        snapshot_ts_raw = snapshot.get("snapshot_ts_utc")
        if not isinstance(snapshot_id, str) or snapshot_id == "":
            return False
        if not isinstance(snapshot_ts_raw, str) or snapshot_ts_raw == "":
            return False
        try:
            snapshot_ts = parse_rfc3339_utc(snapshot_ts_raw)
        except ValueError:
            return False
        if snapshot_id in snapshot_ts_by_id:
            return False
        snapshot_ts_by_id[snapshot_id] = snapshot_ts

    for attempt in attempts:
        provenance = attempt.get("residual_inputs", {}).get("provenance", {})
        if not isinstance(provenance, dict):
            return False
        snapshot_id = provenance.get("state_snapshot_id")
        attempt_ts_raw = attempt.get("attempt_ts_utc")
        if not isinstance(snapshot_id, str) or snapshot_id == "":
            return False
        if not isinstance(attempt_ts_raw, str) or attempt_ts_raw == "":
            return False
        try:
            attempt_ts = parse_rfc3339_utc(attempt_ts_raw)
        except ValueError:
            return False
        snapshot_ts = snapshot_ts_by_id.get(snapshot_id)
        if snapshot_ts is None:
            return False
        if snapshot_ts > attempt_ts:
            return False
    return True


def has_mixed_semantics(record: dict[str, Any], projection: dict[str, Any]) -> bool:
    return record.get("version_pointers") != projection


def residual_provenance_aligned(
    attempt: dict[str, Any],
    manifest_projection: dict[str, Any],
) -> bool:
    provenance = attempt.get("residual_inputs", {}).get("provenance", {})
    version_pointers = attempt.get("version_pointers", {})
    for field in RESIDUAL_PROVENANCE_PINNED_FIELDS:
        if field not in provenance:
            return False
        value = provenance[field]
        if value != manifest_projection.get(field):
            return False
        if field in version_pointers and value != version_pointers.get(field):
            return False
    return True


def updates_referentially_integral(
    attempts: list[dict[str, Any]],
    updates: list[dict[str, Any]],
) -> bool:
    attempts_by_id: dict[str, dict[str, Any]] = {}
    for attempt in attempts:
        attempt_id = attempt.get("attempt_id")
        if isinstance(attempt_id, str) and attempt_id:
            attempts_by_id[attempt_id] = attempt

    for update in updates:
        source_attempt_id = update.get("source_attempt_id")
        if not isinstance(source_attempt_id, str) or source_attempt_id == "":
            return False
        source_attempt = attempts_by_id.get(source_attempt_id)
        if source_attempt is None:
            return False

        patch_partition = update.get("state_patch", {}).get("partition")
        allowed_partitions = source_attempt.get("allowed_update_partitions")
        if not isinstance(allowed_partitions, list):
            return False
        if patch_partition not in allowed_partitions:
            return False

        if patch_partition == "diagnosis_state":
            if source_attempt.get("diagnosis_update_eligibility") != "eligible":
                return False
            if source_attempt.get("assistance_mode_derived") != "closed_book":
                return False
            if source_attempt.get("assistance_derivation_quality") != "derived_from_telemetry":
                return False
            if source_attempt.get("evidence_channel") not in DIAGNOSTIC_EVIDENCE_CHANNELS:
                return False
    return True


def updates_snapshot_ref_integrity(
    updates: list[dict[str, Any]],
    snapshots: list[dict[str, Any]],
) -> bool:
    known_snapshot_ids: set[str] = {GENESIS_SNAPSHOT_ID}
    for snapshot in snapshots:
        snapshot_id = snapshot.get("snapshot_id")
        if not isinstance(snapshot_id, str) or snapshot_id == "":
            return False
        known_snapshot_ids.add(snapshot_id)

    for update in updates:
        snapshot_id = update.get("snapshot_id")
        if not isinstance(snapshot_id, str) or snapshot_id == "":
            return False
        if snapshot_id not in known_snapshot_ids:
            return False
    return True


def timeline_records_consistent(
    manifest: dict[str, Any],
    attempts: list[dict[str, Any]],
    precommits: list[dict[str, Any]],
    telemetry_events: list[dict[str, Any]],
    snapshots: list[dict[str, Any]],
    updates: list[dict[str, Any]],
    migrations: list[dict[str, Any]],
    safe_mode_transitions: list[dict[str, Any]] | None = None,
    quarantine_decisions: list[dict[str, Any]] | None = None,
    anchor_audits: list[dict[str, Any]] | None = None,
) -> bool:
    timeline_id = manifest.get("timeline_id")
    if not isinstance(timeline_id, str) or timeline_id == "":
        return False
    all_records = (
        attempts
        + precommits
        + telemetry_events
        + snapshots
        + updates
        + migrations
        + list(safe_mode_transitions or [])
        + list(quarantine_decisions or [])
        + list(anchor_audits or [])
    )
    for record in all_records:
        if record.get("timeline_id") != timeline_id:
            return False
    return True


def migration_manifest_lineage_coherent(
    manifest: dict[str, Any],
    migrations: list[dict[str, Any]],
) -> bool:
    epoch_index = manifest.get("epoch_index")
    predecessor_run_id = manifest.get("predecessor_run_id")
    migration_event_id = manifest.get("migration_event_id")
    bootstrap = manifest.get("bootstrap_snapshot_ref")
    run_id = manifest.get("run_id")

    if not is_strict_int(epoch_index) or epoch_index <= 0:
        return False
    if epoch_index == 1:
        return len(migrations) == 0

    if not isinstance(predecessor_run_id, str) or predecessor_run_id == "":
        return False
    if predecessor_run_id == run_id:
        return False
    if not isinstance(migration_event_id, str) or migration_event_id == "":
        return False
    if not isinstance(bootstrap, dict):
        return False
    required_bootstrap = {
        "source_run_id",
        "source_snapshot_id",
        "source_state_hash",
        "source_replay_fingerprint",
    }
    if missing_required_fields(bootstrap, required_bootstrap):
        return False
    if bootstrap.get("source_run_id") != predecessor_run_id:
        return False

    if len(migrations) != 1:
        return False
    migration = migrations[0]
    if migration.get("migration_event_id") != migration_event_id:
        return False
    if migration.get("source_run_id") != predecessor_run_id:
        return False
    if migration.get("source_snapshot_id") != bootstrap.get("source_snapshot_id"):
        return False
    if migration.get("source_state_hash") != bootstrap.get("source_state_hash"):
        return False
    if migration.get("source_replay_fingerprint") != bootstrap.get("source_replay_fingerprint"):
        return False
    if migration.get("target_manifest_replay_fingerprint") != manifest.get("replay_fingerprint"):
        return False
    return True


def migration_event_precedes_attempts(
    events: list[dict[str, Any]],
    manifest: dict[str, Any],
) -> bool:
    epoch_index = manifest.get("epoch_index")
    if not is_strict_int(epoch_index) or epoch_index <= 0:
        return False
    if epoch_index == 1:
        return True

    migration_seq: int | None = None
    first_attempt_seq: int | None = None
    expected_migration_event_id = manifest.get("migration_event_id")
    for event in events:
        seq = event.get("ledger_sequence_no")
        if not is_strict_int(seq):
            return False
        if event.get("event_type") == "state_migration":
            payload = event.get("payload", {})
            if payload.get("migration_event_id") == expected_migration_event_id:
                migration_seq = seq
        if event.get("event_type") == "attempt_precommitted":
            if first_attempt_seq is None or seq < first_attempt_seq:
                first_attempt_seq = seq

    if migration_seq is None:
        return False
    if first_attempt_seq is None:
        return True
    return migration_seq < first_attempt_seq
