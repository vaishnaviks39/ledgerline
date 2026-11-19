"""Deterministic checks.

Since v0.3 these are informational: they are stored as `warnings` and shown to reviewers.
Routing is decided by the model, which applies the AP policy itself (see pipeline.py).
"""
from __future__ import annotations

import re
import sqlite3

from .models import Invoice
from .reference import ReferenceData
from decimal import Decimal

GSTIN_PATTERN = re.compile(r"\d{2}[A-Z]{5}\d{4}[A-Z][1-9A-Z]Z[0-9A-Z]")
GSTIN_ALPHABET = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"
BUYER_STATE_CODE = "27"  # Maharashtra
TOTALS_TOLERANCE = Decimal("1.00")


def gstin_checksum(first14: str) -> str:
    total = 0
    for i, ch in enumerate(first14):
        product = GSTIN_ALPHABET.index(ch) * (1 if i % 2 == 0 else 2)
        total += product // 36 + product % 36
    return GSTIN_ALPHABET[(36 - total % 36) % 36]


def is_valid_gstin(gstin: str | None) -> bool:
    """Validate a GSTIN's format and check digit."""
    if not gstin:
        return False
    return GSTIN_PATTERN.match(gstin.strip().upper()) is not None


def find_vendor(ref: ReferenceData, supplier_name: str | None) -> dict | None:
    if not supplier_name:
        return None
    for vendor in ref.vendors:
        if vendor["legal_name"].strip().lower() == supplier_name.strip().lower():
            return vendor
    return None


def check_vendor(vendor: dict | None) -> list[str]:
    return [] if vendor else ["vendor_unknown"]


def check_gstin(inv: Invoice) -> list[str]:
    if inv.currency == "INR" and not is_valid_gstin(inv.supplier_gstin):
        return ["gstin_invalid"]
    return []


def check_tax_type(inv: Invoice, buyer_state: str = BUYER_STATE_CODE) -> list[str]:
    """Policy: domestic documents only; compare GSTIN state code with the buyer's."""
    if inv.currency != "INR" or not inv.supplier_gstin:
        return []
    intra_state = inv.supplier_gstin.strip()[:2] == str(buyer_state).strip().zfill(2)
    if intra_state and inv.igst > 0:
        return ["tax_type_mismatch"]
    if not intra_state and (inv.cgst > 0 or inv.sgst > 0):
        return ["tax_type_mismatch"]
    return []


def _dec(value) -> Decimal:
    """Exact decimal from a stored amount (avoids binary floating point, policy)."""
    return Decimal(str(value or 0))


def check_totals(inv: Invoice) -> list[str]:
    """Policy §3: lines + CGST + SGST + IGST + round-off vs total, ₹1.00 tolerance (inclusive)."""
    if inv.total is None:
        return []
    computed = (sum((_dec(item.amount) for item in inv.line_items), Decimal("0"))
                + _dec(inv.cgst) + _dec(inv.sgst) + _dec(inv.igst) + _dec(inv.round_off))
    return [] if abs(computed - _dec(inv.total)) <= TOTALS_TOLERANCE else ["totals_mismatch"]


def check_duplicate(conn: sqlite3.Connection, ref: ReferenceData, inv: Invoice) -> list[str]:
    row = conn.execute(
        "SELECT id FROM invoices WHERE supplier_name = ? AND invoice_number = ?",
        (inv.supplier_name, inv.invoice_number),
    ).fetchone()
    if row:
        return ["duplicate"]
    for paid in ref.paid_invoices:
        if paid["supplier_name"] == inv.supplier_name and paid["invoice_number"] == inv.invoice_number:
            return ["duplicate"]
    return []


def check_bank_details(inv: Invoice, vendor: dict | None) -> list[str]:
    if vendor and inv.ifsc and vendor.get("ifsc") and inv.ifsc != vendor["ifsc"]:
        return ["bank_details_changed"]
    return []


def run_checks(conn: sqlite3.Connection, ref: ReferenceData, inv: Invoice) -> list[str]:
    vendor = find_vendor(ref, inv.supplier_name)
    return (
        check_gstin(inv)
        + check_vendor(vendor)
        + check_tax_type(inv, ref.buyer.get("state_code", BUYER_STATE_CODE))
        + check_totals(inv)
        + check_duplicate(conn, ref, inv)
        + check_bank_details(inv, vendor)
    )
