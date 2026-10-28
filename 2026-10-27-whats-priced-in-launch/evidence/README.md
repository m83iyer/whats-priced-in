# whats-priced-in

Price in, implied bet out.

A market price is a bet someone already made. This library runs that price backwards through a small equity model and reports the growth, margin, horizon, or dividend yield the bet assumes. You bring the cost of equity. The arithmetic is deterministic. The core path does not call a language model, and it will not tell you to buy or sell.

The tickers in this repo are fictional. Not a recommendation.

## Install

Python 3.10 or newer.

```bash
python -m pip install -e ".[dev]"
wpi solve -f examples/synth.yaml
```

`wpi` and `whats-priced-in` are the same command. If the script directory is not on your `PATH`, run `python -m whats_priced_in` instead. If the `python` command itself is missing, use `python3` in those same places.

## Sixty seconds

Synthetic Holdings (SYNTH) is not a company. The price is $150. Trailing free cash flow to equity is $8 a share, on $40 of revenue, which is a 20% margin. You set the cost of equity at 11%, fade growth to 4% after year 10, and treat the earnings as cash to the owner (payout 100%).

```bash
wpi solve -f examples/synth.yaml
```

The price implies **7.17%** constant growth in those earnings for ten years.

At that growth the model splits the $150 into **$66.30** from the explicit years and **$83.70** from the terminal value (**55.80%** of the value). Year-10 earnings are **$16.00**.

Grow the same $8 at 6% (revenue up 6% a year, margin held at 20%) and the model value is **$137.60**, short of the price. To make $150 with 6% revenue growth, the constant margin has to be **21.80%**:

```bash
wpi solve --mode margin -f examples/synth.yaml --revenue-growth 0.06
```

The 100% payout does not fund the growth. The result says so. It fits an asset-light story, or an earnings figure that is already net of the reinvestment you believe. If growth needs retained cash, lower the payout. At a 60% payout the same $150 implies **14.10%** growth.

Currency and scale are inputs. They are printed on every result. Choosing INR does not select a tax rate, a cost of equity, or even the crore scale.

- `examples/narmada.yaml` — fictional, ₹ crore, shares in crore so that price × shares is the market cap. Implied growth **12.92%**.
- `examples/creek.yaml` — fictional, AED million, 80% payout. Implied growth **5.24%**.

Cost of equity is yours. On SYNTH, 9% implies **2.68%** growth and 13% implies **11.01%** growth:

```bash
wpi sens -f examples/synth.yaml --parameter cost_of_equity --values 0.09,0.13
```

## The model

Two-stage cash flow to equity, Gordon terminal.

```
E_t = E_0*(1+g)^t; CF_t = payout*E_t; V = sum_{t=1..N} CF_t/(1+r)^t + CF_N*(1+g_T)/((r-g_T)*(1+r)^N)
```

`E_0` is the earnings figure you pass (FCFE, PAT, FFO, or owner earnings). It is not itself discounted. Year 1 is that figure grown once. `g` is the constant rate solved so that `V` equals the price, in per-share mode, or the market cap, in aggregate mode.

Earnings and the target have to be in one scale. In crore mode a share count is in crore, because market cap = price × shares. The engine does not multiply by 10,000,000. `SCALE_FACTORS` is there if you want base currency units yourself.

Mid-year discounting is optional (`discount_convention: mid_year`). It multiplies the year-end value by `(1+r)^0.5`. The default is year-end. The result says which one ran.

Tax is not in the formula. Pass after-tax earnings. If you set `tax_rate`, it is disclosed and not used again. Changing it does not move the value.

An audit case, separate from SYNTH, is frozen in `tests/fixtures/golden_synth.json`: earnings 10, growth 8%, cost of equity 10%, terminal growth 3%, five years, payout 100%. Equity value **$181.58**. When explicit growth equals terminal growth, every horizon collapses to the Gordon perpetuity `E_0 * (1+g) / (r-g)`. `check.py` fails if that identity or the audit value drifts.

## Assumptions that stay on the page

Every solve, value, sensitivity, diff, and card places a **Key assumptions** block next to the answer. The six lines are basis, payout, terminal, timing, tax, and scale. `--json` repeats that block as `key_assumptions` (a diff uses `key_assumptions_before` and `key_assumptions_after`). `print(result)` prints the same block the CLI prints. The longer Disclosure essay follows the block. Warnings are a separate list. An empty list is printed as `none`, not omitted.

Revenue and the tax rate can sit on an assumption file. In a growth solve they are listed under "Recorded, not used in this solve". They move a margin solve, or the prose, not the implied growth.

Verbatim command output for the launch claims is in [docs/LAUNCH_RECEIPTS.md](docs/LAUNCH_RECEIPTS.md).

## Before and after an earnings print

`examples/diff/pre.yaml` is the SYNTH case. `examples/diff/post.yaml` raises earnings from $8 to $8.80 and revenue from $40 to $44. The price stays $150.

```bash
wpi diff examples/diff/pre.yaml examples/diff/post.yaml
```

Implied growth goes from 7.17% to **5.88%** (**-1.30 pp**). Revenue is in the change table and marked `disclosed only`. Earnings are marked `moves implied growth`. At the old 7.17% growth, the new earnings are worth **$165.00**. The model is linear in the earnings base, so a 10% earnings change is a 10% value change when every other growth input stays put.

An SVG card:

```bash
wpi card -f examples/synth.yaml -o synth-card.svg
wpi diff examples/diff/pre.yaml examples/diff/post.yaml --card diff-card.svg
```

## Dividend yield

Wharf Synthetic REIT is fictional. Price $100, next dividend $6.50, FFO $8, cost of equity 10%.

```bash
wpi solve --mode yield -f examples/dividend.yaml
```

Forward yield **6.50%**, coverage **1.23x**, payout **81.25%**. A flat perpetuity at a 10% cost of equity is worth **$65.00**, so the price is not explained by a dividend that never grows. Under `g = r - D1/P`, the price implies **3.50%** dividend growth. Scenarios hold D1 fixed and vary growth after that distribution.

Trailing dividends use `P = D0*(1+g)/(r-g)`. The result says which identity ran. Coverage divides the earnings you typed by the dividend you typed. It does not align periods for you.

## CLI

```
wpi solve    [--mode growth|margin|years|yield] [-f file | --example name] [--json] [--card out.svg]
wpi value    --growth 0.06 [-f file]
wpi sens     [-f file] [--parameter cost_of_equity] [--values 0.09,0.11,0.13]
wpi diff     before.yaml after.yaml [--price 150] [--card out.svg]
wpi card     -f file -o card.svg
```

Rates are decimals: `0.11`, not `11`. A cost of equity of 11 is rejected.

Without a file, pass `--currency` and `--scale`. Nothing about the market is assumed.

`--json` prints the full payload. `key_assumptions` sits next to the answer, then the disclosure and the warnings.

## Library

```python
from whats_priced_in import Assumptions, solve_growth

result = solve_growth(Assumptions(
    ticker="SYNTH",
    currency="USD",
    scale="unit",
    price=150,
    earnings=8,
    cost_of_equity=0.11,
    terminal_growth=0.04,
    years=10,
    payout=1.0,
    earnings_basis="fcfe",
    tax_rate=0.21,
))
result.implied_growth    # the 7.17% figure, as a decimal
result.key_assumptions  # basis, payout, terminal, timing, tax, scale, beside that figure
result.disclosure        # the same six items, as the longer essay
print(result)            # Key assumptions, then the essay
```

`value_growth` prices a growth rate you choose. `solve_margin` and `solve_years` answer the other two equity questions. `implied_dividend` is the yield reading. `diff_assumptions` is the earnings diff.

## Markets, without a feed

| Habit | currency | scale | share count |
| --- | --- | --- | --- |
| Indian filings, ₹ crore | `INR` | `crore` | crore shares |
| US, per share | `USD` | `unit` | omit shares |
| US, $ million | `USD` | `million` | millions of shares |
| UAE, AED million | `AED` | `million` | millions of shares |

`lakh`, `thousand`, and `billion` are scales too. Any three-letter currency code is accepted. The symbol table knows `$`, `₹`, and `AED`; anything else is printed as the code.

Live quotes are not in this version. `fetch_nse_quote`, `fetch_edgar_companyfacts`, and `fetch_dfm_quote` raise `LiveDataNotImplemented`. They are stubs for NSE, US EDGAR, and Dubai (DFM). A future fetcher should return numbers and leave the cost of equity to the caller. Numbers in, numbers out.

## Check the arithmetic

```bash
python check.py
pytest
```

`check.py` recomputes the documented strings above from the engine and fails if the README has drifted. It also recomputes the audit case from a closed form that is not the library loop. See [CONTRIBUTING.md](CONTRIBUTING.md).

## License

MIT. Manoj ([@miyer83](https://x.com/miyer83)).
