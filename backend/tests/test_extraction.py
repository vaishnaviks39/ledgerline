import json

from ledgerline.extraction import extract
from ledgerline.llm.fake import CANNED_EXTRACTION, FakeClient


def test_extract_accepts_json_wrapped_in_code_fence(monkeypatch, ref):
    # gpt-4o-mini replies like this (seen on dev_001 in the starter run)
    fenced = "```json\n" + json.dumps(CANNED_EXTRACTION) + "\n```"
    client = FakeClient([fenced, fenced])
    monkeypatch.setattr("ledgerline.extraction.get_client", lambda: client)

    data, _ = extract("INVOICE TEXT", ref)

    assert data["invoice_number"] == "SIS/26-27/0042"