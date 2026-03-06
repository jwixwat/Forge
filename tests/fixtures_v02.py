"""Fixtures for v0.2 content IR ingestion tests."""

from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from typing import Any


def clone(value: Any) -> Any:
    return deepcopy(value)


def v02_bundle_path() -> Path:
    return (
        Path(__file__).resolve().parents[1]
        / "content_ir"
        / "releases"
        / "content.v2026.03.04.regex.v0.2.json"
    )


def load_valid_v02_bundle() -> dict[str, Any]:
    return json.loads(v02_bundle_path().read_text(encoding="utf-8"))
