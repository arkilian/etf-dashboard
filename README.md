# ETF Dashboard

Streamlit dashboard for ETF holdings analysis with scoring, tagging, and reusable investment filters.

## Stack
- Python 3.11+
- Streamlit
- pandas
- yfinance
- plotly

## Features
- Discover ETF CSV files from `data/etf_lists/`
- Load one or multiple ETFs into a unified holdings dataset
- Enrich holdings with cached yfinance market and financial statement data
- Compute financial metrics such as P/E, ROIC proxy, margins, growth, FCF, leverage, and beta
- Score each company with `quality_score` and `risk_score`
- Generate tags such as `High Quality`, `Cash Machine`, `Speculative`, and `Expensive`
- Filter holdings by sector, country, weight, market cap, tags, and investment styles
- Show ETF-level analysis and the top companies by score

## Project Structure
- `data_loader.py`: ETF data loading and yfinance enrichment
- `metrics_engine.py`: normalized financial metrics
- `scoring.py`: quality and risk scoring
- `tags.py`: investment tag generation
- `filters.py`: reusable investment filters
- `app.py`: Streamlit UI and dashboard orchestration
- `app/main.py`: compatibility entrypoint for the root app
- `data/etf_lists/`: source ETF holdings CSV files

## Setup
```bash
python -m venv .venv
source .venv/Scripts/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

## Run
```bash
streamlit run app.py
```
