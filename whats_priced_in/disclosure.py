"""The six disclosures. Tax is stated and not applied."""

from whats_priced_in.model import PAYOUT_WARNING, payout_warning
from whats_priced_in.scale import BASIS_LABELS, SCALE_DETAIL


def percent(rate):
    return f"{rate * 100:.2f}%"


def basis_label(assumptions):
    return BASIS_LABELS[assumptions.earnings_basis]


def timing_label(assumptions):
    if assumptions.discount_convention == "mid_year":
        return "mid-year"
    return "end of year"


def scale_label(assumptions):
    if assumptions.per_share and assumptions.scale == "unit":
        return f"{assumptions.currency} per share"
    if assumptions.per_share:
        return f"{assumptions.currency} {assumptions.scale}"
    return f"{assumptions.currency} {assumptions.scale}"


def terminal_label(assumptions):
    return f"Gordon {percent(assumptions.terminal_growth)}"


def tax_label(assumptions):
    if assumptions.tax_rate is None:
        return "not applied"
    return f"{percent(assumptions.tax_rate)} disclosed, not applied"


def equity_items(assumptions, growth, years_text):
    """Six disclosure essays plus the rows that sit under them."""
    basis = assumptions.earnings_basis
    if basis == "pat":
        basis_text = (
            "The starting figure is profit after tax. Payout converts PAT into cash flow to equity. "
            "At 100%, PAT is treated as distributable cash."
        )
    elif basis == "ffo":
        basis_text = (
            "The starting figure is funds from operations, before the payout scalar. "
            "Payout then scales it."
        )
    elif basis == "owner_earnings":
        basis_text = (
            "The starting figure is owner earnings, before the payout scalar. Payout then scales it."
        )
    else:
        basis_text = (
            "The starting figure is free cash flow to equity, before the payout scalar. "
            "Payout then scales it. At 100%, that FCFE is discounted as given. A lower payout haircuts it."
        )

    if assumptions.payout == 1:
        payout_text = (
            "Payout is 100.00% of each year's earnings, treated as cash flow to equity. "
            "This is not a dividend forecast. Nothing is retained inside the model."
        )
        if basis == "pat":
            payout_text += " PAT is treated as fully distributable."
    else:
        retained = percent(1 - assumptions.payout)
        payout_text = (
            f"Payout is {percent(assumptions.payout)} of each year's earnings, treated as cash flow to equity. "
            "This is not a dividend forecast. "
            f"The model retains {retained} of earnings, and that retention is not what funds the growth. "
            "Growth is an assumption on the earnings base."
        )

    year_n = years_text if isinstance(years_text, int) else assumptions.years
    terminal_text = (
        "Terminal value is a Gordon growth perpetuity. "
        f"The cash flow in year {year_n} grows once more at {percent(assumptions.terminal_growth)} "
        "and is capitalised at cost of equity minus terminal growth "
        f"({percent(assumptions.cost_of_equity)} - {percent(assumptions.terminal_growth)}). "
        "There is no fade inside the perpetuity."
    )
    if assumptions.discount_convention == "mid_year":
        timing_text = (
            "Cash flows are discounted to mid-year. The year-end value is multiplied by (1+r)^0.5. "
            "The terminal value is dated at the final year-end and then brought forward by that same half year."
        )
    else:
        timing_text = (
            "Cash flows are dated at each year-end and discounted for that many full years. "
            "The terminal value is dated at the same final year-end."
        )
    if assumptions.tax_rate is None:
        tax_text = (
            "Tax is not applied inside the model. The earnings input is taken as already after tax."
        )
    else:
        tax_text = (
            "Tax is not applied inside the model. The earnings input is taken as already after tax. "
            f"A tax rate of {percent(assumptions.tax_rate)} is disclosed and not reapplied. "
            "Changing it does not move the value."
        )
    detail = SCALE_DETAIL[assumptions.scale]
    if assumptions.per_share:
        scale_text = (
            f"Per-share mode. Price and earnings are per share, in {assumptions.currency}. "
            f"Scale is {assumptions.scale} ({detail}). No share count was applied."
        )
    else:
        scale_text = (
            f"Aggregate mode. Earnings and the target are both in {assumptions.currency} {assumptions.scale} "
            f"({detail}). A share count, if set, is in that same scale: crore shares when the scale is crore, "
            "millions of shares when the scale is million. Market cap = price × shares, in that scale. "
            "The engine does not multiply by the scale factor."
        )
    items = [
        {"key": "basis", "title": "Basis", "text": basis_text},
        {"key": "payout", "title": "Payout", "text": payout_text},
        {"key": "terminal", "title": "Terminal", "text": terminal_text},
        {"key": "timing", "title": "Timing", "text": timing_text},
        {"key": "tax", "title": "Tax", "text": tax_text},
        {"key": "scale", "title": "Scale", "text": scale_text},
    ]
    warning = payout_warning(assumptions.payout, growth, assumptions.terminal_growth)
    warnings = [warning] if warning else []
    return items, warnings


def render_disclosure(items, warnings, heading="Disclosure"):
    lines = [heading]
    for item in items:
        lines.append(f"  {item['key']:<10}{item['text']}")
    lines.append("Warnings")
    if not warnings:
        lines.append("  none")
    else:
        for warning in warnings:
            lines.append(f"  {warning}")
    return "\n".join(lines)


def warning_or_empty(payout, growth, terminal_growth):
    text = payout_warning(payout, growth, terminal_growth)
    return [text] if text else []


# Re-exported so callers can mention the canonical sentence.
CANONICAL_PAYOUT_WARNING = PAYOUT_WARNING
