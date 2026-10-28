"""Loop versus closed form, and the identities the model has to keep."""

from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path

import pytest

from tests.closed_form import closed_form_value
from whats_priced_in import Assumptions, ModelError, load_example, solve_growth, value_growth
from whats_priced_in.disclosure import REQUIRED_KEYS, UNFUNDED_GROWTH
from whats_priced_in.scales import SCALE_FACTORS

GOLDEN = json.loads(Path("tests/fixtures/golden_synth.json").read_text(encoding="utf-8"))


def test_audit_case_matches_closed_form_and_golden_file():
    assumptions = Assumptions(
        currency="USD",
        scale="unit",
        earnings=10,
        cost_of_equity=0.10,
        terminal_growth=0.03,
        years=5,
        payout=1.0,
    )
    explicit, terminal, total = closed_form_value(10, 0.08, 0.10, 0.03, 5, 1.0)
    valued = value_growth(0.08, assumptions)
    assert valued.breakdown.explicit_pv == pytest.approx(explicit, abs=1e-9)
    assert valued.breakdown.terminal_pv == pytest.approx(terminal, abs=1e-9)
    assert valued.breakdown.equity_value == pytest.approx(total, abs=1e-9)
    assert explicit == pytest.approx(GOLDEN["audit"]["explicit_pv"], abs=1e-9)
    assert terminal == pytest.approx(GOLDEN["audit"]["terminal_pv"], abs=1e-9)
    assert total == pytest.approx(GOLDEN["audit"]["equity_value"], abs=1e-9)
    assert valued.breakdown.equity_value == pytest.approx(181.58184042854214, abs=1e-9)


def test_gordon_identity_when_growth_equals_terminal():
    gordon = 10 * 1.04 / (0.11 - 0.04)
    for years in (1, 3, 5, 10, 20):
        valued = value_growth(
            0.04,
            Assumptions(
                currency="USD",
                scale="unit",
                earnings=10,
                cost_of_equity=0.11,
                terminal_growth=0.04,
                years=years,
                payout=1.0,
            ),
        )
        assert valued.breakdown.equity_value == pytest.approx(gordon, abs=1e-8)


def test_growth_equal_to_cost_of_equity_uses_the_flat_sum():
    # Each discounted cash flow is the starting earnings when g == r.
    earnings0, years, payout, cost, terminal = 10.0, 5, 1.0, 0.10, 0.03
    explicit = payout * earnings0 * years
    terminal_pv = payout * earnings0 * (1 + terminal) / (cost - terminal)
    valued = value_growth(
        cost,
        Assumptions(
            currency="INR",
            scale="lakh",
            earnings=earnings0,
            cost_of_equity=cost,
            terminal_growth=terminal,
            years=years,
            payout=payout,
        ),
    )
    assert valued.breakdown.explicit_pv == pytest.approx(explicit, abs=1e-9)
    assert valued.breakdown.terminal_pv == pytest.approx(terminal_pv, abs=1e-9)


def test_closed_form_matches_when_growth_exceeds_the_discount_rate():
    explicit, terminal, total = closed_form_value(8, 0.15, 0.10, 0.03, 5, 0.8)
    valued = value_growth(
        0.15,
        Assumptions(
            currency="AED",
            scale="million",
            earnings=8,
            cost_of_equity=0.10,
            terminal_growth=0.03,
            years=5,
            payout=0.8,
        ),
    )
    assert valued.breakdown.equity_value == pytest.approx(total, abs=1e-8)
    assert valued.breakdown.explicit_pv == pytest.approx(explicit, abs=1e-8)
    assert valued.breakdown.terminal_pv == pytest.approx(terminal, abs=1e-8)


def test_synth_implied_growth_is_frozen():
    solved = solve_growth(load_example("synth"))
    assert solved.implied_growth == pytest.approx(GOLDEN["synth_implied_growth"], abs=1e-8)
    assert solved.breakdown.equity_value == pytest.approx(150, abs=1e-6)
    assert solved.breakdown.explicit_pv == pytest.approx(GOLDEN["synth_explicit_pv"], abs=1e-4)
    assert solved.breakdown.terminal_pv == pytest.approx(GOLDEN["synth_terminal_pv"], abs=1e-4)
    assert abs(solved.breakdown.equity_value - solved.target) < 1e-6


def test_value_is_linear_in_earnings_and_payout(synth):
    low = value_growth(0.05, replace(synth, earnings=8))
    high = value_growth(0.05, replace(synth, earnings=16))
    assert high.breakdown.equity_value == pytest.approx(2 * low.breakdown.equity_value, abs=1e-8)
    half = value_growth(0.05, replace(synth, payout=0.5))
    assert half.breakdown.equity_value == pytest.approx(0.5 * low.breakdown.equity_value, abs=1e-8)


def test_partials_move_in_the_expected_direction(synth):
    base = value_growth(0.05, synth).breakdown.equity_value
    assert value_growth(0.07, synth).breakdown.equity_value > base
    richer = replace(synth, cost_of_equity=0.13)
    assert value_growth(0.05, richer).breakdown.equity_value < base
    longer_terminal = replace(synth, terminal_growth=0.05)
    assert value_growth(0.05, longer_terminal).breakdown.equity_value > base


def test_mid_year_is_the_year_end_value_shifted_half_a_year():
    assumptions = Assumptions(
        currency="USD",
        scale="unit",
        earnings=10,
        cost_of_equity=0.10,
        terminal_growth=0.03,
        years=5,
        payout=1.0,
    )
    end = value_growth(0.08, assumptions)
    mid = value_growth(0.08, replace(assumptions, discount_convention="mid_year"))
    assert mid.breakdown.equity_value == pytest.approx(
        end.breakdown.equity_value * (1.10**0.5), abs=1e-9
    )
    assert mid.breakdown.terminal_share == pytest.approx(end.breakdown.terminal_share, abs=1e-12)


def test_round_trip_solve_on_several_growth_rates(synth):
    base = replace(synth, earnings=10, cost_of_equity=0.12, terminal_growth=0.03, years=8, payout=0.7)
    for growth in (0.0, 0.03, 0.08, 0.15, -0.02):
        price = value_growth(growth, base).breakdown.equity_value
        solved = solve_growth(replace(base, price=price))
        assert solved.implied_growth == pytest.approx(growth, abs=1e-8)


def test_tax_rate_and_basis_and_revenue_do_not_move_implied_growth(synth):
    base = solve_growth(synth).implied_growth
    assert solve_growth(replace(synth, tax_rate=0.35)).implied_growth == base
    assert solve_growth(replace(synth, earnings_basis="pat")).implied_growth == base
    assert solve_growth(replace(synth, revenue=999)).implied_growth == base


def test_mid_year_implied_growth_is_lower_than_year_end(synth):
    end = solve_growth(synth).implied_growth
    mid = solve_growth(replace(synth, discount_convention="mid_year")).implied_growth
    assert mid < end


def test_disclosure_always_has_the_six_keys_and_the_payout_warning(synth):
    solved = solve_growth(synth)
    assert tuple(item.key for item in solved.disclosure.items) == REQUIRED_KEYS
    assert UNFUNDED_GROWTH in solved.disclosure.warnings
    assert "not reapplied" in solved.disclosure.text_for("tax")
    creek = solve_growth(load_example("creek"))
    assert creek.disclosure.warnings == ()
    assert "AED" in creek.disclosure.text_for("scale")


def test_pat_full_payout_is_stated_on_the_narmada_case():
    solved = solve_growth(load_example("narmada"))
    assert "PAT is treated as fully distributable" in solved.disclosure.text_for("payout")
    assert UNFUNDED_GROWTH in solved.disclosure.warnings


def test_per_share_conversion_preserves_implied_growth():
    aggregate = load_example("narmada")
    from whats_priced_in import as_per_share

    per_share = as_per_share(aggregate)
    assert per_share.earnings == pytest.approx(8)
    assert per_share.price == pytest.approx(200)
    assert per_share.scale == "unit"
    assert per_share.shares is None
    assert solve_growth(aggregate).implied_growth == pytest.approx(
        solve_growth(per_share).implied_growth, abs=1e-12
    )


def test_inconsistent_market_cap_names_the_scale():
    narmada = load_example("narmada")
    with pytest.raises(ModelError, match="crore"):
        solve_growth(replace(narmada, market_cap=21_000))


def test_rejected_inputs(synth):
    with pytest.raises(ModelError, match="decimal"):
        solve_growth(replace(synth, cost_of_equity=11))
    with pytest.raises(ModelError, match="exceed terminal"):
        solve_growth(replace(synth, terminal_growth=0.2))
    with pytest.raises(ModelError, match="Payout is zero"):
        solve_growth(replace(synth, payout=0))
    with pytest.raises(ModelError, match="positive earnings"):
        solve_growth(replace(synth, earnings=-5))
    with pytest.raises(ModelError, match="search"):
        solve_growth(replace(synth, price=0.5))
    with pytest.raises(ModelError, match="Unknown scale"):
        value_growth(0.05, replace(synth, scale="arab"))
    with pytest.raises(ModelError, match="three-letter"):
        value_growth(0.05, replace(synth, currency="US"))


def test_currency_is_not_welded_to_a_scale():
    solved = solve_growth(
        Assumptions(
            currency="INR",
            scale="million",
            earnings=10,
            cost_of_equity=0.12,
            terminal_growth=0.04,
            price=80,
            years=8,
            payout=0.5,
        )
    )
    assert "INR" in solved.disclosure.text_for("scale")
    assert "million" in solved.disclosure.text_for("scale")
    assert SCALE_FACTORS["crore"] == 100 * SCALE_FACTORS["lakh"] == 10_000_000


def test_year_one_earnings_are_the_base_grown_once(synth):
    valued = value_growth(0.08, synth)
    assert valued.breakdown.earnings_path[0] == pytest.approx(8 * 1.08)
    assert valued.breakdown.cashflow_path[0] == pytest.approx(valued.breakdown.earnings_path[0])
