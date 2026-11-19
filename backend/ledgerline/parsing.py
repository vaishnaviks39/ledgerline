"""Turn the strings the model copies off the page into Python values."""
from __future__ import annotations

import re
from datetime import date
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation

from dateutil import parser as dateparser

# ---------- amounts ----------

MULTIPLIERS = {"lakh": Decimal(100_000), "lac": Decimal(100_000), "crore": Decimal(10_000_000)}
AMOUNT = re.compile(r"([+-]?\d+(?:\.\d+)?)\s*(lakhs?|lacs?|crores?)?")


def parse_amount(value) -> float | None:
    """Policy §1: Rs. / ₹ / INR / $ / USD prefixes, /- suffix, Indian grouping, lakh and crore.

    Parsed exactly with Decimal and rounded to 2 places. Raises ValueError rather than guessing.
    """
    if value is None or value == "":
        return None
    if isinstance(value, (int, float, Decimal)):
        return float(Decimal(str(value)).quantize(Decimal("0.01"), ROUND_HALF_UP))
    text = str(value).strip().lower()
    negative = text.startswith("(") and text.endswith(")")
    text = text.strip("()")
    text = re.sub(r"\b(rs|inr|usd)\b\.?", "", text)
    text = text.replace("₹", "").replace("$", "").replace("/-", "").replace(",", "").strip()
    match = AMOUNT.fullmatch(text)
    if not match:
        raise ValueError(f"unrecognised amount: {value!r}")
    try:
        amount = Decimal(match[1])
    except InvalidOperation as exc:
        raise ValueError(f"unrecognised amount: {value!r}") from exc
    word = (match[2] or "").rstrip("s")
    amount *= MULTIPLIERS.get(word, Decimal(1))
    if negative:
        amount = -amount
    return float(amount.quantize(Decimal("0.01"), ROUND_HALF_UP))


# ---------- dates ----------

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