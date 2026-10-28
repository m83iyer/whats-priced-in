"""Fail if the documented numbers drift from the engine.

The closed form lives in tests/closed_form.py. The library discounts with a loop.
This script also checks that the README still quotes the formatted toy results,
and that the tree has not picked up a feed, a model call, or a real issuer pack.
"""

from __future__ import annotations

import json
import sys
from dataclasses import replace
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from tests.closed_form import closed_form_value  # noqa: E402

from whats_priced_in import (  # noqa: E402
    FORMULA,
    Assumptions,
    __version__,
    load_assumptions,
    load_example,
    solve_growth,
    solve_margin,
    value_growth,
)
from whats_priced_in._version import __version__ as version_module  # noqa: E402
from whats_priced_in.card import render_diff_card, render_growth_card  # noqa: E402
from whats_priced_in.dividend import implied_dividend, load_dividend_example  # noqa: E402
from whats_priced_in.earnings_assumption_diff import diff_assumptions  # noqa: E402
from whats_priced_in.formatting import (  # noqa: E402
    format_money,
    format_multiple,
    format_percent,
    format_pp,
)

SKIP_PARTS = {
    ".git",
    "uploads",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    ".venv",
    "venv",
    "dist",
    "build",
}
TEXT_SUFFIXES = {".py", ".md", ".yml", ".yaml", ".toml", ".json", ".txt"}


def run_checks() -> list[str]:
    failures: list[str] = []

    def need(condition: bool, message: str) -> None:
        if not condition:
            failures.append(message)

    audit = Assumptions(
        currency="USD",
        scale="unit",
        earnings=10,
        cost_of_equity=0.10,
        terminal_growth=0.03,
        years=5,
        payout=1.0,
        price=None,
    )
    explicit, terminal, total = closed_form_value(10, 0.08, 0.10, 0.03, 5, 1.0)
    valued = value_growth(0.08, audit)
    need(abs(valued.breakdown.explicit_pv - explicit) < 1e-9, "audit explicit PV drifted from the closed form")
    need(abs(valued.breakdown.terminal_pv - terminal) < 1e-9, "audit terminal PV drifted from the closed form")
    need(abs(valued.breakdown.equity_value - total) < 1e-9, "audit equity value drifted from the closed form")

    golden = json.loads((ROOT / "tests" / "fixtures" / "golden_synth.json").read_text(encoding="utf-8"))
    audit_file = golden["audit"]
    need(abs(explicit - audit_file["explicit_pv"]) < 1e-9, "closed form explicit PV drifted from golden_synth.json")
    need(abs(terminal - audit_file["terminal_pv"]) < 1e-9, "closed form terminal PV drifted from golden_synth.json")
    need(abs(total - audit_file["equity_value"]) < 1e-9, "closed form equity value drifted from golden_synth.json")

    gordon = 10 * 1.04 / (0.11 - 0.04)
    for years in (1, 5, 10, 20):
        collapsed = value_growth(
            0.04,
            replace(audit, cost_of_equity=0.11, terminal_growth=0.04, years=years),
        )
        need(
            abs(collapsed.breakdown.equity_value - gordon) < 1e-8,
            f"Gordon identity failed at {years} years",
        )

    synth = load_example("synth")
    solved = solve_growth(synth)
    need(
        abs(solved.implied_growth - golden["synth_implied_growth"]) < 1e-8,
        "SYNTH implied growth drifted from golden_synth.json",
    )
    at_golden_g = value_growth(golden["synth_implied_growth"], synth)
    need(
        abs(at_golden_g.breakdown.explicit_pv - golden["synth_explicit_pv"]) < 1e-6,
        "SYNTH explicit PV drifted",
    )
    need(
        abs(at_golden_g.breakdown.terminal_pv - golden["synth_terminal_pv"]) < 1e-6,
        "SYNTH terminal PV drifted",
    )
    need(
        abs(at_golden_g.breakdown.year_n_earnings - golden["synth_year_n_earnings"]) < 1e-6,
        "SYNTH year-10 earnings drifted",
    )

    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    margin = solve_margin(synth, revenue_growth=0.06)
    at_six = value_growth(0.06, synth)
    payout_60 = solve_growth(replace(synth, payout=0.6))
    coe_9 = solve_growth(replace(synth, cost_of_equity=0.09))
    coe_13 = solve_growth(replace(synth, cost_of_equity=0.13))
    narmada = solve_growth(load_example("narmada"))
    creek = solve_growth(load_example("creek"))
    pre = load_assumptions(ROOT / "examples" / "diff" / "pre.yaml")
    post = load_assumptions(ROOT / "examples" / "diff" / "post.yaml")
    diff = diff_assumptions(pre, post)
    dividend = implied_dividend(load_dividend_example())
    per_share = True

    required = {
        "formula": FORMULA,
        "synth growth": format_percent(solved.implied_growth),
        "explicit": format_money(solved.breakdown.explicit_pv, "USD", "unit", per_share=per_share),
        "terminal": format_money(solved.breakdown.terminal_pv, "USD", "unit", per_share=per_share),
        "terminal share": format_percent(solved.breakdown.terminal_share),
        "year 10": format_money(solved.breakdown.year_n_earnings, "USD", "unit", per_share=per_share),
        "value at 6%": format_money(at_six.breakdown.equity_value, "USD", "unit", per_share=per_share),
        "margin": format_percent(margin.margin_end),
        "payout 60": format_percent(payout_60.implied_growth),
        "coe 9": format_percent(coe_9.implied_growth),
        "coe 13": format_percent(coe_13.implied_growth),
        "narmada": format_percent(narmada.implied_growth),
        "creek": format_percent(creek.implied_growth),
        "post growth": format_percent(diff.implied_growth_after),
        "growth delta": format_pp(diff.delta_implied_growth),
        "post value": format_money(diff.value_after, "USD", "unit", per_share=per_share),
        "audit value": format_money(total, "USD", "unit", per_share=per_share),
        "forward yield": format_percent(dividend.cash_yield),
        "coverage": format_multiple(dividend.coverage or 0),
        "dividend payout": format_percent(dividend.payout or 0),
        "dividend growth": format_percent(0 if dividend.implied_growth is None else dividend.implied_growth),
        "flat value": format_money(
            0 if dividend.flat_perpetuity_value is None else dividend.flat_perpetuity_value,
            "USD",
            "unit",
            per_share=per_share,
        ),
    }
    for label, text in required.items():
        need(text in readme, f"README is missing {label}: {text}")

    for phrase in ("Not a recommendation", "MIT", "Manoj", "miyer83", "examples/diff"):
        need(phrase in readme, f"README is missing {phrase!r}")

    card = render_growth_card(solved)
    need("7.17%" in card or format_percent(solved.implied_growth) in card, "growth card is missing the implied growth")
    need("Not a recommendation" in card, "growth card dropped the recommendation line")
    need("buy" not in card.lower(), "growth card contains 'buy'")
    need(
        card.index(format_percent(solved.implied_growth)) < card.index("Key assumptions"),
        "growth card does not place key assumptions after the answer",
    )
    diff_card = render_diff_card(diff)
    need(format_percent(diff.implied_growth_after) in diff_card, "diff card is missing the post implied growth")
    need(
        diff_card.index(format_percent(diff.implied_growth_after)) < diff_card.index("Key assumptions"),
        "diff card does not place key assumptions after the answer",
    )
    for label in ("Key assumptions", "basis", "payout", "terminal", "timing", "tax", "scale"):
        need(label in card, f"growth card is missing {label}")
        need(label in diff_card, f"diff card is missing {label}")

    receipts_path = ROOT / "docs" / "LAUNCH_RECEIPTS.md"
    need(receipts_path.is_file(), "docs/LAUNCH_RECEIPTS.md is missing")
    if receipts_path.is_file():
        receipts = receipts_path.read_text(encoding="utf-8")
        receipt_bits = {
            "synth growth": format_percent(solved.implied_growth),
            "explicit": format_money(solved.breakdown.explicit_pv, "USD", "unit", per_share=per_share),
            "terminal pv": format_money(solved.breakdown.terminal_pv, "USD", "unit", per_share=per_share),
            "terminal share": format_percent(solved.breakdown.terminal_share),
            "margin": format_percent(margin.margin_end),
            "post growth": format_percent(diff.implied_growth_after),
            "growth delta": format_pp(diff.delta_implied_growth),
            "post value": format_money(diff.value_after, "USD", "unit", per_share=per_share),
            "narmada": format_percent(narmada.implied_growth),
            "creek": format_percent(creek.implied_growth),
            "forward yield": format_percent(dividend.cash_yield),
            "dividend growth": format_percent(0 if dividend.implied_growth is None else dividend.implied_growth),
            "key assumptions": "Key assumptions",
            "basis": "basis",
            "payout": "payout",
            "terminal label": "terminal",
            "timing": "timing",
            "tax": "tax",
            "scale": "scale",
            "live data": "LiveDataNotImplemented",
            "license": "LICENSE",
            "years mode": "solve --mode years",
            "yield mode": "solve --mode yield",
            "value command": "value --growth 0.06",
            "sensitivity command": "--parameter cost_of_equity",
            "json solve": "solve -f examples/synth.yaml --json",
            "json key": '"key_assumptions"',
            "json diff keys": "key_assumptions_before",
            "svg card": "<svg",
            "library print": "print(result)",
            "library field": "result.key_assumptions",
        }
        for label, text in receipt_bits.items():
            need(text in receipts, f"LAUNCH_RECEIPTS.md is missing {label}: {text}")

    pyproject = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    need(f'version = "{__version__}"' in pyproject, "pyproject version drifted from the package")
    need(__version__ == version_module, "package version imports drifted")

    for path in _text_files():
        text = path.read_text(encoding="utf-8", errors="replace")
        relative = path.relative_to(ROOT).as_posix()
        if relative == "check.py":
            continue
        lowered = text.lower()
        if "groww" in lowered:
            failures.append(f"{relative}: contains Groww")
        if "lorem ipsum" in lowered:
            failures.append(f"{relative}: placeholder copy")
        # The checker names the bans. Don't fail it for quoting them.
        if relative != "check.py":
            for phrase in ("you should buy", "you should sell", "strong buy", "price target", "guaranteed return"):
                if phrase in lowered:
                    failures.append(f"{relative}: contains {phrase!r}")
            for needle in (
                "import urllib",
                "import requests",
                "import httpx",
                "import socket",
                "openai",
                "anthropic",
                "langchain",
                "/workspace",
            ):
                if needle in lowered:
                    failures.append(f"{relative}: contains {needle!r}")
        if path.name not in {"fetchers.py", "check.py"} and ("TODO" in text or "FIXME" in text):
            failures.append(f"{relative}: unfinished marker outside fetchers.py")
    return failures


def _text_files():
    for path in ROOT.rglob("*"):
        if not path.is_file():
            continue
        if any(part in SKIP_PARTS or part.endswith(".egg-info") for part in path.parts):
            continue
        if path.suffix.lower() in TEXT_SUFFIXES:
            yield path


def main() -> int:
    failures = run_checks()
    for item in failures:
        print("XX", item)
    if failures:
        print(f"MISMATCH ({len(failures)})")
        return 1
    print("ALL MATCH")
    return 0


if __name__ == "__main__":
    sys.exit(main())
