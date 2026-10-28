"""Command line. `wpi` and `whats-priced-in` call this main."""

import argparse
import json
import sys

from whats_priced_in.api import solve_growth, solve_margin, solve_years, value_growth
from whats_priced_in.assumptions import Assumptions, load_assumptions, load_example
from whats_priced_in.card import svg_for
from whats_priced_in.dividend import implied_dividend
from whats_priced_in.earnings_assumption_diff import diff_assumptions
from whats_priced_in.sensitivity import run_sensitivity


def main(argv=None):
    parser = argparse.ArgumentParser(prog="wpi", description="Price in, implied bet out.")
    sub = parser.add_subparsers(dest="command", required=True)

    solve = sub.add_parser("solve")
    _add_source(solve)
    solve.add_argument("--mode", choices=("growth", "margin", "years", "yield"), default="growth")
    solve.add_argument("--revenue-growth", type=float)
    solve.add_argument("--growth", type=float)
    solve.add_argument("--json", action="store_true")
    solve.add_argument("--card")
    solve.set_defaults(func=_solve)

    value = sub.add_parser("value")
    _add_source(value)
    value.add_argument("--growth", type=float, required=True)
    value.add_argument("--json", action="store_true")
    value.set_defaults(func=_value)

    sens = sub.add_parser("sens")
    _add_source(sens)
    sens.add_argument("--parameter")
    sens.add_argument("--values")
    sens.add_argument("--json", action="store_true")
    sens.set_defaults(func=_sens)

    diff = sub.add_parser("diff")
    diff.add_argument("before")
    diff.add_argument("after")
    diff.add_argument("--price", type=float)
    diff.add_argument("--card")
    diff.add_argument("--json", action="store_true")
    diff.set_defaults(func=_diff)

    card = sub.add_parser("card")
    _add_source(card)
    card.add_argument("-o", "--output", required=True)
    card.set_defaults(func=_card)

    args = parser.parse_args(argv)
    try:
        args.func(args)
    except ValueError as exc:
        print(exc, file=sys.stderr)
        return 1
    return 0


def _add_source(parser):
    parser.add_argument("-f", "--file")
    parser.add_argument("--example")
    parser.add_argument("--ticker")
    parser.add_argument("--name")
    parser.add_argument("--notes")
    parser.add_argument("--currency")
    parser.add_argument("--scale")
    parser.add_argument("--price", type=float)
    parser.add_argument("--shares", type=float)
    parser.add_argument("--market-cap", type=float)
    parser.add_argument("--earnings", type=float)
    parser.add_argument("--revenue", type=float)
    parser.add_argument("--cost-of-equity", type=float)
    parser.add_argument("--terminal-growth", type=float)
    parser.add_argument("--years", type=int)
    parser.add_argument("--payout", type=float)
    parser.add_argument("--earnings-basis")
    parser.add_argument("--tax-rate", type=float)
    parser.add_argument("--discount-convention")
    parser.add_argument("--dividend", type=float)
    parser.add_argument("--dividend-timing")


def _assumptions(args):
    if args.file and args.example:
        raise ValueError("Pass a file or an example, not both.")
    if args.file:
        assumptions = load_assumptions(args.file)
    elif args.example:
        assumptions = load_example(args.example)
    else:
        if not getattr(args, "currency", None) or not getattr(args, "scale", None):
            raise ValueError("Without a file, pass --currency and --scale.")
        assumptions = Assumptions(currency=args.currency, scale=args.scale)
    overrides = {}
    mapping = {
        "ticker": "ticker",
        "name": "name",
        "notes": "notes",
        "currency": "currency",
        "scale": "scale",
        "price": "price",
        "shares": "shares",
        "market_cap": "market_cap",
        "earnings": "earnings",
        "revenue": "revenue",
        "cost_of_equity": "cost_of_equity",
        "terminal_growth": "terminal_growth",
        "years": "years",
        "payout": "payout",
        "earnings_basis": "earnings_basis",
        "tax_rate": "tax_rate",
        "discount_convention": "discount_convention",
        "dividend": "dividend",
        "dividend_timing": "dividend_timing",
    }
    for arg_name, field in mapping.items():
        value = getattr(args, arg_name, None)
        if value is not None:
            overrides[field] = value
    if overrides:
        assumptions = assumptions.replace(**overrides)
    return assumptions


def _emit(reading, as_json, card_path=None):
    if card_path:
        from pathlib import Path

        Path(card_path).write_text(svg_for(reading))
    if as_json:
        print(json.dumps(reading.payload, indent=2))
        return
    print(reading.text)
    if card_path:
        print(f"Card written to {card_path}")


def _solve(args):
    assumptions = _assumptions(args)
    if args.mode == "growth":
        reading = solve_growth(assumptions)
    elif args.mode == "margin":
        if args.revenue_growth is None:
            if assumptions.revenue_growth is None:
                raise ValueError("A margin solve needs --revenue-growth.")
            revenue_growth = assumptions.revenue_growth
        else:
            revenue_growth = args.revenue_growth
        reading = solve_margin(assumptions, revenue_growth)
    elif args.mode == "years":
        if args.growth is None:
            raise ValueError("A horizon solve needs --growth.")
        reading = solve_years(assumptions, args.growth)
    else:
        reading = implied_dividend(assumptions)
    _emit(reading, args.json, args.card)


def _value(args):
    _emit(value_growth(args.growth, _assumptions(args)), args.json)


def _sens(args):
    parameter = args.parameter.replace("-", "_") if args.parameter else None
    values = None
    if args.values:
        values = [float(part) for part in args.values.split(",") if part.strip() != ""]
    reading = run_sensitivity(_assumptions(args), parameter, values)
    _emit(reading, args.json)


def _diff(args):
    before = load_assumptions(args.before)
    after = load_assumptions(args.after)
    if args.price is not None:
        before = before.replace(price=args.price, market_cap=None)
        after = after.replace(price=args.price, market_cap=None)
    reading = diff_assumptions(before, after)
    _emit(reading, args.json, args.card)


def _card(args):
    reading = solve_growth(_assumptions(args))
    from pathlib import Path

    Path(args.output).write_text(svg_for(reading))
    print(reading.text)
    print(f"Card written to {args.output}")


if __name__ == "__main__":
    sys.exit(main())
