import json

from ledgerline.config import get_settings
from ledgerline.llm.fake import FakeClient
from ledgerline.pipeline import process_document

DISPUTED = get_settings().data_dir / "invoices" / "disputed"


def run(conn, ref, monkeypatch, filename, reply):
    text = json.dumps(reply)
    client = FakeClient([text, text])
    monkeypatch.setattr("ledgerline.extraction.get_client", lambda: client)
    raw = (DISPUTED / filename).read_text(encoding="utf-8")
    return process_document(conn, ref, raw, filename.rsplit(".", 1)[0], filename=filename)


def test_disp_01_garbled_gstin_goes_to_review_and_is_not_corrected(conn, ref, monkeypatch):
    # Ruling: needs review (gstin_invalid, vendor_unknown); the GSTIN is not auto-corrected to Sitara's.
    invoice = run(conn, ref, monkeypatch, "disp_01.txt", {
        "document_type": "invoice", "supplier_name": "Sitara Industrial Supplies Pvt. Ltd.",
        "supplier_gstin": "27AAKCS4B21M1ZW", "invoice_number": "SIS/26-27/0055", "invoice_date": "30/04/2026",
        "currency": "INR", "subtotal": "13840.00", "cgst": "1245.60", "sgst": "1245.60", "igst": "0.00",
        "round_off": "-0.20", "total": "16331.00", "bank_account": "XXXXXXXXXX5678", "ifsc": "ZEPH0001234",
        "po_number": "PO-2026-0138", "notes": "",
        "line_items": [
            {"description": "SS Hex Bolt M10x40 (Box/100)", "quantity": "8", "unit_price": "1450.00",
             "amount": "11600.00"},
            {"description": "Allen Cap Screw M8x25 (Box/100)", "quantity": "2", "unit_price": "1120.00",
             "amount": "2240.00"},
        ],
        "requires_review": False, "review_reasons": [],
    })
    assert invoice["needs_review"] is True
    assert invoice["review_reasons"] == ["gstin_invalid", "vendor_unknown"]
    assert invoice["supplier_gstin"] == "27AAKCS4B21M1ZW"
    assert invoice["required_approvals"] == 1


def test_disp_02_revised_invoice_reusing_a_paid_number_is_a_duplicate(conn, ref, monkeypatch):
    # Ruling: needs review (duplicate) of paid SIS/26-27/0018; duplicates cannot be approved (policy §4.4).
    invoice = run(conn, ref, monkeypatch, "disp_02.txt", {
        "document_type": "invoice", "supplier_name": "Sitara Industrial Supplies Pvt. Ltd.",
        "supplier_gstin": "27AAKCS4821M1ZW", "invoice_number": "SIS/26-27/0018", "invoice_date": "02/04/2026",
        "currency": "INR", "subtotal": "30400.00", "cgst": "2736.00", "sgst": "2736.00", "igst": "0.00",
        "round_off": "0.00", "total": "35872.00", "bank_account": "XXXXXXXXXX5678", "ifsc": "ZEPH0001234",
        "po_number": "PO-2026-0098", "notes": "",
        "line_items": [
            {"description": "SS Hex Bolt M10x40 (Box/100)", "quantity": "20", "unit_price": "1520.00",
             "amount": "30400.00"},
        ],
        "requires_review": False, "review_reasons": [],
    })
    assert invoice["needs_review"] is True
    assert invoice["review_reasons"] == ["duplicate"]