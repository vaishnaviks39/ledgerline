import json

from ledgerline import cli
from ledgerline.config import get_settings
from ledgerline.llm.fake import FakeClient


def test_batch_never_skips_a_document(tmp_path, monkeypatch):
    in_dir = tmp_path / "in"
    in_dir.mkdir()
    (in_dir / "a_good.txt").write_text("INVOICE", encoding="utf-8")
    (in_dir / "b_bad.TXT").write_bytes(b"\xff\xfe not utf-8")
    client = FakeClient(["not json at all"] * 4)
    monkeypatch.setattr("ledgerline.extraction.get_client", lambda: client)
    out = tmp_path / "out.jsonl"

    cli.main(["predict", "--input", str(in_dir), "--reference", str(get_settings().data_dir / "reference"),
              "--output", str(out)])

    lines = [json.loads(line) for line in out.read_text(encoding="utf-8").splitlines()]
    assert [line["document_id"] for line in lines] == ["a_good", "b_bad"]
    assert all(line["needs_review"] and "processing_error" in line["review_reasons"] for line in lines)