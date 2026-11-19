from ledgerline.flags import flag_on


def test_flags_are_off_by_default(monkeypatch):
    monkeypatch.delenv("LEDGERLINE_FLAG_EXAMPLE", raising=False)
    assert flag_on("EXAMPLE") is False


def test_flag_is_on_only_when_set_to_1(monkeypatch):
    monkeypatch.setenv("LEDGERLINE_FLAG_EXAMPLE", "1")
    assert flag_on("EXAMPLE") is True
    monkeypatch.setenv("LEDGERLINE_FLAG_EXAMPLE", "yes")
    assert flag_on("EXAMPLE") is False