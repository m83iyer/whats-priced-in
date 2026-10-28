"""Recompute the README figures and the audit case.

The audit value is a closed form. It does not call the library year loop.
"""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from whats_priced_in import (  # noqa: E402
    Assumptions,
    load_assumptions,
    load_example,
    solve_growth,
    solve_margin,
    solve_years,
    value_growth,
)
from whats_priced_in.card import growth_svg  # noqa: E402
from whats_priced_in.dividend import implied_dividend, load_dividend_example  # noqa: E402
from whats_priced_in.earnings_assumption_diff import diff_assumptions  # noqa: E402
from whats_priced_in.model import present_value  # noqa: E402


def closed_form(earnings, growth, cost, terminal, years, payout):
    """Gordon two-stage value without the library's year loop."""
    if cost <= terminal:
        raise ValueError("Terminal growth must be below the cost of equity.")
    if abs(growth - terminal) < 1e-15:
        return payout * earnings * (1 + growth) / (cost - growth)
    annuity = payout * earnings * (1 + growth) / (cost - growth) * (1 - ((1 + growth) / (1 + cost)) ** years)
    terminal_value = (
        payout * earnings * (1 + growth) ** years * (1 + terminal) / ((cost - terminal) * (1 + cost) ** years)
    )
    return annuity + terminal_value


def main():
    readme = (ROOT / "README.md").read_text()
    golden = json.loads((ROOT / "tests" / "fixtures" / "golden_synth.json").read_text())
    failures = []

    def expect(label, condition):
        if not condition:
            failures.append(label)

    synth = load_example("synth")
    growth = solve_growth(synth)
    valued = value_growth(0.06, synth)
    margin = solve_margin(synth, 0.06)
    thinner = solve_growth(synth.replace(payout=0.6))
    sensitive_low = solve_growth(synth.replace(cost_of_equity=0.09))
    sensitive_high = solve_growth(synth.replace(cost_of_equity=0.13))
    diff = diff_assumptions(
        load_assumptions(ROOT / "examples/diff/pre.yaml"),
        load_assumptions(ROOT / "examples/diff/post.yaml"),
    )
    india = solve_growth(load_example("narmada"))
    uae = solve_growth(load_example("creek"))
    yielded = implied_dividend(load_dividend_example())

    claims = {
        "7.17%": f"{growth.implied_growth * 100:.2f}%",
        "$66.30": f"${growth.valuation.explicit_pv:,.2f}",
        "$83.70": f"${growth.valuation.terminal_pv:,.2f}",
        "55.80%": f"{growth.valuation.terminal_share * 100:.2f}%",
        "$16.00": f"${growth.valuation.year_n_earnings:,.2f}",
        "$137.60": f"${valued.valuation.equity_value:,.2f}",
        "21.80%": f"{margin.payload['margin'] * 100:.2f}%",
        "14.10%": f"{thinner.implied_growth * 100:.2f}%",
        "12.92%": f"{india.implied_growth * 100:.2f}%",
        "5.24%": f"{uae.implied_growth * 100:.2f}%",
        "2.68%": f"{sensitive_low.implied_growth * 100:.2f}%",
        "11.01%": f"{sensitive_high.implied_growth * 100:.2f}%",
        "5.88%": f"{diff.growth_after * 100:.2f}%",
        "-1.30": f"{(diff.growth_after - diff.growth_before) * 100:.2f}",
        "$165.00": f"${diff.value_after:,.2f}",
        "6.50%": f"{(load_dividend_example().dividend / load_dividend_example().price) * 100:.2f}%",
        "1.23x": f"{load_dividend_example().earnings / load_dividend_example().dividend:.2f}x",
        "81.25%": f"{(load_dividend_example().dividend / load_dividend_example().earnings) * 100:.2f}%",
        "$65.00": f"${load_dividend_example().dividend / load_dividend_example().cost_of_equity:,.2f}",
        "3.50%": f"{yielded.implied_growth * 100:.2f}%",
    }
    for documented, recomputed in claims.items():
        expect(f"{documented} recomputed as {recomputed}", documented == recomputed and documented in readme)

    expect("formula still in the README", "E_t = E_0*(1+g)^t" in readme)
    expect("yield text states 6.50%", "6.50%" in str(yielded))

    audit_closed = closed_form(
        golden["earnings"],
        golden["growth"],
        golden["cost_of_equity"],
        golden["terminal_growth"],
        golden["years"],
        golden["payout"],
    )
    audit_library = present_value(
        golden["earnings"],
        golden["growth"],
        golden["cost_of_equity"],
        golden["terminal_growth"],
        golden["years"],
        golden["payout"],
    ).equity_value
    expect("closed-form audit is 181.58", round(audit_closed, 2) == golden["equity_value"])
    expect("library audit matches the closed form", round(audit_library, 2) == round(audit_closed, 2))
    expect("README still states the audit value", "$181.58" in readme)

    gordon = golden["earnings"] * (1 + golden["terminal_growth"]) / (
        golden["cost_of_equity"] - golden["terminal_growth"]
    )
    # Identity at the audit's terminal rate, not its explicit growth.
    identity_growth = golden["terminal_growth"]
    gordon = golden["earnings"] * (1 + identity_growth) / (golden["cost_of_equity"] - identity_growth)
    for years in (1, 5, 10, 20):
        closed = closed_form(
            golden["earnings"],
            identity_growth,
            golden["cost_of_equity"],
            identity_growth,
            years,
            golden["payout"],
        )
        library = present_value(
            golden["earnings"],
            identity_growth,
            golden["cost_of_equity"],
            identity_growth,
            years,
            golden["payout"],
        ).equity_value
        expect(f"Gordon identity at {years} years", abs(closed - gordon) < 1e-9 and abs(library - gordon) < 1e-6)

    card = growth_svg(growth)
    for label in ("basis", "payout", "terminal", "timing", "tax", "scale"):
        expect(f"card states {label}", label in card)

    # Horizon search still runs.
    expect("horizon solve prints", "Closest horizon" in str(solve_years(synth, 0.12)))
    bare = solve_growth(
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
    expect("library growth is 7.17%", f"{bare.implied_growth * 100:.2f}%" == "7.17%")
    expect("key assumptions sit beside the figure", bare.key_assumptions["basis"] == "FCFE")

    if failures:
        print("MISMATCH")
        for failure in failures:
            print(f"- {failure}")
        return 1
    print("ALL MATCH")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
