"""Observation vocabulary registry keyed by pinned semantics."""

from __future__ import annotations

from typing import Any

from .measurement_frame import enumerate_projection_vocab


class ObservationVocabularyRegistry:
    """Provides known observation vocab sets for a semantic binding."""

    def __init__(self) -> None:
        # v0.1 default binding used by acceptance fixtures.
        self._vocab_by_binding: dict[tuple[str, str, str | None, str | None], set[str]] = {
            (
                "obsenc.v0.1.0",
                "hyp_hash_001",
                None,
                None,
            ): {
                "SLOT(a=pass,b=fail)",
                "SLOT(a=pass,b=pass)",
                "SLOT(a=fail,b=fail)",
            }
        }

    def get_vocab(
        self,
        obs_encoder_version: str,
        hypothesis_space_hash: str,
        calibration_projection_id: str | None = None,
        measurement_surface_id: str | None = None,
    ) -> set[str] | None:
        key = (
            obs_encoder_version,
            hypothesis_space_hash,
            calibration_projection_id,
            measurement_surface_id,
        )
        vocab = self._vocab_by_binding.get(key)
        if vocab is None and calibration_projection_id is not None:
            vocab = self._vocab_by_binding.get(
                (obs_encoder_version, hypothesis_space_hash, calibration_projection_id, None)
            )
        if vocab is None:
            vocab = self._vocab_by_binding.get((obs_encoder_version, hypothesis_space_hash, None, None))
        if vocab is None:
            return None
        return set(vocab)

    def register_vocab(
        self,
        obs_encoder_version: str,
        hypothesis_space_hash: str,
        vocab: set[str] | list[str],
        calibration_projection_id: str | None = None,
        measurement_surface_id: str | None = None,
    ) -> None:
        normalized = {str(value) for value in vocab if isinstance(value, str) and value}
        self._vocab_by_binding[
            (obs_encoder_version, hypothesis_space_hash, calibration_projection_id, measurement_surface_id)
        ] = normalized

    def register_bundle(self, bundle: dict[str, Any]) -> None:
        measurement_surfaces = bundle.get("measurement_surfaces")
        observation_schemas = bundle.get("observation_schemas")
        probe_families = bundle.get("probe_families")
        if (
            not isinstance(measurement_surfaces, list)
            or not isinstance(observation_schemas, list)
            or not isinstance(probe_families, list)
        ):
            return
        observation_schema_by_id = {
            str(row.get("observation_schema_id")): row
            for row in observation_schemas
            if isinstance(row, dict) and isinstance(row.get("observation_schema_id"), str)
        }
        measurement_surface_by_id = {
            str(row.get("measurement_surface_id")): row
            for row in measurement_surfaces
            if isinstance(row, dict) and isinstance(row.get("measurement_surface_id"), str)
        }
        for family in probe_families:
            if not isinstance(family, dict):
                continue
            measurement_surface_refs = family.get("measurement_surface_refs")
            calibration_contract = family.get("calibration_contract")
            if not isinstance(measurement_surface_refs, list) or not isinstance(calibration_contract, dict):
                continue
            projection = calibration_contract.get("calibration_target_projection")
            if not isinstance(projection, dict):
                continue
            calibration_projection_id = projection.get("projection_id")
            if not isinstance(calibration_projection_id, str) or calibration_projection_id == "":
                continue
            for surface_id in measurement_surface_refs:
                if not isinstance(surface_id, str):
                    continue
                surface = measurement_surface_by_id.get(surface_id)
                if not isinstance(surface, dict):
                    continue
                obs_binding = surface.get("obs_binding")
                observation_schema_ref = surface.get("observation_schema_ref")
                if not isinstance(obs_binding, dict) or not isinstance(observation_schema_ref, str):
                    continue
                obs_encoder_version = obs_binding.get("obs_encoder_version")
                hypothesis_space_hash = obs_binding.get("hypothesis_space_hash")
                observation_schema = observation_schema_by_id.get(observation_schema_ref)
                if not isinstance(obs_encoder_version, str) or not isinstance(hypothesis_space_hash, str):
                    continue
                if not isinstance(observation_schema, dict):
                    continue
                vocab = enumerate_projection_vocab(projection, observation_schema)
                if not vocab:
                    continue
                self.register_vocab(
                    obs_encoder_version,
                    hypothesis_space_hash,
                    vocab,
                    calibration_projection_id=calibration_projection_id,
                    measurement_surface_id=surface_id,
                )
                generic_key = (obs_encoder_version, hypothesis_space_hash, None, None)
                prior_generic = self._vocab_by_binding.get(generic_key)
                if prior_generic is None:
                    self._vocab_by_binding[generic_key] = set(vocab)
                elif prior_generic == vocab:
                    self._vocab_by_binding[generic_key] = set(vocab)
                else:
                    # Do not overwrite a generic binding once multiple projection-specific
                    # vocabularies exist for the same encoder/keyspace pair.
                    pass
