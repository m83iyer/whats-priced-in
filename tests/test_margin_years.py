"""Margin path and horizon solves."""

from __future__ import annotations

from dataclasses import replace

import pytest

from whats_priced_in import solve_margin, solve_years, value_growth


def test_constant_margin_matches_the_linear_earnings_model(synth):
    full = value_growth(0.06, replace(synth, earnings=synth.revenue))
    expected = 150 / full.breakdown.equity_value
    solved = solve_margin(synth, revenue_growth=0.06)
    assert solved.constant is True
    assert solved.margin_end == pytest.approx(expected, abs=1e-9)
    assert solved.breakdown.equity_value == pytest.approx(150, abs=1e-6)
    assert solved.trailing_margin == pytest.approx(0.20)
    assert all(margin == pytest.approx(solved.margin_end) for margin in solved.margin_path)
    assert solved.breakdown.earnings_path[0] == pytest.approx(solved.revenue_path[0] * solved.margin_end)


def test_fade_runs_from_the_starting_margin_to_the_solved_one(synth):
    solved = solve_margin(synth, revenue_growth=0.06, margin_start=0.10)
    assert solved.constant is False
    assert solved.margin_path[0] == pytest.approx(0.10)
    assert solved.margin_path[-1] == pytest.approx(solved.margin_end)
    assert solved.breakdown.equity_value == pytest.approx(solved.target, abs=1e-6)
    assert solved.margin_end != pytest.approx(0.10)


def test_years_at_twelve_percent_clears_on_year_four(synth):
    solved = solve_years(synth, growth=0.12, max_years=12)
    assert solved.direction == "increasing"
    assert solved.identified is True
    assert solved.closest_years == 3
    assert solved.years_that_clear == 4
    assert solved.grid[2].equity_value == pytest.approx(146.5336, abs=1e-3)
    assert solved.grid[3].equity_value == pytest.approx(155.9258, abs=1e-3)


def test_equal_growth_does_not_identify_a_horizon(synth):
    solved = solve_years(synth, growth=synth.terminal_growth, max_years=6)
    assert solved.identified is False
    assert solved.direction == "flat"
    assert solved.years_that_clear is None
    assert "not identified" in solved.note
    values = [point.equity_value for point in solved.grid]
    assert max(values) - min(values) < 1e-8


def test_growth_below_terminal_makes_a_longer_horizon_worth_less(synth):
    solved = solve_years(synth, growth=0.02, max_years=8)
    assert solved.direction == "decreasing"
    assert solved.grid[0].equity_value > solved.grid[-1].equity_value
