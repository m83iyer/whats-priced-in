"""Currency codes and reporting scales.

The engine never converts. Earnings and the price (or market cap) must already
be in one scale. ``SCALE_FACTORS`` is metadata for callers who want base units:
1 crore = 10,000,000 currency units. Picking INR does not select a tax rate, a
cost of equity, or the crore scale. Those stay explicit fields.
"""

from __future__ import annotations

from whats_priced_in.errors import ModelError

SCALE_FACTORS: dict[str, float] = {
    "unit": 1.0,
    "thousand": 1_000.0,
    "lakh": 100_000.0,
    "million": 1_000_000.0,
    "crore": 10_000_000.0,
    "billion": 1_000_000_000.0,
}

SCALE_NOTES: dict[str, str] = {
    "unit": "one currency unit; use this for per-share figures",
    "thousand": "thousands of currency units",
    "lakh": "lakhs (100,000); used in some Indian filings",
    "million": "millions of currency units",
    "crore": "crores (10,000,000); standard for Indian market cap and profit",
    "billion": "billions of currency units",
}

# Symbols for display. Unknown ISO codes are printed as the code plus a space.
CURRENCY_SYMBOLS: dict[str, str] = {
    "USD": "$",
    "INR": "₹",
    "AED": "AED ",
    "EUR": "€",
    "GBP": "£",
}


def normalise_currency(currency: str) -> str:
    if not isinstance(currency, str):
        raise ModelError("currency must be a three-letter code such as INR, USD, or AED.")
    code = currency.strip().upper()
    if len(code) != 3 or not code.isalpha():
        raise ModelError(
            f"currency {currency!r} is not a three-letter code. "
            "Use INR, USD, AED, or any other ISO-style code. The engine does not assume a market."
        )
    return code


def normalise_scale(scale: str) -> str:
    if not isinstance(scale, str):
        raise ModelError(
            "scale must be one of: " + ", ".join(SCALE_FACTORS) + "."
        )
    name = scale.strip().lower()
    if name not in SCALE_FACTORS:
        raise ModelError(
            f"Unknown scale {scale!r}. Use one of: {', '.join(SCALE_FACTORS)}."
        )
    return name


def to_base_units(amount: float, scale: str) -> float:
    """Convert ``amount`` expressed in ``scale`` into currency units.

    The DCF does not call this. A crore of profit stays a crore inside the solve.
    """

    name = normalise_scale(scale)
    return amount * SCALE_FACTORS[name]
