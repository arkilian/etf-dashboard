"""Streamlit app entrypoint for ETF investment analysis."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from data_loader import list_available_etfs, load_etf_data
from filters import apply_investment_filters, is_high_quality
from metrics_engine import compute_financial_metrics
from scoring import apply_scores
from tags import apply_tags

st.set_page_config(page_title="ETF Investment Analyzer", layout="wide")

PERCENT_COLUMNS = [
    "Weight (%)",
    "roic",
    "roe",
    "gross_margin",
    "operating_margin",
    "net_margin",
    "revenue_growth",
    "earnings_growth",
]

NUMBER_COLUMNS = [
    "pe_ratio",
    "price_to_sales",
    "debt_to_equity",
    "beta",
    "quality_score",
    "risk_score",
]

CURRENCY_COLUMNS = [
    "Market Value",
    "market_cap",
    "free_cash_flow",
    "current_price",
]


@st.cache_data(show_spinner=True)
def load_analysis_dataset(
    etf_names: tuple[str, ...],
    enrich_with_yfinance: bool,
    max_tickers: int,
) -> pd.DataFrame:
    """Load, enrich, score, and tag the selected ETFs."""
    dataframe = load_etf_data(
        etf_names,
        enrich_with_yfinance=enrich_with_yfinance,
        max_tickers=max_tickers,
    )
    dataframe = compute_financial_metrics(dataframe)
    dataframe = apply_scores(dataframe)
    dataframe = apply_tags(dataframe)
    return dataframe


def render() -> None:
    """Render the ETF investment analyzer."""
    st.title("ETF Investment Analyzer")
    st.caption("Professional ETF holdings analysis with quality scoring, risk scoring, and tagging.")

    etf_map = list_available_etfs()
    if not etf_map:
        st.warning("No ETF CSV files were found in data/etf_lists.")
        return

    selected_etfs, enrich_with_yfinance, max_tickers = _render_data_sidebar(list(etf_map))
    if not selected_etfs:
        st.info("Select at least one ETF to begin the analysis.")
        return

    dataframe = load_analysis_dataset(tuple(selected_etfs), enrich_with_yfinance, max_tickers)
    filtered = _apply_sidebar_filters(dataframe)

    _render_etf_level_analysis(filtered)
    _render_top_companies(filtered)
    _render_holdings_table(filtered)


def _render_data_sidebar(etf_names: list[str]) -> tuple[list[str], bool, int]:
    """Render sidebar controls for data loading."""
    st.sidebar.header("Data")
    selected_etfs = st.sidebar.multiselect("ETF selection", etf_names, default=etf_names[:1])
    enrich_with_yfinance = st.sidebar.checkbox("Enrich with yfinance", value=True)
    max_tickers = st.sidebar.slider("Max tickers to query", min_value=10, max_value=200, value=75, step=5)
    return selected_etfs, enrich_with_yfinance, max_tickers


def _apply_sidebar_filters(dataframe: pd.DataFrame) -> pd.DataFrame:
    """Apply UI filters to the scored dataset."""
    filtered = dataframe.copy()

    st.sidebar.header("Investment Filters")
    filtered = apply_investment_filters(
        filtered,
        only_high_quality=st.sidebar.checkbox("High Quality"),
        only_compounders=st.sidebar.checkbox("Compounders"),
        only_value=st.sidebar.checkbox("Value"),
        only_growth=st.sidebar.checkbox("Growth"),
        score_range=st.sidebar.slider("Quality score range", min_value=0, max_value=10, value=(0, 10)),
    )

    st.sidebar.header("Company Filters")
    filtered = _filter_categorical(filtered, "Sector")
    filtered = _filter_categorical(filtered, "Location")
    filtered = _filter_numeric_range(filtered, "Weight (%)", "Weight (%)")
    filtered = _filter_numeric_range(filtered, "market_cap", "Market cap (USD)")
    filtered = _filter_by_tag(filtered)

    return _sort_dataframe(filtered)


def _filter_categorical(dataframe: pd.DataFrame, column: str) -> pd.DataFrame:
    """Filter a dataframe by a categorical column."""
    if column not in dataframe.columns:
        return dataframe

    options = sorted(value for value in dataframe[column].dropna().unique().tolist() if value)
    if not options:
        return dataframe

    selected = st.sidebar.multiselect(column, options, default=options)
    if not selected:
        return dataframe.iloc[0:0]

    return dataframe[dataframe[column].isin(selected)]


def _filter_numeric_range(dataframe: pd.DataFrame, column: str, label: str) -> pd.DataFrame:
    """Filter a dataframe by a numeric range slider."""
    if column not in dataframe.columns:
        return dataframe

    numeric_series = pd.to_numeric(dataframe[column], errors="coerce").dropna()
    if numeric_series.empty:
        return dataframe

    minimum = float(numeric_series.min())
    maximum = float(numeric_series.max())
    if minimum == maximum:
        return dataframe

    selected = st.sidebar.slider(label, min_value=minimum, max_value=maximum, value=(minimum, maximum))
    mask = pd.to_numeric(dataframe[column], errors="coerce").between(selected[0], selected[1], inclusive="both")
    return dataframe[mask.fillna(False)]


def _filter_by_tag(dataframe: pd.DataFrame) -> pd.DataFrame:
    """Filter the dataframe by generated tags."""
    if "tags" not in dataframe.columns:
        return dataframe

    all_tags = sorted({tag for tag_list in dataframe["tags"] for tag in tag_list})
    if not all_tags:
        return dataframe

    selected_tags = st.sidebar.multiselect("Tags", all_tags, default=all_tags)
    if not selected_tags:
        return dataframe.iloc[0:0]

    return dataframe[dataframe["tags"].map(lambda items: any(tag in items for tag in selected_tags))]


def _sort_dataframe(dataframe: pd.DataFrame) -> pd.DataFrame:
    """Sort the holdings table based on sidebar preferences."""
    if dataframe.empty:
        return dataframe

    sort_candidates = [
        column
        for column in ["quality_score", "risk_score", "Weight (%)", "market_cap", "Ticker"]
        if column in dataframe.columns
    ]
    sort_by = st.sidebar.selectbox("Sort by", sort_candidates, index=0)
    ascending = st.sidebar.checkbox("Ascending sort", value=False)
    return dataframe.sort_values(by=sort_by, ascending=ascending, kind="mergesort")


def _render_etf_level_analysis(dataframe: pd.DataFrame) -> None:
    """Render ETF-level KPIs and summary."""
    average_quality = dataframe["quality_score"].mean() if "quality_score" in dataframe.columns else None
    average_risk = dataframe["risk_score"].mean() if "risk_score" in dataframe.columns else None
    high_quality_pct = _compute_high_quality_percentage(dataframe)

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Companies", f"{len(dataframe)}")
    col2.metric("Average quality score", _format_number(average_quality, digits=2))
    col3.metric("Average risk score", _format_number(average_risk, digits=2))
    col4.metric("High-quality companies", _format_percent(high_quality_pct))

    if dataframe.empty:
        st.info("No companies match the selected filters.")
        return

    summary = (
        dataframe.groupby("ETF", dropna=False)
        .agg(
            companies=("Ticker", "count"),
            avg_quality_score=("quality_score", "mean"),
            avg_risk_score=("risk_score", "mean"),
            high_quality_pct=("quality_score", lambda series: (series >= 8).mean() * 100),
        )
        .reset_index()
    )
    st.subheader("ETF-Level Analysis")
    st.dataframe(_format_summary_table(summary), width="stretch", hide_index=True)


def _render_top_companies(dataframe: pd.DataFrame) -> None:
    """Render the top 10 companies by quality score."""
    st.subheader("Top 10 Companies by Score")
    if dataframe.empty:
        st.write("No rows available.")
        return

    columns = [
        column
        for column in ["ETF", "Ticker", "Name", "Sector", "quality_score", "risk_score", "tags_display"]
        if column in dataframe.columns
    ]
    top_companies = dataframe.nlargest(10, ["quality_score", "revenue_growth"], keep="all")[columns]
    st.dataframe(top_companies, width="stretch", hide_index=True)


def _render_holdings_table(dataframe: pd.DataFrame) -> None:
    """Render the styled holdings table."""
    st.subheader("Holdings Table")
    if dataframe.empty:
        st.write("No holdings match the current filters.")
        return

    display_columns = [
        "ETF",
        "Ticker",
        "Name",
        "Sector",
        "Location",
        "Weight (%)",
        "market_cap",
        "current_price",
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
        "quality_score",
        "risk_score",
        "tags_display",
        "yfinance_symbol",
    ]
    available_columns = [column for column in display_columns if column in dataframe.columns]
    table = dataframe[available_columns].rename(columns={"tags_display": "tags"})
    st.dataframe(_build_table_style(table), width="stretch", hide_index=True)


def _build_table_style(dataframe: pd.DataFrame) -> pd.io.formats.style.Styler:
    """Apply formatting and score coloring to the holdings table."""
    formatters: dict[str, object] = {}
    for column in PERCENT_COLUMNS:
        if column in dataframe.columns:
            formatters[column] = _format_percent_value
    for column in NUMBER_COLUMNS:
        if column in dataframe.columns:
            formatters[column] = lambda value: _format_number(value, digits=2)
    for column in CURRENCY_COLUMNS:
        if column in dataframe.columns:
            formatters[column] = _format_currency

    styled = dataframe.style.format(formatters, na_rep="-")

    if "quality_score" in dataframe.columns:
        styled = styled.apply(_quality_score_style, subset=["quality_score"])
    if "risk_score" in dataframe.columns:
        styled = styled.apply(_risk_score_style, subset=["risk_score"])

    return styled


def _quality_score_style(series: pd.Series) -> list[str]:
    """Color quality score cells without matplotlib dependency."""
    styles: list[str] = []
    for value in series:
        if value is None or pd.isna(value):
            styles.append("")
            continue
        numeric = float(value)
        if numeric >= 8:
            styles.append("background-color: #d1fae5; color: #065f46;")
        elif numeric >= 5:
            styles.append("background-color: #fef3c7; color: #92400e;")
        else:
            styles.append("background-color: #fee2e2; color: #991b1b;")
    return styles


def _risk_score_style(series: pd.Series) -> list[str]:
    """Color risk score cells without matplotlib dependency."""
    styles: list[str] = []
    for value in series:
        if value is None or pd.isna(value):
            styles.append("")
            continue
        numeric = float(value)
        if numeric <= 1:
            styles.append("background-color: #d1fae5; color: #065f46;")
        elif numeric <= 3:
            styles.append("background-color: #fef3c7; color: #92400e;")
        else:
            styles.append("background-color: #fee2e2; color: #991b1b;")
    return styles


def _format_summary_table(dataframe: pd.DataFrame) -> pd.DataFrame:
    """Format ETF summary values for display."""
    summary = dataframe.copy()
    for column in ["avg_quality_score", "avg_risk_score"]:
        if column in summary.columns:
            summary[column] = summary[column].map(lambda value: _format_number(value, 2))
    if "high_quality_pct" in summary.columns:
        summary["high_quality_pct"] = summary["high_quality_pct"].map(_format_percent_value)
    return summary


def _compute_high_quality_percentage(dataframe: pd.DataFrame) -> float | None:
    """Compute the share of high-quality companies."""
    if dataframe.empty:
        return None

    high_quality_count = int(dataframe.apply(is_high_quality, axis=1).sum())
    return (high_quality_count / len(dataframe)) * 100 if len(dataframe) else None


def _format_number(value: object, digits: int = 2) -> str:
    """Format a number with a configurable number of decimals."""
    if value is None or pd.isna(value):
        return "-"
    return f"{float(value):,.{digits}f}"


def _format_percent(value: object) -> str:
    """Format a percent value."""
    if value is None or pd.isna(value):
        return "-"
    return f"{float(value):.1f}%"


def _format_percent_value(value: object) -> str:
    """Format percentage-point metrics."""
    if value is None or pd.isna(value):
        return "-"
    return f"{float(value):.1f}%"


def _format_currency(value: object) -> str:
    """Format large currency values compactly."""
    if value is None or pd.isna(value):
        return "-"

    numeric = float(value)
    abs_numeric = abs(numeric)
    if abs_numeric >= 1_000_000_000:
        return f"${numeric / 1_000_000_000:,.2f}B"
    if abs_numeric >= 1_000_000:
        return f"${numeric / 1_000_000:,.2f}M"
    if abs_numeric >= 1_000:
        return f"${numeric / 1_000:,.2f}K"
    return f"${numeric:,.2f}"


if __name__ == "__main__":
    render()
