"""Token pricing for the cost dashboard and the llm_calls table."""
from __future__ import annotations

# USD per MILLION tokens: (input, output). The starter stored per-thousand prices here,
# so every recorded cost was ~1000x too low. Check against the providers' pricing pages.
USD_PER_MTOK: dict[str, tuple[float, float]] = {
    "claude-opus-5-5": (4.0, 20.0),
    "claude-sonnet-5-5": (2.0, 10.0),
    "claude-haiku-5-5": (0.1, 0.5),
    "claude-opus-4-5": (5.0, 25.0),
    "claude-sonnet-4-5": (3.0, 15.0),
    "gpt-4o-mini": (0.15, 0.60),
}


def _price(model: str) -> tuple[float, float]:
    """Exact name first, then the longest known name the model starts with (e.g. dated versions)."""
    if model in USD_PER_MTOK:
        return USD_PER_MTOK[model]
    for name in sorted(USD_PER_MTOK, key=len, reverse=True):
        if model.startswith(name):
            return USD_PER_MTOK[name]
    return (0.0, 0.0)


def cost_usd(model: str, input_tokens: int, output_tokens: int) -> float:
    input_price, output_price = _price(model)
    return (input_tokens * input_price + output_tokens * output_price) / 1_000_000