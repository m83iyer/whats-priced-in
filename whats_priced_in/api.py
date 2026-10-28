"""Public solves. Numbers in, numbers out."""

from whats_priced_in.disclosure import equity_items, render_disclosure
from whats_priced_in.model import (
    FORMULA,
    MODEL_NAME,
    VERSION,
    HORIZON_LIMIT,
    implied_growth,
    present_value,
)
from whats_priced_in.render import (
    growth_text,
    horizon_text,
    key_pairs,
    margin_text,
    value_text,
)


class Reading:
    def __init__(self, text, payload, assumptions, implied_growth, key_assumptions, disclosure, warnings, mode, valuation=None):
        self.text = text
        self.payload = payload
        self.assumptions = assumptions
        self.implied_growth = implied_growth
        self.key_assumptions = key_assumptions
        self.disclosure = disclosure
        self.warnings = warnings
        self.mode = mode
        self.valuation = valuation

    def __str__(self):
        return self.text


def solve_growth(assumptions):
    target = assumptions.require_equity()
    valuation = implied_growth(
        assumptions.earnings,
        assumptions.cost_of_equity,
        assumptions.terminal_growth,
        assumptions.years,
        assumptions.payout,
        target,
        assumptions.discount_convention,
    )
    items, warnings = equity_items(assumptions, valuation.growth, assumptions.years)
    pairs = key_pairs(assumptions, valuation.growth)
    text = growth_text(assumptions, valuation, items, warnings)
    payload = {
        "model": MODEL_NAME,
        "version": VERSION,
        "mode": "growth",
        "formula": FORMULA,
        "ticker": assumptions.ticker,
        "name": assumptions.name,
        "currency": assumptions.currency,
        "scale": assumptions.scale,
        "unit_mode": "per_share" if assumptions.per_share else "aggregate",
        "per_share": assumptions.per_share,
        "implied_growth": valuation.growth,
        "key_assumptions": dict(pairs),
        "target": target,
        "equity_value": valuation.equity_value,
        "residual": valuation.equity_value - target,
        "explicit_pv": valuation.explicit_pv,
        "terminal_pv": valuation.terminal_pv,
        "terminal_value_at_horizon": valuation.terminal_value_at_horizon,
        "terminal_share": valuation.terminal_share,
        "year_n_earnings": valuation.year_n_earnings,
        "earnings_path": valuation.earnings_path,
        "cashflow_path": valuation.cashflow_path,
        "assumptions": _assumption_payload(assumptions),
        "disclosure": {"items": items, "warnings": warnings},
        "warnings": list(warnings),
    }
    return Reading(
        text,
        payload,
        assumptions,
        valuation.growth,
        dict(pairs),
        render_disclosure(items, warnings),
        warnings,
        "growth",
        valuation,
    )


def value_growth(growth, assumptions):
    _rate("growth", growth)
    target = assumptions.require_equity()
    valuation = present_value(
        assumptions.earnings,
        growth,
        assumptions.cost_of_equity,
        assumptions.terminal_growth,
        assumptions.years,
        assumptions.payout,
        assumptions.discount_convention,
    )
    items, warnings = equity_items(assumptions, growth, assumptions.years)
    pairs = key_pairs(assumptions, growth)
    text = value_text(assumptions, valuation, items, warnings)
    payload = {
        "model": MODEL_NAME,
        "version": VERSION,
        "mode": "value",
        "formula": FORMULA,
        "growth": growth,
        "equity_value": valuation.equity_value,
        "key_assumptions": dict(pairs),
        "target": target,
        "explicit_pv": valuation.explicit_pv,
        "terminal_pv": valuation.terminal_pv,
        "terminal_share": valuation.terminal_share,
        "year_n_earnings": valuation.year_n_earnings,
        "assumptions": _assumption_payload(assumptions),
        "disclosure": {"items": items, "warnings": warnings},
        "warnings": list(warnings),
    }
    return Reading(
        text,
        payload,
        assumptions,
        growth,
        dict(pairs),
        render_disclosure(items, warnings),
        warnings,
        "value",
        valuation,
    )


def solve_margin(assumptions, revenue_growth):
    _rate("revenue_growth", revenue_growth)
    if assumptions.revenue is None or assumptions.revenue <= 0:
        raise ValueError("A margin solve needs positive revenue.")
    target = assumptions.require_equity()
    unit = present_value(
        assumptions.revenue,
        revenue_growth,
        assumptions.cost_of_equity,
        assumptions.terminal_growth,
        assumptions.years,
        assumptions.payout,
        assumptions.discount_convention,
    )
    if unit.equity_value == 0:
        raise ValueError("Revenue does not produce a value to scale.")
    margin = target / unit.equity_value
    items, warnings = equity_items(assumptions, revenue_growth, assumptions.years)
    extras = [("revenue growth", f"{revenue_growth * 100:.2f}%")]
    pairs = key_pairs(assumptions, revenue_growth, extras=extras)
    text = margin_text(assumptions, margin, revenue_growth, items, warnings)
    payload = {
        "model": MODEL_NAME,
        "version": VERSION,
        "mode": "margin",
        "margin": margin,
        "revenue_growth": revenue_growth,
        "key_assumptions": dict(pairs),
        "target": target,
        "assumptions": _assumption_payload(assumptions),
        "disclosure": {"items": items, "warnings": warnings},
        "warnings": list(warnings),
    }
    return Reading(
        text,
        payload,
        assumptions,
        None,
        dict(pairs),
        render_disclosure(items, warnings),
        warnings,
        "margin",
    )


def solve_years(assumptions, growth):
    _rate("growth", growth)
    target = assumptions.require_equity()
    grid = []
    for years in range(1, HORIZON_LIMIT + 1):
        valuation = present_value(
            assumptions.earnings,
            growth,
            assumptions.cost_of_equity,
            assumptions.terminal_growth,
            years,
            assumptions.payout,
            assumptions.discount_convention,
        )
        grid.append(
            {
                "years": years,
                "value": valuation.equity_value,
                "gap": valuation.equity_value - target,
            }
        )
    items, warnings = equity_items(assumptions, growth, assumptions.years)
    extras = [("growth held fixed", f"{growth * 100:.2f}%")]
    pairs = key_pairs(assumptions, growth, years_text="searched 1 through 20", extras=extras)
    text = horizon_text(assumptions, growth, grid, items, warnings)
    payload = {
        "model": MODEL_NAME,
        "version": VERSION,
        "mode": "years",
        "growth": growth,
        "grid": grid,
        "key_assumptions": dict(pairs),
        "target": target,
        "assumptions": _assumption_payload(assumptions),
        "disclosure": {"items": items, "warnings": warnings},
        "warnings": list(warnings),
    }
    return Reading(
        text,
        payload,
        assumptions,
        None,
        dict(pairs),
        render_disclosure(items, warnings),
        warnings,
        "years",
    )


def _assumption_payload(assumptions):
    return {
        "currency": assumptions.currency,
        "scale": assumptions.scale,
        "earnings": assumptions.earnings,
        "cost_of_equity": assumptions.cost_of_equity,
        "terminal_growth": assumptions.terminal_growth,
        "years": assumptions.years,
        "payout": assumptions.payout,
        "earnings_basis": assumptions.earnings_basis,
        "discount_convention": assumptions.discount_convention,
        "ticker": assumptions.ticker,
        "name": assumptions.name,
        "price": assumptions.price,
        "shares": assumptions.shares,
        "market_cap": assumptions.market_cap,
        "revenue": assumptions.revenue,
        "revenue_growth": assumptions.revenue_growth,
        "tax_rate": assumptions.tax_rate,
        "notes": assumptions.notes,
    }


def _rate(name, value):
    if value is None:
        raise ValueError(f"Need a {name.replace('_', ' ')}.")
    if abs(value) >= 1:
        raise ValueError(f"Rates are decimals: 0.11, not 11. {name.replace('_', ' ')} is {value}.")
