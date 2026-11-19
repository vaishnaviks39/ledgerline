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
from datetime import date

GSTIN_PATTERN = re.compile(r"\d{2}[A-Z]{5}\d{4}[A-Z][1-9A-Z]Z[0-9A-Z]")
GSTIN_ALPHABET = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"
BUYER_STATE_CODE = "27"  # Maharashtra
TOTALS_TOLERANCE = Decimal("1.00")
# Reasons the model may add on top of the code's checks. Everything else is decided by code only.
MODEL_ADDABLE_REASONS = {"suspicious_content"}


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


def normalize_name(name: str | None) -> str:
    """Policy: supplier key for foreign documents: case-insensitive, no spaces or punctuation."""
    return re.sub(r"[^a-z0-9]", "", (name or "").lower())


def find_vendor(ref: ReferenceData, inv: Invoice) -> dict | None:
    """Policy: domestic suppliers by GSTIN alone; foreign suppliers by normalised legal name."""
    if inv.currency == "INR":
        gstin = (inv.supplier_gstin or "").strip().upper()
        if not gstin:
            return None
        return next((v for v in ref.vendors if v["gstin"].strip().upper() == gstin), None)
    key = normalize_name(inv.supplier_name)
    if not key:
        return None
    return next((v for v in ref.vendors if normalize_name(v["legal_name"]) == key), None)


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


def _digits(value: str | None) -> str:
    return re.sub(r"\D", "", value or "")


def check_bank_details(inv: Invoice, vendor: dict | None) -> list[str]:
    """Policy §3: account digits-only, IFSC case-insensitive; skip if vendor unknown or no bank details shown."""
    if not vendor:
        return []
    doc_account, doc_ifsc = _digits(inv.bank_account), (inv.ifsc or "").strip().upper()
    if not doc_account and not doc_ifsc:
        return []
    file_account, file_ifsc = _digits(vendor.get("bank_account")), (vendor.get("ifsc") or "").strip().upper()
    if (doc_account and doc_account != file_account) or (doc_ifsc and doc_ifsc != file_ifsc):
        return ["bank_details_changed"]
    return []

CREDIT_NOTE_PATTERNS = [
    re.compile(r'"Typ"\s*:\s*"CRN"'),  # e-invoice DocDtls.Typ
    re.compile(r"^\s*credit\s+note\b", re.IGNORECASE | re.MULTILINE),  # a title line
]

SUSPICIOUS_PATTERNS = [
    # HTML or script markup (policy)
    re.compile(r"<\s*/?\s*(script|img|iframe|svg|object|embed|style|link|meta|a)\b", re.IGNORECASE),
    re.compile(r"\bon[a-z]+\s*=", re.IGNORECASE),
    re.compile(r"javascript\s*:", re.IGNORECASE),
    # Text addressed to automated systems or AI (policy)
    re.compile(r"\b(ai|llm|gpt|chatgpt|language model)s?\b", re.IGNORECASE),
    re.compile(r"\bautomat(ed|ion)\s+(\w+\s+){0,2}(processing|system|assistant)s?\b", re.IGNORECASE),
    re.compile(r"\b(requires?_review|needs_review|review_reasons)\b", re.IGNORECASE),
    re.compile(r"\b(ignore|disregard|skip)\b.{0,40}\b(instruction|check|rule|polic|review)", re.IGNORECASE),
    re.compile(r"\bpre-?(verified|approved)\b", re.IGNORECASE),
]


def check_credit_note(inv: Invoice, raw_text: str) -> list[str]:
    if inv.document_type == "credit_note" or any(p.search(raw_text) for p in CREDIT_NOTE_PATTERNS):
        return ["credit_note"]
    return []


def check_foreign_currency(inv: Invoice) -> list[str]:
    return [] if (inv.currency or "INR").strip().upper() == "INR" else ["foreign_currency"]


def check_vendor_new(inv: Invoice, vendor: dict | None) -> list[str]:
    """Policy: onboarded fewer than 90 days before the document date."""
    if not vendor or not inv.invoice_date or not vendor.get("onboarded_on"):
        return []
    onboarded = date.fromisoformat(vendor["onboarded_on"].strip())
    return ["vendor_new"] if (inv.invoice_date - onboarded).days < 90 else []


def check_suspicious_content(raw_text: str) -> list[str]:
    return ["suspicious_content"] if any(p.search(raw_text) for p in SUSPICIOUS_PATTERNS) else []


def run_checks(conn: sqlite3.Connection, ref: ReferenceData, inv: Invoice, raw_text: str = "") -> list[str]:
    vendor = find_vendor(ref, inv)
    return (
        check_credit_note(inv, raw_text)
        + check_gstin(inv)
        + check_vendor(vendor)
        + check_vendor_new(inv, vendor)
        + check_tax_type(inv, ref.buyer.get("state_code", BUYER_STATE_CODE))
        + check_totals(inv)
        + check_foreign_currency(inv)
        + check_duplicate(conn, ref, inv)
        + check_bank_details(inv, vendor)
        + check_suspicious_content(raw_text)
    )
