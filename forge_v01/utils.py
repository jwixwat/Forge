"""Shared validation helpers."""

from __future__ import annotations

import hashlib
import json
import math
import re
from datetime import datetime, timezone
from typing import Any, Iterable


def missing_required_fields(record: Any, required: Iterable[str]) -> list[str]:
    if not isinstance(record, dict):
        return sorted(list(required))
    return sorted([field for field in required if field not in record])


def is_non_empty_string(value: Any) -> bool:
    return isinstance(value, str) and value != ""


def is_strict_int(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def is_strict_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def is_probability(value: Any) -> bool:
    if not is_strict_number(value):
        return False
    numeric = float(value)
    return 0.0 <= numeric <= 1.0


def float_equal(a: float, b: float, tolerance: float = 1e-6) -> bool:
    return abs(a - b) <= tolerance


def _canonical_number(value: float) -> str:
    if not math.isfinite(value):
        raise ValueError("non_finite_float_not_supported_for_canonical_hash")
    if value == 0.0:
        return "0"
    text = format(value, ".17g").replace("E", "e")
    text = re.sub(r"e\+?", "e", text)
    return text


def _canonical_json(value: Any) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int):
        return str(value)
    if isinstance(value, float):
        return _canonical_number(value)
    if isinstance(value, str):
        return json.dumps(value, ensure_ascii=True, separators=(",", ":"))
    if isinstance(value, list):
        return "[" + ",".join(_canonical_json(item) for item in value) + "]"
    if isinstance(value, dict):
        items: list[str] = []
        for key in sorted(value.keys()):
            if not isinstance(key, str):
                raise TypeError("canonical_json_requires_string_keys")
            items.append(
                json.dumps(key, ensure_ascii=True, separators=(",", ":"))
                + ":"
                + _canonical_json(value[key])
            )
        return "{" + ",".join(items) + "}"
    raise TypeError(f"canonical_json_unsupported_type:{type(value).__name__}")


def stable_json_dumps(value: Any) -> str:
    return _canonical_json(value)


def sha256_json(value: Any) -> str:
    payload = stable_json_dumps(value).encode("utf-8")
    return "sha256:" + hashlib.sha256(payload).hexdigest()


RFC3339_UTC_RE = re.compile(
    r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,6})?Z$"
)


def is_rfc3339_utc(value: Any) -> bool:
    if not isinstance(value, str) or not RFC3339_UTC_RE.match(value):
        return False
    try:
        parse_rfc3339_utc(value)
    except ValueError:
        return False
    return True


def parse_rfc3339_utc(value: str) -> datetime:
    if not isinstance(value, str) or not RFC3339_UTC_RE.match(value):
        raise ValueError("invalid_rfc3339_utc")
    dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if dt.tzinfo is None:
        raise ValueError("timestamp_missing_tz")
    return dt.astimezone(timezone.utc)
