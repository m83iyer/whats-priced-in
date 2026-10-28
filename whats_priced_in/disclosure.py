"""Disclosure objects. Tax, payout, terminal, timing, basis, and scale stay visible."""

from __future__ import annotations

from dataclasses import dataclass

from whats_priced_in.assumptions import Assumptions, unit_mode
from whats_priced_in.errors import ModelError
from whats_priced_in.scales import SCALE_NOTES

REQUIRED_KEYS = ("basis", "payout", "terminal", "timing", "tax", "scale")

UNFUNDED_GROWTH = (
    "Payout is at or above 95% while growth is above the terminal rate. "
    "The model does not use retained earnings to fund that growth. "
    "That fits an asset-light business, or earnings that are already net of the reinvestment you believe. "
    "If growth needs reinvestment, lower the payout."
)

PAYOUT_ABOVE_EARNINGS = (
    "Payout is above 100%. Cash to equity exceeds earnings in every year "
    "(borrowing or asset sales). The model uses the figure as given."
)

TERMINAL_HEAVY = (
    "More than 75% of the value is the terminal perpetuity. "
    "The explicit years are not doing much of the work."
)

HIGH_TERMINAL_GROWTH = (
    "Terminal growth is above 8%. That is faster than many long-run nominal economies. "
    "It is allowed, and it is doing a lot of quiet work."
)

HIGH_COST_OF_EQUITY = (
    "Cost of equity is 25% or higher. Check that you passed a decimal (0.25, not 25) "
    "and that you mean a rate this high."
)


@dataclass(frozen=True, slots=True)
class DisclosureItem:
    key: str
    title: str
    text: str


@dataclass(frozen=True, slots=True)
class Disclosure:
    items: tuple[DisclosureItem, ...]
    warnings: tuple[str, ...] = ()

    def text_for(self, key: str) -> str:
        for item in self.items:
            if item.key == key:
                return item.text
        raise KeyError(key)

    def with_warnings(self, warnings: tuple[str, ...]) -> "Disclosure":
        return Disclosure(items=self.items, warnings=warnings)


def complete(disclosure: Disclosure) -> Disclosure:
    keys = [item.key for item in disclosure.items]
    missing = [key for key in REQUIRED_KEYS if key not in keys]
    if missing:
        raise ModelError(f"Disclosure is missing {missing}. This is a bug in the library.")
    if len(keys) != len(set(keys)):
        raise ModelError("Disclosure repeats a key. This is a bug in the library.")
    return disclosure


def growth_disclosure(assumptions: Assumptions) -> Disclosure:
    """The six items for the two-stage cash-flow model, before solve-specific warnings."""

    item = assumptions
    basis = _basis_text(item)
    payout = _payout_text(item)
    terminal = (
        f"Terminal value is a Gordon growth perpetuity. The cash flow in year {item.years} "
        f"grows once more at {item.terminal_growth:.2%} and is capitalised at "
        f"cost of equity minus terminal growth "
        f"({item.cost_of_equity:.2%} - {item.terminal_growth:.2%}). "
        "There is no fade inside the perpetuity."
    )
    if item.discount_convention == "end_of_year":
        timing = (
            "Cash flows are dated at each year-end and discounted for that many full years. "
            "The terminal value is dated at the same final year-end."
        )
    else:
        timing = (
            "Mid-year convention. The year-end present value, explicit cash flows and terminal "
            "together, is multiplied by (1 + cost of equity) ^ 0.5. "
            "That is the whole adjustment. Cash flows are not redated individually."
        )
    if item.tax_rate is None:
        tax = (
            "Tax is not applied inside the model. The earnings input is taken as already after tax. "
            "No tax rate was supplied."
        )
    else:
        tax = (
            "Tax is not applied inside the model. The earnings input is taken as already after tax. "
            f"A tax rate of {item.tax_rate:.2%} is disclosed and not reapplied. "
            "Changing it does not move the value."
        )
    scale = _scale_text(item)
    disclosure = Disclosure(
        items=(
            DisclosureItem("basis", "Basis", basis),
            DisclosureItem("payout", "Payout", payout),
            DisclosureItem("terminal", "Terminal", terminal),
            DisclosureItem("timing", "Timing", timing),
            DisclosureItem("tax", "Tax", tax),
            DisclosureItem("scale", "Scale", scale),
        )
    )
    return complete(disclosure)


def growth_warnings(
    assumptions: Assumptions,
    growth: float,
    terminal_share: float,
) -> tuple[str, ...]:
    warnings: list[str] = []
    if assumptions.payout > 1:
        warnings.append(PAYOUT_ABOVE_EARNINGS)
    if assumptions.payout >= 0.95 and growth > assumptions.terminal_growth + 1e-12:
        warnings.append(UNFUNDED_GROWTH)
    if terminal_share > 0.75:
        warnings.append(TERMINAL_HEAVY)
    if assumptions.terminal_growth > 0.08:
        warnings.append(HIGH_TERMINAL_GROWTH)
    if assumptions.cost_of_equity >= 0.25:
        warnings.append(HIGH_COST_OF_EQUITY)
    if assumptions.earnings < 0:
        warnings.append(
            "Earnings are negative. A higher growth rate makes the losses larger, "
            "so value falls as growth rises. Implied growth is not solved in that case."
        )
    return tuple(warnings)


def _basis_text(item: Assumptions) -> str:
    texts = {
        "fcfe": (
            "The starting figure is free cash flow to equity, before the payout scalar. "
            "Payout then scales it. At 100%, that FCFE is discounted as given. "
            "A lower payout haircuts it."
        ),
        "pat": (
            "The starting figure is profit after tax. Payout converts PAT into cash flow to equity. "
            "At 100%, PAT is treated as distributable cash."
        ),
        "ffo": (
            "The starting figure is funds from operations. Payout converts FFO into the "
            "distribution the model discounts."
        ),
        "owner_earnings": (
            "The starting figure is owner earnings. Payout is the fraction treated as cash to the owner."
        ),
    }
    return texts[item.earnings_basis]


def _payout_text(item: Assumptions) -> str:
    if item.payout >= 0.999 and item.payout <= 1.001:
        retained = "Nothing is retained inside the model."
    elif item.payout > 1:
        retained = "Cash to equity exceeds earnings, so retention is negative."
    else:
        retained = (
            f"The model retains {1.0 - item.payout:.2%} of earnings, and that retention is not "
            "what funds the growth. Growth is an assumption on the earnings base."
        )
    text = (
        f"Payout is {item.payout:.2%} of each year's earnings, treated as cash flow to equity. "
        "This is not a dividend forecast. "
        f"{retained}"
    )
    if item.earnings_basis == "pat" and item.payout >= 0.999:
        text += " PAT is treated as fully distributable."
    return text


def _scale_text(item: Assumptions) -> str:
    note = SCALE_NOTES[item.scale]
    mode = unit_mode(item)
    if mode == "per_share":
        return (
            f"Per-share mode. Price and earnings are per share, in {item.currency}. "
            f"Scale is {item.scale} ({note}). No share count was applied."
        )
    if mode == "aggregate":
        return (
            f"Aggregate mode. Earnings and the target are both in {item.currency} {item.scale} "
            f"({note}). A share count, if set, is in that same scale: "
            "crore shares when the scale is crore, millions of shares when the scale is million. "
            "Market cap = price × shares, in that scale. The engine does not multiply by the scale factor."
        )
    return (
        f"No price was set. The value is in the same units as earnings: {item.currency} {item.scale} "
        f"({note})."
    )
