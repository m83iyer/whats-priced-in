"""Yield, coverage, and the two Gordon identities."""

from __future__ import annotations

import pytest

from whats_priced_in import ModelError
from whats_priced_in.disclosure import REQUIRED_KEYS
from whats_priced_in.dividend import DividendCase, implied_dividend, load_dividend_example


def test_wharf_forward_reading():
    result = implied_dividend(load_dividend_example())
    assert result.yield_kind == "forward"
    assert result.cash_yield == pytest.approx(0.065)
    assert result.coverage == pytest.approx(8 / 6.5)
    assert result.payout == pytest.approx(6.5 / 8)
    assert result.implied_growth == pytest.approx(0.10 - 0.065)
    assert result.flat_perpetuity_value == pytest.approx(65)
    implied = next(row for row in result.scenarios if "implied by the price" in row.note)
    assert implied.model_value == pytest.approx(100)
    assert implied.versus_price == 0
    assert tuple(item.key for item in result.disclosure.items) == REQUIRED_KEYS
    assert "D1" in result.disclosure.text_for("terminal")
    assert "not applied" in result.disclosure.text_for("tax").lower() or "Tax is not applied" in result.disclosure.text_for("tax")


def test_trailing_identity_solves_back_to_the_price():
    result = implied_dividend(
        DividendCase(
            currency="AED",
            scale="unit",
            price=100,
            annual_dividend=5,
            dividend_timing="trailing",
            earnings=8,
            cost_of_equity=0.10,
        )
    )
    expected = (100 * 0.10 - 5) / (100 + 5)
    assert result.implied_growth == pytest.approx(expected, abs=1e-12)
    assert result.yield_kind == "trailing"
    implied = next(row for row in result.scenarios if "implied by the price" in row.note)
    assert implied.model_value == pytest.approx(100, abs=1e-8)


def test_uncovered_dividend_is_warned_and_implied_growth_can_be_negative():
    result = implied_dividend(
        DividendCase(
            currency="USD",
            scale="unit",
            price=100,
            annual_dividend=12,
            earnings=8,
            cost_of_equity=0.10,
        )
    )
    assert result.coverage < 1
    assert result.implied_growth < 0
    assert any("Coverage is below 1" in warning for warning in result.disclosure.warnings)
    assert any("negative" in warning for warning in result.disclosure.warnings)


def test_zero_dividend_cannot_explain_a_positive_price():
    with pytest.raises(ModelError, match="zero dividend"):
        implied_dividend(
            DividendCase(currency="USD", scale="unit", price=100, annual_dividend=0, cost_of_equity=0.10)
        )


def test_growth_at_or_above_the_discount_rate_is_blank():
    result = implied_dividend(
        DividendCase(
            currency="USD",
            scale="unit",
            price=100,
            annual_dividend=6.5,
            earnings=8,
            cost_of_equity=0.10,
            growth=0.15,
        )
    )
    row = next(item for item in result.scenarios if item.growth == pytest.approx(0.15))
    assert row.model_value is None
    assert "not defined" in row.note


def test_missing_cost_of_equity_still_reports_the_cash_yield():
    result = implied_dividend(
        DividendCase(currency="INR", scale="unit", price=80, annual_dividend=4, earnings=5)
    )
    assert result.cash_yield == pytest.approx(0.05)
    assert result.implied_growth is None
    assert result.coverage == pytest.approx(1.25)
    assert any("cost of equity" in warning.lower() for warning in result.disclosure.warnings)
