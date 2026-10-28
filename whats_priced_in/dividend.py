"""Dividend yield, coverage, and the growth a promised dividend needs.

This is the REIT / holding-company reading. It is not the two-stage earnings
model. A promised dividend and a price imply a cash yield immediately. With a
cost of equity they also imply a perpetual growth rate.

Next-dividend identity (the default, ``dividend_timing='next'``):

    price = D1 / (r - g)    so    g = r - D1 / price

Trailing identity:

    price = D0 * (1 + g) / (r - g)
    g = (price * r - D0) / (price + D0)

Scenarios in the next-dividend case hold D1 fixed and vary growth after that
distribution. Tax is not applied. Coverage is earnings divided by the dividend you
typed. Periods are not aligned for you.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from whats_priced_in.assumptions import _read_mapping
from whats_priced_in.disclosure import Disclosure, DisclosureItem, complete
from whats_priced_in.errors import ModelError
from whats_priced_in.scales import SCALE_NOTES, normalise_currency, normalise_scale

DEFAULT_DIVIDEND_GROWTHS = (0.0, 0.02, 0.03, 0.04)
_DIVIDEND_FIELDS = (
    "ticker",
    "name",
    "currency",
    "scale",
    "price",
    "annual_dividend",
    "dividend_timing",
    "earnings",
    "earnings_basis",
    "cost_of_equity",
    "growth",
    "notes",
)
_STRING_FIELDS = {
    "ticker",
    "name",
    "currency",
    "scale",
    "dividend_timing",
    "earnings_basis",
    "notes",
}


@dataclass(frozen=True, slots=True)
class DividendCase:
    currency: str
    scale: str
    price: float
    annual_dividend: float
    dividend_timing: str = "next"
    earnings: float | None = None
    earnings_basis: str = "ffo"
    cost_of_equity: float | None = None
    growth: float | None = None
    ticker: str | None = None
    name: str | None = None
    notes: str = ""


@dataclass(frozen=True, slots=True)
class YieldScenario:
    growth: float
    model_value: float | None
    versus_price: float | None
    note: str


@dataclass(frozen=True, slots=True)
class DividendResult:
    price: float
    annual_dividend: float
    dividend_timing: str
    cash_yield: float
    yield_kind: str
    coverage: float | None
    payout: float | None
    implied_growth: float | None
    flat_perpetuity_value: float | None
    scenarios: tuple[YieldScenario, ...]
    case: DividendCase
    disclosure: Disclosure

    @property
    def key_assumptions(self) -> dict[str, str]:
        from whats_priced_in.formatting import dividend_key_assumption_pairs

        return dict(dividend_key_assumption_pairs(self))

    def __str__(self) -> str:
        from whats_priced_in.formatting import format_dividend

        text = format_dividend(self)
        return text[:-1] if text.endswith("\n") else text


def implied_dividend(
    case: DividendCase,
    growth_scenarios: tuple[float, ...] = DEFAULT_DIVIDEND_GROWTHS,
) -> DividendResult:
    item = prepare_dividend(case)
    if item.annual_dividend < 0:
        raise ModelError("annual_dividend cannot be negative.")
    if item.annual_dividend == 0 and item.price > 0:
        raise ModelError(
            "A zero dividend cannot explain a positive price in this perpetuity. "
            "The cash yield is zero at every growth rate."
        )

    kind = "forward" if item.dividend_timing == "next" else "trailing"
    cash_yield = item.annual_dividend / item.price
    coverage, payout = _coverage(item)
    implied = None
    flat = None
    if item.cost_of_equity is not None:
        implied = _implied_growth(item.price, item.annual_dividend, item.cost_of_equity, item.dividend_timing)
        flat = item.annual_dividend / item.cost_of_equity

    scenarios = _scenarios(item, growth_scenarios, implied)
    disclosure = _disclosure(item, coverage, payout, implied)
    return DividendResult(
        price=item.price,
        annual_dividend=item.annual_dividend,
        dividend_timing=item.dividend_timing,
        cash_yield=cash_yield,
        yield_kind=kind,
        coverage=coverage,
        payout=payout,
        implied_growth=implied,
        flat_perpetuity_value=flat,
        scenarios=scenarios,
        case=item,
        disclosure=disclosure,
    )


def growing_perpetuity(
    dividend: float,
    growth: float,
    cost_of_equity: float,
    timing: str,
) -> float:
    if growth >= cost_of_equity:
        raise ModelError(
            "Growing perpetuity needs growth below the cost of equity. "
            f"Got growth {growth:.2%} and cost of equity {cost_of_equity:.2%}."
        )
    if timing == "next":
        return dividend / (cost_of_equity - growth)
    if timing == "trailing":
        return dividend * (1.0 + growth) / (cost_of_equity - growth)
    raise ModelError("dividend_timing must be 'next' or 'trailing'.")


def prepare_dividend(case: DividendCase) -> DividendCase:
    timing = case.dividend_timing.strip().lower()
    basis = case.earnings_basis.strip().lower()
    if timing not in ("next", "trailing"):
        raise ModelError("dividend_timing must be 'next' or 'trailing'.")
    if basis not in ("fcfe", "pat", "ffo", "owner_earnings"):
        raise ModelError("earnings_basis must be fcfe, pat, ffo, or owner_earnings.")
    if case.price <= 0:
        raise ModelError("price must be positive.")
    if case.cost_of_equity is not None and (case.cost_of_equity <= 0 or case.cost_of_equity >= 1):
        raise ModelError(
            f"cost_of_equity is {case.cost_of_equity}. Pass a decimal (0.10 for 10%)."
        )
    if case.earnings is not None and case.earnings < 0:
        raise ModelError("earnings for a dividend coverage ratio cannot be negative.")
    if case.growth is not None and case.growth <= -1:
        raise ModelError("growth of -100% or worse is rejected.")
    ticker = case.ticker.strip() if isinstance(case.ticker, str) else case.ticker
    name = case.name.strip() if isinstance(case.name, str) else case.name
    return DividendCase(
        currency=normalise_currency(case.currency),
        scale=normalise_scale(case.scale),
        price=float(case.price),
        annual_dividend=float(case.annual_dividend),
        dividend_timing=timing,
        earnings=None if case.earnings is None else float(case.earnings),
        earnings_basis=basis,
        cost_of_equity=None if case.cost_of_equity is None else float(case.cost_of_equity),
        growth=None if case.growth is None else float(case.growth),
        ticker=ticker or None,
        name=name or None,
        notes=case.notes.strip() if isinstance(case.notes, str) else "",
    )


def load_dividend(path: str | Path) -> DividendCase:
    raw = dict(_read_mapping(path))
    unknown = sorted(set(raw) - set(_DIVIDEND_FIELDS))
    if unknown:
        raise ModelError(
            f"Unknown fields in {path}: {', '.join(unknown)}. "
            f"Allowed: {', '.join(_DIVIDEND_FIELDS)}."
        )
    missing = [key for key in ("currency", "scale", "price", "annual_dividend") if raw.get(key) is None]
    if missing:
        raise ModelError(f"Missing {', '.join(missing)} in {path}.")
    kwargs: dict[str, Any] = {}
    for key in _DIVIDEND_FIELDS:
        if key not in raw or raw[key] is None:
            continue
        value = raw[key]
        if key in _STRING_FIELDS:
            if not isinstance(value, str):
                raise ModelError(f"{key} in {path} must be a string.")
            kwargs[key] = value
        else:
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                raise ModelError(f"{key} in {path} must be a number.")
            kwargs[key] = float(value)
    return prepare_dividend(DividendCase(**kwargs))


def load_dividend_example(name: str = "dividend") -> DividendCase:
    from whats_priced_in.assumptions import examples_dir

    path = examples_dir() / f"{name}.yaml"
    if not path.is_file():
        raise ModelError(f"No dividend example at {path}.")
    return load_dividend(path)


def _implied_growth(price: float, dividend: float, cost_of_equity: float, timing: str) -> float:
    if timing == "next":
        return cost_of_equity - dividend / price
    return (price * cost_of_equity - dividend) / (price + dividend)


def _coverage(case: DividendCase) -> tuple[float | None, float | None]:
    if case.earnings is None or case.earnings == 0 or case.annual_dividend == 0:
        return None, None
    return case.earnings / case.annual_dividend, case.annual_dividend / case.earnings


def _scenarios(
    case: DividendCase,
    growths: tuple[float, ...],
    implied: float | None,
) -> tuple[YieldScenario, ...]:
    points = list(growths)
    if case.growth is not None:
        points.append(case.growth)
    if implied is not None:
        points.append(implied)
    unique: list[float] = []
    for rate in sorted(points):
        if any(abs(rate - seen) < 5e-5 for seen in unique):
            continue
        unique.append(rate)

    rows: list[YieldScenario] = []
    for rate in unique:
        note_bits: list[str] = []
        if implied is not None and abs(rate - implied) < 5e-5:
            note_bits.append("implied by the price")
        if case.growth is not None and abs(rate - case.growth) < 5e-5:
            note_bits.append("stated growth")
        if case.cost_of_equity is None:
            rows.append(YieldScenario(rate, None, None, "needs a cost of equity"))
            continue
        if rate >= case.cost_of_equity:
            rows.append(
                YieldScenario(
                    rate,
                    None,
                    None,
                    "not defined; growth is not below the cost of equity",
                )
            )
            continue
        value = growing_perpetuity(case.annual_dividend, rate, case.cost_of_equity, case.dividend_timing)
        versus = value / case.price - 1.0
        if abs(value - case.price) < 1e-6:
            versus = 0.0
        rows.append(YieldScenario(rate, value, versus, "; ".join(note_bits)))
    return tuple(rows)


def _disclosure(
    case: DividendCase,
    coverage: float | None,
    payout: float | None,
    implied: float | None,
) -> Disclosure:
    if case.earnings is None:
        basis = (
            f"No earnings figure was supplied, so coverage is blank. "
            f"The label on the earnings slot is {case.earnings_basis.upper()}, unused."
        )
    else:
        basis = (
            f"The earnings figure is {case.earnings_basis.upper()}. "
            "Coverage divides that figure by the dividend you supplied. "
            "Periods are not aligned for you."
        )
    if payout is None:
        payout_text = "Payout is blank because coverage could not be computed."
    else:
        payout_text = (
            f"Payout is {payout:.2%}, the dividend divided by the earnings figure. "
            "It is a coverage identity, not the payout scalar of the two-stage earnings model."
        )
    if case.dividend_timing == "next":
        terminal = (
            "There is no explicit horizon. The terminal assumption is the perpetual growth itself. "
            "Next dividend D1 is the distribution you entered, held fixed across scenarios. "
            "Value at a growth rate g is D1 / (r - g). "
            "Implied growth is r - D1 / price."
        )
        timing = (
            "The dividend is treated as next period's distribution (forward yield = dividend / price). "
            "Growth applies after that distribution, not before it."
        )
    else:
        terminal = (
            "There is no explicit horizon. The dividend is trailing (D0). "
            "In a scenario, next dividend is D0 * (1 + g), and value is D0 * (1 + g) / (r - g). "
            "Implied growth solves that equation for the price."
        )
        timing = (
            "The dividend is the trailing distribution. Cash yield is trailing yield, dividend / price. "
            "A forward yield needs a growth rate and is the scenario table, not the headline yield."
        )
    tax = (
        "Tax is not applied. Coverage and yield use the dividend and the earnings figure as supplied. "
        "No tax rate is an input of this reading."
    )
    scale = (
        f"Per-share figures in {case.currency}. Scale is {case.scale} "
        f"({SCALE_NOTES[normalise_scale(case.scale)]}). "
        "The dividend and the price are in that currency. Nothing is converted."
    )
    warnings: list[str] = []
    if coverage is not None and coverage < 1:
        warnings.append(
            "The dividend is larger than the earnings figure. Coverage is below 1."
        )
    if implied is not None and implied < 0:
        warnings.append(
            "The promised yield is above the cost of equity, so the perpetual growth that fits "
            "the price is negative. The price does not assume growth. It assumes a shrinking "
            "distribution, or a lower required return than the one you entered."
        )
    if case.cost_of_equity is None:
        warnings.append(
            "No cost of equity was supplied. Cash yield and coverage still stand. "
            "Implied growth and perpetuity values are blank until you pass one."
        )
    disclosure = Disclosure(
        items=(
            DisclosureItem("basis", "Basis", basis),
            DisclosureItem("payout", "Payout", payout_text),
            DisclosureItem("terminal", "Terminal", terminal),
            DisclosureItem("timing", "Timing", timing),
            DisclosureItem("tax", "Tax", tax),
            DisclosureItem("scale", "Scale", scale),
        ),
        warnings=tuple(warnings),
    )
    return complete(disclosure)
