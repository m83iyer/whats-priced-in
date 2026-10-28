"""Assumption sets. Every field that can move a value is stored here, in the open."""

from __future__ import annotations

from dataclasses import dataclass, fields, replace
from pathlib import Path
from typing import Any, Mapping

import yaml

from whats_priced_in.errors import ModelError
from whats_priced_in.scales import normalise_currency, normalise_scale

EARNINGS_BASES = ("fcfe", "pat", "ffo", "owner_earnings")
DISCOUNT_CONVENTIONS = ("end_of_year", "mid_year")

# Fields whose values enter the constant-growth solve. Everything else is
# disclosed and does not move implied growth. Tax is deliberately absent:
# the earnings figure is already after tax, and tax_rate is never reapplied.
GROWTH_INPUTS = frozenset(
    {
        "earnings",
        "cost_of_equity",
        "terminal_growth",
        "years",
        "payout",
        "discount_convention",
        "price",
        "shares",
        "market_cap",
    }
)

RATE_FIELDS = frozenset(
    {
        "cost_of_equity",
        "terminal_growth",
        "payout",
        "tax_rate",
        "revenue_growth",
    }
)

MONEY_FIELDS = frozenset({"price", "earnings", "revenue", "market_cap"})


@dataclass(frozen=True, slots=True)
class Assumptions:
    """Inputs for a reverse equity value.

    Rates are decimals: ``0.11`` means 11%. ``currency`` and ``scale`` have no
    default, so a market is never assumed. ``years``, ``payout``,
    ``earnings_basis``, and ``discount_convention`` do have defaults; the
    result always prints the values that actually ran.

    Payout is the fraction of each year's earnings treated as cash flow to
    equity. At 1.0 the earnings are fully distributable. That is a cash-flow
    assumption, not a dividend forecast, and it does not fund growth out of
    retained earnings.

    ``tax_rate`` is recorded and disclosed. It is not applied. Pass earnings
    that are already after tax (PAT, FCFE, FFO, or owner earnings).
    """

    currency: str
    scale: str
    earnings: float
    cost_of_equity: float
    terminal_growth: float
    years: int = 10
    payout: float = 1.0
    earnings_basis: str = "fcfe"
    discount_convention: str = "end_of_year"
    ticker: str | None = None
    name: str | None = None
    price: float | None = None
    shares: float | None = None
    market_cap: float | None = None
    revenue: float | None = None
    revenue_growth: float | None = None
    tax_rate: float | None = None
    notes: str = ""


ASSUMPTION_FIELDS = tuple(field.name for field in fields(Assumptions))


def canonical(assumptions: Assumptions) -> Assumptions:
    ticker = assumptions.ticker.strip() if isinstance(assumptions.ticker, str) else assumptions.ticker
    name = assumptions.name.strip() if isinstance(assumptions.name, str) else assumptions.name
    notes = assumptions.notes.strip() if isinstance(assumptions.notes, str) else ""
    return replace(
        assumptions,
        currency=normalise_currency(assumptions.currency),
        scale=normalise_scale(assumptions.scale),
        earnings_basis=str(assumptions.earnings_basis).strip().lower(),
        discount_convention=str(assumptions.discount_convention).strip().lower(),
        ticker=ticker or None,
        name=name or None,
        notes=notes,
    )


def prepare(assumptions: Assumptions) -> Assumptions:
    """Normalise codes and reject inputs that would make the model a muddle."""

    item = canonical(assumptions)
    if item.earnings_basis not in EARNINGS_BASES:
        raise ModelError(
            f"earnings_basis {item.earnings_basis!r} is not one of {', '.join(EARNINGS_BASES)}."
        )
    if item.discount_convention not in DISCOUNT_CONVENTIONS:
        raise ModelError(
            "discount_convention must be 'end_of_year' or 'mid_year'. "
            f"Got {item.discount_convention!r}."
        )
    _finite("earnings", item.earnings)
    _finite("cost_of_equity", item.cost_of_equity)
    _finite("terminal_growth", item.terminal_growth)
    _finite("payout", item.payout)
    _optional_finite("price", item.price)
    _optional_finite("shares", item.shares)
    _optional_finite("market_cap", item.market_cap)
    _optional_finite("revenue", item.revenue)
    _optional_finite("revenue_growth", item.revenue_growth)
    _optional_finite("tax_rate", item.tax_rate)

    if isinstance(item.years, bool) or not isinstance(item.years, int):
        raise ModelError("years must be an integer.")
    if item.years < 1 or item.years > 100:
        raise ModelError("years must be from 1 to 100.")

    if item.cost_of_equity <= 0 or item.cost_of_equity >= 1:
        raise ModelError(
            f"cost_of_equity is {item.cost_of_equity}. Pass a decimal (0.11 for 11%), "
            "greater than 0 and less than 1."
        )
    if item.terminal_growth >= 1 or item.terminal_growth <= -0.5:
        raise ModelError(
            f"terminal_growth is {item.terminal_growth}. Pass a decimal (0.04 for 4%)."
        )
    if item.cost_of_equity <= item.terminal_growth:
        raise ModelError(
            "Cost of equity must exceed terminal growth. "
            f"Got cost of equity {item.cost_of_equity:.2%} and terminal growth {item.terminal_growth:.2%}."
        )
    if item.payout < 0 or item.payout > 5:
        raise ModelError(
            f"payout is {item.payout}. Pass a fraction of earnings (1.0 for 100%, 0.6 for 60%)."
        )
    if item.tax_rate is not None and (item.tax_rate < 0 or item.tax_rate >= 1):
        raise ModelError(
            f"tax_rate is {item.tax_rate}. Pass a decimal. It is disclosed and not applied."
        )
    if item.price is not None and item.price <= 0:
        raise ModelError("price must be positive.")
    if item.shares is not None and item.shares <= 0:
        raise ModelError("shares must be positive.")
    if item.market_cap is not None and item.market_cap <= 0:
        raise ModelError("market_cap must be positive.")
    if item.revenue is not None and item.revenue <= 0:
        raise ModelError("revenue must be positive when it is set.")
    if item.revenue_growth is not None and item.revenue_growth <= -1:
        raise ModelError("revenue_growth of -100% or worse wipes the revenue path.")
    _check_target_consistency(item)
    return item


def unit_mode(assumptions: Assumptions) -> str:
    """How to read the earnings unit.

    ``per_share`` — a price and no share count. Earnings are per share.
    ``aggregate`` — a market cap, or a price times shares. Earnings are in ``scale``.
    ``earnings_units`` — no price information. The value is just in the earnings unit.
    """

    if assumptions.shares is not None and assumptions.price is None and assumptions.market_cap is None:
        raise ModelError("shares is set without a price or a market cap, so the target is undefined.")
    if assumptions.market_cap is not None or assumptions.shares is not None:
        return "aggregate"
    if assumptions.price is not None:
        return "per_share"
    return "earnings_units"


def resolve_target(assumptions: Assumptions) -> float | None:
    """Price, or market cap, in the same scale as earnings. None if no price was given."""

    mode = unit_mode(assumptions)
    if mode == "earnings_units":
        return None
    if mode == "per_share":
        return assumptions.price
    if assumptions.price is not None and assumptions.shares is not None:
        return assumptions.price * assumptions.shares
    return assumptions.market_cap


def as_per_share(assumptions: Assumptions) -> Assumptions:
    """Divide aggregate figures by the share count.

    Shares are in the same scale as earnings. ₹ crore of profit and crore shares
    become rupees per share. The scale on the returned set is ``unit``.
    """

    item = prepare(assumptions)
    if item.shares is None:
        raise ModelError(
            "as_per_share needs a positive share count, in the same scale as earnings."
        )
    if item.price is None:
        if item.market_cap is None:
            raise ModelError("as_per_share needs a price or a market cap.")
        price = item.market_cap / item.shares
    else:
        price = item.price
    return prepare(
        replace(
            item,
            earnings=item.earnings / item.shares,
            revenue=None if item.revenue is None else item.revenue / item.shares,
            price=price,
            shares=None,
            market_cap=None,
            scale="unit",
        )
    )


def _check_target_consistency(item: Assumptions) -> None:
    if item.price is None or item.shares is None or item.market_cap is None:
        return
    implied = item.price * item.shares
    scale = max(abs(item.market_cap), 1e-12)
    if abs(implied - item.market_cap) / scale > 1e-6:
        hint = ""
        if item.scale == "crore":
            hint = " If market cap is in ₹ crore, the share count has to be in crore too."
        elif item.scale == "million":
            hint = " If market cap is in millions, the share count has to be in millions too."
        raise ModelError(
            f"price × shares = {implied} but market_cap is {item.market_cap}.{hint}"
        )


def _finite(name: str, value: Any) -> None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ModelError(f"{name} must be a number.")
    if value != value or value in (float("inf"), float("-inf")):
        raise ModelError(f"{name} must be finite.")


def _optional_finite(name: str, value: Any) -> None:
    if value is None:
        return
    _finite(name, value)


def examples_dir() -> Path:
    for parent in Path(__file__).resolve().parents:
        candidate = parent / "examples" / "synth.yaml"
        if candidate.is_file():
            return candidate.parent
    raise ModelError(
        "Could not find examples/synth.yaml. Run from a checkout of this repo, "
        "or pass --assumptions and the numbers directly."
    )


def load_example(name: str) -> Assumptions:
    path = examples_dir() / f"{name}.yaml"
    if not path.is_file():
        known = sorted(p.stem for p in examples_dir().glob("*.yaml"))
        raise ModelError(f"Unknown example {name!r}. Files in examples/: {', '.join(known)}.")
    return load_assumptions(path)


def load_assumptions(path: str | Path) -> Assumptions:
    raw = _read_mapping(path)
    unknown = sorted(set(raw) - set(ASSUMPTION_FIELDS))
    if unknown:
        raise ModelError(
            f"Unknown fields in {path}: {', '.join(unknown)}. "
            f"Allowed: {', '.join(ASSUMPTION_FIELDS)}."
        )
    missing = [
        key
        for key in ("currency", "scale", "earnings", "cost_of_equity", "terminal_growth")
        if raw.get(key) is None
    ]
    if missing:
        raise ModelError(f"Missing {', '.join(missing)} in {path}.")
    kwargs: dict[str, Any] = {}
    for key in ASSUMPTION_FIELDS:
        if key not in raw or raw[key] is None:
            continue
        kwargs[key] = _coerce_assumption(key, raw[key], path)
    try:
        built = Assumptions(**kwargs)
    except TypeError as exc:
        raise ModelError(f"Could not read assumptions from {path}: {exc}") from exc
    return prepare(built)


def _coerce_assumption(key: str, value: Any, path: str | Path) -> Any:
    if key == "years":
        if isinstance(value, bool) or not isinstance(value, (int, float)) or int(value) != value:
            raise ModelError(f"years in {path} must be an integer.")
        return int(value)
    if key in {"ticker", "name", "currency", "scale", "earnings_basis", "discount_convention", "notes"}:
        if not isinstance(value, str):
            raise ModelError(f"{key} in {path} must be a string.")
        return value
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ModelError(f"{key} in {path} must be a number.")
    return float(value)


def _read_mapping(path: str | Path) -> Mapping[str, Any]:
    file = Path(path)
    if not file.is_file():
        raise ModelError(f"No such file: {file}")
    try:
        loaded = yaml.safe_load(file.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        raise ModelError(f"Could not parse {file}: {exc}") from exc
    if loaded is None:
        raise ModelError(f"{file} is empty.")
    if not isinstance(loaded, dict):
        raise ModelError(f"{file} must be a mapping of assumption fields.")
    return loaded
