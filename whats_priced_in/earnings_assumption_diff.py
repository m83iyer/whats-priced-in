"""What changed between two assumption sets, and what that does to the implied bet.

Load a pre-earnings file and a post-earnings file. The change table lists every
field that moved, and whether that field enters the constant-growth solve.
Revenue, tax, and the earnings basis are disclosed. They do not move implied
growth. Tax is never reapplied.

The value comparison holds growth at the pre-earnings implied rate and revalues
each set under its own other assumptions. If only the earnings base changed,
the value moves in proportion to earnings, because the model is linear in that
base.
"""

from __future__ import annotations

from dataclasses import dataclass, fields

from whats_priced_in.assumptions import GROWTH_INPUTS, Assumptions, prepare, resolve_target, unit_mode
from whats_priced_in.dcf import solve_growth, value_growth
from whats_priced_in.disclosure import Disclosure
from whats_priced_in.errors import ModelError


@dataclass(frozen=True, slots=True)
class FieldChange:
    field: str
    before: object
    after: object
    affects_implied_growth: bool


@dataclass(frozen=True, slots=True)
class DiffResult:
    changes: tuple[FieldChange, ...]
    implied_growth_before: float
    implied_growth_after: float
    delta_implied_growth: float
    reference_growth: float
    value_before: float
    value_after: float
    delta_value: float | None
    values_comparable: bool
    target_before: float
    target_after: float
    before: Assumptions
    after: Assumptions
    disclosure_before: Disclosure
    disclosure_after: Disclosure

    @property
    def key_assumptions(self) -> dict[str, dict[str, str]]:
        from whats_priced_in.formatting import key_assumptions_payload

        return {
            "before": key_assumptions_payload(self.before),
            "after": key_assumptions_payload(self.after),
        }

    def __str__(self) -> str:
        from whats_priced_in.formatting import format_diff

        text = format_diff(self)
        return text[:-1] if text.endswith("\n") else text


def diff_assumptions(
    before: Assumptions,
    after: Assumptions,
    reference_growth: float | None = None,
    price: float | None = None,
) -> DiffResult:
    """Compare two prepared assumption sets at the same price, unless they carry their own.

    ``price`` overrides the price on both sets. Share counts and market caps are
    left as each file wrote them. If you override the price and a share count
    is set, the target becomes price times shares, and it is checked against a
    stated market cap.
    """

    left = prepare(before)
    right = prepare(after)
    if price is not None:
        left = prepare(_override_price(left, price))
        right = prepare(_override_price(right, price))

    changes = tuple(_changes(left, right))
    solved_before = solve_growth(left)
    solved_after = solve_growth(right)
    anchor = solved_before.implied_growth if reference_growth is None else reference_growth
    value_before = value_growth(anchor, left).breakdown.equity_value
    value_after = value_growth(anchor, right).breakdown.equity_value
    comparable = _comparable(left, right)
    target_before = resolve_target(left)
    target_after = resolve_target(right)
    if target_before is None or target_after is None:
        raise ModelError("Both assumption sets need a price or a market cap.")
    return DiffResult(
        changes=changes,
        implied_growth_before=solved_before.implied_growth,
        implied_growth_after=solved_after.implied_growth,
        delta_implied_growth=solved_after.implied_growth - solved_before.implied_growth,
        reference_growth=anchor,
        value_before=value_before,
        value_after=value_after,
        delta_value=(value_after - value_before) if comparable else None,
        values_comparable=comparable,
        target_before=target_before,
        target_after=target_after,
        before=left,
        after=right,
        disclosure_before=solved_before.disclosure,
        disclosure_after=solved_after.disclosure,
    )


def _override_price(item: Assumptions, price: float) -> Assumptions:
    from dataclasses import replace

    if item.market_cap is not None and item.shares is None:
        raise ModelError(
            "A price override needs a per-share file, or a file with a share count. "
            "This file has a market cap and no shares, so the override would not know the new market cap."
        )
    market_cap = item.market_cap
    if item.shares is not None:
        market_cap = price * item.shares
    return replace(item, price=price, market_cap=market_cap)


def _changes(before: Assumptions, after: Assumptions) -> list[FieldChange]:
    found: list[FieldChange] = []
    for field in fields(Assumptions):
        left = getattr(before, field.name)
        right = getattr(after, field.name)
        if left == right:
            continue
        found.append(
            FieldChange(
                field=field.name,
                before=left,
                after=right,
                affects_implied_growth=field.name in GROWTH_INPUTS,
            )
        )
    return found


def _comparable(before: Assumptions, after: Assumptions) -> bool:
    return (
        before.currency == after.currency
        and before.scale == after.scale
        and unit_mode(before) == unit_mode(after)
    )
