import math
from pathlib import Path

import pytest

from whats_priced_in import Assumptions, SCALE_FACTORS, load_example, solve_growth, value_growth
from whats_priced_in.fetchers import (
    LiveDataNotImplemented,
    fetch_dfm_quote,
    fetch_edgar_companyfacts,
    fetch_nse_quote,
)
from whats_priced_in.model import present_value


def test_scale_factor_is_not_applied_to_market_cap():
    india = load_example("narmada")
    assert SCALE_FACTORS["crore"] == 10_000_000
    assert india.target() == 20_000
    assert solve_growth(india).payload["target"] == 20_000


def test_tax_rate_does_not_move_the_value():
    synth = load_example("synth")
    base = value_growth(0.06, synth).valuation.equity_value
    other = value_growth(0.06, synth.replace(tax_rate=0.99)).valuation.equity_value
    assert base == other


def test_mid_year_multiplies_by_sqrt_one_plus_r():
    synth = load_example("synth")
    year_end = value_growth(0.06, synth).valuation.equity_value
    mid = value_growth(0.06, synth.replace(discount_convention="mid_year")).valuation.equity_value
    assert math.isclose(mid, year_end * (1.11 ** 0.5), rel_tol=1e-12)


def test_percent_cost_of_equity_is_rejected():
    with pytest.raises(ValueError, match="0.11"):
        Assumptions(
            ticker="SYNTH",
            currency="USD",
            scale="unit",
            price=150,
            earnings=8,
            cost_of_equity=11,
            terminal_growth=0.04,
        )


def test_gordon_identity_is_independent_of_horizon():
    gordon = 10 * 1.03 / (0.10 - 0.03)
    for years in (1, 5, 10, 30):
        value = present_value(10, 0.03, 0.10, 0.03, years, 1.0).equity_value
        assert math.isclose(value, gordon, rel_tol=1e-9)


def test_fetchers_do_not_call_the_network():
    source = Path("whats_priced_in/fetchers.py").read_text(encoding="utf-8")
    assert "urllib" not in source
    assert "requests" not in source
    for call in (
        lambda: fetch_nse_quote("NARMADA"),
        lambda: fetch_edgar_companyfacts("0000000000"),
        lambda: fetch_dfm_quote("CREEK"),
    ):
        with pytest.raises(LiveDataNotImplemented) as caught:
            call()
        assert "network" in str(caught.value)


def test_library_print_states_key_assumptions():
    result = solve_growth(
        Assumptions(
            ticker="SYNTH",
            currency="USD",
            scale="unit",
            price=150,
            earnings=8,
            cost_of_equity=0.11,
            terminal_growth=0.04,
            years=10,
            payout=1.0,
            earnings_basis="fcfe",
            tax_rate=0.21,
        )
    )
    assert math.isclose(result.implied_growth, 0.07174705988709829, rel_tol=1e-9, abs_tol=1e-12)
    text = str(result)
    assert "Key assumptions" in text
    assert "basis" in result.disclosure and "scale" in result.disclosure
    assert "Synthetic Holdings" not in text
