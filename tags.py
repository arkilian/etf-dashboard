"""Generate investment classification tags."""

from __future__ import annotations

import pandas as pd


def generate_tags(row: pd.Series) -> list[str]:
    """Generate descriptive investment tags for one company."""
    tags: list[str] = []

    if _value_gte(row.get("quality_score"), 8):
        tags.append("High Quality")
    if _value_gt(row.get("roic"), 12) and _value_gt(row.get("free_cash_flow"), 0):
        tags.append("Cash Machine")
    if _value_gt(row.get("debt_to_equity"), 2):
        tags.append("High Debt")
    if _is_speculative(row):
        tags.append("Speculative")
    if _is_expensive(row):
        tags.append("Expensive")
    if _is_value(row):
        tags.append("Value")
    if _is_growth(row):
        tags.append("Growth")

    return tags


def apply_tags(dataframe: pd.DataFrame) -> pd.DataFrame:
    """Attach tags as list and user-friendly string columns."""
    if dataframe.empty:
        return dataframe.copy()

    tagged = dataframe.copy()
    tagged["tags"] = tagged.apply(generate_tags, axis=1)
    tagged["tags_display"] = tagged["tags"].map(lambda items: ", ".join(items) if items else "")
    return tagged


def _is_speculative(row: pd.Series) -> bool:
    """Return whether a company looks speculative."""
    has_growth = _value_gt(row.get("revenue_growth"), 15) or _value_gt(row.get("earnings_growth"), 15)
    lacks_profit = _value_lte(row.get("net_margin"), 0) or _value_lte(row.get("free_cash_flow"), 0)
    return has_growth and lacks_profit


def _is_expensive(row: pd.Series) -> bool:
    """Return whether a company looks expensive."""
    return _value_gt(row.get("pe_ratio"), 35) or _value_gt(row.get("price_to_sales"), 8)


def _is_value(row: pd.Series) -> bool:
    """Return whether a company looks attractively valued."""
    return _value_lte(row.get("pe_ratio"), 15) and _value_gt(row.get("free_cash_flow"), 0)


def _is_growth(row: pd.Series) -> bool:
    """Return whether a company looks like a growth stock."""
    return _value_gt(row.get("revenue_growth"), 12) or _value_gt(row.get("earnings_growth"), 12)


def _value_gt(value: object, threshold: float) -> bool:
    """Return whether a value is above a threshold."""
    if value is None or pd.isna(value):
        return False
    return float(value) > threshold


def _value_gte(value: object, threshold: float) -> bool:
    """Return whether a value is above or equal to a threshold."""
    if value is None or pd.isna(value):
        return False
    return float(value) >= threshold


def _value_lte(value: object, threshold: float) -> bool:
    """Return whether a value is below or equal to a threshold."""
    if value is None or pd.isna(value):
        return False
    return float(value) <= threshold
