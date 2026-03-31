"""Shared helpers for formatting and filtering."""

from __future__ import annotations


def format_billions(value: float | None) -> str:
    """Format a numeric value in billions."""
    if value is None:
        return "-"
    return f"{value / 1_000_000_000:.2f}B"


def format_millions(value: float | None) -> str:
    """Format a numeric value in millions."""
    if value is None:
        return "-"
    return f"{value / 1_000_000:.2f}M"
