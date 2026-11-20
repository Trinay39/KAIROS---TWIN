"""Authoritative ML feature contract for training and inference.

The production model is trained and served with the exact order defined by
``FeatureEngine.FEATURE_NAMES``. CSV columns use the same names with an ``X_``
prefix, while live inference uses raw feature names.
"""
from __future__ import annotations

from typing import Mapping, Sequence

import numpy as np

from core.feature_engine import FeatureEngine


RAW_FEATURE_NAMES: tuple[str, ...] = tuple(FeatureEngine.FEATURE_NAMES)
PREFIXED_FEATURE_NAMES: tuple[str, ...] = tuple(
    f"X_{name}" for name in RAW_FEATURE_NAMES
)
EXPECTED_FEATURE_COUNT = len(RAW_FEATURE_NAMES)


class FeatureContractError(ValueError):
    """Raised when features do not match the production feature contract."""


def validate_raw_feature_mapping(features: Mapping[str, float]) -> None:
    """Fail loudly if a raw feature mapping misses or adds any feature."""
    actual = set(features)
    expected = set(RAW_FEATURE_NAMES)
    missing = sorted(expected - actual)
    unexpected = sorted(actual - expected)
    if missing or unexpected:
        details = []
        if missing:
            details.append(f"missing required features: {missing}")
        if unexpected:
            details.append(f"unexpected features: {unexpected}")
        raise FeatureContractError("; ".join(details))

    if len(features) != EXPECTED_FEATURE_COUNT:
        raise FeatureContractError(
            f"feature count mismatch: expected {EXPECTED_FEATURE_COUNT}, got {len(features)}"
        )


def validate_prefixed_feature_columns(columns: Sequence[str]) -> None:
    """Validate CSV/dataframe feature columns against the contract."""
    actual = set(columns)
    expected = set(PREFIXED_FEATURE_NAMES)
    missing = sorted(expected - actual)
    unexpected = sorted(actual - expected)
    if missing or unexpected:
        details = []
        if missing:
            details.append(f"missing required feature columns: {missing}")
        if unexpected:
            details.append(f"unexpected feature columns: {unexpected}")
        raise FeatureContractError("; ".join(details))


def raw_mapping_to_array(features: Mapping[str, float]) -> np.ndarray:
    """Convert a validated raw feature mapping to a 2D model input array."""
    validate_raw_feature_mapping(features)
    return np.array([[float(features[name]) for name in RAW_FEATURE_NAMES]], dtype=np.float32)


def prefixed_feature_order() -> list[str]:
    """Return CSV feature columns in production order."""
    return list(PREFIXED_FEATURE_NAMES)


def raw_feature_order() -> list[str]:
    """Return raw inference feature names in production order."""
    return list(RAW_FEATURE_NAMES)
