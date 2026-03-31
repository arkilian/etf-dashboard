"""Overview page for ETF holdings analysis."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st

try:
    from app.data_sources.etf_holdings import discover_etf_csv_files, load_holdings_for_etf
    from app.data_sources.yfinance_client import enrich_holdings_with_market_data
    from app.utils.helpers import format_billions
except ModuleNotFoundError:
    from data_sources.etf_holdings import discover_etf_csv_files, load_holdings_for_etf
    from data_sources.yfinance_client import enrich_holdings_with_market_data
    from utils.helpers import format_billions

ETF_LISTS_DIR = Path(__file__).resolve().parents[2] / "data" / "etf_lists"


@st.cache_data(show_spinner=False)
def _load_holdings_cached(etf_name: str) -> pd.DataFrame:
    return load_holdings_for_etf(etf_name=etf_name, base_dir=ETF_LISTS_DIR)


@st.cache_data(show_spinner=True)
def _enrich_cached(holdings: pd.DataFrame, max_tickers: int) -> pd.DataFrame:
    return enrich_holdings_with_market_data(holdings=holdings, max_tickers=max_tickers)


def render() -> None:
    """Render the ETF overview page."""
    st.title("ETF Dashboard")
    st.caption("Load ETF holdings from CSV, enrich with yfinance, and filter positions.")

    etf_files = discover_etf_csv_files(ETF_LISTS_DIR)
    if not etf_files:
        st.warning("No ETF CSV files found in data/etf_lists.")
        return

    selected_etf = st.sidebar.selectbox("ETF", list(etf_files.keys()))
    enrich_with_market = st.sidebar.checkbox("Enrich with yfinance", value=True)
    max_tickers = st.sidebar.slider("Max tickers to query", 10, 120, 40, 5)

    holdings = _load_holdings_cached(selected_etf)
    dataframe = holdings.copy()

    if enrich_with_market:
        dataframe = _enrich_cached(dataframe, max_tickers=max_tickers)

    filtered = _apply_filters(dataframe)
    _render_summary(filtered)
    _render_table(filtered)


def _apply_filters(dataframe: pd.DataFrame) -> pd.DataFrame:
    """Apply sidebar filters and return filtered dataframe."""
    filtered = dataframe.copy()
    st.sidebar.markdown("### Filters")

    if "Sector" in filtered.columns:
        sectors = sorted(value for value in filtered["Sector"].dropna().unique().tolist() if value)
        selected_sectors = st.sidebar.multiselect("Sector", sectors, default=sectors)
        if selected_sectors:
            filtered = filtered[filtered["Sector"].isin(selected_sectors)]

    if "Location" in filtered.columns:
        countries = sorted(value for value in filtered["Location"].dropna().unique().tolist() if value)
        selected_countries = st.sidebar.multiselect("Country", countries, default=countries)
        if selected_countries:
            filtered = filtered[filtered["Location"].isin(selected_countries)]

    if "Weight (%)" in filtered.columns and not filtered["Weight (%)"].dropna().empty:
        weight_min = float(filtered["Weight (%)"].min())
        weight_max = float(filtered["Weight (%)"].max())
        selected_weight = st.sidebar.slider(
            "Weight (%)",
            min_value=weight_min,
            max_value=weight_max,
            value=(weight_min, weight_max),
        )
        filtered = filtered[
            (filtered["Weight (%)"] >= selected_weight[0])
            & (filtered["Weight (%)"] <= selected_weight[1])
        ]

    if "market_cap" in filtered.columns and not filtered["market_cap"].dropna().empty:
        cap_min = float(filtered["market_cap"].min())
        cap_max = float(filtered["market_cap"].max())
        selected_cap = st.sidebar.slider(
            "Market cap (USD)",
            min_value=cap_min,
            max_value=cap_max,
            value=(cap_min, cap_max),
            format="%.0f",
        )
        filtered = filtered[
            (filtered["market_cap"] >= selected_cap[0])
            & (filtered["market_cap"] <= selected_cap[1])
        ]

    return filtered


def _render_summary(dataframe: pd.DataFrame) -> None:
    """Render top-level KPIs."""
    total_positions = len(dataframe)
    total_weight = dataframe["Weight (%)"].sum() if "Weight (%)" in dataframe.columns else 0.0
    avg_market_cap = (
        dataframe["market_cap"].mean()
        if "market_cap" in dataframe.columns and not dataframe["market_cap"].dropna().empty
        else None
    )

    col1, col2, col3 = st.columns(3)
    col1.metric("Positions", f"{total_positions}")
    col2.metric("Total weight", f"{total_weight:.2f}%")
    col3.metric("Avg market cap", format_billions(avg_market_cap) if avg_market_cap else "-")


def _render_table(dataframe: pd.DataFrame) -> None:
    """Render the holdings table."""
    preferred_columns = [
        "ETF",
        "Ticker",
        "Name",
        "Sector",
        "Location",
        "Weight (%)",
        "Market Value",
        "market_cap",
        "current_price",
        "yfinance_symbol",
    ]

    columns = [column for column in preferred_columns if column in dataframe.columns]
    table = dataframe[columns] if columns else dataframe
    st.dataframe(table, width="stretch")
