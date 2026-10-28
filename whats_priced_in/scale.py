"""Scale names. The engine does not multiply by these factors."""

SCALE_FACTORS = {
    "unit": 1,
    "thousand": 1_000,
    "lakh": 100_000,
    "million": 1_000_000,
    "crore": 10_000_000,
    "billion": 1_000_000_000,
}

SCALE_DETAIL = {
    "unit": "one currency unit; use this for per-share figures",
    "thousand": "thousands of currency units",
    "lakh": "lakhs (100,000)",
    "million": "millions of currency units",
    "crore": "crores (10,000,000); standard for Indian market cap and profit",
    "billion": "billions of currency units",
}

BASIS_LABELS = {
    "fcfe": "FCFE",
    "pat": "PAT",
    "ffo": "FFO",
    "owner_earnings": "owner earnings",
}
