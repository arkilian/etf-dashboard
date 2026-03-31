from pathlib import Path

from app.data_sources.etf_holdings import load_holdings_from_csv


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
