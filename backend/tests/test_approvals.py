import sqlite3

import pytest
from fastapi.testclient import TestClient

from ledgerline.api import app


@pytest.fixture
def api(tmp_path, monkeypatch, fake_llm):
    db_path = tmp_path / "api.db"
    monkeypatch.setenv("LEDGERLINE_DB", str(db_path))
    return TestClient(app), db_path


def upload(client, name="doc.txt"):
    return client.post("/api/invoices", files={"file": (name, b"invoice text", "text/plain")}).json()["id"]


def approve(client, invoice_id, user="kavya", note="ok"):
    return client.post(f"/api/invoices/{invoice_id}/approve", json={"user_id": user, "note": note})


def sql(db_path, query, params=()):
    with sqlite3.connect(db_path) as conn:
        return conn.execute(query, params).fetchall()


def payments(db_path, invoice_id):
    return sql(db_path, "SELECT COUNT(*) FROM payments WHERE invoice_id = ?", (invoice_id,))[0][0]


def test_double_click_creates_exactly_one_payment(api):
    client, db_path = api
    invoice_id = upload(client)
    approve(client, invoice_id)
    second = approve(client, invoice_id)
    assert second.json()["status"] == "approved"
    assert payments(db_path, invoice_id) == 1


def test_same_person_approving_twice_counts_once(api):
    client, db_path = api
    invoice_id = upload(client)
    sql(db_path, "UPDATE invoices SET required_approvals = 2 WHERE id = ?", (invoice_id,))
    approve(client, invoice_id, user="kavya")
    result = approve(client, invoice_id, user="kavya").json()
    assert result["status"] != "approved"
    assert payments(db_path, invoice_id) == 0


def test_two_people_reach_two_approvals(api):
    client, db_path = api
    invoice_id = upload(client)
    sql(db_path, "UPDATE invoices SET required_approvals = 2 WHERE id = ?", (invoice_id,))
    approve(client, invoice_id, user="kavya")
    assert approve(client, invoice_id, user="sunil").json()["status"] == "approved"
    assert payments(db_path, invoice_id) == 1


def test_duplicate_cannot_be_approved(api):
    client, db_path = api
    upload(client, "first.txt")
    duplicate_id = upload(client, "second.txt")  # same supplier and invoice number
    response = approve(client, duplicate_id, note="looked at it")
    assert response.status_code == 409
    assert payments(db_path, duplicate_id) == 0


def test_reviewed_document_needs_a_note(api):
    client, db_path = api
    invoice_id = upload(client)
    sql(db_path, "UPDATE invoices SET needs_review = 1, status = 'needs_review', "
                 "review_reasons_json = '[\"vendor_new\"]' WHERE id = ?", (invoice_id,))
    assert approve(client, invoice_id, note="").status_code == 422
    assert payments(db_path, invoice_id) == 0
    assert approve(client, invoice_id, note="Called vendor, onboarding confirmed").json()["status"] == "approved"


def test_credit_note_cannot_be_approved(api):
    client, db_path = api
    invoice_id = upload(client)
    sql(db_path, "UPDATE invoices SET document_type = 'credit_note' WHERE id = ?", (invoice_id,))
    assert approve(client, invoice_id).status_code == 409
    assert payments(db_path, invoice_id) == 0


def test_paid_invoice_cannot_be_rejected(api):
    client, db_path = api
    invoice_id = upload(client)
    approve(client, invoice_id)
    response = client.post(f"/api/invoices/{invoice_id}/reject", json={"user_id": "farhan", "note": "no"})
    assert response.status_code == 409
    assert sql(db_path, "SELECT status FROM invoices WHERE id = ?", (invoice_id,))[0][0] == "approved"