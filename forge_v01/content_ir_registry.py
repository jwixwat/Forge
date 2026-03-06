"""Runtime content IR bundle registry for v0.2 ingestion."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

from .content_ir_loader import load_content_ir_bundle
from .content_ir_validator import validate_content_ir_bundle
from .content_ir_hashing import (
    fingerprint_observation_schema_semantics,
    fingerprint_response_canonicalization,
    fingerprint_response_parse_ir,
    fingerprint_rubric_semantics,
)


@dataclass
class _BundleIndexes:
    items: dict[str, dict[str, Any]]
    probe_families: dict[str, dict[str, Any]]
    rubrics: dict[str, dict[str, Any]]
    commitments: dict[str, dict[str, Any]]
    response_schemas: dict[str, dict[str, Any]]
    observation_schemas: dict[str, dict[str, Any]]
    measurement_surfaces: dict[str, dict[str, Any]]
    forms: dict[str, dict[str, Any]]
    generators: dict[str, dict[str, Any]]
    feedback_policies: dict[str, dict[str, Any]]
    delivery_artifacts: dict[str, dict[str, Any]]


class ContentIRRegistry:
    """Stores validated content IR bundles keyed by content IR version."""

    def __init__(
        self,
        validator: Callable[[dict[str, Any]], list[str]] | None = None,
        identity_index_path: str | Path | None = None,
        measurement_surface_identity_index_path: str | Path | None = None,
    ) -> None:
        if identity_index_path is not None and measurement_surface_identity_index_path is not None:
            raise ValueError(
                "content_ir_identity_index_path_conflict:use_only_measurement_surface_identity_index_path"
            )
        self._validator = validator or validate_content_ir_bundle
        self._bundles_by_version: dict[str, dict[str, Any]] = {}
        self._indexes_by_version: dict[str, _BundleIndexes] = {}
        resolved_index_path = (
            measurement_surface_identity_index_path
            if measurement_surface_identity_index_path is not None
            else identity_index_path
        )
        self._identity_index_path = Path(resolved_index_path) if resolved_index_path is not None else None
        self._measurement_surface_fingerprint_by_id = self._load_measurement_surface_index()

    def register_bundle(self, bundle: dict[str, Any]) -> None:
        errors = self._validator(bundle)
        if errors:
            raise ValueError("content_ir_invalid: " + "; ".join(errors))
        content_ir_version = bundle["content_ir_version"]
        if content_ir_version in self._bundles_by_version:
            raise ValueError(f"content_ir_duplicate_version:{content_ir_version}")
        self._enforce_measurement_surface_identity(bundle)
        self._bundles_by_version[content_ir_version] = bundle
        self._indexes_by_version[content_ir_version] = self._build_indexes(bundle)
        self._persist_measurement_surface_index()

    def register_bundle_from_path(self, path: str) -> None:
        bundle = load_content_ir_bundle(path)
        self.register_bundle(bundle)

    def get_bundle(self, content_ir_version: str) -> dict[str, Any]:
        if content_ir_version not in self._bundles_by_version:
            raise KeyError(content_ir_version)
        return self._bundles_by_version[content_ir_version]

    def resolve_commitment(self, content_ir_version: str, commitment_id: str) -> dict[str, Any]:
        indexes = self._get_indexes(content_ir_version)
        if commitment_id not in indexes.commitments:
            raise KeyError(commitment_id)
        return indexes.commitments[commitment_id]

    def resolve_probe_family(self, content_ir_version: str, probe_family_id: str) -> dict[str, Any]:
        indexes = self._get_indexes(content_ir_version)
        if probe_family_id not in indexes.probe_families:
            raise KeyError(probe_family_id)
        return indexes.probe_families[probe_family_id]

    def resolve_item(self, content_ir_version: str, item_id: str) -> dict[str, Any]:
        indexes = self._get_indexes(content_ir_version)
        if item_id not in indexes.items:
            raise KeyError(item_id)
        return indexes.items[item_id]

    def deterministic_rubric_exists(self, content_ir_version: str, item_id: str) -> bool:
        indexes = self._get_indexes(content_ir_version)
        item = indexes.items.get(item_id)
        if item is None:
            raise KeyError(item_id)
        rubric_ref = item["rubric_ref"]
        rubric = indexes.rubrics.get(rubric_ref)
        if rubric is None:
            raise KeyError(rubric_ref)
        return bool(rubric.get("deterministic"))

    def _get_indexes(self, content_ir_version: str) -> _BundleIndexes:
        if content_ir_version not in self._indexes_by_version:
            raise KeyError(content_ir_version)
        return self._indexes_by_version[content_ir_version]

    def _build_indexes(self, bundle: dict[str, Any]) -> _BundleIndexes:
        return _BundleIndexes(
            items={row["item_id"]: row for row in bundle.get("items", [])},
            probe_families={row["probe_family_id"]: row for row in bundle.get("probe_families", [])},
            rubrics={row["rubric_id"]: row for row in bundle.get("rubrics", [])},
            commitments={row["commitment_id"]: row for row in bundle.get("commitments", [])},
            response_schemas={row["response_schema_id"]: row for row in bundle.get("response_schemas", [])},
            observation_schemas={
                row["observation_schema_id"]: row for row in bundle.get("observation_schemas", [])
            },
            measurement_surfaces={
                row["measurement_surface_id"]: row for row in bundle.get("measurement_surfaces", [])
            },
            forms={row["form_id"]: row for row in bundle.get("forms", [])},
            generators={row["generator_id"]: row for row in bundle.get("generators", [])},
            feedback_policies={row["feedback_policy_id"]: row for row in bundle.get("feedback_policies", [])},
            delivery_artifacts={row["artifact_id"]: row for row in bundle.get("delivery_artifacts", [])},
        )

    def _enforce_measurement_surface_identity(self, bundle: dict[str, Any]) -> None:
        rows = bundle.get("measurement_surfaces", [])
        if not isinstance(rows, list):
            return
        observation_schema_by_id = {
            str(row.get("observation_schema_id")): row
            for row in bundle.get("observation_schemas", [])
            if isinstance(row, dict) and isinstance(row.get("observation_schema_id"), str) and row.get("observation_schema_id")
        }
        response_schema_by_id = {
            str(row.get("response_schema_id")): row
            for row in bundle.get("response_schemas", [])
            if isinstance(row, dict) and isinstance(row.get("response_schema_id"), str) and row.get("response_schema_id")
        }
        rubric_by_id = {
            str(row.get("rubric_id")): row
            for row in bundle.get("rubrics", [])
            if isinstance(row, dict) and isinstance(row.get("rubric_id"), str) and row.get("rubric_id")
        }
        for row in rows:
            if not isinstance(row, dict):
                continue
            surface_id = row.get("measurement_surface_id")
            if not isinstance(surface_id, str) or surface_id == "":
                continue
            fingerprint = self._measurement_surface_fingerprint(
                row,
                observation_schema_by_id=observation_schema_by_id,
                response_schema_by_id=response_schema_by_id,
                rubric_by_id=rubric_by_id,
            )
            prior = self._measurement_surface_fingerprint_by_id.get(surface_id)
            if prior is None:
                self._measurement_surface_fingerprint_by_id[surface_id] = fingerprint
                continue
            if prior != fingerprint:
                raise ValueError(f"content_ir_measurement_surface_repoint:{surface_id}")

    def _load_measurement_surface_index(self) -> dict[str, str]:
        if self._identity_index_path is None or not self._identity_index_path.exists():
            return {}
        raw = json.loads(self._identity_index_path.read_text(encoding="utf-8"))
        if not isinstance(raw, dict):
            raise ValueError("content_ir_identity_index_invalid_format")
        loaded: dict[str, str] = {}
        for key, value in raw.items():
            if not isinstance(key, str) or key == "":
                raise ValueError("content_ir_identity_index_invalid_surface_id")
            if not isinstance(value, str) or value == "":
                raise ValueError("content_ir_identity_index_invalid_fingerprint")
            loaded[key] = value
        return loaded

    def _persist_measurement_surface_index(self) -> None:
        if self._identity_index_path is None:
            return
        self._identity_index_path.parent.mkdir(parents=True, exist_ok=True)
        payload = json.dumps(
            self._measurement_surface_fingerprint_by_id,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
        )
        temp_path = self._identity_index_path.with_suffix(self._identity_index_path.suffix + ".tmp")
        temp_path.write_text(payload, encoding="utf-8")
        temp_path.replace(self._identity_index_path)

    @staticmethod
    def _measurement_surface_fingerprint(
        row: dict[str, Any],
        *,
        observation_schema_by_id: dict[str, dict[str, Any]],
        response_schema_by_id: dict[str, dict[str, Any]],
        rubric_by_id: dict[str, dict[str, Any]],
    ) -> str:
        obs_binding = row.get("obs_binding")
        if isinstance(obs_binding, dict):
            canonical_binding = {
                "obs_encoder_version": obs_binding.get("obs_encoder_version"),
                "hypothesis_space_hash": obs_binding.get("hypothesis_space_hash"),
            }
        else:
            canonical_binding = {}
        observation_schema_ref = row.get("observation_schema_ref")
        response_schema_ref = row.get("response_schema_ref")
        rubric_ref = row.get("rubric_ref")
        semantic_anchor = {
            "observation_schema_semantics_hash": (
                fingerprint_observation_schema_semantics(observation_schema_by_id[str(observation_schema_ref)])
                if isinstance(observation_schema_ref, str) and observation_schema_ref in observation_schema_by_id
                else None
            ),
            "response_schema_ref": response_schema_ref,
            "canonicalization_hash": (
                fingerprint_response_canonicalization(response_schema_by_id[str(response_schema_ref)])
                if isinstance(response_schema_ref, str) and response_schema_ref in response_schema_by_id
                else None
            ),
            "parse_ir_hash": (
                fingerprint_response_parse_ir(response_schema_by_id[str(response_schema_ref)])
                if isinstance(response_schema_ref, str) and response_schema_ref in response_schema_by_id
                else None
            ),
            "rubric_ref": rubric_ref,
            "rubric_semantics_hash": (
                fingerprint_rubric_semantics(rubric_by_id[str(rubric_ref)])
                if isinstance(rubric_ref, str) and rubric_ref in rubric_by_id
                else None
            ),
            "obs_binding": canonical_binding,
        }
        return hashlib.sha256(
            json.dumps(semantic_anchor, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
        ).hexdigest()
