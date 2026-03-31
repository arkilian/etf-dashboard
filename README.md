# ETF Dashboard

Streamlit dashboard for ETF holdings analysis.

## Stack
- Python 3.11+
- Streamlit
- pandas
- yfinance

## Current Features
- Discover ETF CSV files from `data/etf_lists/`
- Load holdings for one or multiple ETFs
- Parse localized numeric formats (for example `550 769 537,60`)
- Enrich holdings with market fields from yfinance
- Filter by sector, country, weight, and market cap
- Show a holdings table and summary KPIs

## Project Structure
- `app/data_sources/etf_holdings.py`: ETF CSV discovery and loading
- `app/data_sources/yfinance_client.py`: yfinance enrichment helpers
- `app/pages/overview.py`: dashboard page with filters and table
- `data/etf_lists/`: holdings CSV files

## Setup
```bash
python -m venv .venv
source .venv/Scripts/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

## Run
```bash
streamlit run app/main.py
```
