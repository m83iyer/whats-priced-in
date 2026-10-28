"""Assumption sets. Currency and scale are inputs; nothing about a market is assumed."""

from dataclasses import asdict, dataclass, fields
from pathlib import Path

import yaml

from whats_priced_in.scale import SCALE_FACTORS

_RATE_FIELDS = {"cost_of_equity", "terminal_growth", "revenue_growth"}
_BASIS = {"fcfe", "pat", "ffo", "owner_earnings"}


def project_root():
    return Path(__file__).resolve().parents[1]


def _decimal_rate(name, value):
    if value is None:
        return
    if abs(value) >= 1:
        raise ValueError(f"Rates are decimals: 0.11, not 11. {name.replace('_', ' ')} is {value}.")


@dataclass
class Assumptions:
    ticker: str = ""
    name: str | None = None
    notes: str | None = None
    currency: str = "USD"
    scale: str = "unit"
    price: float | None = None
    shares: float | None = None
    market_cap: float | None = None
    earnings: float | None = None
    revenue: float | None = None
    revenue_growth: float | None = None
    cost_of_equity: float | None = None
    terminal_growth: float | None = None
    years: int = 10
    payout: float = 1.0
    earnings_basis: str = "fcfe"
    tax_rate: float | None = None
    discount_convention: str = "end_of_year"
    dividend: float | None = None
    dividend_timing: str = "forward"

    def __post_init__(self):
        self.ticker = "" if self.ticker is None else str(self.ticker)
        self.currency = str(self.currency).upper()
        if len(self.currency) != 3 or not self.currency.isalpha():
            raise ValueError("Currency is a three-letter code.")
        self.scale = str(self.scale).lower()
        if self.scale not in SCALE_FACTORS:
            known = ", ".join(SCALE_FACTORS)
            raise ValueError(f"Scale must be one of {known}.")
        self.earnings_basis = str(self.earnings_basis).strip().lower().replace(" ", "_")
        if self.earnings_basis not in _BASIS:
            raise ValueError("Earnings basis is fcfe, pat, ffo, or owner earnings.")
        self.discount_convention = _convention(self.discount_convention)
        self.dividend_timing = _timing(self.dividend_timing)
        self.years = int(self.years)
        if self.years < 1:
            raise ValueError("Years has to be at least 1.")
        for name in (
            "price",
            "shares",
            "market_cap",
            "earnings",
            "revenue",
            "revenue_growth",
            "cost_of_equity",
            "terminal_growth",
            "payout",
            "tax_rate",
            "dividend",
        ):
            value = getattr(self, name)
            if value is not None:
                setattr(self, name, float(value))
        for name in _RATE_FIELDS:
            _decimal_rate(name, getattr(self, name))
        if self.payout is not None and (self.payout < 0 or self.payout > 1):
            raise ValueError("Payout is a decimal from 0 to 1. 100% is 1, not 100.")
        if (
            self.cost_of_equity is not None
            and self.terminal_growth is not None
            and self.cost_of_equity <= self.terminal_growth
        ):
            raise ValueError("Terminal growth must be below the cost of equity.")

    @property
    def per_share(self):
        return self.market_cap is None and self.shares is None

    def target(self):
        if self.market_cap is not None:
            return self.market_cap
        if self.shares is not None:
            if self.price is None:
                raise ValueError("A share count needs a price. Market cap = price × shares.")
            return self.price * self.shares
        if self.price is None:
            raise ValueError("Pass a price, or a market cap.")
        return self.price

    def require_equity(self):
        missing = [
            name
            for name in ("earnings", "cost_of_equity", "terminal_growth")
            if getattr(self, name) is None
        ]
        if missing:
            raise ValueError("Need earnings, cost of equity, and terminal growth.")
        if self.earnings <= 0:
            raise ValueError("Earnings have to be positive.")
        if self.cost_of_equity <= 0:
            raise ValueError("Cost of equity has to be positive.")
        target = self.target()
        if target <= 0:
            raise ValueError("The target has to be positive.")
        return target

    def replace(self, **changes):
        data = asdict(self)
        data.update(changes)
        return Assumptions(**data)


def _convention(value):
    text = str(value).strip().lower().replace("-", "_").replace(" ", "_")
    if text in {"end_of_year", "year_end", "end"}:
        return "end_of_year"
    if text in {"mid_year", "midyear"}:
        return "mid_year"
    raise ValueError("Discount convention is end_of_year or mid_year.")


def _timing(value):
    text = str(value).strip().lower()
    if text in {"forward", "d1", "next"}:
        return "forward"
    if text in {"trailing", "d0"}:
        return "trailing"
    raise ValueError("Dividend timing is forward (D1) or trailing (D0).")


def _known_fields():
    return {item.name for item in fields(Assumptions)}


def assumptions_from_mapping(data):
    if not isinstance(data, dict):
        raise ValueError("An assumption file is a mapping.")
    unknown = sorted(set(data) - _known_fields())
    if unknown:
        raise ValueError(f"Unknown assumption field: {unknown[0]}.")
    cleaned = {key: value for key, value in data.items() if value is not None}
    return Assumptions(**cleaned)


def load_assumptions(path):
    raw = yaml.safe_load(Path(path).read_text())
    return assumptions_from_mapping(raw or {})


def load_example(name):
    path = project_root() / "examples" / f"{name}.yaml"
    if not path.is_file():
        raise ValueError(f"No example named {name}.")
    return load_assumptions(path)
