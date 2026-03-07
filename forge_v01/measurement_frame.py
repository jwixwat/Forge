"""Authoritative measurement-frame helpers for v0.3 runtime."""

from __future__ import annotations

from itertools import product
from typing import Any


def derive_obs_key_from_projection(
    projection: dict[str, Any],
    observation_features: dict[str, Any],
    *,
    observation_status: str,
) -> str | None:
    if observation_status != "valid":
        return None
    mapping_rules = projection.get("mapping_rules") if isinstance(projection, dict) else None
    if not isinstance(mapping_rules, list) or not mapping_rules:
        return None
    parts: list[str] = []
    for rule in sorted(
        [row for row in mapping_rules if isinstance(row, dict)],
        key=lambda row: str(row.get("target", "")),
    ):
        source_features = rule.get("source_features")
        if not isinstance(source_features, list) or not source_features:
            return None
        feature_parts: list[str] = []
        for feature_id in source_features:
            if not isinstance(feature_id, str) or feature_id == "":
                return None
            if feature_id not in observation_features:
                return None
            feature_parts.append(f"{feature_id}={observation_features[feature_id]}")
        parts.append("|".join(feature_parts))
    if not parts:
        return None
    return ";".join(parts)


def enumerate_projection_vocab(
    projection: dict[str, Any],
    observation_schema: dict[str, Any],
) -> set[str]:
    mapping_rules = projection.get("mapping_rules") if isinstance(projection, dict) else None
    if not isinstance(mapping_rules, list) or not mapping_rules:
        return set()
    feature_map = _observation_feature_map(observation_schema)
    vocab: set[str] = set()
    for rule in mapping_rules:
        if not isinstance(rule, dict):
            continue
        source_features = rule.get("source_features")
        if not isinstance(source_features, list) or not source_features:
            return set()
        allowed_lists: list[list[Any]] = []
        normalized_feature_ids: list[str] = []
        for feature_id in source_features:
            if not isinstance(feature_id, str) or feature_id == "":
                return set()
            feature = feature_map.get(feature_id)
            if not isinstance(feature, dict):
                return set()
            allowed_values = feature.get("allowed_values")
            if not isinstance(allowed_values, list) or not allowed_values:
                return set()
            normalized_feature_ids.append(feature_id)
            allowed_lists.append(list(allowed_values))
        for combo in product(*allowed_lists):
            part = "|".join(f"{feature_id}={value}" for feature_id, value in zip(normalized_feature_ids, combo))
            vocab.add(part)
    return vocab


def _observation_feature_map(observation_schema: dict[str, Any]) -> dict[str, dict[str, Any]]:
    features = observation_schema.get("features")
    if not isinstance(features, list):
        return {}
    feature_map: dict[str, dict[str, Any]] = {}
    for feature in features:
        if not isinstance(feature, dict):
            continue
        feature_id = feature.get("feature_id")
        if isinstance(feature_id, str) and feature_id:
            feature_map[feature_id] = feature
    return feature_map
