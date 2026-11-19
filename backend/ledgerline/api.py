"""HTTP API used by the reviewer UI.  Run: uvicorn ledgerline.api:app --reload"""
from __future__ import annotations

from fastapi import Depends, FastAPI, Header, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from . import db
from .config import USD_TO_INR, get_settings
from .pipeline import process_document
from .reference import load_reference

app = FastAPI(title="Ledgerline API", version="0.3.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


def get_conn():
    conn = db.connect(get_settings().db_path)
    try:
        yield conn
    finally:
        conn.close()


def get_org(x_org_id: str = Header(default="meridian")) -> str:
    return x_org_id


class DecisionRequest(BaseModel):
    user_id: str
    note: str = ""


@app.get("/api/health")
def health() -> dict:
    return {"ok": True}


@app.post("/api/invoices")
async def upload_invoice(file: UploadFile, org_id: str = Depends(get_org), conn=Depends(get_conn)):
    raw_text = (await file.read()).decode("utf-8")
    document_id = (file.filename or "upload").rsplit(".", 1)[0]
    return process_document(conn, load_reference(), raw_text, document_id, org_id=org_id, filename=file.filename)


@app.get("/api/invoices")
def list_invoices(org_id: str = Depends(get_org), conn=Depends(get_conn)):
    rows = conn.execute(
        "SELECT id, document_id, supplier_name, invoice_number, invoice_date, currency, total, status, "
        "needs_review FROM invoices WHERE org_id = ? ORDER BY id DESC",
        (org_id,),
    ).fetchall()
    return [dict(r) for r in rows]


@app.get("/api/invoices/{invoice_id}")
def get_invoice(invoice_id: int, conn=Depends(get_conn)):
    invoice = db.get_invoice(conn, invoice_id)
    if invoice is None:
        raise HTTPException(status_code=404, detail="Invoice not found")
    return invoice


def _approval_count(conn, invoice_id: int) -> int:
    return conn.execute("SELECT COUNT(DISTINCT user_id) FROM approvals WHERE invoice_id = ?",
                        (invoice_id,)).fetchone()[0]


@app.post("/api/invoices/{invoice_id}/approve")
def approve_invoice(invoice_id: int, body: DecisionRequest, conn=Depends(get_conn)):
    """Policy §4, enforced on the server. Safe under double-clicks and retries."""
    invoice = db.get_invoice(conn, invoice_id)
    if invoice is None:
        raise HTTPException(status_code=404, detail="Invoice not found")
    user_id = body.user_id.strip()
    if not user_id:
        raise HTTPException(status_code=422, detail="user_id is required")
    required = max(int(invoice["required_approvals"]), 1)  # §4.3: never paid without a human approval

    if invoice["status"] == "approved":  # retry or double-click: change nothing
        return {"id": invoice_id, "approvals": _approval_count(conn, invoice_id),
                "required_approvals": required, "status": "approved"}
    if invoice["status"] == "rejected":
        raise HTTPException(status_code=409, detail="Invoice was rejected and cannot be approved")
    if invoice["document_type"] == "credit_note" or "credit_note" in invoice["review_reasons"]:
        raise HTTPException(status_code=409, detail="Credit notes are never approved for payment (policy §2)")
    if "duplicate" in invoice["review_reasons"]:
        raise HTTPException(status_code=409, detail="Duplicates cannot be approved; reject instead (policy §4.4)")
    if invoice["needs_review"] and not body.note.strip():
        raise HTTPException(status_code=422, detail="A note is required to approve a reviewed document (policy §4.5)")

    # §4.2: the unique index makes a second approval by the same person a no-op.
    conn.execute("INSERT OR IGNORE INTO approvals (invoice_id, user_id, note) VALUES (?, ?, ?)",
                 (invoice_id, user_id, body.note))
    approvals = _approval_count(conn, invoice_id)
    status = invoice["status"]
    if approvals >= required:
        # §4.6: only the request that flips the status creates the payment; the unique index backs it up.
        flipped = conn.execute("UPDATE invoices SET status = 'approved' WHERE id = ? AND status <> 'approved'",
                               (invoice_id,)).rowcount
        if flipped == 1:
            conn.execute("INSERT OR IGNORE INTO payments (invoice_id, amount) VALUES (?, ?)",
                         (invoice_id, invoice["total"]))
        status = "approved"
    conn.commit()
    return {"id": invoice_id, "approvals": approvals, "required_approvals": required, "status": status}


@app.post("/api/invoices/{invoice_id}/reject")
def reject_invoice(invoice_id: int, body: DecisionRequest, conn=Depends(get_conn)):
    invoice = db.get_invoice(conn, invoice_id)
    if invoice is None:
        raise HTTPException(status_code=404, detail="Invoice not found")
    if invoice["status"] == "approved":
        raise HTTPException(status_code=409, detail="Invoice is approved and has a payment instruction")
    if invoice["status"] != "rejected":
        conn.execute("UPDATE invoices SET status = 'rejected' WHERE id = ?", (invoice_id,))
        conn.commit()
    return {"id": invoice_id, "status": "rejected"}


@app.get("/api/stats")
def stats(org_id: str = Depends(get_org), conn=Depends(get_conn)):
    """Feeds the cost dashboard."""
    row = conn.execute(
        "SELECT COUNT(DISTINCT c.invoice_id) AS invoices, COALESCE(SUM(c.cost_usd), 0) AS cost_usd "
        "FROM llm_calls c JOIN invoices i ON i.id = c.invoice_id WHERE i.org_id = ?",
        (org_id,),
    ).fetchone()
    total_inr = row["cost_usd"] * USD_TO_INR
    return {
        "invoices_processed": row["invoices"],
        "llm_cost_inr": round(total_inr, 2),
        "avg_llm_cost_per_invoice_inr": round(total_inr / row["invoices"], 4) if row["invoices"] else 0.0,
    }
