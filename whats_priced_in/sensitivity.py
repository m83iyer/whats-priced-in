"""Sensitivity tables. One assumption moves. The rest stay put, and say so."""

from __future__ import annotations

from dataclasses import dataclass, replace

from whats_priced_in.assumptions import Assumptions, prepare, resolve_target
from whats_priced_in.dcf import Valuation, solve_growth, value_growth
from whats_priced_in.disclosure import Disclosure
from whats_priced_in.errors import ModelError

GROWTH_GRID = (0.0, 0.02, 0.04, 0.06, 0.08, 0.10, 0.12, 0.15, 0.20)
PAYOUT_GRID = (0.60, 0.80, 1.0)
TERMINAL_GRID = (0.02, 0.03, 0.04, 0.05, 0.06)


@dataclass(frozen=True, slots=True)
class SensRow:
    parameter: str
    value: float
    implied_growth: float | None
    equity_value: float | None
    versus_target: float | None
    note: str = ""


@dataclass(frozen=True, slots=True)
class SensTable:
    parameter: str
    kind: str
    base: float | None
    rows: tuple[SensRow, ...]
    assumptions: Assumptions
    disclosure: Disclosure
    target: float | None

    @property
    def key_assumptions(self) -> dict[str, str]:
        from whats_priced_in.formatting import key_assumptions_payload

        return key_assumptions_payload(self.assumptions)

    def __str__(self) -> str:
        from whats_priced_in.formatting import format_sensitivity

        text = format_sensitivity([self])
        return text[:-1] if text.endswith("\n") else text


def value_sensitivity(
    assumptions: Assumptions,
    growth_rates: tuple[float, ...] | list[float] | None = None,
) -> SensTable:
    """Equity value if growth is each rate in the grid. Other inputs stay put."""

    item = prepare(assumptions)
    rates = tuple(GROWTH_GRID if growth_rates is None else growth_rates)
    target = resolve_target(item)
    rows: list[SensRow] = []
    anchor: Valuation | None = None
    for rate in rates:
        try:
            valuation = value_growth(rate, item)
        except ModelError as exc:
            rows.append(SensRow("growth", float(rate), float(rate), None, None, str(exc)))
            continue
        if anchor is None:
            anchor = valuation
        versus = None if target is None else valuation.breakdown.equity_value / target - 1.0
        rows.append(
            SensRow(
                parameter="growth",
                value=float(rate),
                implied_growth=float(rate),
                equity_value=valuation.breakdown.equity_value,
                versus_target=versus,
            )
        )
    if anchor is None:
        raise ModelError("None of the growth rates could be valued.")
    disclosure = anchor.disclosure
    if target is not None:
        try:
            disclosure = solve_growth(item, target).disclosure
        except ModelError:
            disclosure = anchor.disclosure
    return SensTable(
        parameter="growth",
        kind="value",
        base=None,
        rows=tuple(rows),
        assumptions=item,
        disclosure=disclosure,
        target=target,
    )


def implied_growth_sensitivity(
    assumptions: Assumptions,
    parameter: str,
    values: tuple[float, ...] | list[float] | None = None,
) -> SensTable:
    """Implied growth if one discount or payout assumption changes.

    The price and the earnings stay put. ``parameter`` is ``cost_of_equity``,
    ``terminal_growth``, ``payout``, or ``years``.
    """

    item = prepare(assumptions)
    if parameter not in {"cost_of_equity", "terminal_growth", "payout", "years"}:
        raise ModelError(
            "Sensitivity parameter must be cost_of_equity, terminal_growth, payout, or years."
        )
    grid = tuple(values) if values is not None else _default_grid(item, parameter)
    target = resolve_target(item)
    if target is None:
        raise ModelError("Implied-growth sensitivity needs a price or a market cap.")
    rows: list[SensRow] = []
    try:
        disclosure = solve_growth(item, target).disclosure
    except ModelError:
        disclosure = None
    for raw in grid:
        trial, note = _with_parameter(item, parameter, raw)
        if trial is None:
            rows.append(SensRow(parameter, float(raw), None, None, None, note))
            continue
        try:
            solved = solve_growth(trial, target=target)
        except ModelError as exc:
            rows.append(SensRow(parameter, float(raw), None, None, None, str(exc)))
            continue
        if disclosure is None:
            disclosure = solved.disclosure
        rows.append(
            SensRow(
                parameter=parameter,
                value=float(raw),
                implied_growth=solved.implied_growth,
                equity_value=solved.breakdown.equity_value,
                versus_target=solved.breakdown.equity_value / target - 1.0,
                note=note,
            )
        )
    if disclosure is None:
        # Every row failed. Still disclose the base assumptions.
        disclosure = value_growth(item.terminal_growth, item).disclosure
    base = {
        "cost_of_equity": item.cost_of_equity,
        "terminal_growth": item.terminal_growth,
        "payout": item.payout,
        "years": float(item.years),
    }[parameter]
    return SensTable(
        parameter=parameter,
        kind="implied_growth",
        base=base,
        rows=tuple(rows),
        assumptions=item,
        disclosure=disclosure,
        target=target,
    )


def _default_grid(item: Assumptions, parameter: str) -> tuple[float, ...]:
    if parameter == "cost_of_equity":
        rates = tuple(item.cost_of_equity + step for step in (-0.02, -0.01, 0.0, 0.01, 0.02))
        return tuple(rate for rate in rates if rate > item.terminal_growth and 0 < rate < 1)
    if parameter == "terminal_growth":
        return tuple(rate for rate in TERMINAL_GRID if rate < item.cost_of_equity)
    if parameter == "payout":
        return PAYOUT_GRID
    horizons = [5, 10, 15, 20]
    if item.years not in horizons:
        horizons.append(item.years)
    return tuple(sorted(set(horizons)))


def _with_parameter(item: Assumptions, parameter: str, raw: float) -> tuple[Assumptions | None, str]:
    if parameter == "years":
        if int(raw) != raw or raw < 1 or raw > 100:
            return None, "years must be an integer from 1 to 100."
        return replace(item, years=int(raw)), ""
    if parameter == "cost_of_equity":
        if raw <= item.terminal_growth or raw <= 0 or raw >= 1:
            return None, "cost of equity must exceed terminal growth and be a decimal below 1."
        return replace(item, cost_of_equity=raw), ""
    if parameter == "terminal_growth":
        if raw >= item.cost_of_equity or raw <= -0.5 or raw >= 1:
            return None, "terminal growth must be a decimal below the cost of equity."
        return replace(item, terminal_growth=raw), ""
    if raw < 0 or raw > 5:
        return None, "payout must be a fraction of earnings."
    return replace(item, payout=raw), ""
