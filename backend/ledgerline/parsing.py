"""Turn the strings the model copies off the page into Python values."""
from __future__ import annotations

import re
from datetime import date

from dateutil import parser as dateparser


def parse_amount(value) -> float | None:
    """'₹ 1,23,456.00' -> 123456.0"""
    if value is None or value == "":
        return None
    if isinstance(value, (int, float)):
        return float(value)
    cleaned = str(value).replace("₹", "").replace("INR", "").replace(",", "").strip()
    return float(cleaned)


NUMERIC_DATE = re.compile(r"(\d{1,2})[/.\-](\d{1,2})[/.\-](\d{4})")
ISO_DATE = re.compile(r"(\d{4})-(\d{1,2})-(\d{1,2})")


def parse_date(value, month_first: bool = False) -> date | None:
    """Policy §1: Indian vendors print day first; US vendors (country US) print month first."""
    if not value:
        return None
    text = str(value).strip()
    if m := ISO_DATE.fullmatch(text):
        return date(int(m[1]), int(m[2]), int(m[3]))
    if m := NUMERIC_DATE.fullmatch(text):
        first, second, year = int(m[1]), int(m[2]), int(m[3])
        month, day = (first, second) if month_first else (second, first)
        return date(year, month, day)  # an impossible date raises ValueError instead of guessing
    return dateparser.parse(text, dayfirst=not month_first).date()  # written dates, e.g. "25 Apr 2026"