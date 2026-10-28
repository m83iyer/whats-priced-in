"""Every answer path states the six key assumptions beside the figure."""

from __future__ import annotations

from dataclasses import replace

from whats_priced_in import load_assumptions, load_example, solve_growth, solve_margin, solve_years, value_growth
from whats_priced_in.cli import main
from whats_priced_in.card import render_diff_card, render_growth_card
from whats_priced_in.dividend import implied_dividend, load_dividend_example
from whats_priced_in.earnings_assumption_diff import diff_assumptions
from whats_priced_in.formatting import (
    KEY_ASSUMPTION_LABELS,
    diff_payload,
    dividend_payload,
    format_diff,
    format_dividend,
    format_margin,
    format_sensitivity,
    format_solve_growth,
    format_valuation,
    format_years,
    growth_payload,
    margin_payload,
    sensitivity_payload,
    valuation_payload,
    years_payload,
)
from whats_priced_in.sensitivity import implied_growth_sensitivity, value_sensitivity


def _labels_in_block(text: str, headline: str) -> list[str]:
    start = text.index(headline)
    assumptions_at = text.index("Key assumptions", start)
    disclosure_at = text.index("Disclosure", assumptions_at)
    block = text[assumptions_at:disclosure_at]
    starters = []
    for line in block.splitlines():
        if not line or line == "Key assumptions" or line.startswith("assumption"):
            continue
        starters.append(line.split("  ")[0].strip())
    return starters


def _require(text: str, headline: str) -> None:
    assert text.index(headline) < text.index("Key assumptions")
    assert text.index("Key assumptions") < text.index("Disclosure")
    starters = _labels_in_block(text, headline)
    for label in KEY_ASSUMPTION_LABELS:
        assert label in starters


def test_growth_value_margin_and_years_place_the_six_labels_before_the_essay():
    synth = load_example("synth")
    growth = solve_growth(synth)
    assert str(growth) == format_solve_growth(growth)[:-1]
    _require(str(growth), "Implied constant growth")
    assert "7.17%" in str(growth)

    valued = value_growth(0.06, synth)
    assert str(valued) == format_valuation(valued)[:-1]
    _require(str(valued), "Model value")
    assert "$137.60" in str(valued)

    margin = solve_margin(synth, revenue_growth=0.06)
    assert str(margin) == format_margin(margin)[:-1]
    _require(str(margin), "Constant margin")
    assert "21.80%" in str(margin)
    assert margin.key_assumptions["revenue growth"] == "6.00%"

    years = solve_years(synth, growth=0.12)
    assert str(years) == format_years(years)[:-1]
    _require(str(years), "Closest horizon")
    assert years.key_assumptions["growth held fixed"] == "12.00%"


def test_yield_and_sensitivity_place_the_six_labels_before_the_essay():
    dividend = implied_dividend(load_dividend_example())
    assert str(dividend) == format_dividend(dividend)[:-1]
    _require(str(dividend), "Forward yield")
    assert dividend.key_assumptions["terminal"] == "growing perpetuity, no explicit horizon"
    assert "3.50%" in str(dividend)

    synth = load_example("synth")
    tables = [value_sensitivity(synth), implied_growth_sensitivity(synth, "cost_of_equity", (0.09, 0.13))]
    text = format_sensitivity(tables)
    assert str(tables[0]) == format_sensitivity([tables[0]])[:-1]
    _require(text, "what's priced in")
    assert text.index("Key assumptions") < text.index("Value if growth")


def test_diff_table_keeps_both_sides_next_to_the_growth_delta():
    result = diff_assumptions(
        load_assumptions("examples/diff/pre.yaml"),
        load_assumptions("examples/diff/post.yaml"),
    )
    text = format_diff(result)
    assert str(result) == text[:-1]
    _require(text, "implied growth")
    assert "5.88%" in text
    assert result.key_assumptions["before"]["earnings"] == "$8.00"
    assert result.key_assumptions["after"]["earnings"] == "$8.80"
    assert result.key_assumptions["before"]["basis"] == result.key_assumptions["after"]["basis"] == "FCFE"
    for label in KEY_ASSUMPTION_LABELS:
        assert label in result.key_assumptions["before"]
        assert label in result.key_assumptions["after"]

    mismatched = diff_assumptions(load_example("synth"), replace(load_example("synth"), currency="INR"))
    mismatched_text = format_diff(mismatched)
    _require(mismatched_text, "implied growth")
    assert "Value delta is blank" in mismatched_text


def test_json_puts_key_assumptions_beside_the_answer_field():
    synth = load_example("synth")
    growth = growth_payload(solve_growth(synth))
    assert list(growth).index("key_assumptions") == list(growth).index("implied_growth") + 1

    valued = valuation_payload(value_growth(0.06, synth))
    assert list(valued).index("key_assumptions") == list(valued).index("equity_value") + 1

    margin = margin_payload(solve_margin(synth, revenue_growth=0.06))
    assert list(margin).index("key_assumptions") == list(margin).index("margin_end") + 1

    years = years_payload(solve_years(synth, growth=0.12))
    assert list(years).index("key_assumptions") == list(years).index("closest_years") + 1

    dividend = dividend_payload(implied_dividend(load_dividend_example()))
    assert list(dividend).index("key_assumptions") == list(dividend).index("implied_growth") + 1

    sens = sensitivity_payload([value_sensitivity(synth)])
    assert list(sens).index("key_assumptions") < list(sens).index("tables")

    diff = diff_payload(
        diff_assumptions(
            load_assumptions("examples/diff/pre.yaml"),
            load_assumptions("examples/diff/post.yaml"),
        )
    )
    order = list(diff)
    assert order.index("key_assumptions_before") == order.index("delta_implied_growth") + 1
    assert order.index("key_assumptions_after") == order.index("key_assumptions_before") + 1

    for payload in (growth, valued, margin, years, dividend, sens):
        for label in KEY_ASSUMPTION_LABELS:
            assert label in payload["key_assumptions"]


def test_cards_repeat_the_six_labels_after_the_figure():
    solved = solve_growth(load_example("synth"))
    svg = render_growth_card(solved)
    assert svg.index("7.17%") < svg.index("Key assumptions")
    start = svg.index("Key assumptions")
    block = svg[start: svg.index("Not a recommendation", start)]
    for label in KEY_ASSUMPTION_LABELS:
        assert label in block
    assert "buy" not in svg.lower()
    assert "sell" not in svg.lower()

    diff = diff_assumptions(
        load_assumptions("examples/diff/pre.yaml"),
        load_assumptions("examples/diff/post.yaml"),
    )
    diff_svg = render_diff_card(diff)
    assert diff_svg.index("5.88%") < diff_svg.index("Key assumptions")
    diff_start = diff_svg.index("Key assumptions")
    diff_block = diff_svg[diff_start: diff_svg.index("Not a recommendation", diff_start)]
    for label in KEY_ASSUMPTION_LABELS:
        assert label in diff_block
    assert "$8.00 → $8.80" in diff_block or "$8.00 → $8.80" in diff_svg


def test_card_command_prints_the_six_labels_before_the_path(tmp_path, capsys):
    destination = tmp_path / "synth-card.svg"
    assert main(["card", "--example", "synth", "-o", str(destination)]) == 0
    out = capsys.readouterr().out
    assert "7.17%" in out
    assert "$66.30" in out
    assert out.index("Key assumptions") < out.index("Disclosure")
    assert out.index("Disclosure") < out.index("Card written to")
    block = out[out.index("Key assumptions"): out.index("Disclosure")]
    for label in KEY_ASSUMPTION_LABELS:
        assert label in block
    svg = destination.read_text(encoding="utf-8")
    assert "Key assumptions" in svg
    assert "$66.30" in svg
    assert "55.80%" in svg
