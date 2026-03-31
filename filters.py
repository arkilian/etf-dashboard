"""Reusable investment filter helpers."""

from __future__ import annotations

import pandas as pd


def is_high_quality(row: pd.Series) -> bool:
    """Return whether a company meets the high-quality threshold."""
    quality_score = row.get("quality_score")
    return bool(pd.notna(quality_score) and float(quality_score) >= 8)


def is_compounder(row: pd.Series) -> bool:
    """Return whether a company matches the compounder profile."""
    return (
        _value_gt(row.get("roic"), 12)
        and _value_gt(row.get("free_cash_flow"), 0)
        and _value_gt(row.get("revenue_growth"), 5)
    )


def is_value_stock(row: pd.Series) -> bool:
    """Return whether a company looks like a value stock."""
    return (
        _value_lte(row.get("pe_ratio"), 15)
        and _value_lt(row.get("price_to_sales"), 3)
        and _value_gt(row.get("free_cash_flow"), 0)
    )


def is_growth_stock(row: pd.Series) -> bool:
    """Return whether a company looks like a growth stock."""
    return (
        _value_gt(row.get("revenue_growth"), 12)
        and _value_gt(row.get("earnings_growth"), 10)
    ) or (
        _value_gt(row.get("revenue_growth"), 15)
        and _value_gt(row.get("price_to_sales"), 4)
    )


def apply_investment_filters(
    dataframe: pd.DataFrame,
    *,
    only_high_quality: bool = False,
    only_compounders: bool = False,
    only_value: bool = False,
    only_growth: bool = False,
    score_range: tuple[int, int] = (0, 10),
) -> pd.DataFrame:
    """Apply investment filter toggles and score boundaries."""
    if dataframe.empty:
        return dataframe.copy()

    filtered = dataframe.copy()
    filtered = filtered[
        filtered["quality_score"].fillna(0).between(score_range[0], score_range[1], inclusive="both")
    ]

    if only_high_quality:
        filtered = filtered[filtered.apply(is_high_quality, axis=1)]
    if only_compounders:
        filtered = filtered[filtered.apply(is_compounder, axis=1)]
    if only_value:
        filtered = filtered[filtered.apply(is_value_stock, axis=1)]
    if only_growth:
        filtered = filtered[filtered.apply(is_growth_stock, axis=1)]

    return filtered


def _value_gt(value: object, threshold: float) -> bool:
    """Return whether a value is above a threshold."""
    if value is None or pd.isna(value):
        return False
    return float(value) > threshold


def _value_lt(value: object, threshold: float) -> bool:
    """Return whether a value is below a threshold."""
    if value is None or pd.isna(value):
        return False
    return float(value) < threshold


def _value_lte(value: object, threshold: float) -> bool:
    """Return whether a value is below or equal to a threshold."""
    if value is None or pd.isna(value):
        return False
    return float(value) <= threshold
