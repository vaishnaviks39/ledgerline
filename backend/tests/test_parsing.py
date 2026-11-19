from datetime import date

from ledgerline.parsing import parse_amount, parse_date


def test_parse_amount_indian_grouping():
    assert parse_amount("1,23,456.00") == 123456.0


def test_parse_amount_rupee_symbol():
    assert parse_amount("₹ 2,480.00") == 2480.0


def test_parse_amount_passes_numbers_through():
    assert parse_amount(1789.2) == 1789.2


def test_parse_amount_empty_is_none():
    assert parse_amount("") is None


def test_parse_date_iso():
    assert parse_date("2026-04-25") == date(2026, 4, 25)


def test_parse_date_with_slashes_is_day_first():
    # Policy §1: Indian vendors print day first. The starter's test asserted 4 March.
    assert parse_date("03/04/2026") == date(2026, 4, 3)


def test_parse_date_day_first_when_unambiguous():
    assert parse_date("25/04/2026") == date(2026, 4, 25)

def test_parse_date_with_dashes_is_day_first():
    assert parse_date("11-04-2026") == date(2026, 4, 11)


def test_parse_date_with_dots_is_day_first():
    assert parse_date("05.04.2026") == date(2026, 4, 5)


def test_parse_date_month_first_for_us_vendors():
    # dev_014 CloudNimbus (country US): 04/03/2026 is 3 April
    assert parse_date("04/03/2026", month_first=True) == date(2026, 4, 3)