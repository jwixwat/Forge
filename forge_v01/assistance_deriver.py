"""Deterministic assistance-mode derivation from immutable telemetry events."""

from __future__ import annotations

from typing import Any


def derive_assistance_mode_from_telemetry(
    telemetry_events: list[dict[str, Any]],
) -> tuple[str, list[str]]:
    """Return (assistance_mode_derived, reason_codes).

    Derivation is intentionally conservative:
    - any tool usage => tool_assisted
    - any open-book/resource/hint/paste signals => open_book
    - empty/unusable stream => mixed (fail closed for diagnosis authority)
    """

    if not telemetry_events:
        return ("mixed", ["missing_telemetry_window"])

    saw_tool = False
    saw_open_signals = False
    reason_codes: list[str] = []

    for event in telemetry_events:
        kind = event.get("telemetry_kind")
        if kind == "tool_call":
            saw_tool = True
        elif kind in {"resource_access", "hint_request", "paste"}:
            saw_open_signals = True
        elif kind == "ui_mode_toggle":
            mode = event.get("mode")
            if mode in {"open_book", "mixed"}:
                saw_open_signals = True
            elif mode == "tool_assisted":
                saw_tool = True

    if saw_tool:
        reason_codes.append("tool_signal_present")
        return ("tool_assisted", reason_codes)
    if saw_open_signals:
        reason_codes.append("open_book_signal_present")
        return ("open_book", reason_codes)
    reason_codes.append("no_assistance_signals")
    return ("closed_book", reason_codes)

