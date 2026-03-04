"""Deterministic replay with idempotency protections."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from . import audit_queries
from .assistance_deriver import derive_assistance_mode_from_telemetry
from .constants import (
    DIAGNOSTIC_EVIDENCE_CHANNELS,
    EVENT_ID_PREFIX_BY_TYPE,
    EVENT_PAYLOAD_ID_FIELD_BY_TYPE,
    EVENT_TYPES,
    GENESIS_SNAPSHOT_ID,
    GOVERNOR_MULTIPLIERS,
    REPLAY_NORMALIZATION_TARGET_SCHEMA_VERSION,
)
from .contract_validator import ContractValidator
from .ledger_store import LedgerStore
from .mutation_guard import MutationGuard
from .utils import (
    float_equal,
    is_strict_int,
    is_strict_number,
    parse_rfc3339_utc,
    sha256_json,
)


@dataclass
class ReplayResult:
    run_id: str
    attempts_seen: int = 0
    attempts_applied: int = 0
    updates_seen: int = 0
    updates_applied: int = 0
    diagnosis_updates_applied: int = 0
    checkpoints_seen: int = 0
    checkpoints_verified: int = 0
    last_verified_snapshot_hash: str = ""
    last_verified_snapshot_event_id: str = ""
    final_state_hash: str = ""
    errors: list[str] = field(default_factory=list)


@dataclass
class TimelineReplayResult:
    timeline_id: str
    run_results: list[ReplayResult] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


class ReplayEngine:
    """Replays stored records deterministically and idempotently."""

    def __init__(
        self,
        validator: ContractValidator,
        mutation_guard: MutationGuard,
    ) -> None:
        self._validator = validator
        self._mutation_guard = mutation_guard

    def replay_run(self, run_id: str, ledger: LedgerStore) -> ReplayResult:
        result = ReplayResult(run_id=run_id)
        raw_manifest = ledger.get_manifest(run_id)
        manifest, manifest_norm_errors = self._validator.normalize_record_for_replay(
            "manifest",
            raw_manifest,
            target_schema_version=REPLAY_NORMALIZATION_TARGET_SCHEMA_VERSION,
        )
        if manifest is None:
            result.errors.extend([f"manifest:{err}" for err in manifest_norm_errors])
            result.final_state_hash = sha256_json(_empty_state())
            return result
        state = _empty_state()
        current_safe_mode_state = "NORMAL"
        current_safe_mode_profile_id: str | None = None
        epoch_index = manifest.get("epoch_index")
        migration_required = is_strict_int(epoch_index) and epoch_index > 1
        migration_seen = False
        first_precommit_seen = False
        expected_migration_event_id = manifest.get("migration_event_id")
        events, sequence_errors = _order_events_by_ledger_sequence(ledger.get_events(run_id))
        if sequence_errors:
            result.errors.extend([f"event_order:{e}" for e in sequence_errors])
            result.final_state_hash = sha256_json(state)
            return result
        attempt_payload_hash_by_id: dict[str, str] = {}
        update_payload_hash_by_id: dict[str, str] = {}
        valid_attempts_by_id: dict[str, dict[str, Any]] = {}
        valid_precommits_by_event_id: dict[str, dict[str, Any]] = {}
        valid_precommits_by_attempt_id: dict[str, dict[str, Any]] = {}
        precommit_sequence_by_attempt_id: dict[str, int] = {}
        valid_telemetry_by_id: dict[str, dict[str, Any]] = {}
        telemetry_sequence_by_id: dict[str, int] = {}
        committed_snapshot_ids: set[str] = {GENESIS_SNAPSHOT_ID}
        committed_snapshot_ts_by_id: dict[str, Any] = {
            GENESIS_SNAPSHOT_ID: parse_rfc3339_utc("1970-01-01T00:00:00Z")
        }

        for event in events:
            event_id = str(event.get("event_id", ""))
            event_type = str(event.get("event_type", ""))
            event_run_id = event.get("run_id")
            if event_run_id != run_id:
                result.errors.append(f"event:{event_id}:event_run_id_mismatch_replay_run")
                continue
            if event_type not in EVENT_TYPES:
                result.errors.append(f"event:{event_id}:unknown_event_type:{event_type}")
                continue

            payload = event.get("payload")
            if not isinstance(payload, dict):
                result.errors.append(f"event:{event_id}:payload_not_object")
                continue
            payload_run_id = payload.get("run_id")
            if payload_run_id != event_run_id:
                result.errors.append(f"event:{event_id}:payload_run_id_mismatch_event_header")
                continue
            expected_prefix = EVENT_ID_PREFIX_BY_TYPE.get(event_type)
            payload_id_field = EVENT_PAYLOAD_ID_FIELD_BY_TYPE.get(event_type)
            if expected_prefix is None or payload_id_field is None:
                result.errors.append(f"event:{event_id}:event_type_id_contract_missing")
                continue
            payload_id = payload.get(payload_id_field)
            if not isinstance(payload_id, str) or payload_id == "":
                result.errors.append(f"event:{event_id}:payload_id_missing:{payload_id_field}")
                continue
            if not event_id.startswith(expected_prefix):
                result.errors.append(
                    f"event:{event_id}:event_id_prefix_mismatch_expected:{expected_prefix}"
                )
                continue

            if event_type == "attempt_precommitted":
                first_precommit_seen = True
                if migration_required and not migration_seen:
                    result.errors.append("migration:required_before_attempt_precommit")
                    continue
                normalized_payload, normalize_errors = self._validator.normalize_record_for_replay(
                    "attempt_precommit",
                    payload,
                    target_schema_version=REPLAY_NORMALIZATION_TARGET_SCHEMA_VERSION,
                )
                if normalized_payload is None:
                    result.errors.extend(
                        [f"precommit:{event_id}:{e}" for e in normalize_errors]
                    )
                    continue
                payload = normalized_payload
                precommit_event_id = payload.get("precommit_event_id")
                attempt_id = payload.get("attempt_id")
                errors = self._validator.validate_attempt_precommit(payload, manifest)
                if errors:
                    result.errors.extend([f"precommit:{precommit_event_id}:{e}" for e in errors])
                    continue
                if isinstance(precommit_event_id, str):
                    valid_precommits_by_event_id[precommit_event_id] = payload
                if isinstance(attempt_id, str):
                    valid_precommits_by_attempt_id[attempt_id] = payload
                    seq = event.get("ledger_sequence_no")
                    if is_strict_int(seq):
                        precommit_sequence_by_attempt_id[attempt_id] = int(seq)
                continue

            if event_type == "state_migration":
                normalized_payload, normalize_errors = self._validator.normalize_record_for_replay(
                    "state_migration",
                    payload,
                    target_schema_version=REPLAY_NORMALIZATION_TARGET_SCHEMA_VERSION,
                )
                if normalized_payload is None:
                    result.errors.extend(
                        [f"migration:{event_id}:{e}" for e in normalize_errors]
                    )
                    continue
                payload = normalized_payload
                migration_event_id = payload.get("migration_event_id")
                errors = self._validator.validate_state_migration_event(payload, manifest)
                if errors:
                    result.errors.extend([f"migration:{migration_event_id}:{e}" for e in errors])
                    continue
                if not migration_required:
                    result.errors.append("migration:unexpected_for_initial_epoch")
                    continue
                if migration_seen:
                    result.errors.append("migration:duplicate_migration_event")
                    continue
                if first_precommit_seen:
                    result.errors.append("migration:must_precede_attempt_precommit")
                    continue
                if migration_event_id != expected_migration_event_id:
                    result.errors.append("migration:manifest_migration_event_id_mismatch")
                    continue
                migration_seen = True
                continue

            if event_type == "attempt_telemetry":
                normalized_payload, normalize_errors = self._validator.normalize_record_for_replay(
                    "attempt_telemetry",
                    payload,
                    target_schema_version=REPLAY_NORMALIZATION_TARGET_SCHEMA_VERSION,
                )
                if normalized_payload is None:
                    result.errors.extend(
                        [f"telemetry:{event_id}:{e}" for e in normalize_errors]
                    )
                    continue
                payload = normalized_payload
                telemetry_event_id = payload.get("telemetry_event_id")
                errors = self._validator.validate_attempt_telemetry_event(payload, manifest)
                if errors:
                    result.errors.extend([f"telemetry:{telemetry_event_id}:{e}" for e in errors])
                    continue
                if isinstance(telemetry_event_id, str):
                    valid_telemetry_by_id[telemetry_event_id] = payload
                    seq = event.get("ledger_sequence_no")
                    if is_strict_int(seq):
                        telemetry_sequence_by_id[telemetry_event_id] = int(seq)
                continue

            if event_type == "attempt_observed":
                normalized_payload, normalize_errors = self._validator.normalize_record_for_replay(
                    "attempt",
                    payload,
                    target_schema_version=REPLAY_NORMALIZATION_TARGET_SCHEMA_VERSION,
                )
                if normalized_payload is None:
                    result.errors.extend(
                        [f"attempt:{event_id}:{e}" for e in normalize_errors]
                    )
                    continue
                payload = normalized_payload
                attempt_id = payload.get("attempt_id")
                result.attempts_seen += 1
                attempt_id_str = str(attempt_id)
                payload_hash = sha256_json(payload)
                prior_payload_hash = attempt_payload_hash_by_id.get(attempt_id_str)
                if prior_payload_hash is not None:
                    if prior_payload_hash != payload_hash:
                        result.errors.append(
                            f"attempt:{attempt_id}:duplicate_attempt_id_conflicting_payload"
                        )
                    continue
                attempt_payload_hash_by_id[attempt_id_str] = payload_hash
                errors = self._validator.validate_attempt(payload, manifest)
                if errors:
                    result.errors.extend([f"attempt:{attempt_id}:{e}" for e in errors])
                    continue
                precommit_event_id = payload.get("precommit_event_id")
                precommit = valid_precommits_by_event_id.get(str(precommit_event_id))
                if precommit is None:
                    result.errors.append(
                        f"attempt:{attempt_id}:precommit_missing_or_not_committed:{precommit_event_id}"
                    )
                    continue
                if valid_precommits_by_attempt_id.get(str(attempt_id)) is not precommit:
                    result.errors.append(f"attempt:{attempt_id}:precommit_attempt_binding_mismatch")
                    continue
                if not audit_queries.precommit_semantics_binding_consistent(payload, precommit):
                    result.errors.append(f"attempt:{attempt_id}:precommit_semantics_binding_mismatch")
                    continue
                if precommit.get("precommit_hash") != payload.get("precommit_hash"):
                    result.errors.append(f"attempt:{attempt_id}:precommit_hash_mismatch")
                    continue
                presented_ts_raw = precommit.get("presented_ts_utc")
                observed_ts_raw = payload.get("attempt_ts_utc")
                if not isinstance(presented_ts_raw, str) or not isinstance(observed_ts_raw, str):
                    result.errors.append(f"attempt:{attempt_id}:invalid_timestamps")
                    continue
                try:
                    presented_ts = parse_rfc3339_utc(presented_ts_raw)
                    observed_ts = parse_rfc3339_utc(observed_ts_raw)
                except ValueError:
                    result.errors.append(f"attempt:{attempt_id}:invalid_timestamps")
                    continue
                if presented_ts > observed_ts:
                    result.errors.append(f"attempt:{attempt_id}:precommit_after_observation")
                    continue
                observed_seq = event.get("ledger_sequence_no")
                precommit_seq = precommit_sequence_by_attempt_id.get(str(attempt_id))
                if not is_strict_int(observed_seq):
                    result.errors.append(f"attempt:{attempt_id}:observed_event_sequence_invalid")
                    continue
                if precommit_seq is None:
                    result.errors.append(
                        f"attempt:{attempt_id}:precommit_sequence_missing:{precommit_event_id}"
                    )
                    continue
                if precommit_seq >= int(observed_seq):
                    result.errors.append(f"attempt:{attempt_id}:precommit_not_before_observed_by_sequence")
                    continue
                telemetry_event_ids = payload.get("telemetry_event_ids")
                if not isinstance(telemetry_event_ids, list) or not telemetry_event_ids:
                    result.errors.append(f"attempt:{attempt_id}:telemetry_event_ids_missing")
                    continue
                run_id = payload.get("run_id")
                timeline_id = payload.get("timeline_id")
                learner_id = payload.get("learner_id")
                declared_telemetry_ids: set[str] = set()
                telemetry_window: list[dict[str, Any]] = []
                declared_has_response_submitted = False
                for telemetry_event_id in telemetry_event_ids:
                    telemetry_event_id_str = str(telemetry_event_id)
                    if telemetry_event_id_str in declared_telemetry_ids:
                        result.errors.append(
                            f"attempt:{attempt_id}:telemetry_event_id_duplicate_declared:{telemetry_event_id_str}"
                        )
                        telemetry_window = []
                        break
                    declared_telemetry_ids.add(telemetry_event_id_str)
                    telemetry_event = valid_telemetry_by_id.get(telemetry_event_id_str)
                    if telemetry_event is None:
                        result.errors.append(
                            f"attempt:{attempt_id}:telemetry_event_missing_or_not_committed:{telemetry_event_id}"
                        )
                        telemetry_window = []
                        break
                    if telemetry_event.get("attempt_id") != attempt_id:
                        result.errors.append(
                            f"attempt:{attempt_id}:telemetry_event_attempt_mismatch:{telemetry_event_id}"
                        )
                        telemetry_window = []
                        break
                    if telemetry_event.get("run_id") != run_id:
                        result.errors.append(
                            f"attempt:{attempt_id}:telemetry_event_run_mismatch:{telemetry_event_id}"
                        )
                        telemetry_window = []
                        break
                    if telemetry_event.get("timeline_id") != timeline_id:
                        result.errors.append(
                            f"attempt:{attempt_id}:telemetry_event_timeline_mismatch:{telemetry_event_id}"
                        )
                        telemetry_window = []
                        break
                    if telemetry_event.get("learner_id") != learner_id:
                        result.errors.append(
                            f"attempt:{attempt_id}:telemetry_event_learner_mismatch:{telemetry_event_id}"
                        )
                        telemetry_window = []
                        break
                    telemetry_ts_raw = telemetry_event.get("telemetry_ts_utc")
                    if not isinstance(telemetry_ts_raw, str):
                        result.errors.append(
                            f"attempt:{attempt_id}:telemetry_event_invalid_timestamp:{telemetry_event_id}"
                        )
                        telemetry_window = []
                        break
                    try:
                        telemetry_ts = parse_rfc3339_utc(telemetry_ts_raw)
                    except ValueError:
                        result.errors.append(
                            f"attempt:{attempt_id}:telemetry_event_invalid_timestamp:{telemetry_event_id}"
                        )
                        telemetry_window = []
                        break
                    telemetry_seq = telemetry_sequence_by_id.get(telemetry_event_id_str)
                    if telemetry_seq is None:
                        result.errors.append(
                            f"attempt:{attempt_id}:telemetry_event_sequence_missing:{telemetry_event_id}"
                        )
                        telemetry_window = []
                        break
                    if not (precommit_seq < telemetry_seq <= int(observed_seq)):
                        result.errors.append(
                            f"attempt:{attempt_id}:telemetry_event_outside_sequence_window:{telemetry_event_id}"
                        )
                        telemetry_window = []
                        break
                    if telemetry_ts < presented_ts:
                        result.errors.append(
                            f"attempt:{attempt_id}:telemetry_event_before_presented:{telemetry_event_id}"
                        )
                        telemetry_window = []
                        break
                    if telemetry_ts > observed_ts:
                        result.errors.append(
                            f"attempt:{attempt_id}:telemetry_event_after_observation:{telemetry_event_id}"
                        )
                        telemetry_window = []
                        break
                    telemetry_window.append(telemetry_event)
                    if telemetry_event.get("telemetry_kind") == "response_submitted":
                        declared_has_response_submitted = True
                if not telemetry_window:
                    continue
                if not declared_has_response_submitted:
                    result.errors.append(
                        f"attempt:{attempt_id}:response_submitted_missing_declared_window"
                    )
                    continue

                derived_telemetry_window: list[dict[str, Any]] = []
                derived_telemetry_ids: set[str] = set()
                derived_has_response_submitted = False
                for telemetry_event_id, telemetry_event in valid_telemetry_by_id.items():
                    if telemetry_event.get("attempt_id") != attempt_id:
                        continue
                    if telemetry_event.get("run_id") != run_id:
                        continue
                    if telemetry_event.get("timeline_id") != timeline_id:
                        continue
                    if telemetry_event.get("learner_id") != learner_id:
                        continue
                    telemetry_ts_raw = telemetry_event.get("telemetry_ts_utc")
                    if not isinstance(telemetry_ts_raw, str):
                        result.errors.append(
                            f"attempt:{attempt_id}:telemetry_event_invalid_timestamp:{telemetry_event_id}"
                        )
                        derived_telemetry_window = []
                        break
                    try:
                        telemetry_ts = parse_rfc3339_utc(telemetry_ts_raw)
                    except ValueError:
                        result.errors.append(
                            f"attempt:{attempt_id}:telemetry_event_invalid_timestamp:{telemetry_event_id}"
                        )
                        derived_telemetry_window = []
                        break
                    telemetry_seq = telemetry_sequence_by_id.get(telemetry_event_id)
                    if telemetry_seq is None:
                        result.errors.append(
                            f"attempt:{attempt_id}:telemetry_event_sequence_missing:{telemetry_event_id}"
                        )
                        derived_telemetry_window = []
                        break
                    if not (precommit_seq < telemetry_seq <= int(observed_seq)):
                        continue
                    if telemetry_ts < presented_ts:
                        result.errors.append(
                            f"attempt:{attempt_id}:telemetry_event_before_presented:{telemetry_event_id}"
                        )
                        derived_telemetry_window = []
                        break
                    if telemetry_ts > observed_ts:
                        result.errors.append(
                            f"attempt:{attempt_id}:telemetry_event_after_observation:{telemetry_event_id}"
                        )
                        derived_telemetry_window = []
                        break
                    derived_telemetry_ids.add(telemetry_event_id)
                    derived_telemetry_window.append(telemetry_event)
                    if telemetry_event.get("telemetry_kind") == "response_submitted":
                        derived_has_response_submitted = True
                if not derived_telemetry_window:
                    result.errors.append(f"attempt:{attempt_id}:telemetry_window_empty_derived")
                    continue
                if not derived_has_response_submitted:
                    result.errors.append(
                        f"attempt:{attempt_id}:response_submitted_missing_derived_window"
                    )
                    continue
                if declared_telemetry_ids != derived_telemetry_ids:
                    missing_ids = sorted(list(derived_telemetry_ids - declared_telemetry_ids))
                    extra_ids = sorted(list(declared_telemetry_ids - derived_telemetry_ids))
                    if missing_ids:
                        result.errors.append(
                            f"attempt:{attempt_id}:telemetry_window_missing_declared_ids:{','.join(missing_ids)}"
                        )
                    if extra_ids:
                        result.errors.append(
                            f"attempt:{attempt_id}:telemetry_window_extra_declared_ids:{','.join(extra_ids)}"
                        )
                    continue

                derived_assistance_mode, _ = derive_assistance_mode_from_telemetry(
                    derived_telemetry_window
                )
                if payload.get("assistance_mode_derived") != derived_assistance_mode:
                    result.errors.append(
                        f"attempt:{attempt_id}:assistance_mode_derived_mismatch_recomputed"
                    )
                    continue
                if payload.get("assistance_derivation_quality") != "derived_from_telemetry":
                    result.errors.append(
                        f"attempt:{attempt_id}:assistance_derivation_quality_not_telemetry_derived"
                    )
                    continue
                if payload.get("assistance_mode") != payload.get("assistance_mode_derived"):
                    result.errors.append(
                        f"attempt:{attempt_id}:assistance_mode_claimed_mismatch_derived"
                    )
                    continue
                provenance = payload.get("residual_inputs", {}).get("provenance", {})
                provenance_snapshot_id = provenance.get("state_snapshot_id")
                if not isinstance(provenance_snapshot_id, str) or provenance_snapshot_id == "":
                    result.errors.append(f"attempt:{attempt_id}:provenance_snapshot_id_invalid")
                    continue
                provenance_snapshot_ts = committed_snapshot_ts_by_id.get(provenance_snapshot_id)
                if provenance_snapshot_ts is None:
                    result.errors.append(
                        f"attempt:{attempt_id}:provenance_snapshot_missing_or_not_committed:{provenance_snapshot_id}"
                    )
                    continue
                if provenance_snapshot_ts > observed_ts:
                    result.errors.append(
                        f"attempt:{attempt_id}:provenance_snapshot_after_observation:{provenance_snapshot_id}"
                    )
                    continue
                result.attempts_applied += 1
                if isinstance(attempt_id, str):
                    valid_attempts_by_id[attempt_id] = payload
                continue

            if event_type == "state_update":
                normalized_payload, normalize_errors = self._validator.normalize_record_for_replay(
                    "state_update",
                    payload,
                    target_schema_version=REPLAY_NORMALIZATION_TARGET_SCHEMA_VERSION,
                )
                if normalized_payload is None:
                    result.errors.extend(
                        [f"update:{event_id}:{e}" for e in normalize_errors]
                    )
                    continue
                payload = normalized_payload
                update_id = payload.get("update_id")
                result.updates_seen += 1
                update_id_str = str(update_id)
                payload_hash = sha256_json(payload)
                prior_payload_hash = update_payload_hash_by_id.get(update_id_str)
                if prior_payload_hash is not None:
                    if prior_payload_hash != payload_hash:
                        result.errors.append(
                            f"update:{update_id}:duplicate_update_id_conflicting_payload"
                        )
                    continue
                update_payload_hash_by_id[update_id_str] = payload_hash

                errors = self._validator.validate_state_update_event(payload)
                if errors:
                    result.errors.extend([f"update:{update_id}:{e}" for e in errors])
                    continue
                active_profile_id = current_safe_mode_profile_id
                if active_profile_id is not None:
                    if payload.get("safe_mode_profile_id") != active_profile_id:
                        result.errors.append(
                            f"update:{update_id}:safe_mode_profile_id_mismatch_active_transition"
                        )
                        continue
                if payload.get("timeline_id") != manifest.get("timeline_id"):
                    result.errors.append(f"update:{update_id}:timeline_id_mismatch_manifest")
                    continue
                update_snapshot_id = payload.get("snapshot_id")
                if not isinstance(update_snapshot_id, str) or update_snapshot_id == "":
                    result.errors.append(f"update:{update_id}:snapshot_id_invalid")
                    continue
                if update_snapshot_id not in committed_snapshot_ids:
                    result.errors.append(
                        f"update:{update_id}:snapshot_ref_missing_or_not_committed:{update_snapshot_id}"
                    )
                    continue
                source_attempt_id = payload.get("source_attempt_id")
                source_attempt = valid_attempts_by_id.get(str(source_attempt_id))
                if source_attempt is None:
                    result.errors.append(
                        f"update:{update_id}:source_attempt_missing_or_invalid:{source_attempt_id}"
                    )
                    continue
                patch_partition = payload.get("state_patch", {}).get("partition")
                allowed_partitions = source_attempt.get("allowed_update_partitions")
                if not isinstance(allowed_partitions, list):
                    result.errors.append(
                        f"update:{update_id}:source_attempt_allowed_update_partitions_invalid"
                    )
                    continue
                if patch_partition not in allowed_partitions:
                    result.errors.append(
                        f"update:{update_id}:partition_not_authorized_by_source_attempt:{patch_partition}"
                    )
                    continue
                if patch_partition == "diagnosis_state":
                    if source_attempt.get("diagnosis_update_eligibility") != "eligible":
                        result.errors.append(
                            f"update:{update_id}:diagnosis_partition_requires_eligible_source_attempt"
                        )
                        continue
                    if source_attempt.get("assistance_mode_derived") != "closed_book":
                        result.errors.append(
                            f"update:{update_id}:diagnosis_partition_requires_closed_book_source_attempt"
                        )
                        continue
                    if source_attempt.get("assistance_derivation_quality") != "derived_from_telemetry":
                        result.errors.append(
                            f"update:{update_id}:diagnosis_partition_requires_telemetry_derived_assistance"
                        )
                        continue
                    if source_attempt.get("evidence_channel") not in DIAGNOSTIC_EVIDENCE_CHANNELS:
                        result.errors.append(
                            f"update:{update_id}:diagnosis_partition_requires_diagnostic_channel_source_attempt"
                        )
                        continue

                    proposed_patch = payload.get("proposed_state_patch")
                    if not isinstance(proposed_patch, dict):
                        result.errors.append(f"update:{update_id}:proposed_state_patch_not_object")
                        continue
                    if proposed_patch.get("partition") != patch_partition:
                        result.errors.append(f"update:{update_id}:proposed_patch_partition_mismatch")
                        continue
                    if proposed_patch.get("path") != payload.get("state_patch", {}).get("path"):
                        result.errors.append(f"update:{update_id}:proposed_patch_path_mismatch")
                        continue
                    if proposed_patch.get("op") != payload.get("state_patch", {}).get("op"):
                        result.errors.append(f"update:{update_id}:proposed_patch_op_mismatch")
                        continue

                    if payload.get("mutation_outcome") == "applied":
                        base_value = payload.get("base_value_at_proposal")
                        proposed_value = proposed_patch.get("value")
                        applied_value = payload.get("state_patch", {}).get("value")
                        applied_multiplier = payload.get("applied_update_multiplier")
                        if not is_strict_number(base_value):
                            result.errors.append(f"update:{update_id}:base_value_at_proposal_not_numeric")
                            continue
                        if not is_strict_number(proposed_value):
                            result.errors.append(f"update:{update_id}:proposed_patch_value_not_numeric")
                            continue
                        if not is_strict_number(applied_value):
                            result.errors.append(f"update:{update_id}:state_patch_value_not_numeric")
                            continue
                        if not is_strict_number(applied_multiplier):
                            result.errors.append(f"update:{update_id}:applied_update_multiplier_not_numeric")
                            continue
                        current_base_value = _read_numeric_path_value(
                            state,
                            patch_partition,
                            str(payload.get("state_patch", {}).get("path", "")),
                        )
                        if current_base_value is None:
                            result.errors.append(f"update:{update_id}:state_path_not_numeric")
                            continue
                        if not float_equal(float(base_value), current_base_value, tolerance=1e-8):
                            result.errors.append(f"update:{update_id}:base_value_mismatch_pre_state")
                            continue
                        governor_decision = payload.get("governor_decision")
                        safe_mode_profile_id = payload.get("safe_mode_profile_id")
                        expected_multiplier = _expected_diagnosis_multiplier_for_profile(
                            safe_mode_profile_id,
                            governor_decision,
                        )
                        if expected_multiplier is not None and not float_equal(
                            float(applied_multiplier),
                            expected_multiplier,
                            tolerance=1e-8,
                        ):
                            result.errors.append(f"update:{update_id}:profile_multiplier_mismatch")
                            continue
                        if governor_decision not in GOVERNOR_MULTIPLIERS:
                            result.errors.append(f"update:{update_id}:invalid_governor_decision")
                            continue
                        expected_applied_value = float(base_value) + float(applied_multiplier) * (
                            float(proposed_value) - float(base_value)
                        )
                        if not float_equal(float(applied_value), expected_applied_value, tolerance=1e-8):
                            result.errors.append(f"update:{update_id}:governed_transform_mismatch")
                            continue

                current_hash = sha256_json(state)
                pre_hash = payload.get("pre_state_hash")
                if pre_hash != current_hash:
                    result.errors.append(f"update:{update_id}:pre_state_hash_mismatch")
                    continue

                decision = self._mutation_guard.evaluate(payload)
                if decision.allowed:
                    patched_state = _apply_state_patch(state, payload["state_patch"])
                    expected_post_hash = payload.get("post_state_hash")
                    actual_post_hash = sha256_json(patched_state)
                    if expected_post_hash != actual_post_hash:
                        result.errors.append(f"update:{update_id}:post_state_hash_mismatch")
                        continue
                    state = patched_state
                    result.updates_applied += 1
                    if payload.get("state_patch", {}).get("partition") == "diagnosis_state":
                        result.diagnosis_updates_applied += 1
                else:
                    if payload.get("post_state_hash") != current_hash:
                        result.errors.append(f"update:{update_id}:blocked_post_hash_mismatch")
                continue

            if event_type == "snapshot_checkpoint":
                normalized_payload, normalize_errors = self._validator.normalize_record_for_replay(
                    "state_snapshot",
                    payload,
                    target_schema_version=REPLAY_NORMALIZATION_TARGET_SCHEMA_VERSION,
                )
                if normalized_payload is None:
                    result.errors.extend(
                        [f"snapshot:{event_id}:{e}" for e in normalize_errors]
                    )
                    continue
                payload = normalized_payload
                snapshot_id = payload.get("snapshot_id")
                result.checkpoints_seen += 1
                errors = self._validator.validate_state_snapshot(payload, manifest)
                if errors:
                    result.errors.extend([f"snapshot:{snapshot_id}:{e}" for e in errors])
                    continue
                current_hash = sha256_json(state)
                if payload.get("state_hash") != current_hash:
                    result.errors.append(f"snapshot:{snapshot_id}:state_hash_mismatch_replay")
                    continue
                snapshot_ts = payload.get("snapshot_ts_utc")
                if isinstance(snapshot_id, str) and isinstance(snapshot_ts, str) and snapshot_id != "":
                    try:
                        committed_snapshot_ts_by_id[snapshot_id] = parse_rfc3339_utc(snapshot_ts)
                    except ValueError:
                        result.errors.append(f"snapshot:{snapshot_id}:snapshot_ts_invalid")
                        continue
                    committed_snapshot_ids.add(snapshot_id)
                result.checkpoints_verified += 1
                if isinstance(payload.get("state_hash"), str):
                    result.last_verified_snapshot_hash = payload["state_hash"]
                if isinstance(event_id, str):
                    result.last_verified_snapshot_event_id = event_id
                continue

            if event_type == "safe_mode_transition":
                normalized_payload, normalize_errors = self._validator.normalize_record_for_replay(
                    "safe_mode_transition",
                    payload,
                    target_schema_version=REPLAY_NORMALIZATION_TARGET_SCHEMA_VERSION,
                )
                if normalized_payload is None:
                    result.errors.extend(
                        [f"safe_mode_transition:{event_id}:{e}" for e in normalize_errors]
                    )
                    continue
                payload = normalized_payload
                transition_event_id = payload.get("event_id")
                errors = self._validator.validate_safe_mode_transition_event(payload, manifest)
                if errors:
                    result.errors.extend(
                        [f"safe_mode_transition:{transition_event_id}:{e}" for e in errors]
                    )
                    continue
                prior_state = payload.get("prior_state")
                next_state = payload.get("next_state")
                if prior_state != current_safe_mode_state:
                    result.errors.append(
                        f"safe_mode_transition:{transition_event_id}:prior_state_mismatch_runtime"
                    )
                    continue
                current_safe_mode_state = str(next_state)
                current_safe_mode_profile_id = str(payload.get("profile_id"))
                continue

            if event_type == "quarantine_decision":
                normalized_payload, normalize_errors = self._validator.normalize_record_for_replay(
                    "quarantine_decision",
                    payload,
                    target_schema_version=REPLAY_NORMALIZATION_TARGET_SCHEMA_VERSION,
                )
                if normalized_payload is None:
                    result.errors.extend(
                        [f"quarantine_decision:{event_id}:{e}" for e in normalize_errors]
                    )
                    continue
                payload = normalized_payload
                quarantine_event_id = payload.get("event_id")
                errors = self._validator.validate_quarantine_decision_event(payload, manifest)
                if errors:
                    result.errors.extend(
                        [f"quarantine_decision:{quarantine_event_id}:{e}" for e in errors]
                    )
                    continue
                continue

            if event_type == "anchor_audit":
                normalized_payload, normalize_errors = self._validator.normalize_record_for_replay(
                    "anchor_audit",
                    payload,
                    target_schema_version=REPLAY_NORMALIZATION_TARGET_SCHEMA_VERSION,
                )
                if normalized_payload is None:
                    result.errors.extend(
                        [f"anchor_audit:{event_id}:{e}" for e in normalize_errors]
                    )
                    continue
                payload = normalized_payload
                anchor_audit_event_id = payload.get("event_id")
                errors = self._validator.validate_anchor_audit_event(payload, manifest)
                if errors:
                    result.errors.extend(
                        [f"anchor_audit:{anchor_audit_event_id}:{e}" for e in errors]
                    )
                    continue
                continue

        if migration_required and not migration_seen:
            result.errors.append("migration:missing_required_migration_event")

        result.final_state_hash = sha256_json(state)
        return result

    def replay_timeline(
        self,
        timeline_id: str,
        run_ids: list[str],
        ledger: LedgerStore,
    ) -> TimelineReplayResult:
        result = TimelineReplayResult(timeline_id=timeline_id)
        manifests: list[dict[str, Any]] = []
        for run_id in run_ids:
            manifest = ledger.get_manifest(run_id)
            manifests.append(manifest)

        manifests.sort(key=lambda m: int(m.get("epoch_index", 0)))
        expected_epoch = 1
        predecessor_run_id: str | None = None
        for manifest in manifests:
            run_id = str(manifest.get("run_id"))
            if manifest.get("timeline_id") != timeline_id:
                result.errors.append(f"timeline:{timeline_id}:run_timeline_mismatch:{run_id}")
                continue
            epoch_index = manifest.get("epoch_index")
            if epoch_index != expected_epoch:
                result.errors.append(f"timeline:{timeline_id}:epoch_gap_or_duplicate:{run_id}")
            if expected_epoch == 1:
                predecessor_run_id = run_id
            else:
                if manifest.get("predecessor_run_id") != predecessor_run_id:
                    result.errors.append(
                        f"timeline:{timeline_id}:predecessor_mismatch:{run_id}"
                    )
                predecessor_run_id = run_id
            expected_epoch += 1
            run_result = self.replay_run(run_id, ledger)
            result.run_results.append(run_result)
            if run_result.errors:
                result.errors.extend([f"run:{run_id}:{err}" for err in run_result.errors])
        return result

def _order_events_by_ledger_sequence(
    events: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[str]]:
    if not events:
        return ([], ["empty_event_ledger"])
    errors: list[str] = []
    seen_sequences: set[int] = set()
    seen_event_ids: set[str] = set()
    ordered: list[tuple[int, Any, dict[str, Any]]] = []

    for idx, event in enumerate(events):
        seq = event.get("ledger_sequence_no")
        event_id_raw = event.get("event_id")
        if not isinstance(event_id_raw, str) or event_id_raw == "":
            errors.append(f"invalid_or_missing_event_id[{idx}]")
            continue
        event_id = event_id_raw
        if event_id in seen_event_ids:
            errors.append(f"duplicate_event_id:{event_id}")
            continue
        seen_event_ids.add(event_id)
        if not is_strict_int(seq) or seq <= 0:
            errors.append(f"invalid_or_missing_sequence[{idx}]:{event_id}")
            continue
        if seq in seen_sequences:
            errors.append(f"duplicate_sequence:{seq}")
            continue
        written_ts_raw = event.get("event_written_ts_utc")
        if not isinstance(written_ts_raw, str):
            errors.append(f"invalid_or_missing_event_written_ts[{idx}]:{event_id}")
            continue
        try:
            written_ts = parse_rfc3339_utc(written_ts_raw)
        except ValueError:
            errors.append(f"invalid_event_written_ts[{idx}]:{event_id}")
            continue
        seen_sequences.add(seq)
        ordered.append((seq, written_ts, event))

    if errors:
        return ([], errors)
    ordered.sort(key=lambda pair: pair[0])
    prior_written_ts = None
    for seq, written_ts, event in ordered:
        if prior_written_ts is not None and written_ts < prior_written_ts:
            errors.append(
                f"non_monotonic_event_written_ts:{event.get('event_id')}@seq{seq}"
            )
            continue
        prior_written_ts = written_ts
    if errors:
        return ([], errors)
    return ([event for _, _, event in ordered], [])


def _expected_diagnosis_multiplier_for_profile(
    safe_mode_profile_id: Any,
    governor_decision: Any,
) -> float | None:
    if not isinstance(safe_mode_profile_id, str):
        return None
    if safe_mode_profile_id == "SG_CALIBRATION_GUARD":
        if governor_decision not in GOVERNOR_MULTIPLIERS:
            return None
        return float(GOVERNOR_MULTIPLIERS[governor_decision])
    if safe_mode_profile_id == "SG_SENSOR_UNRELIABLE_GUARD":
        return 0.10
    if safe_mode_profile_id.startswith("SP_"):
        return 0.00
    return None


def _empty_state() -> dict[str, Any]:
    return {
        "diagnosis_state": {},
        "learning_retention_state": {},
    }


def _read_numeric_path_value(
    state: dict[str, Any],
    partition: str,
    path: str,
) -> float | None:
    if partition not in {"diagnosis_state", "learning_retention_state"}:
        return None
    if not isinstance(path, str) or path == "":
        return None
    node: Any = state.get(partition, {})
    keys = path.split(".")
    for key in keys:
        if not isinstance(node, dict):
            return None
        if key not in node:
            return 0.0
        node = node.get(key)
    if not is_strict_number(node):
        return None
    return float(node)


def _apply_state_patch(state: dict[str, Any], patch: dict[str, Any]) -> dict[str, Any]:
    partition = patch["partition"]
    path = str(patch["path"])
    value = patch["value"]
    next_state = {
        "diagnosis_state": dict(state.get("diagnosis_state", {})),
        "learning_retention_state": dict(state.get("learning_retention_state", {})),
    }
    target = next_state[partition]
    keys = path.split(".")
    node = target
    for key in keys[:-1]:
        child = node.get(key)
        if not isinstance(child, dict):
            child = {}
            node[key] = child
        node = child
    node[keys[-1]] = value
    return next_state
