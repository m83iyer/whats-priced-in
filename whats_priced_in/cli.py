"""Command line: solve, value, diff, sens, card."""

from __future__ import annotations

import argparse
import sys
from dataclasses import replace

from whats_priced_in._version import __version__
from whats_priced_in.assumptions import (
    Assumptions,
    load_assumptions,
    load_example,
    prepare,
)
from whats_priced_in.card import render_diff_card, render_growth_card, write_svg
from whats_priced_in.dcf import solve_growth, solve_margin, solve_years, value_growth
from whats_priced_in.dividend import DividendCase, implied_dividend, load_dividend, prepare_dividend
from whats_priced_in.earnings_assumption_diff import diff_assumptions
from whats_priced_in.errors import ModelError
from whats_priced_in.formatting import (
    diff_payload,
    dividend_payload,
    dumps,
    format_diff,
    format_dividend,
    format_margin,
    format_sensitivity,
    format_solve_growth,
    format_valuation,
    format_years,
    growth_payload,
    margin_payload,
    sensitivity_payload,
    valuation_payload,
    years_payload,
)
from whats_priced_in.sensitivity import implied_growth_sensitivity, value_sensitivity

EPILOG = """
examples:
  wpi solve -f examples/synth.yaml
  wpi solve --mode margin -f examples/synth.yaml --revenue-growth 0.06
  wpi solve --mode years -f examples/synth.yaml --growth 0.12
  wpi solve --mode yield -f examples/dividend.yaml
  wpi value --growth 0.06 -f examples/synth.yaml
  wpi sens -f examples/synth.yaml
  wpi diff examples/diff/pre.yaml examples/diff/post.yaml
  wpi card -f examples/synth.yaml -o synth-card.svg

Rates are decimals: 0.11 for 11 percent. Currency and scale are required when
you do not pass a file, so a market is not assumed.
""".strip()


def main(argv: list[str] | None = None) -> int:
    parser = _parser()
    args = parser.parse_args(argv)
    if not getattr(args, "func", None):
        parser.print_help()
        return 2
    try:
        return args.func(args)
    except ModelError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    except OSError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


def cmd_solve(args: argparse.Namespace) -> int:
    if args.card and args.mode != "growth":
        raise ModelError("solve --card writes the growth card. For a diff, use `wpi diff --card`.")
    if args.mode == "yield":
        result = implied_dividend(_load_dividend(args))
        _emit(args, format_dividend(result), dividend_payload(result), card=None)
        return 0
    assumptions = _load_assumptions(args)
    card = None
    if args.mode == "growth":
        result = solve_growth(assumptions)
        if args.card:
            card = str(write_svg(render_growth_card(result), args.card))
        _emit(args, format_solve_growth(result), growth_payload(result, card=card), card=card)
        return 0
    if args.mode == "margin":
        result = solve_margin(
            assumptions,
            revenue_growth=args.revenue_growth,
            margin_start=args.margin_start,
        )
        _emit(args, format_margin(result), margin_payload(result), card=None)
        return 0
    if args.growth is None:
        raise ModelError("Years mode needs --growth, the rate held fixed while the horizon moves.")
    result = solve_years(assumptions, growth=args.growth, max_years=args.max_years)
    _emit(args, format_years(result), years_payload(result), card=None)
    return 0


def cmd_value(args: argparse.Namespace) -> int:
    result = value_growth(args.growth, _load_assumptions(args))
    _emit(args, format_valuation(result), valuation_payload(result), card=None)
    return 0


def cmd_sens(args: argparse.Namespace) -> int:
    assumptions = _load_assumptions(args)
    values = _parse_values(args.values) if args.values else None
    tables = []
    if args.parameter is None or args.parameter == "growth":
        tables.append(value_sensitivity(assumptions, values if args.parameter == "growth" else None))
    if args.parameter is None:
        for name in ("cost_of_equity", "terminal_growth", "payout"):
            tables.append(implied_growth_sensitivity(assumptions, name))
    elif args.parameter != "growth":
        tables.append(implied_growth_sensitivity(assumptions, args.parameter, values))
    _emit(args, format_sensitivity(tables), sensitivity_payload(tables), card=None)
    return 0


def cmd_diff(args: argparse.Namespace) -> int:
    before = load_assumptions(args.before)
    after = load_assumptions(args.after)
    result = diff_assumptions(
        before,
        after,
        reference_growth=args.reference_growth,
        price=args.price,
    )
    card = None
    if args.card:
        card = str(write_svg(render_diff_card(result), args.card))
    _emit(args, format_diff(result), diff_payload(result, card=card), card=card)
    return 0


def cmd_card(args: argparse.Namespace) -> int:
    result = solve_growth(_load_assumptions(args))
    path = str(write_svg(render_growth_card(result), args.output))
    _emit(args, format_solve_growth(result), growth_payload(result, card=path), card=path)
    return 0


def _emit(args: argparse.Namespace, text: str, payload: dict, card: str | None) -> None:
    if args.json:
        sys.stdout.write(dumps(payload))
        return
    sys.stdout.write(text)
    if card:
        sys.stdout.write(f"Card written to {card}\n")


def _load_assumptions(args: argparse.Namespace) -> Assumptions:
    if args.example and args.assumptions:
        raise ModelError("Pass --example or --assumptions, not both.")
    if args.example:
        base = load_example(args.example)
    elif args.assumptions:
        base = load_assumptions(args.assumptions)
    else:
        base = _assumptions_from_flags(args)
        return base
    return _apply_overrides(base, args)


def _load_dividend(args: argparse.Namespace) -> DividendCase:
    if args.example and args.assumptions:
        raise ModelError("Pass --example or --assumptions, not both.")
    if args.example:
        from whats_priced_in.assumptions import examples_dir

        base = load_dividend(examples_dir() / f"{args.example}.yaml")
    elif args.assumptions:
        base = load_dividend(args.assumptions)
    else:
        base = _dividend_from_flags(args)
        return base
    updates = {}
    if args.ticker is not None:
        updates["ticker"] = args.ticker
    if args.currency is not None:
        updates["currency"] = args.currency
    if args.scale is not None:
        updates["scale"] = args.scale
    if args.price is not None:
        updates["price"] = args.price
    if args.earnings is not None:
        updates["earnings"] = args.earnings
    if args.cost_of_equity is not None:
        updates["cost_of_equity"] = args.cost_of_equity
    if args.basis is not None:
        updates["earnings_basis"] = args.basis
    if args.annual_dividend is not None:
        updates["annual_dividend"] = args.annual_dividend
    if args.dividend_timing is not None:
        updates["dividend_timing"] = args.dividend_timing
    if args.growth is not None:
        updates["growth"] = args.growth
    if args.notes is not None:
        updates["notes"] = args.notes
    if not updates:
        return base
    return prepare_dividend(replace(base, **updates))


def _assumptions_from_flags(args: argparse.Namespace) -> Assumptions:
    missing = []
    for flag, attr in (
        ("--currency", "currency"),
        ("--scale", "scale"),
        ("--earnings", "earnings"),
        ("--cost-of-equity", "cost_of_equity"),
        ("--terminal-growth", "terminal_growth"),
    ):
        if getattr(args, attr) is None:
            missing.append(flag)
    if missing:
        raise ModelError(
            "Missing "
            + ", ".join(missing)
            + ". Rates are decimals. Pass --currency and --scale so a market is not assumed, "
            "or pass --assumptions / --example."
        )
    if args.price is None and args.market_cap is None:
        raise ModelError("Pass --price, or --market-cap, or both --price and --shares.")
    return prepare(
        Assumptions(
            ticker=args.ticker,
            name=args.name,
            currency=args.currency,
            scale=args.scale,
            price=args.price,
            shares=args.shares,
            market_cap=args.market_cap,
            earnings=args.earnings,
            revenue=args.revenue,
            revenue_growth=args.revenue_growth,
            cost_of_equity=args.cost_of_equity,
            terminal_growth=args.terminal_growth,
            years=10 if args.years is None else args.years,
            payout=1.0 if args.payout is None else args.payout,
            earnings_basis="fcfe" if args.basis is None else args.basis,
            discount_convention="end_of_year" if args.discount is None else args.discount,
            tax_rate=args.tax_rate,
            notes=args.notes or "",
        )
    )


def _dividend_from_flags(args: argparse.Namespace) -> DividendCase:
    missing = [
        flag
        for flag, attr in (
            ("--currency", "currency"),
            ("--scale", "scale"),
            ("--price", "price"),
            ("--dividend", "annual_dividend"),
        )
        if getattr(args, attr) is None
    ]
    if missing:
        raise ModelError(
            "Yield mode needs " + ", ".join(missing) + ". Or pass -f examples/dividend.yaml."
        )
    return prepare_dividend(
        DividendCase(
            ticker=args.ticker,
            name=args.name,
            currency=args.currency,
            scale=args.scale,
            price=args.price,
            annual_dividend=args.annual_dividend,
            dividend_timing=args.dividend_timing or "next",
            earnings=args.earnings,
            earnings_basis=args.basis or "ffo",
            cost_of_equity=args.cost_of_equity,
            growth=args.growth,
            notes=args.notes or "",
        )
    )


def _apply_overrides(base: Assumptions, args: argparse.Namespace) -> Assumptions:
    mapping = {
        "ticker": args.ticker,
        "name": args.name,
        "currency": args.currency,
        "scale": args.scale,
        "price": args.price,
        "shares": args.shares,
        "market_cap": args.market_cap,
        "earnings": args.earnings,
        "revenue": args.revenue,
        "revenue_growth": getattr(args, "revenue_growth", None),
        "cost_of_equity": args.cost_of_equity,
        "terminal_growth": args.terminal_growth,
        "years": args.years,
        "payout": args.payout,
        "earnings_basis": args.basis,
        "discount_convention": args.discount,
        "tax_rate": args.tax_rate,
        "notes": args.notes,
    }
    updates = {key: value for key, value in mapping.items() if value is not None}
    if not updates:
        return base
    return prepare(replace(base, **updates))


def _parse_values(raw: str) -> tuple[float, ...]:
    try:
        return tuple(float(piece.strip()) for piece in raw.split(",") if piece.strip())
    except ValueError as exc:
        raise ModelError(
            f"--values must be comma-separated decimals, got {raw!r}."
        ) from exc


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="wpi",
        description="Price in, implied bet out. Reverse DCF for a price you already have.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=EPILOG,
    )
    parser.add_argument("--version", action="version", version=f"whats-priced-in {__version__}")
    sub = parser.add_subparsers(dest="command")

    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--json", action="store_true", help="print the JSON payload")
    common.add_argument("-f", "--assumptions", help="YAML file of inputs")
    common.add_argument(
        "--example",
        help="named example in examples/ (synth, narmada, creek, dividend)",
    )
    flags = argparse.ArgumentParser(add_help=False)
    _add_shared_flags(flags)

    solve = sub.add_parser(
        "solve",
        parents=[common, flags],
        help="solve for growth, margin, years, or dividend yield",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    solve.add_argument(
        "--mode",
        choices=("growth", "margin", "years", "yield"),
        default="growth",
        help="what the price is solved for (default: growth)",
    )
    solve.add_argument("--growth", type=float, help="growth held fixed in years mode")
    solve.add_argument("--revenue-growth", dest="revenue_growth", type=float)
    solve.add_argument("--margin-start", dest="margin_start", type=float, help="year-1 margin when fading")
    solve.add_argument("--max-years", dest="max_years", type=int, default=20)
    solve.add_argument("--dividend", dest="annual_dividend", type=float)
    solve.add_argument("--dividend-timing", dest="dividend_timing", choices=("next", "trailing"))
    solve.add_argument("--card", metavar="PATH", help="also write an SVG card (growth mode)")
    solve.set_defaults(func=cmd_solve)

    value = sub.add_parser(
        "value",
        parents=[common, flags],
        help="forward value at a growth rate you choose",
    )
    value.add_argument("--growth", required=True, type=float)
    value.set_defaults(func=cmd_value, card=None, revenue_growth=None)

    sens = sub.add_parser(
        "sens",
        parents=[common, flags],
        help="value or implied growth as one input moves",
    )
    sens.add_argument(
        "--parameter",
        choices=("growth", "cost_of_equity", "terminal_growth", "payout", "years"),
        help="default prints growth, cost of equity, terminal growth, and payout",
    )
    sens.add_argument("--values", help="comma-separated decimals, or integer years")
    sens.set_defaults(func=cmd_sens, card=None, revenue_growth=None)

    diff = sub.add_parser(
        "diff",
        help="what changed between two YAML assumption sets, and the implied-growth delta",
    )
    diff.add_argument("before", help="pre-earnings YAML")
    diff.add_argument("after", help="post-earnings YAML")
    diff.add_argument("--price", type=float, help="override the price on both sets")
    diff.add_argument("--reference-growth", dest="reference_growth", type=float)
    diff.add_argument("--json", action="store_true")
    diff.add_argument("--card", metavar="PATH")
    diff.set_defaults(func=cmd_diff)

    card = sub.add_parser(
        "card",
        parents=[common, flags],
        help="write a What's priced in SVG card",
    )
    card.add_argument("-o", "--output", required=True, help="SVG path")
    card.set_defaults(func=cmd_card, revenue_growth=None)
    return parser


def _add_shared_flags(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--ticker")
    parser.add_argument("--name")
    parser.add_argument("--currency", help="INR, USD, AED, or any three-letter code")
    parser.add_argument(
        "--scale",
        help="unit, thousand, lakh, million, crore, or billion",
    )
    parser.add_argument("--price", type=float)
    parser.add_argument("--shares", type=float, help="same scale as earnings and market cap")
    parser.add_argument("--market-cap", dest="market_cap", type=float)
    parser.add_argument("--earnings", type=float, help="time-0 earnings, FCFE, PAT, or FFO")
    parser.add_argument("--revenue", type=float)
    parser.add_argument("--cost-of-equity", "--coe", dest="cost_of_equity", type=float)
    parser.add_argument("--terminal-growth", "--gt", dest="terminal_growth", type=float)
    parser.add_argument("--years", type=int)
    parser.add_argument("--payout", type=float, help="fraction of earnings that is cash to equity")
    parser.add_argument("--basis", choices=("fcfe", "pat", "ffo", "owner_earnings"))
    parser.add_argument("--discount", choices=("end_of_year", "mid_year"))
    parser.add_argument("--tax-rate", dest="tax_rate", type=float, help="disclosed, not applied")
    parser.add_argument("--notes")
