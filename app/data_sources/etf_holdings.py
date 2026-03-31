"""Utilities to load ETF holdings from local CSV files."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

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


def discover_etf_csv_files(base_dir: str | Path) -> dict[str, Path]:
    """Return available ETF CSV files indexed by display name."""
    directory = Path(base_dir)
    if not directory.exists():
        return {}

    csv_files = sorted(path for path in directory.glob(f"*{CSV_EXTENSION}") if path.is_file())
    return {path.stem: path for path in csv_files}


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


def load_holdings_for_etf(etf_name: str, base_dir: str | Path) -> pd.DataFrame:
    """Load holdings for a selected ETF name from a folder of CSV files."""
    file_map = discover_etf_csv_files(base_dir)
    if etf_name not in file_map:
        raise ValueError(f"ETF '{etf_name}' not found in {base_dir}")
    return load_holdings_from_csv(file_map[etf_name], etf_name=etf_name)


def load_multiple_etfs(etf_names: list[str], base_dir: str | Path) -> pd.DataFrame:
    """Load holdings for multiple ETFs and concatenate into one dataframe."""
    if not etf_names:
        return pd.DataFrame()

    frames = [load_holdings_for_etf(etf_name=name, base_dir=base_dir) for name in etf_names]
    return pd.concat(frames, ignore_index=True)


def _normalize_text(value: object) -> str:
    """Normalize text loaded from CSV."""
    if value is None:
        return ""
    text = str(value)
    text = text.replace("\u00a0", " ").replace("\u202f", " ")
    return text.strip().strip('"')


def _parse_localized_number(value: object) -> float | None:
    """Parse numbers with localized decimal and thousand separators."""
    if value is None:
        return None

    text = _normalize_text(value)
    if not text:
        return None

    normalized = (
        text.replace(" ", "")
        .replace(".", "")
        .replace(",", ".")
        .replace("%", "")
    )

    try:
        return float(normalized)
    except ValueError:
        return None
