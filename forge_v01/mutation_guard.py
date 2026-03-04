"""Diagnosis-state mutation authorization rules."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class MutationDecision:
    allowed: bool
    reason: str


class MutationGuard:
    """Implements no-unlogged-mutation integrity for diagnosis updates."""

    def evaluate(self, state_update_event: dict[str, Any]) -> MutationDecision:
        patch = state_update_event.get("state_patch", {})
        target = patch.get("partition")
        if target != "diagnosis_state":
            return MutationDecision(True, "non_diagnosis_update")

        ledger_status = state_update_event.get("diagnosis_log_write_status")
        outcome = state_update_event.get("mutation_outcome")
        mutation_applied = state_update_event.get("mutation_applied")

        if ledger_status == "committed" and outcome == "applied" and mutation_applied is True:
            return MutationDecision(True, "committed_applied")
        if outcome == "blocked_by_governor":
            return MutationDecision(False, "blocked_by_governor")
        if outcome == "skipped_by_policy":
            return MutationDecision(False, "skipped_by_policy")
        if outcome == "failed_due_to_integrity":
            return MutationDecision(False, "failed_due_to_integrity")
        return MutationDecision(False, "invalid_mutation_outcome")
