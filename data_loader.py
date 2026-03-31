"""Load ETF holdings data and enrich it with yfinance fields."""

from __future__ import annotations

import contextlib
import io
import logging
from functools import lru_cache
from pathlib import Path
from typing import Iterable

import pandas as pd
import yfinance as yf

logging.getLogger("yfinance").setLevel(logging.CRITICAL)

DATA_DIR = Path(__file__).resolve().parent / "data" / "etf_lists"
CSV_EXTENSION = ".csv"

NUMERIC_COLUMNS = [
    "Market Value",
    "Weight (%)",
    "Notional Value",
    "Shares",
    "Price",
]

TEXT_COLUMNS = [
    "Ticker",
    "Name",
    "Sector",
    "Asset Class",
    "Location",
    "Exchange",
    "Market Currency",
]

EXCHANGE_SUFFIX_MAP = {
    "Euronext Amsterdam": ".AS",
    "London Stock Exchange": ".L",
    "SIX Swiss Exchange": ".SW",
    "Nyse Euronext - Euronext Paris": ".PA",
    "Xetra": ".DE",
    "Bolsa De Madrid": ".MC",
    "Borsa Italiana": ".MI",
    "Omx Nordic Exchange Copenhagen A/S": ".CO",
    "Nasdaq Omx Helsinki Ltd.": ".HE",
    "Nyse Euronext - Euronext Brussels": ".BR",
    "Euronext Lisbon": ".LS",
}

BASE_COLUMNS = [
    "ETF",
    "Ticker",
    "Name",
    "Sector",
    "Location",
    "Weight (%)",
    "Market Value",
    "Exchange",
]

YFINANCE_FIELDS = [
    "current_price",
    "market_cap",
    "yfinance_symbol",
    "yf_name",
    "yf_sector",
    "yf_country",
    "pe_ratio_raw",
    "price_to_sales_raw",
    "roic_raw",
    "return_on_assets_raw",
    "roe_raw",
    "gross_margin_raw",
    "operating_margin_raw",
    "net_margin_raw",
    "revenue_growth_raw",
    "earnings_growth_raw",
    "free_cash_flow_raw",
    "debt_to_equity_raw",
    "beta_raw",
]


def list_available_etfs(base_dir: str | Path = DATA_DIR) -> dict[str, Path]:
    """Return discoverable ETF CSV files."""
    return discover_etf_csv_files(base_dir)


def load_etf_data(
    etf_names: Iterable[str],
    *,
    base_dir: str | Path = DATA_DIR,
    enrich_with_yfinance: bool = True,
    max_tickers: int | None = 75,
) -> pd.DataFrame:
    """Load one or more ETFs and optionally enrich them with yfinance data."""
    selected = list(dict.fromkeys(name for name in etf_names if name))
    if not selected:
        return pd.DataFrame(columns=BASE_COLUMNS + YFINANCE_FIELDS)

    frames = [load_holdings_for_etf(etf_name=name, base_dir=base_dir) for name in selected]
    holdings = pd.concat(frames, ignore_index=True)

    if not enrich_with_yfinance:
        return holdings

    return enrich_holdings_with_yfinance(holdings, max_tickers=max_tickers)


def enrich_holdings_with_yfinance(
    holdings: pd.DataFrame,
    *,
    max_tickers: int | None = 75,
) -> pd.DataFrame:
    """Enrich ETF holdings with market and financial statement fields."""
    if holdings.empty:
        return holdings.copy()

    dataframe = holdings.copy()
    dataframe["yfinance_candidates"] = dataframe.apply(
        lambda row: build_yfinance_candidates(row.get("Ticker"), row.get("Exchange")),
        axis=1,
    )

    symbols: list[str] = []
    for candidates in dataframe["yfinance_candidates"].tolist():
        symbols.extend(candidates)

    unique_symbols = _dedupe_preserve_order(symbols)
    if max_tickers is not None:
        unique_symbols = unique_symbols[:max_tickers]

    snapshots = {symbol: fetch_yfinance_snapshot(symbol) for symbol in unique_symbols}
    resolved_records: list[dict[str, object]] = []

    for candidates in dataframe["yfinance_candidates"].tolist():
        resolved_records.append(_resolve_snapshot(candidates, snapshots))

    enriched = pd.concat(
        [
            dataframe.drop(columns=["yfinance_candidates"], errors="ignore").reset_index(drop=True),
            pd.DataFrame(resolved_records),
        ],
        axis=1,
    )

    if "yf_name" in enriched.columns and "Name" in enriched.columns:
        enriched["Name"] = enriched["Name"].fillna("").replace("", pd.NA).fillna(enriched["yf_name"])
    if "yf_sector" in enriched.columns and "Sector" in enriched.columns:
        enriched["Sector"] = enriched["Sector"].fillna("").replace("", pd.NA).fillna(enriched["yf_sector"])
    if "yf_country" in enriched.columns and "Location" in enriched.columns:
        enriched["Location"] = (
            enriched["Location"].fillna("").replace("", pd.NA).fillna(enriched["yf_country"])
        )

    return enriched


@lru_cache(maxsize=512)
def fetch_yfinance_snapshot(symbol: str) -> dict[str, object]:
    """Fetch and cache a yfinance fundamentals snapshot for one symbol."""
    if not symbol:
        return _empty_snapshot(symbol)

    try:
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            ticker = yf.Ticker(symbol)
            info = _safe_get_info(ticker)
            fast_info = _safe_get_fast_info(ticker)
    except Exception:
        return _empty_snapshot(symbol)

    return {
        "yfinance_symbol": symbol,
        "current_price": _first_valid(
            fast_info.get("lastPrice"),
            info.get("currentPrice"),
            info.get("regularMarketPrice"),
            info.get("previousClose"),
        ),
        "market_cap": _first_valid(fast_info.get("marketCap"), info.get("marketCap")),
        "yf_name": _first_valid(info.get("longName"), info.get("shortName")),
        "yf_sector": info.get("sector"),
        "yf_country": info.get("country"),
        "pe_ratio_raw": _first_valid(info.get("trailingPE"), info.get("forwardPE")),
        "price_to_sales_raw": _first_valid(
            info.get("priceToSalesTrailing12Months"),
            info.get("enterpriseToRevenue"),
        ),
        "roic_raw": info.get("returnOnCapital"),
        "return_on_assets_raw": info.get("returnOnAssets"),
        "roe_raw": info.get("returnOnEquity"),
        "gross_margin_raw": info.get("grossMargins"),
        "operating_margin_raw": info.get("operatingMargins"),
        "net_margin_raw": info.get("profitMargins"),
        "revenue_growth_raw": info.get("revenueGrowth"),
        "earnings_growth_raw": info.get("earningsGrowth"),
        "free_cash_flow_raw": info.get("freeCashflow"),
        "debt_to_equity_raw": info.get("debtToEquity"),
        "beta_raw": info.get("beta"),
    }


def _resolve_snapshot(
    candidates: list[str],
    snapshots: dict[str, dict[str, object]],
) -> dict[str, object]:
    """Resolve the best available cached snapshot across symbol candidates."""
    for symbol in candidates:
        snapshot = snapshots.get(symbol)
        if snapshot and _has_meaningful_financial_data(snapshot):
            return snapshot

    for symbol in candidates:
        snapshot = snapshots.get(symbol)
        if snapshot:
            return snapshot

    return _empty_snapshot(candidates[0] if candidates else None)


def _has_meaningful_financial_data(snapshot: dict[str, object]) -> bool:
    """Return whether a snapshot contains enough data to be useful."""
    keys = (
        "market_cap",
        "pe_ratio_raw",
        "price_to_sales_raw",
        "roe_raw",
        "operating_margin_raw",
        "revenue_growth_raw",
        "free_cash_flow_raw",
    )
    return any(snapshot.get(key) is not None for key in keys)


def _safe_get_info(ticker: yf.Ticker) -> dict[str, object]:
    """Safely fetch the info payload from yfinance."""
    try:
        return ticker.get_info() or {}
    except Exception:
        return {}


def _safe_get_fast_info(ticker: yf.Ticker) -> dict[str, object]:
    """Safely fetch the fast_info payload from yfinance."""
    try:
        return dict(ticker.fast_info or {})
    except Exception:
        return {}


def _first_valid(*values: object) -> object | None:
    """Return the first non-null, non-NaN value."""
    for value in values:
        if value is None:
            continue
        if pd.isna(value):
            continue
        return value
    return None


def _empty_snapshot(symbol: str | None) -> dict[str, object]:
    """Build an empty snapshot with the expected schema."""
    return {column: None for column in YFINANCE_FIELDS if column != "yfinance_symbol"} | {
        "yfinance_symbol": symbol
    }


def _dedupe_preserve_order(values: list[str]) -> list[str]:
    """Deduplicate a list while preserving order."""
    return list(dict.fromkeys(value for value in values if value))


def discover_etf_csv_files(base_dir: str | Path) -> dict[str, Path]:
    """Return available ETF CSV files indexed by display name."""
    directory = Path(base_dir)
    if not directory.exists():
        return {}

    csv_files = sorted(path for path in directory.glob(f"*{CSV_EXTENSION}") if path.is_file())
    return {path.stem: path for path in csv_files}


def load_holdings_for_etf(etf_name: str, base_dir: str | Path) -> pd.DataFrame:
    """Load holdings for one ETF from a CSV folder."""
    file_map = discover_etf_csv_files(base_dir)
    if etf_name not in file_map:
        raise ValueError(f"ETF '{etf_name}' not found in {base_dir}")
    return load_holdings_from_csv(file_map[etf_name], etf_name=etf_name)


def load_holdings_from_csv(csv_path: str | Path, etf_name: str | None = None) -> pd.DataFrame:
    """Load and normalize ETF holdings exported as CSV."""
    path = Path(csv_path)
    if not path.exists():
        raise FileNotFoundError(f"ETF CSV not found: {path}")

    dataframe = pd.read_csv(path, skiprows=2, dtype=str, encoding="utf-8-sig")
    dataframe = dataframe.dropna(how="all")
    dataframe.columns = [str(column).strip() for column in dataframe.columns]

    for column in TEXT_COLUMNS:
        if column in dataframe.columns:
            dataframe[column] = dataframe[column].map(_normalize_text)

    for column in NUMERIC_COLUMNS:
        if column in dataframe.columns:
            dataframe[column] = dataframe[column].map(_parse_localized_number)

    dataframe["ETF"] = etf_name or path.stem
    return dataframe


def build_yfinance_candidates(ticker: str, exchange: str | None = None) -> list[str]:
    """Build candidate Yahoo symbols for a ticker."""
    clean_ticker = _normalize_ticker(ticker)
    if not clean_ticker:
        return []

    exchange_name = str(exchange or "").strip()
    suffix = EXCHANGE_SUFFIX_MAP.get(exchange_name, "")

    if any(clean_ticker.endswith(mapped_suffix) for mapped_suffix in EXCHANGE_SUFFIX_MAP.values()):
        candidates = [clean_ticker]
    else:
        candidates = []
        suffix_base = clean_ticker.rstrip(".")
        if suffix:
            candidates.append(f"{suffix_base}{suffix}")
        candidates.append(clean_ticker)

    if clean_ticker.endswith("."):
        no_dot = clean_ticker.rstrip(".")
        if suffix:
            candidates.append(f"{no_dot}{suffix}")
        candidates.append(no_dot)

    return _dedupe_preserve_order(candidates)


def _normalize_text(value: object) -> str:
    """Normalize text loaded from CSV."""
    if value is None:
        return ""
    text = str(value)
    text = text.replace("\u00a0", " ").replace("\u202f", " ")
    return text.strip().strip('"')


def _parse_localized_number(value: object) -> float | None:
    """Parse localized decimal and thousand separators."""
    if value is None:
        return None

    text = _normalize_text(value)
    if not text:
        return None

    normalized = text.replace(" ", "").replace(".", "").replace(",", ".").replace("%", "")
    try:
        return float(normalized)
    except ValueError:
        return None


def _normalize_ticker(ticker: str | None) -> str:
    """Normalize CSV ticker text before building Yahoo symbols."""
    text = str(ticker or "").strip()
    if not text:
        return ""
    text = text.replace("\u00a0", " ").replace("\u202f", " ")
    text = text.replace("/", "-")
    text = " ".join(text.split())
    return text.replace(" ", "-")
