"""Forward value and implied-growth tables."""

from whats_priced_in.disclosure import equity_items, percent, render_disclosure
from whats_priced_in.model import VERSION, implied_growth, present_value
from whats_priced_in.render import flow, header, join_sections, key_block, key_pairs, signed_percent

GROWTH_VALUES = [0.0, 0.02, 0.04, 0.06, 0.08, 0.10, 0.12, 0.15, 0.20]
COST_OF_EQUITY_VALUES = [0.09, 0.10, 0.11, 0.12, 0.13]
TERMINAL_VALUES = [0.02, 0.03, 0.04, 0.05, 0.06]
PAYOUT_VALUES = [0.60, 0.80, 1.00]

PARAMETER_LABELS = {
    "cost_of_equity": "cost of equity",
    "terminal_growth": "terminal growth",
    "payout": "payout",
    "growth": "growth",
}
DEFAULT_GRIDS = {
    "growth": GROWTH_VALUES,
    "cost_of_equity": COST_OF_EQUITY_VALUES,
    "terminal_growth": TERMINAL_VALUES,
    "payout": PAYOUT_VALUES,
}


class SensitivityReading:
    def __init__(self, text, payload, key_assumptions, disclosure, assumptions, warnings):
        self.text = text
        self.payload = payload
        self.key_assumptions = key_assumptions
        self.disclosure = disclosure
        self.assumptions = assumptions
        self.warnings = warnings
        self.mode = "sens"
        self.implied_growth = None

    def __str__(self):
        return self.text


def run_sensitivity(assumptions, parameter=None, values=None):
    assumptions.require_equity()
    base = implied_growth(
        assumptions.earnings,
        assumptions.cost_of_equity,
        assumptions.terminal_growth,
        assumptions.years,
        assumptions.payout,
        assumptions.target(),
        assumptions.discount_convention,
    )
    items, warnings = equity_items(assumptions, base.growth, assumptions.years)
    pairs = key_pairs(assumptions, base.growth)
    chosen = _selection(parameter, values)
    tables = []
    blocks = []
    for name, grid in chosen:
        if name == "growth":
            table, block = _growth_table(assumptions, grid)
        else:
            table, block = _implied_table(assumptions, name, grid)
        tables.append(table)
        blocks.append(block)
    text = join_sections(
        [
            header(assumptions),
            key_block(pairs),
            *blocks,
            render_disclosure(items, warnings),
            "Not a recommendation. Each row moves one input.",
        ]
    )
    payload = {
        "model": "two_stage_fcfe_gordon",
        "version": VERSION,
        "mode": "sens",
        "key_assumptions": dict(pairs),
        "tables": tables,
        "disclosure": {"items": items, "warnings": warnings},
        "warnings": warnings,
    }
    return SensitivityReading(text, payload, dict(pairs), render_disclosure(items, warnings), assumptions, warnings)


def _selection(parameter, values):
    if parameter is None and values is not None:
        raise ValueError("Pass --parameter with --values.")
    if parameter is None:
        return [
            ("growth", GROWTH_VALUES),
            ("cost_of_equity", COST_OF_EQUITY_VALUES),
            ("terminal_growth", TERMINAL_VALUES),
            ("payout", PAYOUT_VALUES),
        ]
    if parameter not in PARAMETER_LABELS:
        known = ", ".join(PARAMETER_LABELS)
        raise ValueError(f"Parameter must be one of {known}.")
    grid = DEFAULT_GRIDS[parameter] if values is None else values
    return [(parameter, grid)]


def _growth_table(assumptions, grid):
    target = assumptions.target()
    rows = []
    lines = [
        "Value if growth is this, and every other assumption stays put.",
        "",
        f"{'growth':<14}{'model value':<24}vs target",
    ]
    for growth in grid:
        _reject_if_percent("growth", growth)
        valuation = present_value(
            assumptions.earnings,
            growth,
            assumptions.cost_of_equity,
            assumptions.terminal_growth,
            assumptions.years,
            assumptions.payout,
            assumptions.discount_convention,
        )
        versus = (valuation.equity_value - target) / target
        rows.append(
            {
                "value": growth,
                "equity_value": valuation.equity_value,
                "versus_target": versus,
                "note": "",
            }
        )
        lines.append(
            f"{percent(growth):<14}{flow(valuation.equity_value, assumptions):<24}{signed_percent(versus)}"
        )
    return {
        "parameter": "growth",
        "kind": "forward_value",
        "base": None,
        "target": target,
        "rows": rows,
    }, "\n".join(lines)


def _implied_table(assumptions, parameter, grid):
    label = PARAMETER_LABELS[parameter]
    base = getattr(assumptions, parameter)
    target = assumptions.target()
    rows = []
    for value in grid:
        _reject_if_percent(parameter, value)
        trial = assumptions.replace(**{parameter: value})
        valuation = implied_growth(
            trial.earnings,
            trial.cost_of_equity,
            trial.terminal_growth,
            trial.years,
            trial.payout,
            trial.target(),
            trial.discount_convention,
        )
        rows.append(
            {
                "value": value,
                "implied_growth": valuation.growth,
                "equity_value": valuation.equity_value,
                "versus_target": valuation.equity_value - trial.target(),
                "note": "",
            }
        )
    lines = [
        f"Implied growth if {label} changes. Price and earnings stay put.",
        f"Base {label}: {percent(base)}.",
        "",
        f"{'value':<14}implied growth",
    ]
    for row in rows:
        lines.append(f"{percent(row['value']):<14}{percent(row['implied_growth'])}")
    return {
        "parameter": parameter,
        "kind": "implied_growth",
        "base": base,
        "target": target,
        "rows": rows,
    }, "\n".join(lines)


def _reject_if_percent(parameter, value):
    if parameter != "payout" and abs(value) >= 1:
        raise ValueError(f"Rates are decimals: 0.11, not 11. {PARAMETER_LABELS[parameter]} is {value}.")
    if parameter == "payout" and (value < 0 or value > 1):
        raise ValueError("Payout is a decimal from 0 to 1. 100% is 1, not 100.")
