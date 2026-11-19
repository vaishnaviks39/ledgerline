"""Flags for rulings that depart from AP_POLICY.md (README Part 2).

Every flag is off by default, so Ledgerline follows the written policy. A flag is switched on
only by setting LEDGERLINE_FLAG_<NAME>=1 in the environment. The flags are listed in
submission/RULINGS.md.
"""
from __future__ import annotations

import os


def flag_on(name: str) -> bool:
    return os.getenv(f"LEDGERLINE_FLAG_{name}", "").strip() == "1"