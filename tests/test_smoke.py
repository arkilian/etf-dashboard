from pathlib import Path

import pandas as pd

from data_loader import load_holdings_from_csv
from filters import is_compounder, is_growth_stock, is_high_quality, is_value_stock
from metrics_engine import compute_financial_metrics
from scoring import calculate_quality_score, calculate_risk_score
from tags import generate_tags


def test_load_holdings_from_csv_parses_localized_numbers(tmp_path: Path) -> None:
    csv_content = (
        "Fund Holdings as of,2026-03-27\n"
        " \n"
        "Ticker,Name,Sector,Asset Class,Market Value,Weight (%),Notional Value,Shares,Price,Location,Exchange,Market Currency\n"
        '"ABC","Example Corp","Technology","Equity","1 234,50","2,30","1 234,50","100,00","12,35","France","Nyse Euronext - Euronext Paris","EUR"\n'
    )
    csv_path = tmp_path / "sample.csv"
    csv_path.write_text(csv_content, encoding="utf-8")

    dataframe = load_holdings_from_csv(csv_path, etf_name="Sample ETF")

    assert len(dataframe) == 1
    assert dataframe.iloc[0]["Ticker"] == "ABC"
    assert dataframe.iloc[0]["Weight (%)"] == 2.30
    assert dataframe.iloc[0]["ETF"] == "Sample ETF"


def test_metrics_scoring_tags_and_filters_flow() -> None:
    dataframe = compute_financial_metrics(
        pd.DataFrame(
            [
                {
                    "Ticker": "ABC",
                    "Sector": "Technology",
                    "roic_raw": 0.18,
                    "roe_raw": 0.22,
                    "operating_margin_raw": 0.20,
                    "gross_margin_raw": 0.55,
                    "net_margin_raw": 0.19,
                    "revenue_growth_raw": 0.12,
                    "earnings_growth_raw": 0.14,
                    "free_cash_flow_raw": 1_000_000.0,
                    "debt_to_equity_raw": 40.0,
                    "beta_raw": 1.1,
                    "pe_ratio_raw": 24.0,
                    "price_to_sales_raw": 4.0,
                }
            ]
        )
    )
    row = dataframe.iloc[0]
    quality_score = calculate_quality_score(row)
    risk_score = calculate_risk_score(row)

    enriched_row = row.copy()
    enriched_row["quality_score"] = quality_score
    enriched_row["risk_score"] = risk_score
    tags = generate_tags(enriched_row)

    assert quality_score >= 8
    assert risk_score >= 0
    assert "High Quality" in tags
    assert is_high_quality(enriched_row)
    assert is_compounder(enriched_row)
    assert isinstance(is_growth_stock(enriched_row), bool)
    assert isinstance(is_value_stock(enriched_row), bool)
