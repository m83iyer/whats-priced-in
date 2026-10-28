# Contributing

The arithmetic is the product. `check.py` recomputes the figures in the README from the engine and fails if those strings have drifted. It also recomputes the audit case in `tests/fixtures/golden_synth.json` from a closed form that does not call the library's year loop, and it checks that equal explicit and terminal growth collapses every horizon to the Gordon perpetuity.

```bash
python -m pip install -e ".[dev]"
python check.py
pytest
```

Tickers in `examples/` are fictional. The fetchers in `whats_priced_in.fetchers` raise `LiveDataNotImplemented` and do not call the network. Cost of equity stays an input.

Rates are decimals (`0.11`, not `11`).
