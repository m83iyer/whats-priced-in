"""Shareable SVG cards. One result, the assumptions that produced it, no advice."""

from __future__ import annotations

from pathlib import Path

from whats_priced_in.dcf import SolveGrowthResult, value_growth
from whats_priced_in.errors import ModelError
from whats_priced_in.earnings_assumption_diff import DiffResult
from whats_priced_in.formatting import (
    diff_key_assumption_card_lines,
    format_money,
    format_percent,
    key_assumption_card_lines,
)

_PAPER = "#f3efe6"
_INK = "#1c1915"
_MUTED = "#5e584e"
_RULE = "#d9d2c5"
_ACCENT = "#9c3418"
_GREEN = "#1f6b4a"


def render_growth_card(result: SolveGrowthResult) -> str:
    item = result.assumptions
    per_share = result.unit_mode == "per_share"
    units = f"{item.currency} · per share" if per_share else f"{item.currency} · {item.scale}"
    growth = format_percent(result.implied_growth)
    price = format_money(result.target, item.currency, item.scale, per_share=per_share)
    earnings = format_money(item.earnings, item.currency, item.scale, per_share=per_share)
    terminal = format_percent(result.breakdown.terminal_share)
    year_n = format_money(result.breakdown.year_n_earnings, item.currency, item.scale, per_share=per_share)
    explicit = format_money(result.breakdown.explicit_pv, item.currency, item.scale, per_share=per_share)
    terminal_pv = format_money(result.breakdown.terminal_pv, item.currency, item.scale, per_share=per_share)
    title = item.ticker or item.name or "what's priced in"
    name = item.name or ""
    chart = _chart(result)
    assumption_lines = key_assumption_card_lines(result.key_assumptions)
    y = 448
    assumption_svg: list[str] = []
    for index, line in enumerate(assumption_lines):
        color = _INK if index == 0 else _MUTED
        assumption_svg.append(
            f'<text x="48" y="{y}" fill="{color}" font-family="{_SANS}" font-size="13">{_esc(line)}</text>'
        )
        y += 20
    flag = ""
    if any("retained earnings" in warning for warning in result.disclosure.warnings):
        flag = (
            f'<text x="48" y="{y + 6}" fill="{_ACCENT}" font-family="{_SANS}" font-size="13">'
            "Flag: growth is not funded by retained cash in this model."
            "</text>"
        )
        footnote_y = y + 30
    else:
        footnote_y = y + 8
    height = max(560, footnote_y + 28)
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="960" height="{height}" viewBox="0 0 960 {height}" role="img">
  <title>What's priced in — {_esc(title)} {_esc(growth)}</title>
  <desc>Reverse two-stage FCFE reading. {_esc(growth)} constant growth. Not a recommendation.</desc>
  <rect width="960" height="{height}" fill="{_PAPER}"/>
  <rect width="8" height="{height}" fill="{_ACCENT}"/>
  <text x="48" y="46" fill="{_ACCENT}" font-family="{_SANS}" font-size="13" letter-spacing="2.4">WHAT'S PRICED IN</text>
  <text x="912" y="46" fill="{_MUTED}" font-family="{_SANS}" font-size="13" text-anchor="end">{_esc(units)}</text>
  <text x="48" y="108" fill="{_INK}" font-family="{_SERIF}" font-size="42">{_esc(title)}</text>
  <text x="48" y="138" fill="{_MUTED}" font-family="{_SERIF}" font-size="16">{_esc(name)}</text>
  <text x="48" y="230" fill="{_INK}" font-family="{_SERIF}" font-size="84">{_esc(growth)}</text>
  <text x="48" y="262" fill="{_MUTED}" font-family="{_SERIF}" font-size="16">constant earnings growth the price assumes</text>
  {chart}
  <line x1="48" y1="300" x2="912" y2="300" stroke="{_RULE}"/>
  <text x="48" y="334" fill="{_MUTED}" font-family="{_SANS}" font-size="12">PRICE</text>
  <text x="48" y="360" fill="{_INK}" font-family="{_SERIF}" font-size="20">{_esc(price)}</text>
  <text x="300" y="334" fill="{_MUTED}" font-family="{_SANS}" font-size="12">EARNINGS NOW</text>
  <text x="300" y="360" fill="{_INK}" font-family="{_SERIF}" font-size="20">{_esc(earnings)}</text>
  <text x="560" y="334" fill="{_MUTED}" font-family="{_SANS}" font-size="12">YEAR {item.years}</text>
  <text x="560" y="360" fill="{_INK}" font-family="{_SERIF}" font-size="20">{_esc(year_n)}</text>
  <text x="780" y="334" fill="{_MUTED}" font-family="{_SANS}" font-size="12">TERMINAL SHARE</text>
  <text x="780" y="360" fill="{_INK}" font-family="{_SERIF}" font-size="20">{_esc(terminal)}</text>
  <line x1="48" y1="390" x2="912" y2="390" stroke="{_RULE}"/>
  <text x="48" y="422" fill="{_INK}" font-family="{_SANS}" font-size="14">Explicit {_esc(explicit)} · terminal {_esc(terminal_pv)}</text>
  {''.join(assumption_svg)}
  {flag}
  <text x="48" y="{footnote_y}" fill="{_INK}" font-family="{_SANS}" font-size="13">Not a recommendation. One model, read backwards.</text>
</svg>
"""


def render_diff_card(result: DiffResult) -> str:
    per_share = result.before.currency == result.after.currency and _same_per_share(result)
    before_g = format_percent(result.implied_growth_before)
    after_g = format_percent(result.implied_growth_after)
    delta = f"{result.delta_implied_growth * 100:+.2f} pp"
    ticker = result.before.ticker or result.after.ticker or "what's priced in"
    name = result.before.name if result.before.name == result.after.name else ""
    assumption_lines = diff_key_assumption_card_lines(
        result.key_assumptions["before"],
        result.key_assumptions["after"],
    )
    y = 248
    assumption_svg: list[str] = []
    for index, line in enumerate(assumption_lines):
        color = _INK if index == 0 else _MUTED
        assumption_svg.append(
            f'<text x="48" y="{y}" fill="{color}" font-family="{_SANS}" font-size="13">{_esc(line)}</text>'
        )
        y += 20
    y += 16
    change_lines = []
    for change in result.changes[:6]:
        role = "moves the growth" if change.affects_implied_growth else "disclosed only"
        text = f"{change.field}   {_short(change.before)}  →  {_short(change.after)}   {role}"
        change_lines.append(
            f'<text x="48" y="{y}" fill="{_INK}" font-family="{_SANS}" font-size="16">{_esc(text)}</text>'
        )
        y += 28
    value_line = ""
    if result.values_comparable and result.delta_value is not None and per_share is not None:
        left = format_money(result.value_before, result.before.currency, result.before.scale, per_share=per_share)
        right = format_money(result.value_after, result.after.currency, result.after.scale, per_share=per_share)
        y += 8
        value_line = (
            f'<text x="48" y="{y}" fill="{_MUTED}" font-family="{_SANS}" font-size="14">'
            f"Value at {before_g}: {_esc(left)} → {_esc(right)}"
            "</text>"
        )
        y += 28
    footnote_y = y + 16
    height = max(540, footnote_y + 32)
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="960" height="{height}" viewBox="0 0 960 {height}" role="img">
  <title>What changed — {_esc(ticker)} {before_g} to {after_g}</title>
  <desc>Earnings assumption diff. Not a recommendation.</desc>
  <rect width="960" height="{height}" fill="{_PAPER}"/>
  <rect width="8" height="{height}" fill="{_ACCENT}"/>
  <text x="48" y="46" fill="{_ACCENT}" font-family="{_SANS}" font-size="13" letter-spacing="2.4">WHAT CHANGED</text>
  <text x="48" y="108" fill="{_INK}" font-family="{_SERIF}" font-size="42">{_esc(ticker)}</text>
  <text x="48" y="140" fill="{_MUTED}" font-family="{_SERIF}" font-size="16">{_esc(name or "")}</text>
  <text x="48" y="210" fill="{_INK}" font-family="{_SERIF}" font-size="28">{before_g}  →  {after_g}</text>
  <text x="520" y="210" fill="{_ACCENT}" font-family="{_SERIF}" font-size="28">{_esc(delta)}</text>
  {''.join(assumption_svg)}
  {''.join(change_lines)}
  {value_line}
  <text x="48" y="{footnote_y}" fill="{_INK}" font-family="{_SANS}" font-size="13">Not a recommendation. Implied growth under each assumption set.</text>
</svg>
"""


def write_svg(svg: str, path: str | Path) -> Path:
    destination = Path(path)
    if destination.parent and not destination.parent.exists():
        raise FileNotFoundError(f"No such directory: {destination.parent}")
    destination.write_text(svg, encoding="utf-8")
    return destination


def _chart(result: SolveGrowthResult) -> str:
    """A small value-versus-growth curve with the price as a horizontal line."""

    item = result.assumptions
    start, stop, steps = 0.0, 0.16, 16
    rates = [start + (stop - start) * i / steps for i in range(steps + 1)]
    values: list[float] = []
    for rate in rates:
        try:
            values.append(value_growth(rate, item).breakdown.equity_value)
        except ModelError:
            values.append(float("nan"))
    if any(value != value for value in values):
        return ""
    left, top, width, height = 560, 150, 340, 120
    low = min(min(values), result.target)
    high = max(max(values), result.target)
    if high <= low:
        return ""
    pad = (high - low) * 0.08
    low -= pad
    high += pad

    def x_of(index: int) -> float:
        return left + width * index / steps

    def y_of(value: float) -> float:
        return top + height - (value - low) / (high - low) * height

    points = " ".join(f"{x_of(i):.1f},{y_of(value):.1f}" for i, value in enumerate(values))
    price_y = y_of(result.target)
    implied_index = (result.implied_growth - start) / (stop - start) * steps
    marker = ""
    if 0 <= implied_index <= steps:
        mx = left + width * implied_index / steps
        my = y_of(result.target)
        marker = f'<circle cx="{mx:.1f}" cy="{my:.1f}" r="4.5" fill="{_ACCENT}"/>'
    return (
        f'<g font-family="{_SANS}" font-size="11" fill="{_MUTED}">'
        f'<line x1="{left}" y1="{price_y:.1f}" x2="{left + width}" y2="{price_y:.1f}" stroke="{_GREEN}" stroke-dasharray="3 3"/>'
        f'<polyline fill="none" stroke="{_INK}" stroke-width="1.6" points="{points}"/>'
        f"{marker}"
        f'<text x="{left}" y="{top + height + 16}">0%</text>'
        f'<text x="{left + width}" y="{top + height + 16}" text-anchor="end">16%</text>'
        f'<text x="{left + width}" y="{top - 8}" text-anchor="end">value vs growth</text>'
        "</g>"
    )


def _short(value: object) -> str:
    if value is None:
        return "n/a"
    if isinstance(value, float):
        return f"{value:.4g}"
    return str(value)


def _same_per_share(result: DiffResult) -> bool | None:
    from whats_priced_in.assumptions import unit_mode

    if unit_mode(result.before) != unit_mode(result.after):
        return None
    return unit_mode(result.before) == "per_share"


def _esc(text: str) -> str:
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


_SERIF = "Palatino, 'Palatino Linotype', Georgia, serif"
_SANS = "Helvetica, Arial, sans-serif"
