"""Append-only ledger storage for attempts, snapshots, and updates."""

from __future__ import annotations

import json
from pathlib import Path
from datetime import datetime, timedelta, timezone
from typing import Any

from .constants import EVENT_ID_PREFIX_BY_TYPE, EVENT_TYPES


class DuplicateRecordError(ValueError):
    """Raised when a unique key would be duplicated."""


class LedgerStore:
    """In-memory + optional JSONL append-only store."""

    def __init__(self, root: str | None = None) -> None:
        self._root = Path(root) if root else None
        self._loaded_runs_from_disk: set[str] = set()
        self.manifests: dict[str, dict[str, Any]] = {}
        self.precommits_by_run: dict[str, list[dict[str, Any]]] = {}
        self.telemetry_by_run: dict[str, list[dict[str, Any]]] = {}
        self.attempts_by_run: dict[str, list[dict[str, Any]]] = {}
        self.snapshots_by_run: dict[str, list[dict[str, Any]]] = {}
        self.updates_by_run: dict[str, list[dict[str, Any]]] = {}
        self.migrations_by_run: dict[str, list[dict[str, Any]]] = {}
        self.events_by_run: dict[str, list[dict[str, Any]]] = {}
        self._precommit_keys: set[tuple[str, str]] = set()
        self._attempt_keys: set[tuple[str, str]] = set()
        self._telemetry_keys: set[tuple[str, str]] = set()
        self._snapshot_keys: set[tuple[str, str]] = set()
        self._update_keys: set[tuple[str, str]] = set()
        self._migration_keys: set[tuple[str, str]] = set()
        self._event_keys: set[tuple[str, str]] = set()
        self._next_event_seq_by_run: dict[str, int] = {}
        self._last_event_written_ts_by_run: dict[str, datetime] = {}

        if self._root:
            self._root.mkdir(parents=True, exist_ok=True)
            (self._root / "manifests").mkdir(parents=True, exist_ok=True)
            (self._root / "ledger").mkdir(parents=True, exist_ok=True)

    def put_manifest(self, manifest: dict[str, Any]) -> None:
        run_id = manifest["run_id"]
        if run_id in self.manifests:
            raise DuplicateRecordError(f"duplicate_manifest:{run_id}")
        if self._root:
            path = self._root / "manifests" / f"run_manifest.{run_id}.json"
            if path.exists():
                raise DuplicateRecordError(f"duplicate_manifest:{run_id}")
        self.manifests[run_id] = manifest
        if self._root:
            path = self._root / "manifests" / f"run_manifest.{run_id}.json"
            path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    def append_attempt_precommit(self, precommit: dict[str, Any]) -> None:
        run_id = precommit["run_id"]
        self._ensure_run_loaded(run_id)
        key = (run_id, precommit["attempt_id"])
        if key in self._precommit_keys:
            raise DuplicateRecordError(f"duplicate_attempt_precommit:{key[0]}:{key[1]}")
        self._precommit_keys.add(key)
        self.precommits_by_run.setdefault(run_id, []).append(precommit)
        event = self._build_event(
            event_type="attempt_precommitted",
            payload=precommit,
            event_id=f"{EVENT_ID_PREFIX_BY_TYPE['attempt_precommitted']}{precommit['precommit_event_id']}",
            event_ts_utc=precommit["presented_ts_utc"],
            session_id=precommit.get("session_id"),
            causal_refs=[],
        )
        self.append_event(event)
        if self._root:
            self._append_jsonl(run_id, "attempt_precommits.jsonl", precommit)

    def append_attempt(self, attempt: dict[str, Any]) -> None:
        run_id = attempt["run_id"]
        self._ensure_run_loaded(run_id)
        key = (run_id, attempt["attempt_id"])
        if key not in self._precommit_keys:
            raise DuplicateRecordError(f"missing_attempt_precommit:{key[0]}:{key[1]}")
        if key in self._attempt_keys:
            raise DuplicateRecordError(f"duplicate_attempt:{key[0]}:{key[1]}")
        self._attempt_keys.add(key)
        self.attempts_by_run.setdefault(run_id, []).append(attempt)
        event = self._build_event(
            event_type="attempt_observed",
            payload=attempt,
            event_id=f"{EVENT_ID_PREFIX_BY_TYPE['attempt_observed']}{attempt['attempt_id']}",
            event_ts_utc=attempt["attempt_ts_utc"],
            session_id=attempt.get("session_id"),
            causal_refs=[],
        )
        self.append_event(event)
        if self._root:
            self._append_jsonl(run_id, "attempts.jsonl", attempt)

    def append_attempt_telemetry(self, telemetry: dict[str, Any]) -> None:
        run_id = telemetry["run_id"]
        self._ensure_run_loaded(run_id)
        key = (run_id, telemetry["telemetry_event_id"])
        if key in self._telemetry_keys:
            raise DuplicateRecordError(f"duplicate_attempt_telemetry:{key[0]}:{key[1]}")
        self._telemetry_keys.add(key)
        self.telemetry_by_run.setdefault(run_id, []).append(telemetry)
        event = self._build_event(
            event_type="attempt_telemetry",
            payload=telemetry,
            event_id=f"{EVENT_ID_PREFIX_BY_TYPE['attempt_telemetry']}{telemetry['telemetry_event_id']}",
            event_ts_utc=telemetry["telemetry_ts_utc"],
            session_id=telemetry.get("session_id"),
            causal_refs=[telemetry.get("attempt_id")],
        )
        self.append_event(event)
        if self._root:
            self._append_jsonl(run_id, "attempt_telemetry.jsonl", telemetry)

    def append_state_snapshot(self, snapshot: dict[str, Any]) -> None:
        run_id = snapshot["run_id"]
        self._ensure_run_loaded(run_id)
        key = (run_id, snapshot["snapshot_id"])
        if key in self._snapshot_keys:
            raise DuplicateRecordError(f"duplicate_snapshot:{key[0]}:{key[1]}")
        self._snapshot_keys.add(key)
        self.snapshots_by_run.setdefault(run_id, []).append(snapshot)
        event = self._build_event(
            event_type="snapshot_checkpoint",
            payload=snapshot,
            event_id=f"{EVENT_ID_PREFIX_BY_TYPE['snapshot_checkpoint']}{snapshot['snapshot_id']}",
            event_ts_utc=snapshot["snapshot_ts_utc"],
            session_id=snapshot.get("session_id"),
            causal_refs=snapshot.get("source_attempt_ids", []),
        )
        self.append_event(event)
        if self._root:
            self._append_jsonl(run_id, "state_snapshots.jsonl", snapshot)

    def append_state_update(self, update: dict[str, Any]) -> None:
        run_id = update["run_id"]
        self._ensure_run_loaded(run_id)
        key = (run_id, update["update_id"])
        if key in self._update_keys:
            raise DuplicateRecordError(f"duplicate_state_update:{key[0]}:{key[1]}")
        self._update_keys.add(key)
        self.updates_by_run.setdefault(run_id, []).append(update)
        event = self._build_event(
            event_type="state_update",
            payload=update,
            event_id=f"{EVENT_ID_PREFIX_BY_TYPE['state_update']}{update['update_id']}",
            event_ts_utc=update["update_ts_utc"],
            session_id=update.get("session_id"),
            causal_refs=[update.get("source_attempt_id")],
        )
        self.append_event(event)
        if self._root:
            self._append_jsonl(run_id, "state_updates.jsonl", update)

    def append_state_migration(self, migration: dict[str, Any]) -> None:
        run_id = migration["run_id"]
        self._ensure_run_loaded(run_id)
        key = (run_id, migration["migration_event_id"])
        if key in self._migration_keys:
            raise DuplicateRecordError(f"duplicate_state_migration:{key[0]}:{key[1]}")
        self._migration_keys.add(key)
        self.migrations_by_run.setdefault(run_id, []).append(migration)
        event = self._build_event(
            event_type="state_migration",
            payload=migration,
            event_id=f"{EVENT_ID_PREFIX_BY_TYPE['state_migration']}{migration['migration_event_id']}",
            event_ts_utc=migration["migration_ts_utc"],
            session_id=migration.get("session_id"),
            causal_refs=[migration.get("source_run_id"), migration.get("source_snapshot_id")],
        )
        self.append_event(event)
        if self._root:
            self._append_jsonl(run_id, "state_migrations.jsonl", migration)

    def append_safe_mode_transition(self, event_payload: dict[str, Any]) -> None:
        event = self._build_event(
            event_type="safe_mode_transition",
            payload=event_payload,
            event_id=f"{EVENT_ID_PREFIX_BY_TYPE['safe_mode_transition']}{event_payload['event_id']}",
            event_ts_utc=str(event_payload["event_ts_utc"]),
            session_id=event_payload.get("session_id"),
            causal_refs=event_payload.get("causal_refs", []),
        )
        self.append_event(event)

    def append_quarantine_decision(self, event_payload: dict[str, Any]) -> None:
        event = self._build_event(
            event_type="quarantine_decision",
            payload=event_payload,
            event_id=f"{EVENT_ID_PREFIX_BY_TYPE['quarantine_decision']}{event_payload['event_id']}",
            event_ts_utc=str(event_payload["event_ts_utc"]),
            session_id=event_payload.get("session_id"),
            causal_refs=event_payload.get("causal_refs", []),
        )
        self.append_event(event)

    def append_anchor_audit(self, event_payload: dict[str, Any]) -> None:
        event = self._build_event(
            event_type="anchor_audit",
            payload=event_payload,
            event_id=f"{EVENT_ID_PREFIX_BY_TYPE['anchor_audit']}{event_payload['event_id']}",
            event_ts_utc=str(event_payload["event_ts_utc"]),
            session_id=event_payload.get("session_id"),
            causal_refs=event_payload.get("causal_refs", []),
        )
        self.append_event(event)

    def append_event(self, event: dict[str, Any]) -> None:
        event_type = event.get("event_type")
        run_id = event.get("run_id")
        event_id = event.get("event_id")
        if event_type not in EVENT_TYPES:
            raise DuplicateRecordError(f"invalid_event_type:{event_type}")
        if not isinstance(run_id, str) or not run_id:
            raise DuplicateRecordError("invalid_event_run_id")
        if not isinstance(event_id, str) or not event_id:
            raise DuplicateRecordError("invalid_event_id")
        self._ensure_run_loaded(run_id)
        key = (run_id, event_id)
        if key in self._event_keys:
            raise DuplicateRecordError(f"duplicate_event:{run_id}:{event_id}")
        next_seq = self._next_event_seq_by_run.get(run_id, 1)
        now = datetime.now(timezone.utc)
        prior_written_ts = self._last_event_written_ts_by_run.get(run_id)
        if prior_written_ts is not None and now <= prior_written_ts:
            now = prior_written_ts + timedelta(microseconds=1)
        materialized_event = dict(event)
        materialized_event["ledger_sequence_no"] = next_seq
        materialized_event["event_written_ts_utc"] = now.isoformat(timespec="microseconds").replace(
            "+00:00", "Z"
        )
        self._event_keys.add(key)
        self._next_event_seq_by_run[run_id] = next_seq + 1
        self._last_event_written_ts_by_run[run_id] = now
        self.events_by_run.setdefault(run_id, []).append(materialized_event)
        if self._root:
            self._append_jsonl(run_id, "events.jsonl", materialized_event)

    def get_manifest(self, run_id: str) -> dict[str, Any]:
        if run_id in self.manifests:
            return self.manifests[run_id]
        if not self._root:
            raise KeyError(run_id)
        path = self._root / "manifests" / f"run_manifest.{run_id}.json"
        if not path.exists():
            raise KeyError(run_id)
        manifest = json.loads(path.read_text(encoding="utf-8"))
        self.manifests[run_id] = manifest
        return manifest

    def get_attempts(self, run_id: str) -> list[dict[str, Any]]:
        self._ensure_run_loaded(run_id)
        return list(self.attempts_by_run.get(run_id, []))

    def get_attempt_telemetry(self, run_id: str) -> list[dict[str, Any]]:
        self._ensure_run_loaded(run_id)
        return list(self.telemetry_by_run.get(run_id, []))

    def get_precommits(self, run_id: str) -> list[dict[str, Any]]:
        self._ensure_run_loaded(run_id)
        return list(self.precommits_by_run.get(run_id, []))

    def get_snapshots(self, run_id: str) -> list[dict[str, Any]]:
        self._ensure_run_loaded(run_id)
        return list(self.snapshots_by_run.get(run_id, []))

    def get_updates(self, run_id: str) -> list[dict[str, Any]]:
        self._ensure_run_loaded(run_id)
        return list(self.updates_by_run.get(run_id, []))

    def get_migrations(self, run_id: str) -> list[dict[str, Any]]:
        self._ensure_run_loaded(run_id)
        return list(self.migrations_by_run.get(run_id, []))

    def get_events(self, run_id: str) -> list[dict[str, Any]]:
        self._ensure_run_loaded(run_id)
        return list(self.events_by_run.get(run_id, []))

    def _build_event(
        self,
        event_type: str,
        payload: dict[str, Any],
        event_id: str,
        event_ts_utc: str,
        session_id: str | None,
        causal_refs: list[Any],
    ) -> dict[str, Any]:
        return {
            "event_id": event_id,
            "event_ts_utc": event_ts_utc,
            "event_type": event_type,
            "run_id": payload["run_id"],
            "session_id": session_id,
            "causal_refs": list(causal_refs),
            "payload": payload,
        }

    def _append_jsonl(self, run_id: str, filename: str, payload: dict[str, Any]) -> None:
        assert self._root is not None
        run_dir = self._root / "ledger" / run_id
        run_dir.mkdir(parents=True, exist_ok=True)
        path = run_dir / filename
        with path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(payload, separators=(",", ":")) + "\n")

    def _ensure_run_loaded(self, run_id: str) -> None:
        if self._root is None or run_id in self._loaded_runs_from_disk:
            return
        run_dir = self._root / "ledger" / run_id
        self.precommits_by_run.setdefault(run_id, [])
        self.telemetry_by_run.setdefault(run_id, [])
        self.attempts_by_run.setdefault(run_id, [])
        self.snapshots_by_run.setdefault(run_id, [])
        self.updates_by_run.setdefault(run_id, [])
        self.migrations_by_run.setdefault(run_id, [])
        self.events_by_run.setdefault(run_id, [])
        if not run_dir.exists():
            self._loaded_runs_from_disk.add(run_id)
            return

        precommits = self._read_jsonl(run_dir / "attempt_precommits.jsonl")
        telemetry = self._read_jsonl(run_dir / "attempt_telemetry.jsonl")
        attempts = self._read_jsonl(run_dir / "attempts.jsonl")
        snapshots = self._read_jsonl(run_dir / "state_snapshots.jsonl")
        updates = self._read_jsonl(run_dir / "state_updates.jsonl")
        migrations = self._read_jsonl(run_dir / "state_migrations.jsonl")
        events = self._read_jsonl(run_dir / "events.jsonl")

        self.precommits_by_run[run_id] = precommits
        self.telemetry_by_run[run_id] = telemetry
        self.attempts_by_run[run_id] = attempts
        self.snapshots_by_run[run_id] = snapshots
        self.updates_by_run[run_id] = updates
        self.migrations_by_run[run_id] = migrations
        self.events_by_run[run_id] = events

        # If typed JSONL artifacts are absent, derive typed views from canonical events.
        if not precommits and events:
            self.precommits_by_run[run_id] = self._event_payloads(events, "attempt_precommitted")
        if not telemetry and events:
            self.telemetry_by_run[run_id] = self._event_payloads(events, "attempt_telemetry")
        if not attempts and events:
            self.attempts_by_run[run_id] = self._event_payloads(events, "attempt_observed")
        if not snapshots and events:
            self.snapshots_by_run[run_id] = self._event_payloads(events, "snapshot_checkpoint")
        if not updates and events:
            self.updates_by_run[run_id] = self._event_payloads(events, "state_update")
        if not migrations and events:
            self.migrations_by_run[run_id] = self._event_payloads(events, "state_migration")

        self._register_loaded_record_keys(run_id)
        self._register_loaded_event_indexes(run_id)
        self._loaded_runs_from_disk.add(run_id)

    def _read_jsonl(self, path: Path) -> list[dict[str, Any]]:
        if not path.exists():
            return []
        rows: list[dict[str, Any]] = []
        with path.open("r", encoding="utf-8") as f:
            for line_no, line in enumerate(f, start=1):
                text = line.strip()
                if text == "":
                    continue
                try:
                    row = json.loads(text)
                except json.JSONDecodeError as exc:
                    raise DuplicateRecordError(
                        f"invalid_jsonl:{path.name}:{line_no}:{exc.msg}"
                    ) from exc
                if not isinstance(row, dict):
                    raise DuplicateRecordError(f"invalid_jsonl_row_not_object:{path.name}:{line_no}")
                rows.append(row)
        return rows

    def _event_payloads(self, events: list[dict[str, Any]], event_type: str) -> list[dict[str, Any]]:
        payloads: list[dict[str, Any]] = []
        for event in events:
            if event.get("event_type") != event_type:
                continue
            payload = event.get("payload")
            if isinstance(payload, dict):
                payloads.append(payload)
        return payloads

    def _register_loaded_record_keys(self, run_id: str) -> None:
        for precommit in self.precommits_by_run.get(run_id, []):
            attempt_id = precommit.get("attempt_id")
            if not isinstance(attempt_id, str) or attempt_id == "":
                raise DuplicateRecordError(f"invalid_attempt_precommit_id:{run_id}")
            key = (run_id, attempt_id)
            if key in self._precommit_keys:
                raise DuplicateRecordError(f"duplicate_attempt_precommit:{run_id}:{attempt_id}")
            self._precommit_keys.add(key)

        for attempt in self.attempts_by_run.get(run_id, []):
            attempt_id = attempt.get("attempt_id")
            if not isinstance(attempt_id, str) or attempt_id == "":
                raise DuplicateRecordError(f"invalid_attempt_id:{run_id}")
            key = (run_id, attempt_id)
            if key in self._attempt_keys:
                raise DuplicateRecordError(f"duplicate_attempt:{run_id}:{attempt_id}")
            self._attempt_keys.add(key)

        for telemetry in self.telemetry_by_run.get(run_id, []):
            telemetry_event_id = telemetry.get("telemetry_event_id")
            if not isinstance(telemetry_event_id, str) or telemetry_event_id == "":
                raise DuplicateRecordError(f"invalid_attempt_telemetry_id:{run_id}")
            key = (run_id, telemetry_event_id)
            if key in self._telemetry_keys:
                raise DuplicateRecordError(
                    f"duplicate_attempt_telemetry:{run_id}:{telemetry_event_id}"
                )
            self._telemetry_keys.add(key)

        for snapshot in self.snapshots_by_run.get(run_id, []):
            snapshot_id = snapshot.get("snapshot_id")
            if not isinstance(snapshot_id, str) or snapshot_id == "":
                raise DuplicateRecordError(f"invalid_snapshot_id:{run_id}")
            key = (run_id, snapshot_id)
            if key in self._snapshot_keys:
                raise DuplicateRecordError(f"duplicate_snapshot:{run_id}:{snapshot_id}")
            self._snapshot_keys.add(key)

        for update in self.updates_by_run.get(run_id, []):
            update_id = update.get("update_id")
            if not isinstance(update_id, str) or update_id == "":
                raise DuplicateRecordError(f"invalid_state_update_id:{run_id}")
            key = (run_id, update_id)
            if key in self._update_keys:
                raise DuplicateRecordError(f"duplicate_state_update:{run_id}:{update_id}")
            self._update_keys.add(key)

        for migration in self.migrations_by_run.get(run_id, []):
            migration_event_id = migration.get("migration_event_id")
            if not isinstance(migration_event_id, str) or migration_event_id == "":
                raise DuplicateRecordError(f"invalid_state_migration_id:{run_id}")
            key = (run_id, migration_event_id)
            if key in self._migration_keys:
                raise DuplicateRecordError(f"duplicate_state_migration:{run_id}:{migration_event_id}")
            self._migration_keys.add(key)

    def _register_loaded_event_indexes(self, run_id: str) -> None:
        events = self.events_by_run.get(run_id, [])
        max_seq = 0
        max_written_ts: datetime | None = None
        seen_sequences: set[int] = set()
        for event in events:
            event_id = event.get("event_id")
            event_run_id = event.get("run_id")
            seq = event.get("ledger_sequence_no")
            written_ts_raw = event.get("event_written_ts_utc")
            if event_run_id != run_id:
                raise DuplicateRecordError(f"event_run_id_mismatch:{run_id}:{event_id}")
            if not isinstance(event_id, str) or event_id == "":
                raise DuplicateRecordError(f"invalid_event_id:{run_id}")
            key = (run_id, event_id)
            if key in self._event_keys:
                raise DuplicateRecordError(f"duplicate_event:{run_id}:{event_id}")
            self._event_keys.add(key)
            if not isinstance(seq, int) or isinstance(seq, bool) or seq <= 0:
                raise DuplicateRecordError(f"invalid_event_sequence:{run_id}:{event_id}")
            if seq in seen_sequences:
                raise DuplicateRecordError(f"duplicate_event_sequence:{run_id}:{seq}")
            seen_sequences.add(seq)
            if seq > max_seq:
                max_seq = seq
            if not isinstance(written_ts_raw, str) or written_ts_raw == "":
                raise DuplicateRecordError(f"invalid_event_written_ts:{run_id}:{event_id}")
            try:
                written_ts = datetime.fromisoformat(written_ts_raw.replace("Z", "+00:00")).astimezone(
                    timezone.utc
                )
            except ValueError as exc:
                raise DuplicateRecordError(
                    f"invalid_event_written_ts:{run_id}:{event_id}"
                ) from exc
            if max_written_ts is None or written_ts > max_written_ts:
                max_written_ts = written_ts
        self._next_event_seq_by_run[run_id] = max_seq + 1 if max_seq > 0 else 1
        if max_written_ts is not None:
            self._last_event_written_ts_by_run[run_id] = max_written_ts
