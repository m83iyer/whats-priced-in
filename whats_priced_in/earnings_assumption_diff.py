"""Pre vs post earnings assumption diff."""

from whats_priced_in.disclosure import equity_items, percent, render_disclosure
from whats_priced_in.model import VERSION, implied_growth, present_value
from whats_priced_in.render import flow, join_sections, key_pairs, signed_flow

GROWTH_INPUTS = [
    "cost_of_equity",
    "discount_convention",
    "earnings",
    "market_cap",
    "payout",
    "price",
    "shares",
    "terminal_growth",
    "years",
]

_FIELD_ORDER = [
    "ticker",
    "name",
    "notes",
    "currency",
    "scale",
    "price",
    "shares",
    "market_cap",
    "earnings",
    "revenue",
    "revenue_growth",
    "cost_of_equity",
    "terminal_growth",
    "years",
    "payout",
    "earnings_basis",
    "tax_rate",
    "discount_convention",
    "dividend",
    "dividend_timing",
]

_MONEY_FIELDS = {"price", "earnings", "revenue", "market_cap", "dividend"}
_RATE_FIELDS = {"cost_of_equity", "terminal_growth", "payout", "revenue_growth", "tax_rate"}

_EXPLANATION = (
    "Value is the model at the pre-earnings implied growth, under each set's own other assumptions. "
    "Revenue is not an input to that solve. The model is linear in the earnings base, so the value moves "
    "with earnings when the other growth inputs stay put."
)


class DiffReading:
    def __init__(self, text, payload, key_assumptions_before, key_assumptions_after, disclosure, before, after, changes):
        self.text = text
        self.payload = payload
        self.key_assumptions = key_assumptions_before
        self.key_assumptions_before = key_assumptions_before
        self.key_assumptions_after = key_assumptions_after
        self.disclosure = disclosure
        self.assumptions = before
        self.before = before
        self.after = after
        self.changes = changes
        self.mode = "diff"
        self.warnings = payload.get("warnings", [])
        self.implied_growth = payload["implied_growth_before"]
        self.growth_before = payload["implied_growth_before"]
        self.growth_after = payload["implied_growth_after"]
        self.value_before = payload["value_before"]
        self.value_after = payload["value_after"]

    def __str__(self):
        return self.text


def diff_assumptions(before, after):
    before.require_equity()
    after.require_equity()
    solved_before = implied_growth(
        before.earnings,
        before.cost_of_equity,
        before.terminal_growth,
        before.years,
        before.payout,
        before.target(),
        before.discount_convention,
    )
    solved_after = implied_growth(
        after.earnings,
        after.cost_of_equity,
        after.terminal_growth,
        after.years,
        after.payout,
        after.target(),
        after.discount_convention,
    )
    valued_after = present_value(
        after.earnings,
        solved_before.growth,
        after.cost_of_equity,
        after.terminal_growth,
        after.years,
        after.payout,
        after.discount_convention,
    )
    items_before, warnings_before = equity_items(before, solved_before.growth, before.years)
    items_after, warnings_after = equity_items(after, solved_after.growth, after.years)
    pairs_before = key_pairs(before, solved_before.growth)
    pairs_after = key_pairs(after, solved_after.growth)
    changes = _changes(before, after)
    table = [_columns("field", "before", "after", "change", "role")]
    for change in changes:
        table.append(
            _columns(
                change["field"],
                _format_side(before, change["field"], change["before"]),
                _format_side(after, change["field"], change["after"]),
                _format_delta(before, change),
                "moves implied growth" if change["affects_implied_growth"] else "disclosed only",
            )
        )
    summary = [
        _columns(
            "implied growth",
            percent(solved_before.growth),
            percent(solved_after.growth),
            f"{(solved_after.growth - solved_before.growth) * 100:.2f} pp",
        ),
        _columns(
            f"value at {percent(solved_before.growth)}",
            flow(solved_before.equity_value, before),
            flow(valued_after.equity_value, after),
            signed_flow(valued_after.equity_value - solved_before.equity_value, before),
        ),
    ]
    essay_before = render_disclosure(items_before, warnings_before)
    essay_after = render_disclosure(items_after, warnings_after)
    if essay_before == essay_after:
        disclosure = render_disclosure(items_before, warnings_before, heading="Disclosure (same on both sides)")
        warnings = warnings_before
    else:
        disclosure = essay_before.replace("Disclosure", "Disclosure (before)", 1) + "\n" + essay_after.replace(
            "Disclosure", "Disclosure (after)", 1
        )
        warnings = warnings_before
    identity = before.ticker if not before.name else f"{before.ticker} · {before.name}"
    text = join_sections(
        [
            "what's priced in · earnings assumption diff",
            identity,
            "\n".join(table),
            "\n".join(summary),
            _key_table(pairs_before, pairs_after),
            _EXPLANATION,
            disclosure,
            "Not a recommendation. A diff of two assumption sets, not a reaction to a headline.",
        ]
    )
    comparable = before.currency == after.currency and before.scale == after.scale and before.per_share == after.per_share
    payload = {
        "model": "earnings_assumption_diff",
        "version": VERSION,
        "changes": [
            {
                "field": change["field"],
                "before": change["before"],
                "after": change["after"],
                "affects_implied_growth": change["affects_implied_growth"],
            }
            for change in changes
        ],
        "implied_growth_before": solved_before.growth,
        "implied_growth_after": solved_after.growth,
        "delta_implied_growth": solved_after.growth - solved_before.growth,
        "key_assumptions_before": dict(pairs_before),
        "key_assumptions_after": dict(pairs_after),
        "reference_growth": solved_before.growth,
        "value_before": solved_before.equity_value,
        "value_after": valued_after.equity_value,
        "delta_value": valued_after.equity_value - solved_before.equity_value,
        "values_comparable": comparable,
        "target_before": before.target(),
        "target_after": after.target(),
        "disclosure_before": {"items": items_before, "warnings": warnings_before},
        "disclosure_after": {"items": items_after, "warnings": warnings_after},
        "growth_inputs": list(GROWTH_INPUTS),
    }
    reading = DiffReading(
        text,
        payload,
        dict(pairs_before),
        dict(pairs_after),
        disclosure,
        before,
        after,
        changes,
    )
    reading.warnings = warnings
    return reading


def _changes(before, after):
    found = []
    for field in _FIELD_ORDER:
        left = getattr(before, field)
        right = getattr(after, field)
        if left != right:
            found.append(
                {
                    "field": field,
                    "before": left,
                    "after": right,
                    "affects_implied_growth": field in GROWTH_INPUTS,
                }
            )
    return found


def _format_side(assumptions, field, value):
    if value is None:
        return "none"
    if field in _MONEY_FIELDS:
        return flow(value, assumptions)
    if field in _RATE_FIELDS:
        return percent(value)
    if field == "shares":
        return f"{value:,.2f} {assumptions.scale}"
    return str(value)


def _format_delta(assumptions, change):
    before = change["before"]
    after = change["after"]
    if isinstance(before, (int, float)) and isinstance(after, (int, float)):
        delta = after - before
        if change["field"] in _MONEY_FIELDS:
            return signed_flow(delta, assumptions)
        if change["field"] in _RATE_FIELDS:
            return f"{delta * 100:+.2f} pp" if delta < 0 or delta > 0 else "0.00 pp"
        if isinstance(before, float) or isinstance(after, float):
            return f"{delta:+.2f}"
        return f"{delta:+d}" if delta else "0"
    return "changed"


def _columns(label, before, after, change, role=""):
    row = f"{label:<22}{before:<22}{after:<22}{change:<18}{role}"
    if not role:
        return row.rstrip()
    return row


def _key_table(before_pairs, after_pairs):
    after_map = dict(after_pairs)
    lines = ["Key assumptions", f"{'assumption':<16}{'before':<31}after"]
    seen = set()
    for key, value in before_pairs:
        lines.append(f"{key:<16}{value:<31}{after_map.get(key, '')}")
        seen.add(key)
    for key, value in after_pairs:
        if key not in seen:
            lines.append(f"{key:<16}{'':<31}{value}")
    return "\n".join(lines)
