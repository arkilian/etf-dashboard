"""Scoring functions for investment quality and risk."""

from __future__ import annotations

import pandas as pd

CYCLICAL_SECTORS = {
    "basic materials",
    "consumer cyclical",
    "consumer discretionary",
    "energy",
    "industrials",
    "real estate",
}


def calculate_quality_score(row: pd.Series) -> int:
    """Return a 0-10 quality score based on profitability and balance sheet rules."""
    score = 0

    if _value_gt(row.get("roic"), 12):
        score += 2
    if _value_gt(row.get("operating_margin"), 15):
        score += 2
    if _value_lt(row.get("debt_to_equity"), 1):
        score += 2
    if _value_gt(row.get("free_cash_flow"), 0):
        score += 2
    if _value_gt(row.get("revenue_growth"), 5):
        score += 2

    return min(score, 10)


def calculate_risk_score(row: pd.Series) -> int:
    """Return a simple additive risk score."""
    score = 0

    if _value_gt(row.get("debt_to_equity"), 2):
        score += 2
    if _value_lte(row.get("free_cash_flow"), 0):
        score += 2
    if _value_gt(row.get("beta"), 1.5):
        score += 1
    if _is_cyclical_sector(row.get("Sector")):
        score += 1

    return score


def apply_scores(dataframe: pd.DataFrame) -> pd.DataFrame:
    """Add quality and risk scores to the dataframe."""
    if dataframe.empty:
        return dataframe.copy()

    scored = dataframe.copy()
    scored["quality_score"] = scored.apply(calculate_quality_score, axis=1)
    scored["risk_score"] = scored.apply(calculate_risk_score, axis=1)
    return scored


def _is_cyclical_sector(value: object) -> bool:
    """Return whether a sector should be treated as cyclical."""
    if value is None or pd.isna(value):
        return False
    return str(value).strip().lower() in CYCLICAL_SECTORS


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
