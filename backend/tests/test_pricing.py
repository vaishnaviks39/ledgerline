import pytest

from ledgerline.config import USD_TO_INR
from ledgerline.llm.pricing import cost_usd


def test_one_million_input_tokens_costs_the_list_price():
    assert cost_usd("gpt-4o-mini", 1_000_000, 0) == pytest.approx(0.15)


def test_baseline_run_cost_matches_the_real_bill():
    # Starter dev run on gpt-4o-mini: 239,991 input + 19,345 output tokens ≈ ₹4.19 (recorded: ₹0.0042)
    assert cost_usd("gpt-4o-mini", 239_991, 19_345) * USD_TO_INR == pytest.approx(4.19, abs=0.01)


def test_dated_model_name_uses_the_base_price():
    assert cost_usd("gpt-4o-mini-2024-07-18", 1_000_000, 0) == pytest.approx(0.15)