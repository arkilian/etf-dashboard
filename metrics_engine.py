"""Compute normalized financial metrics for holdings data."""

from __future__ import annotations

import pandas as pd

METRIC_COLUMNS = [
    "pe_ratio",
    "price_to_sales",
    "roic",
    "roe",
    "gross_margin",
    "operating_margin",
    "net_margin",
    "revenue_growth",
    "earnings_growth",
    "free_cash_flow",
    "debt_to_equity",
    "beta",
]


def compute_financial_metrics(dataframe: pd.DataFrame) -> pd.DataFrame:
    """Compute normalized metrics from raw yfinance fields."""
    if dataframe.empty:
        return dataframe.copy()

    metrics_df = dataframe.copy()
    metrics_df["pe_ratio"] = metrics_df.get("pe_ratio_raw", pd.Series(dtype=float)).map(_to_float)
    metrics_df["price_to_sales"] = metrics_df.get("price_to_sales_raw", pd.Series(dtype=float)).map(_to_float)
    metrics_df["roic"] = metrics_df.apply(_compute_roic, axis=1)
    metrics_df["roe"] = metrics_df.get("roe_raw", pd.Series(dtype=float)).map(_to_percentage_points)
    metrics_df["gross_margin"] = metrics_df.get("gross_margin_raw", pd.Series(dtype=float)).map(
        _to_percentage_points
    )
    metrics_df["operating_margin"] = metrics_df.get(
        "operating_margin_raw",
        pd.Series(dtype=float),
    ).map(_to_percentage_points)
    metrics_df["net_margin"] = metrics_df.get("net_margin_raw", pd.Series(dtype=float)).map(
        _to_percentage_points
    )
    metrics_df["revenue_growth"] = metrics_df.get(
        "revenue_growth_raw",
        pd.Series(dtype=float),
    ).map(_to_percentage_points)
    metrics_df["earnings_growth"] = metrics_df.get(
        "earnings_growth_raw",
        pd.Series(dtype=float),
    ).map(_to_percentage_points)
    metrics_df["free_cash_flow"] = metrics_df.get("free_cash_flow_raw", pd.Series(dtype=float)).map(_to_float)
    metrics_df["debt_to_equity"] = metrics_df.get(
        "debt_to_equity_raw",
        pd.Series(dtype=float),
    ).map(_normalize_debt_to_equity)
    metrics_df["beta"] = metrics_df.get("beta_raw", pd.Series(dtype=float)).map(_to_float)

    return metrics_df


def _compute_roic(row: pd.Series) -> float | None:
    """Compute ROIC or use a safe proxy when unavailable."""
    roic_raw = row.get("roic_raw")
    if pd.notna(roic_raw):
        return _to_percentage_points(roic_raw)

    return _to_percentage_points(row.get("return_on_assets_raw"))


def _to_float(value: object) -> float | None:
    """Safely coerce a value to float."""
    if value is None or pd.isna(value):
        return None

    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _to_percentage_points(value: object) -> float | None:
    """Convert ratio-like values to percentage points."""
    numeric = _to_float(value)
    if numeric is None:
        return None

    if -1.5 <= numeric <= 1.5:
        return numeric * 100
    return numeric


def _normalize_debt_to_equity(value: object) -> float | None:
    """Normalize debt-to-equity values to ratio units."""
    numeric = _to_float(value)
    if numeric is None:
        return None

    if numeric > 10:
        return numeric / 100
    return numeric
