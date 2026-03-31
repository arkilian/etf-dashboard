"""Client helpers to enrich holdings with yfinance data."""

from __future__ import annotations

import contextlib
import io
import logging
import time

import pandas as pd
import yfinance as yf

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

logging.getLogger("yfinance").setLevel(logging.CRITICAL)


def build_yfinance_symbol(ticker: str, exchange: str | None = None) -> str:
    """Build a likely Yahoo Finance symbol based on exchange."""
    candidates = build_yfinance_candidates(ticker=ticker, exchange=exchange)
    return candidates[0] if candidates else ""


def build_yfinance_candidates(ticker: str, exchange: str | None = None) -> list[str]:
    """Build candidate Yahoo symbols for a ticker."""
    clean_ticker = _normalize_ticker(ticker)
    if not clean_ticker:
        return []

    exchange_name = str(exchange or "").strip()
    suffix = EXCHANGE_SUFFIX_MAP.get(exchange_name, "")

    # If ticker already includes a known Yahoo suffix, keep it as first option.
    if any(clean_ticker.endswith(mapped_suffix) for mapped_suffix in EXCHANGE_SUFFIX_MAP.values()):
        candidates = [clean_ticker]
    else:
        candidates = []
        suffix_base = clean_ticker.rstrip(".")
        if suffix:
            candidates.append(f"{suffix_base}{suffix}")
        candidates.append(clean_ticker)

    # LSE tickers sometimes include a trailing dot in provider CSVs.
    if clean_ticker.endswith("."):
        no_dot = clean_ticker.rstrip(".")
        if suffix:
            candidates.append(f"{no_dot}{suffix}")
        candidates.append(no_dot)

    return _dedupe_preserve_order(candidates)


def fetch_ticker_snapshot(yf_symbol: str) -> dict[str, object]:
    """Fetch a compact market snapshot for one Yahoo symbol."""
    ticker = yf.Ticker(yf_symbol)
    info = {}
    current_price = None

    try:
        history = ticker.history(period="5d", interval="1d", auto_adjust=False)
        if history is not None and not history.empty and "Close" in history.columns:
            last_close = history["Close"].dropna()
            if not last_close.empty:
                current_price = float(last_close.iloc[-1])
    except Exception:
        current_price = None

    try:
        info = ticker.get_info() or {}
    except Exception:
        info = {}

    market_cap = info.get("marketCap")
    if current_price is None:
        current_price = info.get("currentPrice") or info.get("regularMarketPrice")

    return {
        "yfinance_symbol": yf_symbol,
        "current_price": current_price,
        "market_cap": market_cap,
        "yf_name": info.get("shortName"),
        "yf_sector": info.get("sector"),
        "yf_country": info.get("country"),
        "yf_currency": info.get("currency"),
    }


def enrich_holdings_with_market_data(
    holdings: pd.DataFrame,
    max_tickers: int | None = 40,
    request_pause_seconds: float = 0.15,
) -> pd.DataFrame:
    """Merge local holdings with market fields from yfinance."""
    if holdings.empty:
        return holdings

    required_cols = {"Ticker", "Exchange"}
    if not required_cols.issubset(set(holdings.columns)):
        return holdings

    dataframe = holdings.copy()
    dataframe["yfinance_symbol"] = dataframe.apply(
        lambda row: build_yfinance_symbol(row.get("Ticker"), row.get("Exchange")),
        axis=1,
    )
    dataframe["yfinance_candidates"] = dataframe.apply(
        lambda row: build_yfinance_candidates(row.get("Ticker"), row.get("Exchange")),
        axis=1,
    )

    candidate_symbols: list[str] = []
    for candidates in dataframe["yfinance_candidates"].tolist():
        candidate_symbols.extend(candidates)

    unique_symbols = _dedupe_preserve_order(candidate_symbols)
    if max_tickers is not None:
        unique_symbols = unique_symbols[:max_tickers]

    snapshots: list[dict[str, object]] = []
    for symbol in unique_symbols:
        try:
            with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                snapshots.append(fetch_ticker_snapshot(symbol))
        except Exception:
            snapshots.append(
                {
                    "yfinance_symbol": symbol,
                    "current_price": None,
                    "market_cap": None,
                    "yf_name": None,
                    "yf_sector": None,
                    "yf_country": None,
                    "yf_currency": None,
                }
            )
        if request_pause_seconds > 0:
            time.sleep(request_pause_seconds)

    if not snapshots:
        return dataframe.drop(columns=["yfinance_candidates"], errors="ignore")

    market_df = pd.DataFrame(snapshots)

    resolved_records: list[dict[str, object]] = []
    for candidates in dataframe["yfinance_candidates"].tolist():
        match = None
        for symbol in candidates:
            rows = market_df[market_df["yfinance_symbol"] == symbol]
            if rows.empty:
                continue
            row = rows.iloc[0].to_dict()
            if row.get("current_price") is not None or row.get("market_cap") is not None:
                match = row
                break
            if match is None:
                match = row
        resolved_records.append(match or {"yfinance_symbol": candidates[0] if candidates else None})

    resolved_df = pd.DataFrame(resolved_records)
    base_df = dataframe.drop(columns=["yfinance_candidates"], errors="ignore").reset_index(drop=True)
    return pd.concat([base_df, resolved_df.drop(columns=["yfinance_symbol"], errors="ignore")], axis=1)


def _normalize_ticker(ticker: str | None) -> str:
    """Normalize CSV ticker text before building Yahoo symbols."""
    text = str(ticker or "").strip()
    if not text:
        return ""
    text = text.replace("\u00a0", " ").replace("\u202f", " ")
    text = text.replace("/", "-")
    text = " ".join(text.split())
    text = text.replace(" ", "-")
    return text


def _dedupe_preserve_order(values: list[str]) -> list[str]:
    """Deduplicate values while preserving insertion order."""
    return list(dict.fromkeys(value for value in values if value))
