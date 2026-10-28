"""Stubs for live quotes. This MVP does not call the network."""


class LiveDataNotImplemented(NotImplementedError):
    """Raised by every live fetcher. The caller supplies the numbers."""


def _refuse(source, what):
    raise LiveDataNotImplemented(
        f"This MVP does not call the network. {what} is a stub for {source}. "
        "Pass price, earnings, currency, and scale yourself."
    )


def fetch_nse_quote(symbol):
    _refuse("NSE", "fetch_nse_quote")


def fetch_edgar_companyfacts(cik):
    _refuse("US EDGAR", "fetch_edgar_companyfacts")


def fetch_dfm_quote(symbol):
    _refuse("Dubai (DFM)", "fetch_dfm_quote")
