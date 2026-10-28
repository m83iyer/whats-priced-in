"""Price in, implied bet out."""

from whats_priced_in.api import solve_growth, solve_margin, solve_years, value_growth
from whats_priced_in.assumptions import Assumptions, load_assumptions, load_example
from whats_priced_in.dividend import implied_dividend, load_dividend_example
from whats_priced_in.earnings_assumption_diff import diff_assumptions
from whats_priced_in.scale import SCALE_FACTORS

__version__ = "0.1.0"

__all__ = [
    "Assumptions",
    "SCALE_FACTORS",
    "diff_assumptions",
    "implied_dividend",
    "load_assumptions",
    "load_dividend_example",
    "load_example",
    "solve_growth",
    "solve_margin",
    "solve_years",
    "value_growth",
]
