"""Two-stage cash flow to equity, read forwards and backwards.

Year-t earnings are ``E_t = E_0 * (1 + g) ** t``. Cash flow is
``CF_t = payout * E_t``. Each cash flow is discounted ``t`` full years at the
cost of equity. Terminal value at year N is a Gordon perpetuity on the last
cash flow:

    CF_N * (1 + g_T) / (r - g_T)

discounted back N years. Implied growth is the constant ``g`` that sets this
value equal to the price or the market cap.

The loop is the implementation. A closed form of the same sum lives in the
tests, not here, so the two can disagree in public if they ever drift.

Mid-year discounting multiplies that year-end value by ``(1 + r) ** 0.5``.
Tax is not in the formula. Margin and horizon solves reuse the same discounting.
"""

from __future__ import annotations

from dataclasses import dataclass, replace

from whats_priced_in.assumptions import Assumptions, prepare, resolve_target, unit_mode
from whats_priced_in.disclosure import complete, growth_disclosure, growth_warnings
from whats_priced_in.disclosure import Disclosure
from whats_priced_in.errors import ModelError

FORMULA = (
    "E_t = E_0*(1+g)^t; CF_t = payout*E_t; "
    "V = sum_{t=1..N} CF_t/(1+r)^t + CF_N*(1+g_T)/((r-g_T)*(1+r)^N)"
)
MID_YEAR_NOTE = "Mid-year: multiply V by (1+r)^0.5."

_GROWTH_FLOOR = -0.80
_GROWTH_START = 0.50
_GROWTH_CAP = 2.0
_SOLVE_ITERATIONS = 200


@dataclass(frozen=True, slots=True)
class ValueBreakdown:
    explicit_pv: float
    terminal_pv: float
    terminal_value_at_horizon: float
    equity_value: float
    terminal_share: float
    earnings_path: tuple[float, ...]
    cashflow_path: tuple[float, ...]

    @property
    def year_n_earnings(self) -> float:
        return self.earnings_path[-1]


@dataclass(frozen=True, slots=True)
class Valuation:
    """Forward value at a chosen growth rate."""

    growth: float
    breakdown: ValueBreakdown
    assumptions: Assumptions
    disclosure: Disclosure
    unit_mode: str
    target: float | None

    @property
    def key_assumptions(self) -> dict[str, str]:
        from whats_priced_in.formatting import key_assumptions_payload

        return key_assumptions_payload(self.assumptions)

    def __str__(self) -> str:
        from whats_priced_in.formatting import format_valuation

        return _one_line_less(format_valuation(self))


@dataclass(frozen=True, slots=True)
class SolveGrowthResult:
    """The constant growth rate that sets model value equal to the target."""

    implied_growth: float
    target: float
    per_share: bool
    breakdown: ValueBreakdown
    assumptions: Assumptions
    disclosure: Disclosure
    unit_mode: str

    @property
    def key_assumptions(self) -> dict[str, str]:
        from whats_priced_in.formatting import key_assumptions_payload

        return key_assumptions_payload(self.assumptions)

    def __str__(self) -> str:
        from whats_priced_in.formatting import format_solve_growth

        return _one_line_less(format_solve_growth(self))


@dataclass(frozen=True, slots=True)
class MarginResult:
    """The margin path that sets model value equal to the target.

    Revenue grows at ``revenue_growth``. Margin is constant, or it fades in a
    straight line from ``margin_start`` in year 1 to ``margin_end`` in year N.
    Earnings in year t are revenue in year t times that year's margin. From
    there the cash flows are the same two-stage model.
    """

    margin_start: float
    margin_end: float
    constant: bool
    revenue_growth: float
    target: float
    per_share: bool
    breakdown: ValueBreakdown
    revenue_path: tuple[float, ...]
    margin_path: tuple[float, ...]
    assumptions: Assumptions
    disclosure: Disclosure
    unit_mode: str
    trailing_margin: float | None

    @property
    def key_assumptions(self) -> dict[str, str]:
        from whats_priced_in.formatting import format_percent, key_assumptions_payload

        return key_assumptions_payload(
            self.assumptions,
            extra=[("revenue growth", format_percent(self.revenue_growth))],
        )

    def __str__(self) -> str:
        from whats_priced_in.formatting import format_margin

        return _one_line_less(format_margin(self))


@dataclass(frozen=True, slots=True)
class YearPoint:
    years: int
    equity_value: float
    gap: float


@dataclass(frozen=True, slots=True)
class YearsResult:
    growth: float
    target: float
    closest_years: int
    closest_value: float
    gap: float
    years_that_clear: int | None
    identified: bool
    direction: str
    note: str
    grid: tuple[YearPoint, ...]
    assumptions: Assumptions
    disclosure: Disclosure
    unit_mode: str

    @property
    def key_assumptions(self) -> dict[str, str]:
        from whats_priced_in.formatting import format_percent, key_assumptions_payload

        payload = key_assumptions_payload(
            self.assumptions,
            extra=[("growth held fixed", format_percent(self.growth))],
        )
        # The file's year count is not the horizon this solve used. The grid is.
        if self.grid:
            payload["explicit years"] = f"searched 1 through {self.grid[-1].years}"
        return payload

    def __str__(self) -> str:
        from whats_priced_in.formatting import format_years

        return _one_line_less(format_years(self))


def _one_line_less(text: str) -> str:
    if text.endswith("\n"):
        return text[:-1]
    return text


def forward_earnings(earnings0: float, growth: float, years: int) -> tuple[float, ...]:
    """Earnings in years 1..N. Year 1 is the starting figure grown once."""

    if years < 1:
        raise ModelError("years must be at least 1.")
    if growth <= -1:
        raise ModelError("growth of -100% or worse wipes the earnings path.")
    level = earnings0
    path: list[float] = []
    for _ in range(years):
        level *= 1.0 + growth
        path.append(level)
    return tuple(path)


def value_growth(growth: float, assumptions: Assumptions) -> Valuation:
    """Forward equity value at a constant earnings growth rate."""

    item = prepare(assumptions)
    _check_growth_rate(growth)
    if item.earnings == 0:
        breakdown = _zero_breakdown(item.years)
    else:
        earnings = forward_earnings(item.earnings, growth, item.years)
        breakdown = _value_earnings_path(earnings, item)
    mode = unit_mode(item)
    disclosure = complete(
        growth_disclosure(item).with_warnings(
            growth_warnings(item, growth, breakdown.terminal_share)
        )
    )
    return Valuation(
        growth=growth,
        breakdown=breakdown,
        assumptions=item,
        disclosure=disclosure,
        unit_mode=mode,
        target=resolve_target(item),
    )


def solve_growth(assumptions: Assumptions, target: float | None = None) -> SolveGrowthResult:
    """Bisect for the constant growth rate that matches ``target``.

    The search runs from -80% to at most 200%, two hundred bisections. Value is
    increasing in growth when earnings and payout are positive, which is required.
    """

    item = prepare(assumptions)
    if target is None:
        target = resolve_target(item)
    if target is None:
        raise ModelError("Pass a price, or a market cap, or a price and a share count.")
    if item.earnings <= 0:
        raise ModelError(
            "Implied growth needs positive earnings. Negative earnings make value fall as growth rises."
        )
    if item.payout == 0:
        raise ModelError(
            "Payout is zero, so every price is unexplained. Raise the payout, or value an explicit cash-flow path."
        )
    if item.payout < 0:
        raise ModelError("payout must be non-negative.")

    def at(rate: float) -> float:
        return value_growth(rate, item).breakdown.equity_value

    low = _GROWTH_FLOOR
    high = _GROWTH_START
    value_low = at(low)
    value_high = at(high)
    if value_high <= value_low:
        raise ModelError(
            "Value is not increasing in growth, so implied growth is not identified. "
            "Earnings and payout need to be positive, and cost of equity must exceed terminal growth."
        )
    if target < value_low:
        raise ModelError(
            f"The target is below the model value at {_GROWTH_FLOOR:.0%} growth "
            f"({value_low:.4g}). Implied growth is not inside the search."
        )
    while value_high < target and high < _GROWTH_CAP - 1e-15:
        high = min(_GROWTH_CAP, high + 0.25)
        value_high = at(high)
    if value_high < target:
        raise ModelError(
            f"Even {high:.0%} growth does not reach the target ({value_high:.4g} versus {target:.4g}). "
            "Check the earnings base, the payout, and the cost of equity."
        )
    for _ in range(_SOLVE_ITERATIONS):
        mid = (low + high) / 2.0
        if at(mid) < target:
            low = mid
        else:
            high = mid
    implied = (low + high) / 2.0
    valuation = value_growth(implied, item)
    return SolveGrowthResult(
        implied_growth=implied,
        target=target,
        per_share=valuation.unit_mode == "per_share",
        breakdown=valuation.breakdown,
        assumptions=item,
        disclosure=valuation.disclosure,
        unit_mode=valuation.unit_mode,
    )


def solve_margin(
    assumptions: Assumptions,
    revenue_growth: float | None = None,
    margin_start: float | None = None,
    target: float | None = None,
) -> MarginResult:
    """Solve a constant margin, or the year-N margin of a straight-line fade.

    ``margin_start`` left empty means the margin is constant. Set it, and the
    solve returns the year-N margin, with year 1 held at ``margin_start``.
    Value is linear in that unknown margin, so the solve is two valuations,
    not a search.
    """

    item = prepare(assumptions)
    if item.revenue is None:
        raise ModelError("Margin solve needs revenue, in the same scale as the target.")
    growth = item.revenue_growth if revenue_growth is None else revenue_growth
    if growth is None:
        raise ModelError("Margin solve needs revenue_growth (a decimal, such as 0.06).")
    if growth <= -1 or growth > 3:
        raise ModelError("revenue_growth must be greater than -100% and at most 300%.")
    if target is None:
        target = resolve_target(item)
    if target is None:
        raise ModelError("Pass a price, or a market cap, or a price and a share count.")
    if item.payout <= 0:
        raise ModelError("Margin solve needs a positive payout. At zero payout the value is zero.")

    constant = margin_start is None
    start = 0.0 if margin_start is None else margin_start
    if margin_start is not None and (margin_start <= -1 or margin_start > 2):
        raise ModelError("margin_start looks wrong. Pass a decimal margin, such as 0.20.")

    def value_at(end_margin: float) -> float:
        path_start = end_margin if constant else start
        earnings, _revenues, _margins = _margin_earnings(
            item.revenue, growth, item.years, path_start, end_margin
        )
        return _value_earnings_path(earnings, item).equity_value

    low_margin = 0.0
    high_margin = 1.0
    value_low = value_at(low_margin)
    value_high = value_at(high_margin)
    slope = value_high - value_low
    if slope <= 0:
        raise ModelError(
            "Raising the margin does not raise value. Check that revenue and payout are positive."
        )
    solved = low_margin + (target - value_low) * (high_margin - low_margin) / slope
    used_start = solved if constant else start
    earnings, revenues, margins = _margin_earnings(
        item.revenue, growth, item.years, used_start, solved
    )
    breakdown = _value_earnings_path(earnings, item)
    if abs(breakdown.equity_value - target) > max(1e-6, abs(target) * 1e-8):
        raise ModelError(
            "Margin solve residual is larger than the linearity of the model allows. This is a bug."
        )
    # A constant margin means earnings grow at the revenue growth rate, so the
    # payout warning can use that rate. A fade is not one growth rate; the
    # revenue growth is still the right flag for "is this path above terminal?"
    disclosure = complete(
        growth_disclosure(item).with_warnings(
            growth_warnings(item, growth, breakdown.terminal_share)
        )
    )
    trailing = None
    if item.earnings > 0 and item.revenue:
        trailing = item.earnings / item.revenue
    return MarginResult(
        margin_start=used_start,
        margin_end=solved,
        constant=constant,
        revenue_growth=growth,
        target=target,
        per_share=unit_mode(item) == "per_share",
        breakdown=breakdown,
        revenue_path=revenues,
        margin_path=margins,
        assumptions=item,
        disclosure=disclosure,
        unit_mode=unit_mode(item),
        trailing_margin=trailing,
    )


def solve_years(
    assumptions: Assumptions,
    growth: float,
    target: float | None = None,
    max_years: int = 20,
) -> YearsResult:
    """Find the explicit horizon that comes closest to the target, at a fixed growth.

    When growth equals terminal growth the value does not depend on the horizon
    (it is a growing perpetuity) and years are not identified. When growth is
    above the terminal rate, a longer horizon is worth more. When it is below,
    a longer horizon is worth less.
    """

    item = prepare(assumptions)
    _check_growth_rate(growth)
    if target is None:
        target = resolve_target(item)
    if target is None:
        raise ModelError("Pass a price, or a market cap, or a price and a share count.")
    if isinstance(max_years, bool) or not isinstance(max_years, int) or max_years < 1 or max_years > 100:
        raise ModelError("max_years must be an integer from 1 to 100.")
    if item.earnings <= 0 or item.payout <= 0:
        raise ModelError("Horizon solve needs positive earnings and a positive payout.")

    grid: list[YearPoint] = []
    for years in range(1, max_years + 1):
        trial = replace(item, years=years)
        equity = value_growth(growth, trial).breakdown.equity_value
        grid.append(YearPoint(years=years, equity_value=equity, gap=equity - target))

    span = grid[-1].equity_value - grid[0].equity_value
    flat = abs(growth - item.terminal_growth) <= 1e-12 or abs(span) <= max(1e-8, abs(target) * 1e-10)
    if flat:
        direction = "flat"
    elif span > 0:
        direction = "increasing"
    else:
        direction = "decreasing"

    closest = min(grid, key=lambda point: (abs(point.gap), point.years))
    clears = _years_that_clear(grid, direction)
    base_years = min(item.years, max_years)
    disclosure = value_growth(growth, replace(item, years=base_years)).disclosure

    if direction == "flat":
        note = (
            "Explicit growth equals terminal growth, so the horizon does not change the value. "
            "It collapses to a growing perpetuity. Implied years are not identified."
        )
        identified = False
        years_that_clear = None
    else:
        identified = True
        years_that_clear = clears
        if direction == "increasing":
            if clears is None:
                note = (
                    f"Value rises with the horizon and still sits short of the target at {max_years} years. "
                    f"Closest is {_years_phrase(closest.years)}."
                )
            else:
                note = (
                    f"No integer horizon hits the target exactly. Closest is {_years_phrase(closest.years)}. "
                    f"The model first clears the target at {_years_phrase(clears)}."
                )
        else:
            if clears is None:
                note = (
                    "Value falls as the horizon gets longer, because explicit growth is below the terminal rate, "
                    "and even 1 year is short of the target."
                )
            else:
                note = (
                    "Value falls as the horizon gets longer, because explicit growth is below the terminal rate. "
                    f"The target stays cleared through {_years_phrase(clears)}."
                )

    return YearsResult(
        growth=growth,
        target=target,
        closest_years=closest.years,
        closest_value=closest.equity_value,
        gap=closest.gap,
        years_that_clear=years_that_clear,
        identified=identified,
        direction=direction,
        note=note,
        grid=tuple(grid),
        assumptions=item,
        disclosure=disclosure,
        unit_mode=unit_mode(item),
    )


def _years_phrase(count: int) -> str:
    return "1 year" if count == 1 else f"{count} years"


def _years_that_clear(grid: list[YearPoint], direction: str) -> int | None:
    clearing = [point.years for point in grid if point.gap >= -1e-8]
    if not clearing:
        return None
    if direction == "decreasing":
        return max(clearing)
    return min(clearing)


def _margin_earnings(
    revenue0: float,
    revenue_growth: float,
    years: int,
    margin_start: float,
    margin_end: float,
) -> tuple[tuple[float, ...], tuple[float, ...], tuple[float, ...]]:
    revenues = forward_earnings(revenue0, revenue_growth, years)
    margins: list[float] = []
    earnings: list[float] = []
    for index, revenue in enumerate(revenues, start=1):
        margin = _margin_on_year(index, years, margin_start, margin_end)
        margins.append(margin)
        earnings.append(revenue * margin)
    return tuple(earnings), revenues, tuple(margins)


def _margin_on_year(year: int, years: int, start: float, end: float) -> float:
    if years <= 1:
        return end
    return start + (end - start) * (year - 1) / (years - 1)


def _value_earnings_path(earnings: tuple[float, ...], assumptions: Assumptions) -> ValueBreakdown:
    cashflows = tuple(assumptions.payout * level for level in earnings)
    terminal = _gordon(cashflows[-1], assumptions.terminal_growth, assumptions.cost_of_equity)
    explicit, terminal_pv = _present_value(
        cashflows, terminal, assumptions.cost_of_equity, assumptions.discount_convention
    )
    equity = explicit + terminal_pv
    share = terminal_pv / equity if equity else float("nan")
    return ValueBreakdown(
        explicit_pv=explicit,
        terminal_pv=terminal_pv,
        terminal_value_at_horizon=terminal,
        equity_value=equity,
        terminal_share=share,
        earnings_path=earnings,
        cashflow_path=cashflows,
    )


def _zero_breakdown(years: int) -> ValueBreakdown:
    zeros = tuple(0.0 for _ in range(years))
    return ValueBreakdown(
        explicit_pv=0.0,
        terminal_pv=0.0,
        terminal_value_at_horizon=0.0,
        equity_value=0.0,
        terminal_share=float("nan"),
        earnings_path=zeros,
        cashflow_path=zeros,
    )


def _gordon(last_cashflow: float, terminal_growth: float, cost_of_equity: float) -> float:
    spread = cost_of_equity - terminal_growth
    if spread <= 0:
        raise ModelError(
            "Cost of equity must exceed terminal growth. "
            f"Got cost of equity {cost_of_equity:.2%} and terminal growth {terminal_growth:.2%}."
        )
    return last_cashflow * (1.0 + terminal_growth) / spread


def _present_value(
    cashflows: tuple[float, ...],
    terminal_at_horizon: float,
    cost_of_equity: float,
    convention: str,
) -> tuple[float, float]:
    explicit = 0.0
    for year, cashflow in enumerate(cashflows, start=1):
        explicit += cashflow / (1.0 + cost_of_equity) ** year
    terminal_pv = terminal_at_horizon / (1.0 + cost_of_equity) ** len(cashflows)
    if convention == "mid_year":
        shift = (1.0 + cost_of_equity) ** 0.5
        explicit *= shift
        terminal_pv *= shift
    elif convention != "end_of_year":
        raise ModelError(f"Unknown discount convention {convention!r}.")
    return explicit, terminal_pv


def _check_growth_rate(growth: float) -> None:
    if isinstance(growth, bool) or not isinstance(growth, (int, float)):
        raise ModelError("growth must be a decimal.")
    if growth != growth or growth in (float("inf"), float("-inf")):
        raise ModelError("growth must be finite.")
    if growth <= -1:
        raise ModelError("growth of -100% or worse wipes the earnings path.")
    if growth > 3:
        raise ModelError("growth above 300% is rejected. Pass a decimal, such as 0.08 for 8%.")
