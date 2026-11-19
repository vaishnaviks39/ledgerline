"""Process one document end to end: extract -> normalise -> check -> route -> persist."""
from __future__ import annotations

import json
import sqlite3
from dataclasses import asdict

from . import db
from .extraction import extract
from .llm.pricing import cost_usd
from .models import Invoice, LineItem
from .parsing import parse_amount, parse_date
from .reference import ReferenceData
from .validation import MODEL_ADDABLE_REASONS, normalize_name, run_checks

HIGH_VALUE_THRESHOLD = 500000  # invoices above this need two approvals

def vendor_country(ref: ReferenceData, data: dict) -> str:
    """Country of the matched vendor (GSTIN for domestic, normalised name otherwise); 'IN' if unknown."""
    gstin = (data.get("supplier_gstin") or "").strip().upper()
    name = normalize_name(data.get("supplier_name"))
    for vendor in ref.vendors:
        if (gstin and vendor["gstin"].strip().upper() == gstin) or (
                not gstin and name and normalize_name(vendor["legal_name"]) == name):
            return (vendor.get("country") or "IN").strip().upper()
    return "IN"

def normalize(data: dict, month_first: bool = False) -> Invoice:
    items = [
        LineItem(
            description=str(item.get("description", "")),
            quantity=parse_amount(item.get("quantity")),
            unit_price=parse_amount(item.get("unit_price")),
            amount=parse_amount(item.get("amount")) or 0.0,
        )
        for item in data.get("line_items") or []
    ]
    return Invoice(
        document_type=data.get("document_type") or "invoice",
        supplier_name=data.get("supplier_name"),
        supplier_gstin=data.get("supplier_gstin"),
        invoice_number=data.get("invoice_number"),
                invoice_date=parse_date(data.get("invoice_date"), month_first=month_first),
        currency=data.get("currency") or "INR",
        subtotal=parse_amount(data.get("subtotal")),
        cgst=parse_amount(data.get("cgst")) or 0.0,
        sgst=parse_amount(data.get("sgst")) or 0.0,
        igst=parse_amount(data.get("igst")) or 0.0,
        round_off=parse_amount(data.get("round_off")) or 0.0,
        total=parse_amount(data.get("total")),
        bank_account=data.get("bank_account"),
        ifsc=data.get("ifsc"),
        po_number=data.get("po_number"),
        notes=data.get("notes"),
        line_items=items,
    )


def process_document(
    conn: sqlite3.Connection,
    ref: ReferenceData,
    raw_text: str,
    document_id: str,
    org_id: str = "meridian",
    filename: str | None = None,
) -> dict:
    data, responses = extract(raw_text, ref)
    inv = normalize(data, month_first=vendor_country(ref, data) == "US")

    # Code decides routing (policy). The model may only add reasons in MODEL_ADDABLE_REASONS;
    # it can never remove a reason, and its yes/no answer is not used.

    code_reasons =  run_checks(conn, ref, inv, raw_text)
    model_raw = data.get("review_reasons") or []

    if isinstance(model_raw, str):
        model_raw = [model_raw]

    model_added = [r for r in model_raw if r in MODEL_ADDABLE_REASONS]
    review_reasons = sorted(set(code_reasons) | set(model_added))
    needs_review = bool(review_reasons)
    # Keep the model's other suggestions visible to reviewers and for audit (policy).
    warnings = [f"model suggested {r} (not applied)" for r in model_raw if r not in review_reasons]

    required_approvals = 2 if (inv.total or 0) > HIGH_VALUE_THRESHOLD else 1
    status = "needs_review" if needs_review else "ready_for_approval"

    cur = conn.execute(
        """INSERT INTO invoices (org_id, document_id, filename, raw_text, document_type, supplier_name,
               supplier_gstin, invoice_number, invoice_date, currency, subtotal, cgst, sgst, igst, round_off,
               total, bank_account, ifsc, po_number, notes, line_items_json, warnings_json, needs_review,
               review_reasons_json, required_approvals, status)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            org_id, document_id, filename, raw_text, inv.document_type, inv.supplier_name, inv.supplier_gstin,
            inv.invoice_number, inv.invoice_date.isoformat() if inv.invoice_date else None, inv.currency,
            inv.subtotal, inv.cgst, inv.sgst, inv.igst, inv.round_off, inv.total, inv.bank_account, inv.ifsc,
            inv.po_number, inv.notes, json.dumps([asdict(i) for i in inv.line_items]), json.dumps(warnings),
            int(needs_review), json.dumps(review_reasons), required_approvals, status,
        ),
    )
    invoice_id = cur.lastrowid
    for r in responses:
        conn.execute(
            "INSERT INTO llm_calls (invoice_id, document_id, model, input_tokens, output_tokens, cost_usd, "
            "latency_ms) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (invoice_id, document_id, r.model, r.input_tokens, r.output_tokens,
             cost_usd(r.model, r.input_tokens, r.output_tokens), r.latency_ms),
        )
    conn.commit()
    return db.get_invoice(conn, invoice_id)
