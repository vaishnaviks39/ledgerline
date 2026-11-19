import json

from ledgerline.config import get_settings
from ledgerline.extraction import mask_accounts
from ledgerline.llm.fake import CANNED_EXTRACTION, FakeClient
from ledgerline.pipeline import process_document

DEV_005 = (get_settings().data_dir / "invoices" / "dev" / "dev_005.eml").read_text(encoding="utf-8")


def sent_text(client):
    return "\n".join(system + "\n" + prompt for system, prompt in client.calls)


def test_no_full_bank_account_is_sent_to_the_provider(conn, ref, fake_llm):
    process_document(conn, ref, DEV_005, "dev_005")
    sent = sent_text(fake_llm)
    accounts = [v["bank_account"] for v in ref.vendors if v["bank_account"]] + ["7781002233445"]
    assert [a for a in accounts if a in sent] == []


def test_vendor_master_and_dev_examples_are_not_sent(conn, ref, fake_llm):
    process_document(conn, ref, DEV_005, "dev_005")
    sent = sent_text(fake_llm)
    assert "vendor_id,legal_name" not in sent      # vendor master header
    assert "NPL/2627/0311" not in sent             # dev_003, one of the leaked examples


def test_full_account_is_restored_from_the_document(conn, ref, monkeypatch):
    reply = json.dumps(dict(CANNED_EXTRACTION, bank_account="XXXXXXXXX3445", ifsc="ORBK0002211"))
    client = FakeClient([reply, reply])
    monkeypatch.setattr("ledgerline.extraction.get_client", lambda: client)
    invoice = process_document(conn, ref, DEV_005, "dev_005")
    assert invoice["bank_account"] == "7781002233445"


def test_spaced_account_number_is_masked():
    masked, _ = mask_accounts("A/c No: 5020 0012 345678")
    assert "5678" in masked
    assert "50200012" not in masked.replace(" ", "")


def test_amounts_dates_and_gstin_are_not_masked():
    text = "GSTIN 27AAKCS4821M1ZW  Dated 25/04/2026  TOTAL 1,10,920.00  Qty 1200"
    masked, _ = mask_accounts(text)
    assert masked == text

def test_hyphenated_invoice_number_is_not_masked():
    # dev_014: "CN-2026-04417" was masked to "CN-XXXXX4417"
    text = "Invoice number      CN-2026-04417"
    assert mask_accounts(text)[0] == text


def test_long_digit_run_inside_an_identifier_is_not_masked():
    text = "Ref: INV-202604417"
    assert mask_accounts(text)[0] == text