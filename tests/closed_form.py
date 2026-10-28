"""Closed form of the two-stage sum. Kept out of the library on purpose.

The library discounts with a loop. This module uses the geometric-sum formula.
Tests and check.py fail if the two disagree.
"""

from __future__ import annotations


def closed_form_value(
    earnings0: float,
    growth: float,
    cost_of_equity: float,
    terminal_growth: float,
    years: int,
    payout: float,
    *,
    mid_year: bool = False,
) -> tuple[float, float, float]:
    """Return explicit PV, terminal PV, and equity value."""

    if cost_of_equity <= terminal_growth:
        raise ValueError("cost of equity must exceed terminal growth")
    if abs(growth - cost_of_equity) < 1e-12:
        explicit = payout * earnings0 * years
    else:
        ratio = (1.0 + growth) / (1.0 + cost_of_equity)
        explicit = (
            payout
            * earnings0
            * (1.0 + growth)
            / (cost_of_equity - growth)
            * (1.0 - ratio**years)
        )
    earnings_n = earnings0 * (1.0 + growth) ** years
    terminal_pv = (
        payout
        * earnings_n
        * (1.0 + terminal_growth)
        / (cost_of_equity - terminal_growth)
        / (1.0 + cost_of_equity) ** years
    )
    if mid_year:
        shift = (1.0 + cost_of_equity) ** 0.5
        explicit *= shift
        terminal_pv *= shift
    return explicit, terminal_pv, explicit + terminal_pv
