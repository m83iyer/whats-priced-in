"""CLI wiring. The numbers themselves are pinned in test_dcf and check.py."""

from __future__ import annotations

import json
import subprocess
import sys
from importlib.metadata import entry_points

import pytest

from whats_priced_in.cli import main
from whats_priced_in.disclosure import REQUIRED_KEYS


def test_console_scripts_are_registered():
    names = {item.name for item in entry_points(group="console_scripts")}
    assert "wpi" in names
    assert "whats-priced-in" in names


def test_solve_prints_the_growth_and_the_disclosure(capsys):
    assert main(["solve", "-f", "examples/synth.yaml"]) == 0
    out = capsys.readouterr().out
    assert "7.17%" in out
    assert "$66.30" in out
    assert "$83.70" in out
    assert "55.80%" in out
    assert "Recorded, not used in this solve" in out
    for key in REQUIRED_KEYS:
        assert key in out
    assert "Not a recommendation" in out
    assert "retained earnings" in out


def test_solve_json_round_trip(capsys):
    assert main(["solve", "--example", "synth", "--json"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["model"] == "two_stage_fcfe_gordon"
    assert payload["mode"] == "growth"
    assert payload["implied_growth"] == pytest.approx(0.07174705988709823, abs=1e-8)
    assert {item["key"] for item in payload["disclosure"]["items"]} == set(REQUIRED_KEYS)
    assert payload["warnings"] == payload["disclosure"]["warnings"]
    assert payload["warnings"]


def test_margin_years_and_yield_commands(capsys):
    assert main(["solve", "--mode", "margin", "-f", "examples/synth.yaml", "--revenue-growth", "0.06"]) == 0
    assert "21.80%" in capsys.readouterr().out

    assert main(["solve", "--mode", "years", "-f", "examples/synth.yaml", "--growth", "0.12"]) == 0
    years = capsys.readouterr().out
    assert "3 years" in years
    assert "4 years" in years

    assert main(["solve", "--mode", "yield", "-f", "examples/dividend.yaml"]) == 0
    yield_out = capsys.readouterr().out
    assert "6.50%" in yield_out
    assert "3.50%" in yield_out
    assert "1.23x" in yield_out
    assert "tax" in yield_out


def test_narmada_prints_rupees_and_crore(capsys):
    assert main(["solve", "-f", "examples/narmada.yaml"]) == 0
    out = capsys.readouterr().out
    assert "12.92%" in out
    assert "₹" in out
    assert "crore" in out


def test_creek_has_no_unfunded_growth_warning(capsys):
    assert main(["solve", "-f", "examples/creek.yaml"]) == 0
    out = capsys.readouterr().out
    assert "5.24%" in out
    assert "AED" in out
    assert "Warnings\n  none" in out


def test_value_sens_and_diff(capsys):
    assert main(["value", "--growth", "0.06", "-f", "examples/synth.yaml"]) == 0
    assert "$137.60" in capsys.readouterr().out

    assert main(["sens", "-f", "examples/synth.yaml"]) == 0
    sens = capsys.readouterr().out
    assert "$137.60" in sens
    assert "2.68%" in sens
    assert "11.01%" in sens

    assert main(["diff", "examples/diff/pre.yaml", "examples/diff/post.yaml"]) == 0
    diff = capsys.readouterr().out
    assert "5.88%" in diff
    assert "-1.30 pp" in diff
    assert "$165.00" in diff
    assert "disclosed only" in diff
    assert "moves implied growth" in diff


def test_flags_without_a_file(capsys):
    code = main(
        [
            "solve",
            "--ticker",
            "SYNTH",
            "--currency",
            "USD",
            "--scale",
            "unit",
            "--price",
            "150",
            "--earnings",
            "8",
            "--cost-of-equity",
            "0.11",
            "--terminal-growth",
            "0.04",
            "--years",
            "10",
            "--payout",
            "1",
            "--basis",
            "fcfe",
        ]
    )
    assert code == 0
    assert "7.17%" in capsys.readouterr().out


def test_whole_number_percent_is_rejected(capsys):
    code = main(
        [
            "solve",
            "--currency",
            "USD",
            "--scale",
            "unit",
            "--earnings",
            "8",
            "--price",
            "150",
            "--cost-of-equity",
            "11",
            "--terminal-growth",
            "0.04",
        ]
    )
    captured = capsys.readouterr()
    assert code == 1
    assert "decimal" in captured.err


def test_missing_currency_is_rejected(capsys):
    code = main(["solve", "--earnings", "8", "--price", "150", "--cost-of-equity", "0.11", "--terminal-growth", "0.04"])
    captured = capsys.readouterr()
    assert code == 1
    assert "--currency" in captured.err


def test_card_and_module_entrypoint(tmp_path, capsys):
    destination = tmp_path / "card.svg"
    assert main(["card", "--example", "synth", "-o", str(destination)]) == 0
    text = destination.read_text(encoding="utf-8")
    assert text.startswith("<svg")
    assert "7.17%" in text
    assert "Card written to" in capsys.readouterr().out

    completed = subprocess.run(
        [sys.executable, "-m", "whats_priced_in", "solve", "--example", "creek", "--json"],
        check=True,
        capture_output=True,
        text=True,
    )
    payload = json.loads(completed.stdout)
    assert payload["currency"] == "AED"
    assert payload["implied_growth"] == pytest.approx(0.052425073343826775, abs=1e-8)


def test_version_and_help():
    with pytest.raises(SystemExit) as exc:
        main(["--version"])
    assert exc.value.code == 0
    assert main([]) == 2
