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

def test_exactly_five_lakh_needs_two_approvals(conn, ref, monkeypatch):
    # dev_017: total is exactly ₹5,00,000.00
    invoice = run_with_reply(conn, ref, monkeypatch, total="500000.00")
    assert invoice["required_approvals"] == 2


def test_just_under_five_lakh_needs_one_approval(conn, ref, monkeypatch):
    invoice = run_with_reply(conn, ref, monkeypatch, total="499999.99")
    assert invoice["required_approvals"] == 1


def test_foreign_currency_invoice_needs_two_approvals(conn, ref, monkeypatch):
    # dev_014: USD 1,298.00, dated 04/03/2026 (month first: 3 April)
    invoice = run_with_reply(conn, ref, monkeypatch, supplier_name="CloudNimbus Inc.", supplier_gstin=None,
                             currency="USD", invoice_number="CN-2026-04417", invoice_date="04/03/2026",
                             total="1298.00")
    assert invoice["required_approvals"] == 2


def test_credit_note_needs_zero_approvals(conn, ref, monkeypatch):
    # dev_007
    invoice = run_with_reply(conn, ref, monkeypatch, document_type="credit_note")
    assert invoice["required_approvals"] == 0


def test_einvoice_crn_is_stored_as_credit_note_even_if_model_says_invoice(conn, ref, monkeypatch):
    reply = json.dumps(dict(CANNED_EXTRACTION, document_type="invoice"))
    client = FakeClient([reply, reply])
    monkeypatch.setattr("ledgerline.extraction.get_client", lambda: client)
    invoice = process_document(conn, ref, '{"DocDtls": {"Typ": "CRN", "No": "KT/CN/2026/006"}}', "doc_crn")
    assert invoice["document_type"] == "credit_note"
    assert invoice["required_approvals"] == 0
    assert "duplicate" not in invoice["review_reasons"]

def test_unparseable_model_reply_goes_to_review(conn, ref, monkeypatch):
    client = FakeClient(["this is not JSON", "this is not JSON"])
    monkeypatch.setattr("ledgerline.extraction.get_client", lambda: client)
    invoice = process_document(conn, ref, "TEXT", "doc_broken")
    assert invoice["needs_review"] is True
    assert "processing_error" in invoice["review_reasons"]
    assert invoice["status"] == "needs_review"


def test_failed_calls_are_still_recorded(conn, ref, monkeypatch):
    client = FakeClient(["this is not JSON", "this is not JSON"])
    monkeypatch.setattr("ledgerline.extraction.get_client", lambda: client)
    invoice = process_document(conn, ref, "TEXT", "doc_broken")
    assert invoice["usage"]["llm_calls"] == 1


def test_impossible_date_goes_to_review(conn, ref, monkeypatch):
    invoice = run_with_reply(conn, ref, monkeypatch, invoice_date="31/02/2026")
    assert "processing_error" in invoice["review_reasons"]


def test_missing_total_goes_to_review(conn, ref, monkeypatch):
    invoice = run_with_reply(conn, ref, monkeypatch, total=None)
    assert "processing_error" in invoice["review_reasons"]