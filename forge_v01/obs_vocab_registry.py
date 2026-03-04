"""Observation vocabulary registry keyed by pinned semantics."""

from __future__ import annotations


class ObservationVocabularyRegistry:
    """Provides known observation vocab sets for a semantic binding."""

    def __init__(self) -> None:
        # v0.1 default binding used by acceptance fixtures.
        self._vocab_by_binding: dict[tuple[str, str], set[str]] = {
            (
                "obsenc.v0.1.0",
                "hyp_hash_001",
            ): {
                "SLOT(a=pass,b=fail)",
                "SLOT(a=pass,b=pass)",
                "SLOT(a=fail,b=fail)",
            }
        }

    def get_vocab(self, obs_encoder_version: str, hypothesis_space_hash: str) -> set[str] | None:
        key = (obs_encoder_version, hypothesis_space_hash)
        vocab = self._vocab_by_binding.get(key)
        if vocab is None:
            return None
        return set(vocab)
