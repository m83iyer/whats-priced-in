# Contributing

Thanks for reading the model before changing it.

## Run the checks

```bash
python -m pip install -e ".[dev]"
pytest
python check.py
```

Both have to pass. `check.py` is the drift gate: documented percentages in the README are produced by the formatters, and the audit case in `tests/fixtures/golden_synth.json` is compared with a closed form that does not live in the library loop. If you change the maths, update the golden file only after you can explain the new number, and update the README by re-running the engine. Do not type a remembered percent.

## What belongs in a change

- A new calculation needs an identity or a closed-form test, not only a snapshot of its own output.
- Disclosure keeps the six keys: basis, payout, terminal, timing, tax, scale. Do not drop one because the CLI got long.
- Tax stays out of the arithmetic. A tax rate may be stored and printed. It may not be reapplied.
- Currency and scale stay explicit. Do not infer crore from INR, or dollars from silence.
- Rates are decimals. `0.11` is 11%. Reject values that look like whole-number percents.
- Examples stay fictional. Do not add a real issuer, a live price, or a recommendation.
- The core path stays free of network calls and language-model calls. Fetchers, if you finish one, return numbers and leave the cost of equity to the caller. They must not emit a recommendation.
- Unfinished markers belong in `whats_priced_in/fetchers.py` only.

## Tone

Say what the price assumes. Do not say what someone should buy or sell. "Not a recommendation" stays on the card and in the CLI.

## License

MIT. Contributions are made under the same license.
