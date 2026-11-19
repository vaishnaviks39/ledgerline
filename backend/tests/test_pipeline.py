from ledgerline.pipeline import process_document

import json

from ledgerline.llm.fake import CANNED_EXTRACTION, FakeClient

def test_process_document_persists_invoice(conn, ref, fake_llm):
    invoice = process_document(conn, ref, "INVOICE TEXT", "doc_001", filename="doc_001.txt")
    assert invoice["supplier_name"] == "Sitara Industrial Supplies Pvt. Ltd."
    assert invoice["total"] == 23458.0
    assert invoice["invoice_date"] == "2026-04-25"
    assert invoice["status"] == "ready_for_approval"
    assert invoice["usage"]["llm_calls"] == 2


def test_document_text_reaches_the_model(conn, ref, fake_llm):
    process_document(conn, ref, "UNIQUE-MARKER-123", "doc_002")
    assert "UNIQUE-MARKER-123" in fake_llm.calls[0][1]


def test_line_items_are_stored(conn, ref, fake_llm):
    invoice = process_document(conn, ref, "INVOICE TEXT", "doc_003")
    assert [item["amount"] for item in invoice["line_items"]] == [17400.0, 2480.0]

def run_with_reply(conn, ref, monkeypatch, **overrides):
    reply = json.dumps(dict(CANNED_EXTRACTION, **overrides))
    client = FakeClient([reply, reply])
    monkeypatch.setattr("ledgerline.extraction.get_client", lambda: client)
    return process_document(conn, ref, "TEXT", "doc_date")


def test_indian_vendor_date_is_day_first(conn, ref, monkeypatch):
    # dev_002: Sitara "03/04/2026" is 3 April 2026 (FY 2026-27)
    invoice = run_with_reply(conn, ref, monkeypatch, invoice_date="03/04/2026")
    assert invoice["invoice_date"] == "2026-04-03"


def test_us_vendor_date_is_month_first(conn, ref, monkeypatch):
    # dev_014: CloudNimbus (country US) "04/03/2026" is 3 April 2026
    invoice = run_with_reply(conn, ref, monkeypatch, supplier_name="CloudNimbus Inc.", supplier_gstin=None,
                             currency="USD", invoice_number="CN-2026-04417", invoice_date="04/03/2026")
    assert invoice["invoice_date"] == "2026-04-03"