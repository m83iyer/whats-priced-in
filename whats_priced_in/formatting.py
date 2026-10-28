"""Human tables and JSON payloads. Display rounding lives here, and only here."""

from __future__ import annotations

import json
from dataclasses import asdict, is_dataclass
from typing import Any

from whats_priced_in._version import __version__
from whats_priced_in.assumptions import (
    GROWTH_INPUTS,
    MONEY_FIELDS,
    RATE_FIELDS,
    Assumptions,
    unit_mode,
)
from whats_priced_in.dcf import (
    FORMULA,
    MID_YEAR_NOTE,
    MarginResult,
    SolveGrowthResult,
    Valuation,
    YearsResult,
)
from whats_priced_in.disclosure import Disclosure
from whats_priced_in.dividend import DividendResult
from whats_priced_in.earnings_assumption_diff import DiffResult
from whats_priced_in.scales import CURRENCY_SYMBOLS
from whats_priced_in.sensitivity import SensTable


def format_percent(rate: float, digits: int = 2) -> str:
    return f"{rate * 100:.{digits}f}%"


def format_pp(delta: float) -> str:
    points = delta * 100
    sign = "+" if points > 0 else ""
    return f"{sign}{points:.2f} pp"


def format_multiple(value: float) -> str:
    return f"{value:.2f}x"


def format_money(amount: float, currency: str, scale: str, *, per_share: bool) -> str:
    sign = "-" if amount < 0 else ""
    symbol = CURRENCY_SYMBOLS.get(currency, f"{currency} ")
    text = f"{sign}{symbol}{abs(amount):,.2f}"
    if per_share or scale == "unit":
        return text
    return f"{text} {scale}"


def format_signed_money(amount: float, currency: str, scale: str, *, per_share: bool) -> str:
    text = format_money(amount, currency, scale, per_share=per_share)
    if amount > 0:
        return f"+{text}"
    return text


def format_signed_percent(rate: float) -> str:
    points = rate * 100
    if points > 0:
        return f"+{points:.2f}%"
    return f"{points:.2f}%"


def dumps(payload: dict[str, Any]) -> str:
    return json.dumps(_jsonable(payload), indent=2) + "\n"


def format_solve_growth(result: SolveGrowthResult) -> str:
    item = result.assumptions
    per_share = result.unit_mode == "per_share"
    lines = [_header(item), ""]
    lines.append(FORMULA)
    if item.discount_convention == "mid_year":
        lines.append(MID_YEAR_NOTE)
    lines.append("")
    target = format_money(result.target, item.currency, item.scale, per_share=per_share)
    if per_share:
        target += " per share"
    rows = [
        ("Implied constant growth", format_percent(result.implied_growth)),
        ("Target", target),
        ("Model value", format_money(result.breakdown.equity_value, item.currency, item.scale, per_share=per_share)),
        ("Explicit-period PV", format_money(result.breakdown.explicit_pv, item.currency, item.scale, per_share=per_share)),
        ("Terminal PV", format_money(result.breakdown.terminal_pv, item.currency, item.scale, per_share=per_share)),
        ("Terminal share", format_percent(result.breakdown.terminal_share)),
        (f"Year-{item.years} earnings", format_money(result.breakdown.year_n_earnings, item.currency, item.scale, per_share=per_share)),
    ]
    lines.append(_rows(rows))
    lines.extend(["", format_assumption_block(result.key_assumptions)])
    unused = _unused_block(item)
    if unused:
        lines.extend(["", "Recorded, not used in this solve", unused])
    lines.extend(["", *_disclosure_block(result.disclosure)])
    lines.append("")
    lines.append("Not a recommendation. One model, read backwards.")
    return "\n".join(lines) + "\n"


def format_valuation(result: Valuation) -> str:
    item = result.assumptions
    per_share = result.unit_mode == "per_share"
    lines = [_header(item), ""]
    lines.append(f"Forward value at growth {format_percent(result.growth)}.")
    lines.append(FORMULA)
    if item.discount_convention == "mid_year":
        lines.append(MID_YEAR_NOTE)
    lines.append("")
    rows = [
        ("Growth", format_percent(result.growth)),
        ("Model value", format_money(result.breakdown.equity_value, item.currency, item.scale, per_share=per_share)),
        ("Explicit-period PV", format_money(result.breakdown.explicit_pv, item.currency, item.scale, per_share=per_share)),
        ("Terminal PV", format_money(result.breakdown.terminal_pv, item.currency, item.scale, per_share=per_share)),
        ("Terminal share", format_percent(result.breakdown.terminal_share)),
        (f"Year-{item.years} earnings", format_money(result.breakdown.year_n_earnings, item.currency, item.scale, per_share=per_share)),
    ]
    if result.target is not None:
        gap = result.breakdown.equity_value - result.target
        rows.append(("Target", format_money(result.target, item.currency, item.scale, per_share=per_share)))
        rows.append(("Gap to target", format_signed_money(gap, item.currency, item.scale, per_share=per_share)))
    lines.append(_rows(rows))
    lines.extend(["", format_assumption_block(result.key_assumptions)])
    lines.extend(["", *_disclosure_block(result.disclosure)])
    lines.append("")
    lines.append("Not a recommendation. One model, read forwards at a growth rate you chose.")
    return "\n".join(lines) + "\n"


def format_margin(result: MarginResult) -> str:
    item = result.assumptions
    per_share = result.unit_mode == "per_share"
    lines = [_header(item), ""]
    if result.constant:
        lines.append(
            f"Constant margin, with revenue growing at {format_percent(result.revenue_growth)}. "
            "Earnings in each year are that year's revenue times the margin."
        )
    else:
        lines.append(
            f"Margin fades from {format_percent(result.margin_start)} in year 1 "
            f"to the solved year-{item.years} margin. Revenue grows at {format_percent(result.revenue_growth)}."
        )
    lines.append("")
    label = "Constant margin" if result.constant else f"Year-{item.years} margin"
    rows = [
        (label, format_percent(result.margin_end)),
        ("Revenue growth", format_percent(result.revenue_growth)),
        ("Target", format_money(result.target, item.currency, item.scale, per_share=per_share)),
        ("Model value", format_money(result.breakdown.equity_value, item.currency, item.scale, per_share=per_share)),
    ]
    if result.trailing_margin is not None:
        rows.append(("Trailing margin", format_percent(result.trailing_margin)))
        rows.append(("Trailing margin is earnings / revenue. It is not the solved margin.", ""))
    lines.append(_rows(rows))
    lines.extend(["", format_assumption_block(result.key_assumptions)])
    lines.append("")
    lines.append("Margin path")
    path_rows = []
    for year, (revenue, margin, earnings) in enumerate(
        zip(result.revenue_path, result.margin_path, result.breakdown.earnings_path), start=1
    ):
        path_rows.append(
            (
                f"Year {year}",
                f"revenue {format_money(revenue, item.currency, item.scale, per_share=per_share)}"
                f"  margin {format_percent(margin)}"
                f"  earnings {format_money(earnings, item.currency, item.scale, per_share=per_share)}",
            )
        )
    lines.append(_rows(path_rows))
    lines.extend(["", *_disclosure_block(result.disclosure)])
    lines.append("")
    lines.append("Not a recommendation. The margin is what the price assumes, given the revenue growth you set.")
    return "\n".join(lines) + "\n"


def format_years(result: YearsResult) -> str:
    item = result.assumptions
    per_share = result.unit_mode == "per_share"
    lines = [_header(item), ""]
    lines.append(result.note)
    lines.append("")
    rows = [
        ("Growth held fixed", format_percent(result.growth)),
        (
            "Closest horizon",
            "not identified" if not result.identified else _years_phrase(result.closest_years),
        ),
        ("Model value at closest", format_money(result.closest_value, item.currency, item.scale, per_share=per_share)),
        ("Gap to target", format_signed_money(result.gap, item.currency, item.scale, per_share=per_share)),
        (
            "Horizon that clears",
            "n/a" if result.years_that_clear is None else _years_phrase(result.years_that_clear),
        ),
        ("Direction", result.direction),
    ]
    lines.append(_rows(rows))
    lines.extend(["", format_assumption_block(result.key_assumptions)])
    lines.append("")
    lines.append("Horizon grid")
    grid_rows = [
        (
            _years_phrase(point.years),
            format_money(point.equity_value, item.currency, item.scale, per_share=per_share)
            + "   gap "
            + format_signed_money(point.gap, item.currency, item.scale, per_share=per_share),
        )
        for point in result.grid
    ]
    lines.append(_rows(grid_rows))
    lines.extend(["", *_disclosure_block(result.disclosure)])
    lines.append("")
    lines.append("Not a recommendation. Horizons are integers. The gap is the honesty.")
    return "\n".join(lines) + "\n"


def format_dividend(result: DividendResult) -> str:
    case = result.case
    lines = [_dividend_header(result), ""]
    yield_label = "Forward yield" if result.yield_kind == "forward" else "Trailing yield"
    rows = [
        (yield_label, format_percent(result.cash_yield)),
        ("Coverage", "n/a" if result.coverage is None else format_multiple(result.coverage)),
        ("Payout", "n/a" if result.payout is None else format_percent(result.payout)),
        ("Implied perpetual growth", "n/a" if result.implied_growth is None else format_percent(result.implied_growth)),
        (
            "Flat perpetuity value",
            "n/a"
            if result.flat_perpetuity_value is None
            else format_money(result.flat_perpetuity_value, case.currency, case.scale, per_share=True),
        ),
    ]
    lines.append(_rows(rows))
    lines.extend(["", format_assumption_block(result.key_assumptions), ""])
    if result.dividend_timing == "next":
        lines.append(
            "Scenarios hold the entered dividend as D1. "
            f"D1 is {format_money(result.annual_dividend, case.currency, case.scale, per_share=True)}."
        )
    else:
        lines.append("Scenarios treat the entered dividend as trailing D0. Next dividend is D0 × (1+g).")
    lines.append("")
    lines.append(f"{'growth':<12}{'model value':<18}{'vs price':<14}note")
    for row in result.scenarios:
        value = "n/a" if row.model_value is None else format_money(row.model_value, case.currency, case.scale, per_share=True)
        versus = "n/a" if row.versus_price is None else format_signed_percent(row.versus_price)
        lines.append(f"{format_percent(row.growth):<12}{value:<18}{versus:<14}{row.note}")
    lines.extend(["", *_disclosure_block(result.disclosure)])
    lines.append("")
    lines.append("Not a recommendation. A yield reading of one perpetuity, not a credit opinion on the dividend.")
    return "\n".join(lines) + "\n"


def format_sensitivity(tables: list[SensTable]) -> str:
    blocks: list[str] = []
    for index, table in enumerate(tables):
        item = table.assumptions
        per_share = table.target is not None and unit_mode(item) == "per_share"
        if index == 0:
            blocks.append(_header(item))
            blocks.append("")
            blocks.append(format_assumption_block(table.key_assumptions))
            blocks.append("")
        if table.kind == "value":
            blocks.append("Value if growth is this, and every other assumption stays put.")
            blocks.append("")
            header = f"{'growth':<14}{'model value':<24}{'vs target'}"
            blocks.append(header)
            for row in table.rows:
                value = "n/a" if row.equity_value is None else format_money(
                    row.equity_value, item.currency, item.scale, per_share=per_share
                )
                versus = "n/a" if row.versus_target is None else format_signed_percent(row.versus_target)
                note = f"  {row.note}" if row.note else ""
                blocks.append(f"{format_percent(row.value):<14}{value:<24}{versus}{note}")
        else:
            blocks.append(
                f"Implied growth if {table.parameter.replace('_', ' ')} changes. "
                "Price and earnings stay put."
            )
            if table.base is not None:
                shown = format_percent(table.base) if table.parameter != "years" else f"{int(table.base)} years"
                blocks.append(f"Base {table.parameter.replace('_', ' ')}: {shown}.")
            blocks.append("")
            blocks.append(f"{'value':<14}{'implied growth'}")
            for row in table.rows:
                label = f"{int(row.value)} years" if table.parameter == "years" else format_percent(row.value)
                growth = "n/a" if row.implied_growth is None else format_percent(row.implied_growth)
                note = f"  {row.note}" if row.note else ""
                blocks.append(f"{label:<14}{growth}{note}")
        blocks.append("")
    blocks.extend(_disclosure_block(tables[-1].disclosure))
    blocks.append("")
    blocks.append("Not a recommendation. Each row moves one input.")
    return "\n".join(blocks) + "\n"


def format_diff(result: DiffResult) -> str:
    lines = ["what's priced in · earnings assumption diff", ""]
    title_bits = []
    if result.before.ticker or result.after.ticker:
        if result.before.ticker == result.after.ticker:
            title_bits.append(result.before.ticker or "")
        else:
            title_bits.append(f"{result.before.ticker or 'n/a'} → {result.after.ticker or 'n/a'}")
    if result.before.name and result.before.name == result.after.name:
        title_bits.append(result.before.name)
    if title_bits:
        lines.append(" · ".join(title_bits))
        lines.append("")
    if not result.changes:
        lines.append("No assumption field changed.")
    else:
        lines.append(f"{'field':<22}{'before':<22}{'after':<22}{'change':<18}role")
        for change in result.changes:
            before = _format_field(change.field, change.before, result.before)
            after = _format_field(change.field, change.after, result.after)
            delta = _format_delta(change.field, change.before, change.after, result.before, result.after)
            role = "moves implied growth" if change.affects_implied_growth else "disclosed only"
            lines.append(f"{change.field:<22}{before:<22}{after:<22}{delta:<18}{role}")
    lines.append("")
    lines.append(
        f"{'implied growth':<22}"
        f"{format_percent(result.implied_growth_before):<22}"
        f"{format_percent(result.implied_growth_after):<22}"
        f"{format_pp(result.delta_implied_growth)}"
    )
    per_share = unit_mode(result.before) == "per_share"
    if result.values_comparable and result.delta_value is not None:
        lines.append(
            f"{'value at ' + format_percent(result.reference_growth):<22}"
            f"{format_money(result.value_before, result.before.currency, result.before.scale, per_share=per_share):<22}"
            f"{format_money(result.value_after, result.after.currency, result.after.scale, per_share=per_share):<22}"
            f"{format_signed_money(result.delta_value, result.before.currency, result.before.scale, per_share=per_share)}"
        )
        lines.append("")
        lines.append(format_diff_key_assumptions(result))
        lines.append("")
        lines.append(
            "Value is the model at the pre-earnings implied growth, under each set's own other assumptions. "
            "Revenue is not an input to that solve. The model is linear in the earnings base, "
            "so the value moves with earnings when the other growth inputs stay put."
        )
    else:
        lines.append("")
        lines.append(format_diff_key_assumptions(result))
        lines.append("")
        lines.append(
            "Value delta is blank because currency, scale, or per-share versus aggregate does not match. "
            "Implied growth is still comparable. It does not depend on the unit label."
        )
    lines.append("")
    same_items = result.disclosure_before.items == result.disclosure_after.items
    same_warnings = result.disclosure_before.warnings == result.disclosure_after.warnings
    if same_items and same_warnings:
        lines.append("Disclosure (same on both sides)")
        lines.extend(_disclosure_block(result.disclosure_before)[1:])
    elif same_items:
        lines.append("Disclosure (same text on both sides)")
        lines.extend(_item_lines(result.disclosure_before))
        lines.append("Warnings · before")
        lines.extend(_warning_lines(result.disclosure_before))
        lines.append("Warnings · after")
        lines.extend(_warning_lines(result.disclosure_after))
    else:
        lines.append("Disclosure · before")
        lines.extend(_disclosure_block(result.disclosure_before)[1:])
        lines.append("")
        lines.append("Disclosure · after")
        lines.extend(_disclosure_block(result.disclosure_after)[1:])
    lines.append("")
    lines.append("Not a recommendation. A diff of two assumption sets, not a reaction to a headline.")
    return "\n".join(lines) + "\n"


def growth_payload(result: SolveGrowthResult, card: str | None = None) -> dict[str, Any]:
    item = result.assumptions
    payload: dict[str, Any] = {
        "model": "two_stage_fcfe_gordon",
        "version": __version__,
        "mode": "growth",
        "formula": FORMULA,
        "ticker": item.ticker,
        "name": item.name,
        "currency": item.currency,
        "scale": item.scale,
        "unit_mode": result.unit_mode,
        "per_share": result.per_share,
        "implied_growth": result.implied_growth,
        "key_assumptions": result.key_assumptions,
        "target": result.target,
        "equity_value": result.breakdown.equity_value,
        "residual": result.breakdown.equity_value - result.target,
        "explicit_pv": result.breakdown.explicit_pv,
        "terminal_pv": result.breakdown.terminal_pv,
        "terminal_value_at_horizon": result.breakdown.terminal_value_at_horizon,
        "terminal_share": result.breakdown.terminal_share,
        "year_n_earnings": result.breakdown.year_n_earnings,
        "earnings_path": list(result.breakdown.earnings_path),
        "cashflow_path": list(result.breakdown.cashflow_path),
        "assumptions": _assumptions_dict(item),
        "disclosure": _disclosure_dict(result.disclosure),
        "warnings": list(result.disclosure.warnings),
    }
    if item.discount_convention == "mid_year":
        payload["mid_year"] = MID_YEAR_NOTE
    if card:
        payload["card"] = card
    return payload


def valuation_payload(result: Valuation) -> dict[str, Any]:
    return {
        "model": "two_stage_fcfe_gordon",
        "version": __version__,
        "mode": "value",
        "formula": FORMULA,
        "growth": result.growth,
        "equity_value": result.breakdown.equity_value,
        "key_assumptions": result.key_assumptions,
        "target": result.target,
        "explicit_pv": result.breakdown.explicit_pv,
        "terminal_pv": result.breakdown.terminal_pv,
        "terminal_share": result.breakdown.terminal_share,
        "year_n_earnings": result.breakdown.year_n_earnings,
        "assumptions": _assumptions_dict(result.assumptions),
        "disclosure": _disclosure_dict(result.disclosure),
        "warnings": list(result.disclosure.warnings),
    }


def margin_payload(result: MarginResult) -> dict[str, Any]:
    return {
        "model": "two_stage_fcfe_gordon",
        "version": __version__,
        "mode": "margin",
        "constant": result.constant,
        "margin_start": result.margin_start,
        "margin_end": result.margin_end,
        "key_assumptions": result.key_assumptions,
        "revenue_growth": result.revenue_growth,
        "trailing_margin": result.trailing_margin,
        "target": result.target,
        "equity_value": result.breakdown.equity_value,
        "revenue_path": list(result.revenue_path),
        "margin_path": list(result.margin_path),
        "earnings_path": list(result.breakdown.earnings_path),
        "assumptions": _assumptions_dict(result.assumptions),
        "disclosure": _disclosure_dict(result.disclosure),
        "warnings": list(result.disclosure.warnings),
    }


def years_payload(result: YearsResult) -> dict[str, Any]:
    return {
        "model": "two_stage_fcfe_gordon",
        "version": __version__,
        "mode": "years",
        "growth": result.growth,
        "target": result.target,
        "closest_years": result.closest_years,
        "key_assumptions": result.key_assumptions,
        "closest_value": result.closest_value,
        "gap": result.gap,
        "years_that_clear": result.years_that_clear,
        "identified": result.identified,
        "direction": result.direction,
        "note": result.note,
        "grid": [
            {"years": point.years, "equity_value": point.equity_value, "gap": point.gap}
            for point in result.grid
        ],
        "assumptions": _assumptions_dict(result.assumptions),
        "disclosure": _disclosure_dict(result.disclosure),
        "warnings": list(result.disclosure.warnings),
    }


def dividend_payload(result: DividendResult) -> dict[str, Any]:
    return {
        "model": "gordon_dividend",
        "version": __version__,
        "mode": "yield",
        "ticker": result.case.ticker,
        "currency": result.case.currency,
        "scale": result.case.scale,
        "price": result.price,
        "annual_dividend": result.annual_dividend,
        "dividend_timing": result.dividend_timing,
        "yield_kind": result.yield_kind,
        "cash_yield": result.cash_yield,
        "coverage": result.coverage,
        "payout": result.payout,
        "implied_growth": result.implied_growth,
        "key_assumptions": result.key_assumptions,
        "flat_perpetuity_value": result.flat_perpetuity_value,
        "scenarios": [
            {
                "growth": row.growth,
                "model_value": row.model_value,
                "versus_price": row.versus_price,
                "note": row.note,
            }
            for row in result.scenarios
        ],
        "disclosure": _disclosure_dict(result.disclosure),
        "warnings": list(result.disclosure.warnings),
    }


def sensitivity_payload(tables: list[SensTable]) -> dict[str, Any]:
    return {
        "model": "two_stage_fcfe_gordon",
        "version": __version__,
        "mode": "sens",
        "key_assumptions": tables[0].key_assumptions,
        "tables": [
            {
                "parameter": table.parameter,
                "kind": table.kind,
                "base": table.base,
                "target": table.target,
                "rows": [
                    {
                        "value": row.value,
                        "implied_growth": row.implied_growth,
                        "equity_value": row.equity_value,
                        "versus_target": row.versus_target,
                        "note": row.note,
                    }
                    for row in table.rows
                ],
            }
            for table in tables
        ],
        "disclosure": _disclosure_dict(tables[-1].disclosure),
        "warnings": list(tables[-1].disclosure.warnings),
    }


def diff_payload(result: DiffResult, card: str | None = None) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "model": "earnings_assumption_diff",
        "version": __version__,
        "changes": [
            {
                "field": change.field,
                "before": change.before,
                "after": change.after,
                "affects_implied_growth": change.affects_implied_growth,
            }
            for change in result.changes
        ],
        "implied_growth_before": result.implied_growth_before,
        "implied_growth_after": result.implied_growth_after,
        "delta_implied_growth": result.delta_implied_growth,
        "key_assumptions_before": result.key_assumptions["before"],
        "key_assumptions_after": result.key_assumptions["after"],
        "reference_growth": result.reference_growth,
        "value_before": result.value_before,
        "value_after": result.value_after,
        "delta_value": result.delta_value,
        "values_comparable": result.values_comparable,
        "target_before": result.target_before,
        "target_after": result.target_after,
        "disclosure_before": _disclosure_dict(result.disclosure_before),
        "disclosure_after": _disclosure_dict(result.disclosure_after),
        "growth_inputs": sorted(GROWTH_INPUTS),
    }
    if card:
        payload["card"] = card
    return payload


def _header(item: Assumptions) -> str:
    bits = ["what's priced in"]
    if item.ticker:
        bits.append(item.ticker)
    lines = [" · ".join(bits)]
    if item.name:
        lines.append(item.name)
    if item.notes:
        lines.append(item.notes)
    return "\n".join(lines)


def _dividend_header(result: DividendResult) -> str:
    bits = ["what's priced in · yield"]
    if result.case.ticker:
        bits.append(result.case.ticker)
    lines = [" · ".join(bits)]
    if result.case.name:
        lines.append(result.case.name)
    if result.case.notes:
        lines.append(result.case.notes)
    return "\n".join(lines)


# Row labels the launch claim treats as the six disclosures. Keep this order.
KEY_ASSUMPTION_LABELS = ("basis", "payout", "terminal", "timing", "tax", "scale")

_CARD_GROUPS = (
    ("basis", "payout", "terminal"),
    ("timing", "tax", "scale"),
    ("cost of equity", "explicit years", "earnings", "dividend", "revenue growth", "growth held fixed"),
)
_CARD_SKIP = {"price", "shares"}


def equity_key_assumption_pairs(
    item: Assumptions,
    extra: list[tuple[str, str]] | None = None,
) -> list[tuple[str, str]]:
    """The assumptions that sit beside an equity answer. Six labels first."""

    per_share = unit_mode(item) == "per_share"
    timing = "end of year" if item.discount_convention == "end_of_year" else "mid-year"
    if item.tax_rate is None:
        tax = "not applied; no rate supplied"
    else:
        tax = f"{format_percent(item.tax_rate)} disclosed, not applied"
    scale = f"{item.currency} per share" if per_share else f"{item.currency} {item.scale}"
    rows = [
        ("basis", item.earnings_basis.upper()),
        ("payout", format_percent(item.payout)),
        ("terminal", f"Gordon {format_percent(item.terminal_growth)}"),
        ("timing", timing),
        ("tax", tax),
        ("scale", scale),
        ("cost of equity", format_percent(item.cost_of_equity)),
        ("explicit years", str(item.years)),
        ("earnings", format_money(item.earnings, item.currency, item.scale, per_share=per_share)),
    ]
    if item.price is not None:
        rows.append(("price", format_money(item.price, item.currency, "unit", per_share=True)))
    if item.shares is not None:
        share_label = f"{item.shares:,.2f}" if item.scale == "unit" else f"{item.shares:,.2f} {item.scale}"
        rows.append(("shares", share_label))
    if extra:
        rows.extend(extra)
    return rows


def key_assumptions_payload(
    item: Assumptions,
    extra: list[tuple[str, str]] | None = None,
) -> dict[str, str]:
    return dict(equity_key_assumption_pairs(item, extra))


def dividend_key_assumption_pairs(result: DividendResult) -> list[tuple[str, str]]:
    case = result.case
    timing = "next dividend (D1)" if result.dividend_timing == "next" else "trailing dividend (D0)"
    scale = f"{case.currency} per share" if case.scale == "unit" else f"{case.currency} {case.scale}"
    cost = "not supplied" if case.cost_of_equity is None else format_percent(case.cost_of_equity)
    rows = [
        ("basis", case.earnings_basis.upper()),
        ("payout", "n/a" if result.payout is None else format_percent(result.payout)),
        ("terminal", "growing perpetuity, no explicit horizon"),
        ("timing", timing),
        ("tax", "not applied; this reading has no tax rate"),
        ("scale", scale),
        ("cost of equity", cost),
        ("dividend", format_money(result.annual_dividend, case.currency, case.scale, per_share=True)),
        ("price", format_money(result.price, case.currency, "unit", per_share=True)),
    ]
    return rows


def format_assumption_block(
    pairs: dict[str, str] | list[tuple[str, str]],
    heading: str = "Key assumptions",
) -> str:
    items = list(pairs.items()) if isinstance(pairs, dict) else list(pairs)
    body = _rows(items)
    if not body:
        return heading
    return heading + "\n" + body


def format_diff_key_assumptions(result: DiffResult) -> str:
    """Before and after, so a changed earnings base sits next to the growth delta."""

    left = result.key_assumptions["before"]
    right = result.key_assumptions["after"]
    labels = list(left)
    for label in right:
        if label not in labels:
            labels.append(label)
    header = ("assumption", "before", "after")
    rows = [
        (label, left.get(label, "n/a"), right.get(label, "n/a"))
        for label in labels
    ]
    return "Key assumptions\n" + _columns(header, rows)


def key_assumption_card_lines(pairs: dict[str, str] | list[tuple[str, str]]) -> list[str]:
    """Short lines for an SVG. The six labels stay on the card, beside the figure."""

    items = list(pairs.items()) if isinstance(pairs, dict) else list(pairs)
    items = [(label, value) for label, value in items if label not in _CARD_SKIP]
    lookup = dict(items)
    used: set[str] = set()
    lines = ["Key assumptions"]
    for group in _CARD_GROUPS:
        parts = [f"{label} {lookup[label]}" for label in group if label in lookup]
        used.update(label for label in group if label in lookup)
        if parts:
            lines.append(" · ".join(parts))
    rest = [f"{label} {value}" for label, value in items if label not in used]
    if rest:
        lines.append(" · ".join(rest))
    return lines


def diff_key_assumption_card_lines(before: dict[str, str], after: dict[str, str]) -> list[str]:
    labels = list(before)
    for label in after:
        if label not in labels:
            labels.append(label)
    pairs: list[tuple[str, str]] = []
    for label in labels:
        left = before.get(label, "n/a")
        right = after.get(label, "n/a")
        pairs.append((label, left if left == right else f"{left} → {right}"))
    return key_assumption_card_lines(pairs)


def _columns(header: tuple[str, str, str], rows: list[tuple[str, str, str]]) -> str:
    labels = [header[0], *[row[0] for row in rows]]
    middles = [header[1], *[row[1] for row in rows]]
    width_label = max(len(item) for item in labels)
    width_middle = max(len(item) for item in middles)
    lines = [
        f"{header[0].ljust(width_label)}  {header[1].ljust(width_middle)}  {header[2]}".rstrip()
    ]
    for label, before, after in rows:
        lines.append(f"{label.ljust(width_label)}  {before.ljust(width_middle)}  {after}".rstrip())
    return "\n".join(lines)


def _unused_block(item: Assumptions) -> str:
    per_share = unit_mode(item) == "per_share"
    rows: list[tuple[str, str]] = []
    if item.revenue is not None:
        rows.append(("Revenue", format_money(item.revenue, item.currency, item.scale, per_share=per_share)))
        if item.earnings:
            rows.append(("Trailing margin", format_percent(item.earnings / item.revenue)))
    if item.revenue_growth is not None:
        rows.append(("Revenue growth", format_percent(item.revenue_growth)))
    if not rows:
        return ""
    return _rows(rows)


def _disclosure_block(disclosure: Disclosure) -> list[str]:
    return ["Disclosure", *_item_lines(disclosure), "Warnings", *_warning_lines(disclosure)]


def _item_lines(disclosure: Disclosure) -> list[str]:
    lines = []
    for item in disclosure.items:
        text = " ".join(item.text.split())
        lines.append(f"  {item.key:<10}{text}")
    return lines


def _warning_lines(disclosure: Disclosure) -> list[str]:
    if not disclosure.warnings:
        return ["  none"]
    return [f"  {' '.join(warning.split())}" for warning in disclosure.warnings]


def _years_phrase(count: int) -> str:
    return "1 year" if count == 1 else f"{count} years"


def _rows(pairs: list[tuple[str, str]]) -> str:
    if not pairs:
        return ""
    width = max(len(label) for label, _value in pairs)
    return "\n".join(f"{label.ljust(width)}  {value}".rstrip() for label, value in pairs)


def _format_field(name: str, value: object, item: Assumptions) -> str:
    if value is None or value == "":
        return "n/a"
    per_share = unit_mode(item) == "per_share"
    if name in RATE_FIELDS and isinstance(value, (int, float)):
        return format_percent(float(value))
    if name in MONEY_FIELDS and isinstance(value, (int, float)):
        share_price = name == "price" or per_share
        scale = "unit" if name == "price" else item.scale
        return format_money(float(value), item.currency, scale, per_share=share_price and name != "market_cap")
    if name == "shares" and isinstance(value, (int, float)):
        if item.scale == "unit":
            return f"{float(value):,.2f}"
        return f"{float(value):,.2f} {item.scale}"
    if name == "years":
        return str(value)
    if name == "earnings_basis" and isinstance(value, str):
        return value.upper()
    if name == "discount_convention":
        return "end of year" if value == "end_of_year" else str(value)
    return str(value)


def _format_delta(
    name: str,
    before: object,
    after: object,
    left: Assumptions,
    right: Assumptions,
) -> str:
    if isinstance(before, bool) or isinstance(after, bool):
        return "n/a"
    if isinstance(before, (int, float)) and isinstance(after, (int, float)):
        delta = float(after) - float(before)
        if name in RATE_FIELDS or name == "revenue_growth":
            return format_pp(delta)
        if name in MONEY_FIELDS and left.currency == right.currency and left.scale == right.scale:
            per_share = unit_mode(left) == "per_share"
            scale = "unit" if name == "price" else left.scale
            return format_signed_money(delta, left.currency, scale, per_share=per_share and name != "market_cap")
        if name == "years":
            return f"{delta:+.0f}"
    return "n/a"


def _assumptions_dict(item: Assumptions) -> dict[str, Any]:
    return asdict(item)


def _disclosure_dict(disclosure: Disclosure) -> dict[str, Any]:
    return {
        "items": [{"key": item.key, "title": item.title, "text": item.text} for item in disclosure.items],
        "warnings": list(disclosure.warnings),
    }


def _jsonable(value: Any) -> Any:
    if is_dataclass(value) and not isinstance(value, type):
        return _jsonable(asdict(value))
    if isinstance(value, dict):
        return {str(key): _jsonable(inner) for key, inner in value.items()}
    if isinstance(value, (list, tuple)):
        return [_jsonable(inner) for inner in value]
    if isinstance(value, float):
        if value != value or value in (float("inf"), float("-inf")):
            return None
        return value
    return value
