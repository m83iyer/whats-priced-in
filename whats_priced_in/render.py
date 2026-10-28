"""Text layout shared by the CLI and print(result)."""

from whats_priced_in.disclosure import (
    basis_label,
    percent,
    render_disclosure,
    scale_label,
    tax_label,
    terminal_label,
    timing_label,
)
from whats_priced_in.model import FORMULA


def money(amount, currency):
    sign = "-" if amount < 0 else ""
    number = f"{abs(amount):,.2f}"
    code = currency.upper()
    if code == "USD":
        return f"{sign}${number}"
    if code == "INR":
        return f"{sign}₹{number}"
    if code == "AED":
        return f"{sign}AED {number}"
    return f"{sign}{code} {number}"


def signed_money(amount, currency):
    if amount > 0:
        return "+" + money(amount, currency)
    return money(amount, currency)


def signed_percent(fraction):
    points = fraction * 100
    if points > 0:
        return f"+{points:.2f}%"
    return f"{points:.2f}%"


def flow(amount, assumptions):
    text = money(amount, assumptions.currency)
    if assumptions.per_share:
        return text
    return f"{text} {assumptions.scale}"


def signed_flow(amount, assumptions):
    if amount > 0:
        return "+" + flow(amount, assumptions)
    return flow(amount, assumptions)


def price_text(amount, assumptions):
    return money(amount, assumptions.currency)


def shares_text(assumptions):
    return f"{assumptions.shares:,.2f} {assumptions.scale}"


def target_text(assumptions):
    text = flow(assumptions.target(), assumptions)
    if assumptions.per_share:
        return f"{text} per share"
    return text


def rows(pairs, width):
    return [f"{label:<{width}}{value}" for label, value in pairs]


def header(assumptions, *, prefix=None):
    title = assumptions.ticker or "case"
    if prefix:
        lines = [f"what's priced in · {prefix} · {title}"]
    else:
        lines = [f"what's priced in · {title}"]
    if assumptions.name:
        lines.append(assumptions.name)
    if assumptions.notes:
        lines.append(assumptions.notes)
    return "\n".join(lines)


def key_pairs(assumptions, growth_for_warning, *, years_text=None, extras=None):
    """Ordered key-assumption rows. `years_text` overrides the explicit-years cell."""
    pairs = [
        ("basis", basis_label(assumptions)),
        ("payout", percent(assumptions.payout)),
        ("terminal", terminal_label(assumptions)),
        ("timing", timing_label(assumptions)),
        ("tax", tax_label(assumptions)),
        ("scale", scale_label(assumptions)),
        ("cost of equity", percent(assumptions.cost_of_equity)),
        ("explicit years", str(assumptions.years if years_text is None else years_text)),
        ("earnings", flow(assumptions.earnings, assumptions)),
    ]
    if assumptions.price is not None:
        pairs.append(("price", price_text(assumptions.price, assumptions)))
    if assumptions.shares is not None:
        pairs.append(("shares", shares_text(assumptions)))
    if extras:
        pairs.extend(extras)
    return pairs


def key_block(pairs, width=16):
    return "Key assumptions\n" + "\n".join(rows(pairs, width))


def recorded_block(assumptions):
    if assumptions.revenue is None:
        return None
    lines = ["Recorded, not used in this solve", f"{'Revenue':<17}{flow(assumptions.revenue, assumptions)}"]
    if assumptions.earnings not in (None, 0) and assumptions.revenue:
        trailing = assumptions.earnings / assumptions.revenue
        lines.append(f"{'Trailing margin':<17}{percent(trailing)}")
    return "\n".join(lines)


def join_sections(sections):
    parts = [part for part in sections if part]
    return "\n\n".join(parts)


def figure_block(pairs, width):
    return "\n".join(rows(pairs, width))


def growth_text(assumptions, valuation, items, warnings):
    figures = figure_block(
        [
            ("Implied constant growth", percent(valuation.growth)),
            ("Target", target_text(assumptions)),
            ("Model value", flow(valuation.equity_value, assumptions)),
            ("Explicit-period PV", flow(valuation.explicit_pv, assumptions)),
            ("Terminal PV", flow(valuation.terminal_pv, assumptions)),
            ("Terminal share", percent(valuation.terminal_share)),
            (f"Year-{assumptions.years} earnings", flow(valuation.year_n_earnings, assumptions)),
        ],
        25,
    )
    body = FORMULA + "\n\n" + figures
    return join_sections(
        [
            header(assumptions),
            body,
            key_block(key_pairs(assumptions, valuation.growth)),
            recorded_block(assumptions),
            render_disclosure(items, warnings),
            "Not a recommendation. One model, read backwards.",
        ]
    )


def value_text(assumptions, valuation, items, warnings):
    gap = valuation.equity_value - assumptions.target()
    figures = figure_block(
        [
            ("Growth", percent(valuation.growth)),
            ("Model value", flow(valuation.equity_value, assumptions)),
            ("Explicit-period PV", flow(valuation.explicit_pv, assumptions)),
            ("Terminal PV", flow(valuation.terminal_pv, assumptions)),
            ("Terminal share", percent(valuation.terminal_share)),
            (f"Year-{assumptions.years} earnings", flow(valuation.year_n_earnings, assumptions)),
            ("Target", flow(assumptions.target(), assumptions)),
            ("Gap to target", flow(gap, assumptions)),
        ],
        20,
    )
    intro = f"Forward value at growth {percent(valuation.growth)}.\n{FORMULA}"
    return join_sections(
        [
            header(assumptions),
            intro + "\n\n" + figures,
            key_block(key_pairs(assumptions, valuation.growth)),
            render_disclosure(items, warnings),
            "Not a recommendation. One model, read forwards at a growth rate you chose.",
        ]
    )


def margin_text(assumptions, margin, revenue_growth, items, warnings):
    trailing = None
    if assumptions.revenue:
        trailing = assumptions.earnings / assumptions.revenue
    figures = [
        ("Constant margin", percent(margin)),
        ("Revenue growth", percent(revenue_growth)),
        ("Target", flow(assumptions.target(), assumptions)),
        ("Model value", flow(assumptions.target(), assumptions)),
    ]
    if trailing is not None:
        figures.append(("Trailing margin", percent(trailing)))
    body = (
        f"Constant margin, with revenue growing at {percent(revenue_growth)}. "
        "Earnings in each year are that year's revenue times the margin.\n\n"
        + figure_block(figures, 69)
    )
    if trailing is not None:
        body += "\nTrailing margin is earnings / revenue. It is not the solved margin."
    path = ["Margin path"]
    for year, revenue in enumerate(_revenue_path(assumptions.revenue, revenue_growth, assumptions.years), start=1):
        earned = revenue * margin
        path.append(
            f"{('Year ' + str(year)):<9}revenue {flow(revenue, assumptions)}  "
            f"margin {percent(margin)}  earnings {flow(earned, assumptions)}"
        )
    extras = [("revenue growth", percent(revenue_growth))]
    return join_sections(
        [
            header(assumptions),
            body,
            key_block(key_pairs(assumptions, revenue_growth, extras=extras)),
            "\n".join(path),
            render_disclosure(items, warnings),
            "Not a recommendation. The margin is what the price assumes, given the revenue growth you set.",
        ]
    )


def _revenue_path(revenue, growth, years):
    for year in range(1, years + 1):
        yield revenue * (1 + growth) ** year


def year_word(count):
    return "1 year" if count == 1 else f"{count} years"


def horizon_text(assumptions, growth, grid, items, warnings):
    closest = min(grid, key=lambda row: (abs(row["gap"]), row["years"]))
    clearing = next((row["years"] for row in grid if row["value"] >= assumptions.target()), None)
    if grid[-1]["value"] < grid[0]["value"]:
        direction = "decreasing"
        clearing = next((row["years"] for row in grid if row["value"] <= assumptions.target()), None)
    elif grid[-1]["value"] == grid[0]["value"]:
        direction = "flat"
    else:
        direction = "increasing"
    exact = next((row for row in grid if abs(row["gap"]) < 1e-6), None)
    if exact:
        intro = f"An integer horizon hits the target at {year_word(exact['years'])}."
    else:
        intro = (
            "No integer horizon hits the target exactly. "
            f"Closest is {year_word(closest['years'])}."
        )
        if clearing is not None:
            intro += f" The model first clears the target at {year_word(clearing)}."
    figures = figure_block(
        [
            ("Growth held fixed", percent(growth)),
            ("Closest horizon", year_word(closest["years"])),
            ("Model value at closest", flow(closest["value"], assumptions)),
            ("Gap to target", flow(closest["gap"], assumptions)),
            ("Horizon that clears", year_word(clearing) if clearing else "none"),
            ("Direction", direction),
        ],
        24,
    )
    table = ["Horizon grid"]
    for row in grid:
        label = year_word(row["years"])
        table.append(
            f"{label:<10}{flow(row['value'], assumptions):<10}gap {signed_flow(row['gap'], assumptions)}"
        )
    extras = [("growth held fixed", percent(growth))]
    return join_sections(
        [
            header(assumptions),
            intro + "\n\n" + figures,
            key_block(
                key_pairs(
                    assumptions,
                    growth,
                    years_text="searched 1 through 20",
                    extras=extras,
                ),
                width=19,
            ),
            "\n".join(table),
            render_disclosure(items, warnings),
            "Not a recommendation. Horizons are integers. The gap is the honesty.",
        ]
    )
