"""Dividend yield. Forward uses D1 / (r - g). Trailing uses D0 * (1+g) / (r - g)."""

from whats_priced_in.assumptions import load_example
from whats_priced_in.disclosure import basis_label, percent, render_disclosure, scale_label
from whats_priced_in.model import VERSION
from whats_priced_in.render import figure_block, header, join_sections, money
from whats_priced_in.scale import SCALE_DETAIL


def load_dividend_example():
    return load_example("dividend")


class YieldReading:
    def __init__(self, text, payload, implied_growth, key_assumptions, disclosure, assumptions):
        self.text = text
        self.payload = payload
        self.implied_growth = implied_growth
        self.key_assumptions = key_assumptions
        self.disclosure = disclosure
        self.assumptions = assumptions
        self.mode = "yield"
        self.warnings = []

    def __str__(self):
        return self.text


def implied_dividend(assumptions):
    if assumptions.price is None or assumptions.price <= 0:
        raise ValueError("A yield reading needs a positive price.")
    if assumptions.dividend is None or assumptions.dividend <= 0:
        raise ValueError("A yield reading needs a positive dividend.")
    if assumptions.earnings is None or assumptions.earnings <= 0:
        raise ValueError("A yield reading needs the earnings figure you want coverage measured against.")
    if assumptions.cost_of_equity is None or assumptions.cost_of_equity <= 0:
        raise ValueError("A yield reading needs a positive cost of equity.")
    if assumptions.cost_of_equity >= 1:
        raise ValueError("Rates are decimals: 0.11, not 11.")
    forward = assumptions.dividend_timing == "forward"
    dividend = assumptions.dividend
    price = assumptions.price
    cost = assumptions.cost_of_equity
    coverage = assumptions.earnings / dividend
    payout = dividend / assumptions.earnings
    if forward:
        implied = cost - dividend / price
    else:
        implied = (price * cost - dividend) / (price + dividend)
    flat = dividend / cost
    items = _items(assumptions, payout, forward)
    warnings = []
    pairs = _pairs(assumptions, payout, forward)
    scenarios = _scenarios(assumptions, implied, forward)
    table = [
        f"{'growth':<12}{'model value':<18}{'vs price':<14}note",
    ]
    for row in scenarios:
        table.append(
            f"{percent(row['growth']):<12}{money(row['value'], assumptions.currency):<18}"
            f"{row['versus']:<14}{row['note']}"
        )
    which = "D1" if forward else "D0"
    blurb = (
        f"Scenarios hold the entered dividend as {which}. "
        f"{which} is {money(dividend, assumptions.currency)}."
    )
    label = "Forward yield" if forward else "Trailing yield"
    figures = figure_block(
        [
            (label, percent(dividend / price)),
            ("Coverage", f"{coverage:.2f}x"),
            ("Payout", percent(payout)),
            ("Implied perpetual growth", percent(implied)),
            ("Flat perpetuity value", money(flat, assumptions.currency)),
        ],
        26,
    )
    text = join_sections(
        [
            header(assumptions, prefix="yield"),
            figures,
            "Key assumptions\n" + "\n".join(f"{label:<16}{value}" for label, value in pairs),
            blurb + "\n\n" + "\n".join(table),
            render_disclosure(items, warnings),
            "Not a recommendation. A yield reading of one perpetuity, not a credit opinion on the dividend.",
        ]
    )
    disclosure = render_disclosure(items, warnings)
    payload = {
        "model": "dividend_perpetuity",
        "version": VERSION,
        "mode": "yield",
        "timing": "D1" if forward else "D0",
        "forward_yield": dividend / price,
        "coverage": coverage,
        "payout": payout,
        "implied_growth": implied,
        "flat_value": flat,
        "key_assumptions": dict(pairs),
        "scenarios": scenarios,
        "disclosure": {"items": items, "warnings": warnings},
        "warnings": warnings,
    }
    return YieldReading(text, payload, implied, dict(pairs), disclosure, assumptions)


def _value_at(assumptions, growth, forward):
    cost = assumptions.cost_of_equity
    dividend = assumptions.dividend
    if growth >= cost:
        raise ValueError("Growth has to be below the cost of equity in this perpetuity.")
    if forward:
        return dividend / (cost - growth)
    return dividend * (1 + growth) / (cost - growth)


def _scenarios(assumptions, implied, forward):
    grid = [0.0, 0.02, 0.03, 0.04]
    if not any(abs(point - implied) < 1e-8 for point in grid):
        grid.append(implied)
    grid.sort()
    rows = []
    for growth in grid:
        value = _value_at(assumptions, growth, forward)
        versus = (value - assumptions.price) / assumptions.price
        note = "implied by the price" if abs(growth - implied) < 1e-8 else ""
        rows.append(
            {
                "growth": growth,
                "value": value,
                "versus": _versus(versus),
                "note": note,
            }
        )
    return rows


def _versus(fraction):
    points = fraction * 100
    if points > 0:
        return f"+{points:.2f}%"
    return f"{points:.2f}%"


def _pairs(assumptions, payout, forward):
    if assumptions.tax_rate is None:
        tax = "not applied; this reading has no tax rate"
    else:
        tax = f"{percent(assumptions.tax_rate)} disclosed, not applied"
    return [
        ("basis", basis_label(assumptions)),
        ("payout", percent(payout)),
        ("terminal", "growing perpetuity, no explicit horizon"),
        ("timing", "next dividend (D1)" if forward else "trailing dividend (D0)"),
        ("tax", tax),
        ("scale", scale_label(assumptions)),
        ("cost of equity", percent(assumptions.cost_of_equity)),
        ("dividend", money(assumptions.dividend, assumptions.currency)),
        ("price", money(assumptions.price, assumptions.currency)),
    ]


def _items(assumptions, payout, forward):
    label = basis_label(assumptions)
    if assumptions.earnings_basis == "ffo":
        basis = (
            "The earnings figure is FFO. Coverage divides that figure by the dividend you supplied. "
            "Periods are not aligned for you."
        )
    else:
        basis = (
            f"The earnings figure is {label}. Coverage divides that figure by the dividend you supplied. "
            "Periods are not aligned for you."
        )
    payout_text = (
        f"Payout is {percent(payout)}, the dividend divided by the earnings figure. "
        "It is a coverage identity, not the payout scalar of the two-stage earnings model."
    )
    if forward:
        terminal = (
            "There is no explicit horizon. The terminal assumption is the perpetual growth itself. "
            "Next dividend D1 is the distribution you entered, held fixed across scenarios. "
            "Value at a growth rate g is D1 / (r - g). Implied growth is r - D1 / price."
        )
        timing = (
            "The dividend is treated as next period's distribution (forward yield = dividend / price). "
            "Growth applies after that distribution, not before it."
        )
    else:
        terminal = (
            "There is no explicit horizon. The terminal assumption is the perpetual growth itself. "
            "Trailing dividend D0 is the distribution you entered. "
            "Value at a growth rate g is D0*(1+g)/(r-g). Implied growth solves price = D0*(1+g)/(r-g)."
        )
        timing = (
            "The dividend is treated as the last paid distribution (trailing yield = dividend / price). "
            "The identity that ran is price = D0*(1+g)/(r-g)."
        )
    if assumptions.tax_rate is None:
        tax = (
            "Tax is not applied. Coverage and yield use the dividend and the earnings figure as supplied. "
            "No tax rate is an input of this reading."
        )
    else:
        tax = (
            "Tax is not applied. Coverage and yield use the dividend and the earnings figure as supplied. "
            f"A tax rate of {percent(assumptions.tax_rate)} is disclosed and not reapplied."
        )
    detail = SCALE_DETAIL[assumptions.scale]
    scale = (
        f"Per-share figures in {assumptions.currency}. Scale is {assumptions.scale} ({detail}). "
        "The dividend and the price are in that currency. Nothing is converted."
    )
    return [
        {"key": "basis", "title": "Basis", "text": basis},
        {"key": "payout", "title": "Payout", "text": payout_text},
        {"key": "terminal", "title": "Terminal", "text": terminal},
        {"key": "timing", "title": "Timing", "text": timing},
        {"key": "tax", "title": "Tax", "text": tax},
        {"key": "scale", "title": "Scale", "text": scale},
    ]
