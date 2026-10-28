"""SVG cards stay well-formed and free of advice."""

from __future__ import annotations

import xml.etree.ElementTree as ET

from whats_priced_in import load_assumptions, load_example, solve_growth
from whats_priced_in.card import render_diff_card, render_growth_card
from whats_priced_in.earnings_assumption_diff import diff_assumptions


def test_growth_card_is_svg_and_states_the_growth():
    svg = render_growth_card(solve_growth(load_example("synth")))
    root = ET.fromstring(svg)
    assert root.tag == "{http://www.w3.org/2000/svg}svg"
    assert "7.17%" in svg
    assert "SYNTH" in svg
    assert "Not a recommendation" in svg
    assert "buy" not in svg.lower()
    assert "sell" not in svg.lower()


def test_diff_card_shows_both_growth_rates():
    result = diff_assumptions(
        load_assumptions("examples/diff/pre.yaml"),
        load_assumptions("examples/diff/post.yaml"),
    )
    svg = render_diff_card(result)
    ET.fromstring(svg)
    assert "7.17%" in svg
    assert "5.88%" in svg
    assert "Not a recommendation" in svg


def test_narmada_card_keeps_the_rupee_and_the_crore_scale():
    svg = render_growth_card(solve_growth(load_example("narmada")))
    ET.fromstring(svg)
    assert "12.92%" in svg
    assert "₹" in svg
    assert "crore" in svg
