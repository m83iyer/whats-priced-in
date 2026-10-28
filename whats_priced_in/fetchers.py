"""Live market data. Stubs only.

The MVP is numbers in, numbers out. These functions exist so a later patch can
fetch a price and an earnings figure without changing the solve. They must
return numbers, not a recommendation, and they must leave the cost of equity
to the caller. Nothing in this module opens a network connection.
"""

from __future__ import annotations

from whats_priced_in.errors import LiveDataNotImplemented


def fetch_nse_quote(symbol: str) -> dict:
    """TODO(NSE): quote and latest earnings for an Indian listing.

    A future implementation should return price, shares, earnings, currency INR,
    and the scale the filing actually uses (often crore). It should not pick a
    cost of equity.
    """

    raise LiveDataNotImplemented(
        "TODO(NSE): live quotes are not implemented. "
        f"Pass numbers for {symbol!r}. Currency INR and scale crore are inputs, not a fetcher. "
        "This MVP does not call the network."
    )


def fetch_edgar_companyfacts(cik: str) -> dict:
    """TODO(EDGAR): SEC company facts for a US filer.

    A future implementation should return plain figures (shares, earnings or
    FCFE, currency USD, scale unit or million). It should not pick a cost of equity.
    """

    raise LiveDataNotImplemented(
        "TODO(EDGAR): SEC companyfacts are not implemented. "
        f"Pass numbers for CIK {cik!r}. Currency USD is an input, not a fetcher. "
        "This MVP does not call the network."
    )


def fetch_dfm_quote(symbol: str) -> dict:
    """TODO(DFM): quote for a Dubai Financial Market listing.

    A future implementation should return price and earnings with currency AED
    and the scale you are actually using (often million). It should not pick a
    cost of equity.
    """

    raise LiveDataNotImplemented(
        "TODO(DFM): Dubai Financial Market quotes are not implemented. "
        f"Pass numbers for {symbol!r}. Currency AED is an input, not a fetcher. "
        "This MVP does not call the network."
    )
