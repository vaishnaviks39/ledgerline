import json

from ledgerline.llm.fake import CANNED_EXTRACTION, FakeClient
from ledgerline.pipeline import process_document


def run_with_model_reply(conn, ref, monkeypatch, **overrides):
    reply = json.dumps(dict(CANNED_EXTRACTION, **overrides))
    client = FakeClient([reply, reply])
    monkeypatch.setattr("ledgerline.extraction.get_client", lambda: client)
    return process_document(conn, ref, "INVOICE TEXT", "doc_routing")


def test_code_check_routes_to_review_even_if_model_says_ready(conn, ref, monkeypatch):
    # GSTIN not in the vendor master; model says it is fine (dev_018 / dev_012 pattern)
    inv = run_with_model_reply(conn, ref, monkeypatch, supplier_gstin="27AAQCA8124J1ZA",
                               requires_review=False, review_reasons=[])
    assert inv["needs_review"] is True
    assert "vendor_unknown" in inv["review_reasons"]


def test_unreliable_model_reason_does_not_route(conn, ref, monkeypatch):
    # Clean Sitara invoice; model wrongly claims vendor_unknown (seen on disp_06)
    inv = run_with_model_reply(conn, ref, monkeypatch, requires_review=True,
                               review_reasons=["vendor_unknown"])
    assert inv["needs_review"] is False
    assert inv["status"] == "ready_for_approval"


def test_model_suspicious_content_is_only_a_warning(conn, ref, monkeypatch):
    # The model's flag is shown to the reviewer but does not route (dev-run false positives)
    inv = run_with_model_reply(conn, ref, monkeypatch, requires_review=False,
                               review_reasons=["suspicious_content"])
    assert inv["needs_review"] is False
    assert "model suggested suspicious_content (not applied)" in inv["warnings"]


def test_unknown_codes_from_model_are_ignored(conn, ref, monkeypatch):
    # dev_019: model returned the made-up code "none"
    inv = run_with_model_reply(conn, ref, monkeypatch, requires_review=True, review_reasons=["none"])
    assert inv["needs_review"] is False