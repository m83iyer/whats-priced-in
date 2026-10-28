"""Two-stage cash flow to equity with a Gordon terminal value."""

from dataclasses import dataclass

FORMULA = (
    "E_t = E_0*(1+g)^t; CF_t = payout*E_t; "
    "V = sum_{t=1..N} CF_t/(1+r)^t + CF_N*(1+g_T)/((r-g_T)*(1+r)^N)"
)
MODEL_NAME = "two_stage_fcfe_gordon"
VERSION = "0.1.0"
HORIZON_LIMIT = 20

PAYOUT_WARNING = (
    "Payout is at or above 95% while growth is above the terminal rate. "
    "The model does not use retained earnings to fund that growth. "
    "That fits an asset-light business, or earnings that are already net of "
    "the reinvestment you believe. If growth needs reinvestment, lower the payout."
)


@dataclass
class Valuation:
    growth: float
    equity_value: float
    explicit_pv: float
    terminal_pv: float
    terminal_value_at_horizon: float
    year_n_earnings: float
    earnings_path: list
    cashflow_path: list

    @property
    def terminal_share(self):
        if self.equity_value == 0:
            return 0.0
        return self.terminal_pv / self.equity_value


def present_value(earnings, growth, cost_of_equity, terminal_growth, years, payout, discount_convention="end_of_year"):
    """Year-end two-stage value. Mid-year multiplies that present value by (1+r)^0.5."""
    if years < 1:
        raise ValueError("Years has to be at least 1.")
    if cost_of_equity <= terminal_growth:
        raise ValueError("Terminal growth must be below the cost of equity.")
    r = cost_of_equity
    earnings_path = []
    cashflow_path = []
    explicit = 0.0
    for t in range(1, years + 1):
        earned = earnings * (1 + growth) ** t
        cash = payout * earned
        earnings_path.append(earned)
        cashflow_path.append(cash)
        explicit += cash / (1 + r) ** t
    cash_n = cashflow_path[-1]
    terminal_at_horizon = cash_n * (1 + terminal_growth) / (r - terminal_growth)
    terminal_pv = terminal_at_horizon / (1 + r) ** years
    equity = explicit + terminal_pv
    if discount_convention == "mid_year":
        factor = (1 + r) ** 0.5
        explicit *= factor
        terminal_pv *= factor
        equity *= factor
    return Valuation(
        growth=growth,
        equity_value=equity,
        explicit_pv=explicit,
        terminal_pv=terminal_pv,
        terminal_value_at_horizon=terminal_at_horizon,
        year_n_earnings=earnings_path[-1],
        earnings_path=earnings_path,
        cashflow_path=cashflow_path,
    )


def implied_growth(earnings, cost_of_equity, terminal_growth, years, payout, target, discount_convention="end_of_year"):
    """Growth g such that present value equals the target."""
    if earnings <= 0:
        raise ValueError("Earnings have to be positive.")
    if target <= 0:
        raise ValueError("The target has to be positive.")
    if payout < 0:
        raise ValueError("Payout cannot be negative.")

    def value_at(growth):
        return present_value(
            earnings, growth, cost_of_equity, terminal_growth, years, payout, discount_convention
        ).equity_value

    if payout == 0 or value_at(5) < target:
        raise ValueError("No growth rate meets the target.")
    low = -0.9
    if value_at(low) > target:
        raise ValueError("The target is below the model even at a large decline.")
    high = 0.0
    while value_at(high) < target:
        high = 0.05 if high == 0 else high * 1.5 + 0.01
        if high > 5:
            raise ValueError("No growth rate meets the target.")
    for _ in range(80):
        mid = (low + high) / 2
        if value_at(mid) < target:
            low = mid
        else:
            high = mid
    growth = (low + high) / 2
    return present_value(
        earnings, growth, cost_of_equity, terminal_growth, years, payout, discount_convention
    )


def payout_warning(payout, growth, terminal_growth):
    if payout >= 0.95 and growth > terminal_growth:
        return PAYOUT_WARNING
    return None
