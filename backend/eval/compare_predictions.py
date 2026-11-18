"""Compare a predictions.jsonl with the dev labels: routing, review reasons and key fields.

Usage (from backend/):  python eval/compare_predictions.py <predictions.jsonl> [labels.jsonl]
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

FIELDS = ["document_type", "supplier_gstin", "invoice_number", "invoice_date", "currency",
          "total", "bank_account", "ifsc", "required_approvals"]


def read_jsonl(path: Path) -> list[dict]:
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def main() -> None:
    pred_path = Path(sys.argv[1])
    label_path = (Path(sys.argv[2]) if len(sys.argv) > 2
                  else Path(__file__).resolve().parents[2] / "data" / "ground_truth" / "dev.jsonl")
    labels = {r["document_id"]: r["expected"] for r in read_jsonl(label_path)}
    preds = {r["document_id"]: r for r in read_jsonl(pred_path)}

    missed, extra, missing = [], [], []
    print("| doc | expected | got | reasons missing | reasons extra | field differences |")
    print("|---|---|---|---|---|---|")
    for doc_id, exp in sorted(labels.items()):
        got = preds.get(doc_id)
        if got is None:
            missing.append(doc_id)
            print(f"| {doc_id} | {'review' if exp['needs_review'] else 'ready'} | MISSING | | | |")
            continue
        exp_review, got_review = bool(exp["needs_review"]), bool(got.get("needs_review"))
        if exp_review and not got_review:
            missed.append(doc_id)
        elif got_review and not exp_review:
            extra.append(doc_id)
        got_reasons = set(got.get("review_reasons") or [])
        reasons_missing = sorted(set(exp["review_reasons"]) - got_reasons)
        reasons_extra = sorted(got_reasons - set(exp["review_reasons"]))
        diffs = [f"{f}: got {got.get(f)!r}, want {exp.get(f)!r}"
                 for f in FIELDS if str(got.get(f)) != str(exp.get(f))]
        print(f"| {doc_id} | {'review' if exp_review else 'ready'} | {'review' if got_review else 'ready'} "
              f"| {', '.join(reasons_missing)} | {', '.join(reasons_extra)} | {'; '.join(diffs)} |")

    needed = sum(1 for e in labels.values() if e["needs_review"])
    print()
    print(f"Documents: {len(labels)}, needed review: {needed}")
    print(f"MISSED REVIEWS (needed review, routed ready): {len(missed)} {missed}")
    print(f"Unnecessary reviews (ready, routed to review): {len(extra)} {extra}")
    print(f"Missing from predictions: {len(missing)} {missing}")


if __name__ == "__main__":
    main()
