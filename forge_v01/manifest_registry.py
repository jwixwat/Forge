"""Run manifest registration and lookup."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .contract_validator import ContractValidator


class ManifestRegistry:
    """Stores run manifests and provides replay projections."""

    def __init__(self, root: str | None = None) -> None:
        self._manifests: dict[str, dict[str, Any]] = {}
        self._root = Path(root) if root else None
        if self._root:
            (self._root / "manifests").mkdir(parents=True, exist_ok=True)

    def register(self, manifest: dict[str, Any], validator: ContractValidator) -> None:
        errors = validator.validate_manifest(manifest)
        if errors:
            raise ValueError("manifest_invalid: " + "; ".join(errors))
        run_id = manifest["run_id"]
        if run_id in self._manifests:
            raise ValueError(f"manifest_duplicate_for_run:{run_id}")
        self._manifests[run_id] = manifest
        if self._root:
            target = self._root / "manifests" / f"run_manifest.{run_id}.json"
            target.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    def get(self, run_id: str) -> dict[str, Any]:
        if run_id in self._manifests:
            return self._manifests[run_id]
        if not self._root:
            raise KeyError(run_id)
        target = self._root / "manifests" / f"run_manifest.{run_id}.json"
        if not target.exists():
            raise KeyError(run_id)
        manifest = json.loads(target.read_text(encoding="utf-8"))
        self._manifests[run_id] = manifest
        return manifest

    def replay_projection(self, run_id: str, validator: ContractValidator) -> dict[str, Any]:
        manifest = self.get(run_id)
        return validator.replay_projection(manifest)
