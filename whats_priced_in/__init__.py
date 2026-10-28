"""Price in, implied bet out.

Reverse equity DCF and dividend-yield readings. The arithmetic is deterministic.
Tax, payout, terminal growth, timing, and scale are returned on every result.
"""

from __future__ import annotations

from whats_priced_in._version import __version__
from whats_priced_in.assumptions import (
    Assumptions,
    as_per_share,
    load_assumptions,
    load_example,
    prepare,
)
from whats_priced_in.dcf import (
    FORMULA,
    MarginResult,
    SolveGrowthResult,
    Valuation,
    YearsResult,
    solve_growth,
    solve_margin,
    solve_years,
    value_growth,
)
from whats_priced_in.disclosure import Disclosure
from whats_priced_in.dividend import DividendCase, DividendResult, implied_dividend, load_dividend
from whats_priced_in.earnings_assumption_diff import DiffResult, diff_assumptions
from whats_priced_in.errors import LiveDataNotImplemented, ModelError
from whats_priced_in.fetchers import fetch_dfm_quote, fetch_edgar_companyfacts, fetch_nse_quote
from whats_priced_in.scales import SCALE_FACTORS, to_base_units

__all__ = [
    "Assumptions",
    "Disclosure",
    "DiffResult",
    "DividendCase",
    "DividendResult",
    "FORMULA",
    "LiveDataNotImplemented",
    "MarginResult",
    "ModelError",
    "SCALE_FACTORS",
    "SolveGrowthResult",
    "Valuation",
    "YearsResult",
    "__version__",
    "as_per_share",
    "diff_assumptions",
    "fetch_dfm_quote",
    "fetch_edgar_companyfacts",
    "fetch_nse_quote",
    "implied_dividend",
    "load_assumptions",
    "load_dividend",
    "load_example",
    "prepare",
    "solve_growth",
    "solve_margin",
    "solve_years",
    "to_base_units",
    "value_growth",
]
