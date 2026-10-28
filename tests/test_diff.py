"""Pre/post earnings diffs."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pytest

from whats_priced_in import ModelError, load_assumptions, load_example
from whats_priced_in.earnings_assumption_diff import diff_assumptions


def test_documented_fixture_moves_growth_and_not_the_revenue_label():
    pre = load_assumptions(Path("examples/diff/pre.yaml"))
    post = load_assumptions(Path("examples/diff/post.yaml"))
    assert pre == load_example("synth")
    result = diff_assumptions(pre, post)
    fields = {change.field: change for change in result.changes}
    assert set(fields) == {"earnings", "revenue"}
    assert fields["earnings"].affects_implied_growth is True
    assert fields["revenue"].affects_implied_growth is False
    assert result.implied_growth_after == pytest.approx(0.05877389163834999, abs=1e-8)
    assert result.delta_implied_growth < 0
    assert result.value_before == pytest.approx(150, abs=1e-6)
    assert result.value_after == pytest.approx(165, abs=1e-6)
    assert result.delta_value == pytest.approx(15, abs=1e-6)
    assert result.values_comparable is True


def test_tax_change_is_disclosed_and_does_not_move_growth(synth):
    result = diff_assumptions(synth, replace(synth, tax_rate=0.30))
    assert result.delta_implied_growth == pytest.approx(0, abs=1e-15)
    change = next(item for item in result.changes if item.field == "tax_rate")
    assert change.affects_implied_growth is False
    assert "21" in result.disclosure_before.text_for("tax") or "21.00%" in result.disclosure_before.text_for("tax")
    assert result.disclosure_before.items != result.disclosure_after.items


def test_currency_label_does_not_move_growth_and_blocks_the_value_delta(synth):
    result = diff_assumptions(synth, replace(synth, currency="INR"))
    assert result.delta_implied_growth == pytest.approx(0, abs=1e-15)
    assert result.values_comparable is False
    assert result.delta_value is None
    assert any(change.field == "currency" and not change.affects_implied_growth for change in result.changes)


def test_unknown_yaml_field_is_rejected(tmp_path):
    path = tmp_path / "bad.yaml"
    path.write_text("ticker: NOPE\nfoo: 1\n", encoding="utf-8")
    with pytest.raises(ModelError, match="Unknown fields"):
        load_assumptions(path)


def test_price_override_applies_to_both_sides(synth):
    other = replace(synth, earnings=8.8)
    result = diff_assumptions(synth, other, price=160)
    assert result.before.price == 160
    assert result.after.price == 160
    assert result.target_before == 160
    assert result.value_before == pytest.approx(160, abs=1e-5)
