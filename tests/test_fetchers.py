"""Live fetchers stay stubs. They must not grow a network client by accident."""

from __future__ import annotations

import pytest

from whats_priced_in import (
    LiveDataNotImplemented,
    fetch_dfm_quote,
    fetch_edgar_companyfacts,
    fetch_nse_quote,
)


def test_nse_stub():
    with pytest.raises(LiveDataNotImplemented, match="NSE"):
        fetch_nse_quote("SYNTH")


def test_edgar_stub():
    with pytest.raises(LiveDataNotImplemented, match="EDGAR"):
        fetch_edgar_companyfacts("0000000000")


def test_dfm_stub():
    with pytest.raises(LiveDataNotImplemented, match="DFM"):
        fetch_dfm_quote("CREEK")


def test_messages_name_the_unfinished_work():
    for function, symbol in (
        (fetch_nse_quote, "NARMADA"),
        (fetch_edgar_companyfacts, "0000000000"),
        (fetch_dfm_quote, "CREEK"),
    ):
        with pytest.raises(LiveDataNotImplemented) as caught:
            function(symbol)
        text = str(caught.value)
        assert "not implemented" in text.lower()
        assert "network" in text.lower()
