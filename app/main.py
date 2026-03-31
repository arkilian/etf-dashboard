"""Main entrypoint for the modular ETF dashboard."""

from __future__ import annotations

import streamlit as st

try:
    from app.pages.overview import render
except ModuleNotFoundError:
    from pages.overview import render

st.set_page_config(page_title="ETF Dashboard", layout="wide")
render()

