"""SVG cards. The growth chart scale is the one that reproduces the receipted SYNTH card."""

from whats_priced_in.model import present_value
from whats_priced_in.render import flow, money, percent


def write_card(reading, path):
    Path = __import__("pathlib").Path
    Path(path).write_text(svg_for(reading))
    return path


def svg_for(reading):
    if reading.mode == "diff":
        return diff_svg(reading)
    if reading.mode == "growth":
        return growth_svg(reading)
    return plain_svg(reading)


def growth_svg(reading):
    assumptions = reading.assumptions
    valuation = reading.valuation
    warned = bool(reading.warnings)
    height = 586 if warned else 560
    footer_y = 558 if warned else 534
    target = assumptions.target()
    points = []
    for step in range(17):
        growth = step / 100
        value = present_value(
            assumptions.earnings,
            growth,
            assumptions.cost_of_equity,
            assumptions.terminal_growth,
            assumptions.years,
            assumptions.payout,
            assumptions.discount_convention,
        ).equity_value
        x = round(560 + step * (340 / 16), 1)
        y = _chart_y(value)
        points.append(f"{x:.1f},{y:.1f}")
    price_y = f"{_chart_y(target):.1f}"
    dot_x = f"{round(560 + (valuation.growth / 0.16) * 340, 1):.1f}"
    lines = _assumption_lines(reading.key_assumptions)
    subtitle = f"{assumptions.currency} · {'per share' if assumptions.per_share else assumptions.scale}"
    flag = ""
    if warned:
        flag = (
            '  <text x="48" y="534" fill="#9c3418" font-family="Helvetica, Arial, sans-serif" '
            'font-size="13">Flag: growth is not funded by retained cash in this model.</text>\n'
        )
    year_label = f"YEAR {assumptions.years}"
    body = f"""<svg xmlns="http://www.w3.org/2000/svg" width="960" height="{height}" viewBox="0 0 960 {height}" role="img">
  <title>What's priced in — {_x(assumptions.ticker)} {_x(percent(valuation.growth))}</title>
  <desc>Reverse two-stage {_x(reading.key_assumptions.get('basis', 'FCFE'))} reading. {_x(percent(valuation.growth))} constant growth. Not a recommendation.</desc>
  <rect width="960" height="{height}" fill="#f3efe6"/>
  <rect width="8" height="{height}" fill="#9c3418"/>
  <text x="48" y="46" fill="#9c3418" font-family="Helvetica, Arial, sans-serif" font-size="13" letter-spacing="2.4">WHAT'S PRICED IN</text>
  <text x="912" y="46" fill="#5e584e" font-family="Helvetica, Arial, sans-serif" font-size="13" text-anchor="end">{_x(subtitle)}</text>
  <text x="48" y="108" fill="#1c1915" font-family="Palatino, 'Palatino Linotype', Georgia, serif" font-size="42">{_x(assumptions.ticker)}</text>
  <text x="48" y="138" fill="#5e584e" font-family="Palatino, 'Palatino Linotype', Georgia, serif" font-size="16">{_x(assumptions.name or '')}</text>
  <text x="48" y="230" fill="#1c1915" font-family="Palatino, 'Palatino Linotype', Georgia, serif" font-size="84">{_x(percent(valuation.growth))}</text>
  <text x="48" y="262" fill="#5e584e" font-family="Palatino, 'Palatino Linotype', Georgia, serif" font-size="16">constant earnings growth the price assumes</text>
  <g font-family="Helvetica, Arial, sans-serif" font-size="11" fill="#5e584e"><line x1="560" y1="{price_y}" x2="900" y2="{price_y}" stroke="#1f6b4a" stroke-dasharray="3 3"/><polyline fill="none" stroke="#1c1915" stroke-width="1.6" points="{' '.join(points)}"/><circle cx="{dot_x}" cy="{price_y}" r="4.5" fill="#9c3418"/><text x="560" y="286">0%</text><text x="900" y="286" text-anchor="end">16%</text><text x="900" y="142" text-anchor="end">value vs growth</text></g>
  <line x1="48" y1="300" x2="912" y2="300" stroke="#d9d2c5"/>
  <text x="48" y="334" fill="#5e584e" font-family="Helvetica, Arial, sans-serif" font-size="12">PRICE</text>
  <text x="48" y="360" fill="#1c1915" font-family="Palatino, 'Palatino Linotype', Georgia, serif" font-size="20">{_x(money(assumptions.price, assumptions.currency) if assumptions.price is not None else flow(target, assumptions))}</text>
  <text x="300" y="334" fill="#5e584e" font-family="Helvetica, Arial, sans-serif" font-size="12">EARNINGS NOW</text>
  <text x="300" y="360" fill="#1c1915" font-family="Palatino, 'Palatino Linotype', Georgia, serif" font-size="20">{_x(flow(assumptions.earnings, assumptions))}</text>
  <text x="560" y="334" fill="#5e584e" font-family="Helvetica, Arial, sans-serif" font-size="12">{_x(year_label)}</text>
  <text x="560" y="360" fill="#1c1915" font-family="Palatino, 'Palatino Linotype', Georgia, serif" font-size="20">{_x(flow(valuation.year_n_earnings, assumptions))}</text>
  <text x="780" y="334" fill="#5e584e" font-family="Helvetica, Arial, sans-serif" font-size="12">TERMINAL SHARE</text>
  <text x="780" y="360" fill="#1c1915" font-family="Palatino, 'Palatino Linotype', Georgia, serif" font-size="20">{_x(percent(valuation.terminal_share))}</text>
  <line x1="48" y1="390" x2="912" y2="390" stroke="#d9d2c5"/>
  <text x="48" y="422" fill="#1c1915" font-family="Helvetica, Arial, sans-serif" font-size="14">Explicit {_x(flow(valuation.explicit_pv, assumptions))} · terminal {_x(flow(valuation.terminal_pv, assumptions))}</text>
  <text x="48" y="448" fill="#1c1915" font-family="Helvetica, Arial, sans-serif" font-size="13">Key assumptions</text><text x="48" y="468" fill="#5e584e" font-family="Helvetica, Arial, sans-serif" font-size="13">{_x(lines[0])}</text><text x="48" y="488" fill="#5e584e" font-family="Helvetica, Arial, sans-serif" font-size="13">{_x(lines[1] if len(lines) > 1 else '')}</text><text x="48" y="508" fill="#5e584e" font-family="Helvetica, Arial, sans-serif" font-size="13">{_x(lines[2] if len(lines) > 2 else '')}</text>
{flag}  <text x="48" y="{footer_y}" fill="#1c1915" font-family="Helvetica, Arial, sans-serif" font-size="13">Not a recommendation. One model, read backwards.</text>
</svg>
"""
    return body


def diff_svg(reading):
    before_pct = percent(reading.growth_before)
    after_pct = percent(reading.growth_after)
    delta = f"{(reading.growth_after - reading.growth_before) * 100:.2f} pp"
    lines = _diff_assumption_lines(reading)
    change_lines = []
    for change in reading.changes:
        if not isinstance(change["before"], (int, float)) or not isinstance(change["after"], (int, float)):
            continue
        role = "moves the growth" if change["affects_implied_growth"] else "disclosed only"
        change_lines.append(
            f"{change['field']}   {_compact(change['before'])}  →  {_compact(change['after'])}   {role}"
        )
    first = change_lines[0] if change_lines else ""
    second = change_lines[1] if len(change_lines) > 1 else ""
    value_line = (
        f"Value at {before_pct}: {flow(reading.value_before, reading.before)} → "
        f"{flow(reading.value_after, reading.after)}"
    )
    name = reading.before.name or ""
    body = f"""<svg xmlns="http://www.w3.org/2000/svg" width="960" height="540" viewBox="0 0 960 540" role="img">
  <title>What changed — {_x(reading.before.ticker)} {_x(before_pct)} to {_x(after_pct)}</title>
  <desc>Earnings assumption diff. Not a recommendation.</desc>
  <rect width="960" height="540" fill="#f3efe6"/>
  <rect width="8" height="540" fill="#9c3418"/>
  <text x="48" y="46" fill="#9c3418" font-family="Helvetica, Arial, sans-serif" font-size="13" letter-spacing="2.4">WHAT CHANGED</text>
  <text x="48" y="108" fill="#1c1915" font-family="Palatino, 'Palatino Linotype', Georgia, serif" font-size="42">{_x(reading.before.ticker)}</text>
  <text x="48" y="140" fill="#5e584e" font-family="Palatino, 'Palatino Linotype', Georgia, serif" font-size="16">{_x(name)}</text>
  <text x="48" y="210" fill="#1c1915" font-family="Palatino, 'Palatino Linotype', Georgia, serif" font-size="28">{_x(before_pct)}  →  {_x(after_pct)}</text>
  <text x="520" y="210" fill="#9c3418" font-family="Palatino, 'Palatino Linotype', Georgia, serif" font-size="28">{_x(delta)}</text>
  <text x="48" y="248" fill="#1c1915" font-family="Helvetica, Arial, sans-serif" font-size="13">Key assumptions</text><text x="48" y="268" fill="#5e584e" font-family="Helvetica, Arial, sans-serif" font-size="13">{_x(lines[0])}</text><text x="48" y="288" fill="#5e584e" font-family="Helvetica, Arial, sans-serif" font-size="13">{_x(lines[1] if len(lines) > 1 else '')}</text><text x="48" y="308" fill="#5e584e" font-family="Helvetica, Arial, sans-serif" font-size="13">{_x(lines[2] if len(lines) > 2 else '')}</text>
  <text x="48" y="344" fill="#1c1915" font-family="Helvetica, Arial, sans-serif" font-size="16">{_x(first)}</text><text x="48" y="372" fill="#1c1915" font-family="Helvetica, Arial, sans-serif" font-size="16">{_x(second)}</text>
  <text x="48" y="408" fill="#5e584e" font-family="Helvetica, Arial, sans-serif" font-size="14">{_x(value_line)}</text>
  <text x="48" y="452" fill="#1c1915" font-family="Helvetica, Arial, sans-serif" font-size="13">Not a recommendation. Implied growth under each assumption set.</text>
</svg>
"""
    return body


def plain_svg(reading):
    headline = reading.key_assumptions.get("basis", reading.mode)
    lines = _assumption_lines(reading.key_assumptions)
    joined = " · ".join(lines)
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="960" height="420" viewBox="0 0 960 420" role="img">
  <title>What's priced in — {_x(reading.assumptions.ticker)}</title>
  <desc>Not a recommendation.</desc>
  <rect width="960" height="420" fill="#f3efe6"/>
  <rect width="8" height="420" fill="#9c3418"/>
  <text x="48" y="80" font-size="28">{_x(headline)}</text>
  <text x="48" y="140" font-size="14">Key assumptions</text>
  <text x="48" y="170" font-size="13">{_x(joined)}</text>
  <text x="48" y="380" font-size="13">Not a recommendation.</text>
</svg>
"""


def _assumption_lines(pairs):
    shown = [(key, value) for key, value in pairs.items() if key != "price"]
    lines = []
    for index in range(0, min(len(shown), 9), 3):
        group = shown[index : index + 3]
        lines.append(" · ".join(f"{key} {value}" for key, value in group))
    while len(lines) < 3:
        lines.append("")
    return lines


def _diff_assumption_lines(reading):
    before = dict(reading.key_assumptions_before)
    after = dict(reading.key_assumptions_after)
    if "earnings" in before and before.get("earnings") != after.get("earnings"):
        before["earnings"] = f"{before['earnings']} → {after['earnings']}"
    return _assumption_lines(before)


def _chart_y(value):
    return round(308.1 - 0.5213 * value, 1)


def _compact(number):
    return f"{float(number):.10f}".rstrip("0").rstrip(".")


def _x(text):
    return (
        str(text)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )
