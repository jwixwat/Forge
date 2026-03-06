"""Filesystem loader helpers for v0.2 content IR bundles."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .content_ir_validator import validate_content_ir_bundle


def load_content_ir_bundle(path: str | Path) -> dict[str, Any]:
    """Load a content IR bundle from JSON file."""
    p = Path(path)
    return json.loads(p.read_text(encoding="utf-8"))


def load_and_validate_content_ir_bundle(path: str | Path) -> tuple[dict[str, Any], list[str]]:
    """Load and validate a content IR bundle from JSON file."""
    bundle = load_content_ir_bundle(path)
    return bundle, validate_content_ir_bundle(bundle)
