# Launch receipts

Evidence commit: `76ea0aa359b2dec184bc595eee5fc7c93b7e3242`

That commit on main contains these transcripts. This line was added in the following commit, because a commit cannot contain its own hash. Check out `76ea0aa359b2dec184bc595eee5fc7c93b7e3242` to see the same transcripts without this stamp.

Evidence for the claims in the X launch post. The transcripts are the CLI output of this repo. The tickers are fictional. Not a recommendation.

Commands are written as `python -m whats_priced_in`. `wpi` and `whats-priced-in` call the same `main` (`pyproject.toml`, `[project.scripts]`). If `python` is not on `PATH`, use `python3`. These transcripts were captured with `python3 -m whats_priced_in`.

## Claim map

| Claim | Where it is true |
| --- | --- |
| Reverse-DCF CLI: price in, assumption out (`wpi` / `python -m whats_priced_in`) | Primary solve below. |
| Solves other implied inputs (margin, horizon, REIT/yield) | Margin, horizon, and yield transcripts below. |
| Pre vs post earnings assumption diff (`earnings_assumption_diff`) | Diff transcript below. The module is `whats_priced_in.earnings_assumption_diff`. |
| India (₹ crore) and UAE (AED) examples in-repo | `examples/narmada.yaml`, `examples/creek.yaml`, and the two transcripts below. |
| Live market data is not wired; the user supplies inputs | Fetcher section below. `fetch_nse_quote`, `fetch_edgar_companyfacts`, and `fetch_dfm_quote` raise `LiveDataNotImplemented`. |
| README has real setup steps | [README](../README.md) Install: `python -m pip install -e ".[dev]"`, then `wpi solve -f examples/synth.yaml` or `python -m whats_priced_in`. |
| Every output states its key assumptions alongside the answer | Solve, margin, horizon, yield, value, sensitivity, and diff transcripts below. JSON solve, value, sensitivity, and diff show `key_assumptions` (a diff also shows `key_assumptions_before` and `key_assumptions_after`). The SVG growth card and SVG diff card show the six labels under the figure, and the `card` command prints the same block before `Card written to`. The Library section is `result.key_assumptions` and `print(result)` for each README library call. |
| Six disclosures: basis, payout, terminal, timing, tax, scale | Those six words are the first rows of every `Key assumptions` block, and the keys of the Disclosure essay. |
| MIT license in the repo | [LICENSE](../LICENSE). Copyright (c) 2026 Manoj. `pyproject.toml` has `license = { text = "MIT" }`. |

## Primary solve

```bash
python -m whats_priced_in solve -f examples/synth.yaml
```

```text
what's priced in · SYNTH
Synthetic Holdings
Fictional company used in the documentation. Not a security and not a recommendation.

E_t = E_0*(1+g)^t; CF_t = payout*E_t; V = sum_{t=1..N} CF_t/(1+r)^t + CF_N*(1+g_T)/((r-g_T)*(1+r)^N)

Implied constant growth  7.17%
Target                   $150.00 per share
Model value              $150.00
Explicit-period PV       $66.30
Terminal PV              $83.70
Terminal share           55.80%
Year-10 earnings         $16.00

Key assumptions
basis           FCFE
payout          100.00%
terminal        Gordon 4.00%
timing          end of year
tax             21.00% disclosed, not applied
scale           USD per share
cost of equity  11.00%
explicit years  10
earnings        $8.00
price           $150.00

Recorded, not used in this solve
Revenue          $40.00
Trailing margin  20.00%

Disclosure
  basis     The starting figure is free cash flow to equity, before the payout scalar. Payout then scales it. At 100%, that FCFE is discounted as given. A lower payout haircuts it.
  payout    Payout is 100.00% of each year's earnings, treated as cash flow to equity. This is not a dividend forecast. Nothing is retained inside the model.
  terminal  Terminal value is a Gordon growth perpetuity. The cash flow in year 10 grows once more at 4.00% and is capitalised at cost of equity minus terminal growth (11.00% - 4.00%). There is no fade inside the perpetuity.
  timing    Cash flows are dated at each year-end and discounted for that many full years. The terminal value is dated at the same final year-end.
  tax       Tax is not applied inside the model. The earnings input is taken as already after tax. A tax rate of 21.00% is disclosed and not reapplied. Changing it does not move the value.
  scale     Per-share mode. Price and earnings are per share, in USD. Scale is unit (one currency unit; use this for per-share figures). No share count was applied.
Warnings
  Payout is at or above 95% while growth is above the terminal rate. The model does not use retained earnings to fund that growth. That fits an asset-light business, or earnings that are already net of the reinvestment you believe. If growth needs reinvestment, lower the payout.

Not a recommendation. One model, read backwards.
```

## Margin solve

```bash
python -m whats_priced_in solve --mode margin -f examples/synth.yaml --revenue-growth 0.06
```

```text
what's priced in · SYNTH
Synthetic Holdings
Fictional company used in the documentation. Not a security and not a recommendation.

Constant margin, with revenue growing at 6.00%. Earnings in each year are that year's revenue times the margin.

Constant margin                                                      21.80%
Revenue growth                                                       6.00%
Target                                                               $150.00
Model value                                                          $150.00
Trailing margin                                                      20.00%
Trailing margin is earnings / revenue. It is not the solved margin.

Key assumptions
basis           FCFE
payout          100.00%
terminal        Gordon 4.00%
timing          end of year
tax             21.00% disclosed, not applied
scale           USD per share
cost of equity  11.00%
explicit years  10
earnings        $8.00
price           $150.00
revenue growth  6.00%

Margin path
Year 1   revenue $42.40  margin 21.80%  earnings $9.24
Year 2   revenue $44.94  margin 21.80%  earnings $9.80
Year 3   revenue $47.64  margin 21.80%  earnings $10.39
Year 4   revenue $50.50  margin 21.80%  earnings $11.01
Year 5   revenue $53.53  margin 21.80%  earnings $11.67
Year 6   revenue $56.74  margin 21.80%  earnings $12.37
Year 7   revenue $60.15  margin 21.80%  earnings $13.11
Year 8   revenue $63.75  margin 21.80%  earnings $13.90
Year 9   revenue $67.58  margin 21.80%  earnings $14.73
Year 10  revenue $71.63  margin 21.80%  earnings $15.62

Disclosure
  basis     The starting figure is free cash flow to equity, before the payout scalar. Payout then scales it. At 100%, that FCFE is discounted as given. A lower payout haircuts it.
  payout    Payout is 100.00% of each year's earnings, treated as cash flow to equity. This is not a dividend forecast. Nothing is retained inside the model.
  terminal  Terminal value is a Gordon growth perpetuity. The cash flow in year 10 grows once more at 4.00% and is capitalised at cost of equity minus terminal growth (11.00% - 4.00%). There is no fade inside the perpetuity.
  timing    Cash flows are dated at each year-end and discounted for that many full years. The terminal value is dated at the same final year-end.
  tax       Tax is not applied inside the model. The earnings input is taken as already after tax. A tax rate of 21.00% is disclosed and not reapplied. Changing it does not move the value.
  scale     Per-share mode. Price and earnings are per share, in USD. Scale is unit (one currency unit; use this for per-share figures). No share count was applied.
Warnings
  Payout is at or above 95% while growth is above the terminal rate. The model does not use retained earnings to fund that growth. That fits an asset-light business, or earnings that are already net of the reinvestment you believe. If growth needs reinvestment, lower the payout.

Not a recommendation. The margin is what the price assumes, given the revenue growth you set.
```

## Horizon solve

```bash
python -m whats_priced_in solve --mode years -f examples/synth.yaml --growth 0.12
```

```text
what's priced in · SYNTH
Synthetic Holdings
Fictional company used in the documentation. Not a security and not a recommendation.

No integer horizon hits the target exactly. Closest is 3 years. The model first clears the target at 4 years.

Growth held fixed       12.00%
Closest horizon         3 years
Model value at closest  $146.53
Gap to target           -$3.47
Horizon that clears     4 years
Direction               increasing

Key assumptions
basis              FCFE
payout             100.00%
terminal           Gordon 4.00%
timing             end of year
tax                21.00% disclosed, not applied
scale              USD per share
cost of equity     11.00%
explicit years     searched 1 through 20
earnings           $8.00
price              $150.00
growth held fixed  12.00%

Horizon grid
1 year    $128.00   gap -$22.00
2 years   $137.23   gap -$12.77
3 years   $146.53   gap -$3.47
4 years   $155.93   gap +$5.93
5 years   $165.40   gap +$15.40
6 years   $174.96   gap +$24.96
7 years   $184.61   gap +$34.61
8 years   $194.35   gap +$44.35
9 years   $204.17   gap +$54.17
10 years  $214.08   gap +$64.08
11 years  $224.08   gap +$74.08
12 years  $234.17   gap +$84.17
13 years  $244.36   gap +$94.36
14 years  $254.63   gap +$104.63
15 years  $265.00   gap +$115.00
16 years  $275.46   gap +$125.46
17 years  $286.01   gap +$136.01
18 years  $296.66   gap +$146.66
19 years  $307.40   gap +$157.40
20 years  $318.24   gap +$168.24

Disclosure
  basis     The starting figure is free cash flow to equity, before the payout scalar. Payout then scales it. At 100%, that FCFE is discounted as given. A lower payout haircuts it.
  payout    Payout is 100.00% of each year's earnings, treated as cash flow to equity. This is not a dividend forecast. Nothing is retained inside the model.
  terminal  Terminal value is a Gordon growth perpetuity. The cash flow in year 10 grows once more at 4.00% and is capitalised at cost of equity minus terminal growth (11.00% - 4.00%). There is no fade inside the perpetuity.
  timing    Cash flows are dated at each year-end and discounted for that many full years. The terminal value is dated at the same final year-end.
  tax       Tax is not applied inside the model. The earnings input is taken as already after tax. A tax rate of 21.00% is disclosed and not reapplied. Changing it does not move the value.
  scale     Per-share mode. Price and earnings are per share, in USD. Scale is unit (one currency unit; use this for per-share figures). No share count was applied.
Warnings
  Payout is at or above 95% while growth is above the terminal rate. The model does not use retained earnings to fund that growth. That fits an asset-light business, or earnings that are already net of the reinvestment you believe. If growth needs reinvestment, lower the payout.

Not a recommendation. Horizons are integers. The gap is the honesty.
```

## Yield solve

```bash
python -m whats_priced_in solve --mode yield -f examples/dividend.yaml
```

```text
what's priced in · yield · WHARF
Wharf Synthetic REIT
Fictional REIT-style case. Price, promised dividend, and FFO only. Not a security.

Forward yield             6.50%
Coverage                  1.23x
Payout                    81.25%
Implied perpetual growth  3.50%
Flat perpetuity value     $65.00

Key assumptions
basis           FFO
payout          81.25%
terminal        growing perpetuity, no explicit horizon
timing          next dividend (D1)
tax             not applied; this reading has no tax rate
scale           USD per share
cost of equity  10.00%
dividend        $6.50
price           $100.00

Scenarios hold the entered dividend as D1. D1 is $6.50.

growth      model value       vs price      note
0.00%       $65.00            -35.00%       
2.00%       $81.25            -18.75%       
3.00%       $92.86            -7.14%        
3.50%       $100.00           0.00%         implied by the price
4.00%       $108.33           +8.33%        

Disclosure
  basis     The earnings figure is FFO. Coverage divides that figure by the dividend you supplied. Periods are not aligned for you.
  payout    Payout is 81.25%, the dividend divided by the earnings figure. It is a coverage identity, not the payout scalar of the two-stage earnings model.
  terminal  There is no explicit horizon. The terminal assumption is the perpetual growth itself. Next dividend D1 is the distribution you entered, held fixed across scenarios. Value at a growth rate g is D1 / (r - g). Implied growth is r - D1 / price.
  timing    The dividend is treated as next period's distribution (forward yield = dividend / price). Growth applies after that distribution, not before it.
  tax       Tax is not applied. Coverage and yield use the dividend and the earnings figure as supplied. No tax rate is an input of this reading.
  scale     Per-share figures in USD. Scale is unit (one currency unit; use this for per-share figures). The dividend and the price are in that currency. Nothing is converted.
Warnings
  none

Not a recommendation. A yield reading of one perpetuity, not a credit opinion on the dividend.
```

## Earnings assumption diff

```bash
python -m whats_priced_in diff examples/diff/pre.yaml examples/diff/post.yaml
```

```text
what's priced in · earnings assumption diff

SYNTH · Synthetic Holdings

field                 before                after                 change            role
earnings              $8.00                 $8.80                 +$0.80            moves implied growth
revenue               $40.00                $44.00                +$4.00            disclosed only

implied growth        7.17%                 5.88%                 -1.30 pp
value at 7.17%        $150.00               $165.00               +$15.00

Key assumptions
assumption      before                         after
basis           FCFE                           FCFE
payout          100.00%                        100.00%
terminal        Gordon 4.00%                   Gordon 4.00%
timing          end of year                    end of year
tax             21.00% disclosed, not applied  21.00% disclosed, not applied
scale           USD per share                  USD per share
cost of equity  11.00%                         11.00%
explicit years  10                             10
earnings        $8.00                          $8.80
price           $150.00                        $150.00

Value is the model at the pre-earnings implied growth, under each set's own other assumptions. Revenue is not an input to that solve. The model is linear in the earnings base, so the value moves with earnings when the other growth inputs stay put.

Disclosure (same on both sides)
  basis     The starting figure is free cash flow to equity, before the payout scalar. Payout then scales it. At 100%, that FCFE is discounted as given. A lower payout haircuts it.
  payout    Payout is 100.00% of each year's earnings, treated as cash flow to equity. This is not a dividend forecast. Nothing is retained inside the model.
  terminal  Terminal value is a Gordon growth perpetuity. The cash flow in year 10 grows once more at 4.00% and is capitalised at cost of equity minus terminal growth (11.00% - 4.00%). There is no fade inside the perpetuity.
  timing    Cash flows are dated at each year-end and discounted for that many full years. The terminal value is dated at the same final year-end.
  tax       Tax is not applied inside the model. The earnings input is taken as already after tax. A tax rate of 21.00% is disclosed and not reapplied. Changing it does not move the value.
  scale     Per-share mode. Price and earnings are per share, in USD. Scale is unit (one currency unit; use this for per-share figures). No share count was applied.
Warnings
  Payout is at or above 95% while growth is above the terminal rate. The model does not use retained earnings to fund that growth. That fits an asset-light business, or earnings that are already net of the reinvestment you believe. If growth needs reinvestment, lower the payout.

Not a recommendation. A diff of two assumption sets, not a reaction to a headline.
```

## India example

```bash
python -m whats_priced_in solve -f examples/narmada.yaml
```

```text
what's priced in · NARMADA
Narmada Synthetic
Fictional Indian case. Earnings and market cap are ₹ crore. Shares are in crore. Not a security.

E_t = E_0*(1+g)^t; CF_t = payout*E_t; V = sum_{t=1..N} CF_t/(1+r)^t + CF_N*(1+g_T)/((r-g_T)*(1+r)^N)

Implied constant growth  12.92%
Target                   ₹20,000.00 crore
Model value              ₹20,000.00 crore
Explicit-period PV       ₹7,969.53 crore
Terminal PV              ₹12,030.47 crore
Terminal share           60.15%
Year-10 earnings         ₹2,696.87 crore

Key assumptions
basis           PAT
payout          100.00%
terminal        Gordon 6.00%
timing          end of year
tax             25.00% disclosed, not applied
scale           INR crore
cost of equity  13.00%
explicit years  10
earnings        ₹800.00 crore
price           ₹200.00
shares          100.00 crore

Disclosure
  basis     The starting figure is profit after tax. Payout converts PAT into cash flow to equity. At 100%, PAT is treated as distributable cash.
  payout    Payout is 100.00% of each year's earnings, treated as cash flow to equity. This is not a dividend forecast. Nothing is retained inside the model. PAT is treated as fully distributable.
  terminal  Terminal value is a Gordon growth perpetuity. The cash flow in year 10 grows once more at 6.00% and is capitalised at cost of equity minus terminal growth (13.00% - 6.00%). There is no fade inside the perpetuity.
  timing    Cash flows are dated at each year-end and discounted for that many full years. The terminal value is dated at the same final year-end.
  tax       Tax is not applied inside the model. The earnings input is taken as already after tax. A tax rate of 25.00% is disclosed and not reapplied. Changing it does not move the value.
  scale     Aggregate mode. Earnings and the target are both in INR crore (crores (10,000,000); standard for Indian market cap and profit). A share count, if set, is in that same scale: crore shares when the scale is crore, millions of shares when the scale is million. Market cap = price × shares, in that scale. The engine does not multiply by the scale factor.
Warnings
  Payout is at or above 95% while growth is above the terminal rate. The model does not use retained earnings to fund that growth. That fits an asset-light business, or earnings that are already net of the reinvestment you believe. If growth needs reinvestment, lower the payout.

Not a recommendation. One model, read backwards.
```

## UAE example

```bash
python -m whats_priced_in solve -f examples/creek.yaml
```

```text
what's priced in · CREEK
Creek Synthetic
Fictional UAE case. Earnings and market cap are AED million. Not a security.

E_t = E_0*(1+g)^t; CF_t = payout*E_t; V = sum_{t=1..N} CF_t/(1+r)^t + CF_N*(1+g_T)/((r-g_T)*(1+r)^N)

Implied constant growth  5.24%
Target                   AED 2,500.00 million
Model value              AED 2,500.00 million
Explicit-period PV       AED 1,138.28 million
Terminal PV              AED 1,361.72 million
Terminal share           54.47%
Year-10 earnings         AED 300.04 million

Key assumptions
basis           FCFE
payout          80.00%
terminal        Gordon 3.00%
timing          end of year
tax             9.00% disclosed, not applied
scale           AED million
cost of equity  10.00%
explicit years  10
earnings        AED 180.00 million

Disclosure
  basis     The starting figure is free cash flow to equity, before the payout scalar. Payout then scales it. At 100%, that FCFE is discounted as given. A lower payout haircuts it.
  payout    Payout is 80.00% of each year's earnings, treated as cash flow to equity. This is not a dividend forecast. The model retains 20.00% of earnings, and that retention is not what funds the growth. Growth is an assumption on the earnings base.
  terminal  Terminal value is a Gordon growth perpetuity. The cash flow in year 10 grows once more at 3.00% and is capitalised at cost of equity minus terminal growth (10.00% - 3.00%). There is no fade inside the perpetuity.
  timing    Cash flows are dated at each year-end and discounted for that many full years. The terminal value is dated at the same final year-end.
  tax       Tax is not applied inside the model. The earnings input is taken as already after tax. A tax rate of 9.00% is disclosed and not reapplied. Changing it does not move the value.
  scale     Aggregate mode. Earnings and the target are both in AED million (millions of currency units). A share count, if set, is in that same scale: crore shares when the scale is crore, millions of shares when the scale is million. Market cap = price × shares, in that scale. The engine does not multiply by the scale factor.
Warnings
  none

Not a recommendation. One model, read backwards.
```

## Value

```bash
python -m whats_priced_in value --growth 0.06 -f examples/synth.yaml
```

```text
what's priced in · SYNTH
Synthetic Holdings
Fictional company used in the documentation. Not a security and not a recommendation.

Forward value at growth 6.00%.
E_t = E_0*(1+g)^t; CF_t = payout*E_t; V = sum_{t=1..N} CF_t/(1+r)^t + CF_N*(1+g_T)/((r-g_T)*(1+r)^N)

Growth              6.00%
Model value         $137.60
Explicit-period PV  $62.63
Terminal PV         $74.96
Terminal share      54.48%
Year-10 earnings    $14.33
Target              $150.00
Gap to target       -$12.40

Key assumptions
basis           FCFE
payout          100.00%
terminal        Gordon 4.00%
timing          end of year
tax             21.00% disclosed, not applied
scale           USD per share
cost of equity  11.00%
explicit years  10
earnings        $8.00
price           $150.00

Disclosure
  basis     The starting figure is free cash flow to equity, before the payout scalar. Payout then scales it. At 100%, that FCFE is discounted as given. A lower payout haircuts it.
  payout    Payout is 100.00% of each year's earnings, treated as cash flow to equity. This is not a dividend forecast. Nothing is retained inside the model.
  terminal  Terminal value is a Gordon growth perpetuity. The cash flow in year 10 grows once more at 4.00% and is capitalised at cost of equity minus terminal growth (11.00% - 4.00%). There is no fade inside the perpetuity.
  timing    Cash flows are dated at each year-end and discounted for that many full years. The terminal value is dated at the same final year-end.
  tax       Tax is not applied inside the model. The earnings input is taken as already after tax. A tax rate of 21.00% is disclosed and not reapplied. Changing it does not move the value.
  scale     Per-share mode. Price and earnings are per share, in USD. Scale is unit (one currency unit; use this for per-share figures). No share count was applied.
Warnings
  Payout is at or above 95% while growth is above the terminal rate. The model does not use retained earnings to fund that growth. That fits an asset-light business, or earnings that are already net of the reinvestment you believe. If growth needs reinvestment, lower the payout.

Not a recommendation. One model, read forwards at a growth rate you chose.
```

## Sensitivity

```bash
python -m whats_priced_in sens -f examples/synth.yaml --parameter cost_of_equity --values 0.09,0.13
```

```text
what's priced in · SYNTH
Synthetic Holdings
Fictional company used in the documentation. Not a security and not a recommendation.

Key assumptions
basis           FCFE
payout          100.00%
terminal        Gordon 4.00%
timing          end of year
tax             21.00% disclosed, not applied
scale           USD per share
cost of equity  11.00%
explicit years  10
earnings        $8.00
price           $150.00

Implied growth if cost of equity changes. Price and earnings stay put.
Base cost of equity: 11.00%.

value         implied growth
9.00%         2.68%
13.00%        11.01%

Disclosure
  basis     The starting figure is free cash flow to equity, before the payout scalar. Payout then scales it. At 100%, that FCFE is discounted as given. A lower payout haircuts it.
  payout    Payout is 100.00% of each year's earnings, treated as cash flow to equity. This is not a dividend forecast. Nothing is retained inside the model.
  terminal  Terminal value is a Gordon growth perpetuity. The cash flow in year 10 grows once more at 4.00% and is capitalised at cost of equity minus terminal growth (11.00% - 4.00%). There is no fade inside the perpetuity.
  timing    Cash flows are dated at each year-end and discounted for that many full years. The terminal value is dated at the same final year-end.
  tax       Tax is not applied inside the model. The earnings input is taken as already after tax. A tax rate of 21.00% is disclosed and not reapplied. Changing it does not move the value.
  scale     Per-share mode. Price and earnings are per share, in USD. Scale is unit (one currency unit; use this for per-share figures). No share count was applied.
Warnings
  Payout is at or above 95% while growth is above the terminal rate. The model does not use retained earnings to fund that growth. That fits an asset-light business, or earnings that are already net of the reinvestment you believe. If growth needs reinvestment, lower the payout.

Not a recommendation. Each row moves one input.
```

## Sensitivity, default grid

```bash
python -m whats_priced_in sens -f examples/synth.yaml
```

```text
what's priced in · SYNTH
Synthetic Holdings
Fictional company used in the documentation. Not a security and not a recommendation.

Key assumptions
basis           FCFE
payout          100.00%
terminal        Gordon 4.00%
timing          end of year
tax             21.00% disclosed, not applied
scale           USD per share
cost of equity  11.00%
explicit years  10
earnings        $8.00
price           $150.00

Value if growth is this, and every other assumption stays put.

growth        model value             vs target
0.00%         $88.97                  -40.68%
2.00%         $102.77                 -31.49%
4.00%         $118.86                 -20.76%
6.00%         $137.60                 -8.27%
8.00%         $159.39                 +6.26%
10.00%        $184.71                 +23.14%
12.00%        $214.08                 +42.72%
15.00%        $267.05                 +78.03%
20.00%        $385.12                 +156.75%

Implied growth if cost of equity changes. Price and earnings stay put.
Base cost of equity: 11.00%.

value         implied growth
9.00%         2.68%
10.00%        5.04%
11.00%        7.17%
12.00%        9.15%
13.00%        11.01%

Implied growth if terminal growth changes. Price and earnings stay put.
Base terminal growth: 4.00%.

value         implied growth
2.00%         9.18%
3.00%         8.25%
4.00%         7.17%
5.00%         5.92%
6.00%         4.41%

Implied growth if payout changes. Price and earnings stay put.
Base payout: 100.00%.

value         implied growth
60.00%        14.10%
80.00%        10.20%
100.00%       7.17%

Disclosure
  basis     The starting figure is free cash flow to equity, before the payout scalar. Payout then scales it. At 100%, that FCFE is discounted as given. A lower payout haircuts it.
  payout    Payout is 100.00% of each year's earnings, treated as cash flow to equity. This is not a dividend forecast. Nothing is retained inside the model.
  terminal  Terminal value is a Gordon growth perpetuity. The cash flow in year 10 grows once more at 4.00% and is capitalised at cost of equity minus terminal growth (11.00% - 4.00%). There is no fade inside the perpetuity.
  timing    Cash flows are dated at each year-end and discounted for that many full years. The terminal value is dated at the same final year-end.
  tax       Tax is not applied inside the model. The earnings input is taken as already after tax. A tax rate of 21.00% is disclosed and not reapplied. Changing it does not move the value.
  scale     Per-share mode. Price and earnings are per share, in USD. Scale is unit (one currency unit; use this for per-share figures). No share count was applied.
Warnings
  Payout is at or above 95% while growth is above the terminal rate. The model does not use retained earnings to fund that growth. That fits an asset-light business, or earnings that are already net of the reinvestment you believe. If growth needs reinvestment, lower the payout.

Not a recommendation. Each row moves one input.
```

## JSON solve

```bash
python -m whats_priced_in solve -f examples/synth.yaml --json
```

```text
{
  "model": "two_stage_fcfe_gordon",
  "version": "0.1.0",
  "mode": "growth",
  "formula": "E_t = E_0*(1+g)^t; CF_t = payout*E_t; V = sum_{t=1..N} CF_t/(1+r)^t + CF_N*(1+g_T)/((r-g_T)*(1+r)^N)",
  "ticker": "SYNTH",
  "name": "Synthetic Holdings",
  "currency": "USD",
  "scale": "unit",
  "unit_mode": "per_share",
  "per_share": true,
  "implied_growth": 0.07174705988709829,
  "key_assumptions": {
    "basis": "FCFE",
    "payout": "100.00%",
    "terminal": "Gordon 4.00%",
    "timing": "end of year",
    "tax": "21.00% disclosed, not applied",
    "scale": "USD per share",
    "cost of equity": "11.00%",
    "explicit years": "10",
    "earnings": "$8.00",
    "price": "$150.00"
  },
  "target": 150.0,
  "equity_value": 149.99999999999972,
  "residual": -2.8421709430404007e-13,
  "explicit_pv": 66.30133976463077,
  "terminal_pv": 83.69866023536896,
  "terminal_value_at_horizon": 237.65573237816704,
  "terminal_share": 0.5579910682357941,
  "year_n_earnings": 15.996058910068937,
  "earnings_path": [
    8.573976479096785,
    9.189134083013114,
    9.84842743637763,
    10.555023149449157,
    11.312315027462393,
    12.123940371199458,
    12.993797447079512,
    13.92606421067595,
    14.925218373590893,
    15.996058910068937
  ],
  "cashflow_path": [
    8.573976479096785,
    9.189134083013114,
    9.84842743637763,
    10.555023149449157,
    11.312315027462393,
    12.123940371199458,
    12.993797447079512,
    13.92606421067595,
    14.925218373590893,
    15.996058910068937
  ],
  "assumptions": {
    "currency": "USD",
    "scale": "unit",
    "earnings": 8.0,
    "cost_of_equity": 0.11,
    "terminal_growth": 0.04,
    "years": 10,
    "payout": 1.0,
    "earnings_basis": "fcfe",
    "discount_convention": "end_of_year",
    "ticker": "SYNTH",
    "name": "Synthetic Holdings",
    "price": 150.0,
    "shares": null,
    "market_cap": null,
    "revenue": 40.0,
    "revenue_growth": null,
    "tax_rate": 0.21,
    "notes": "Fictional company used in the documentation. Not a security and not a recommendation."
  },
  "disclosure": {
    "items": [
      {
        "key": "basis",
        "title": "Basis",
        "text": "The starting figure is free cash flow to equity, before the payout scalar. Payout then scales it. At 100%, that FCFE is discounted as given. A lower payout haircuts it."
      },
      {
        "key": "payout",
        "title": "Payout",
        "text": "Payout is 100.00% of each year's earnings, treated as cash flow to equity. This is not a dividend forecast. Nothing is retained inside the model."
      },
      {
        "key": "terminal",
        "title": "Terminal",
        "text": "Terminal value is a Gordon growth perpetuity. The cash flow in year 10 grows once more at 4.00% and is capitalised at cost of equity minus terminal growth (11.00% - 4.00%). There is no fade inside the perpetuity."
      },
      {
        "key": "timing",
        "title": "Timing",
        "text": "Cash flows are dated at each year-end and discounted for that many full years. The terminal value is dated at the same final year-end."
      },
      {
        "key": "tax",
        "title": "Tax",
        "text": "Tax is not applied inside the model. The earnings input is taken as already after tax. A tax rate of 21.00% is disclosed and not reapplied. Changing it does not move the value."
      },
      {
        "key": "scale",
        "title": "Scale",
        "text": "Per-share mode. Price and earnings are per share, in USD. Scale is unit (one currency unit; use this for per-share figures). No share count was applied."
      }
    ],
    "warnings": [
      "Payout is at or above 95% while growth is above the terminal rate. The model does not use retained earnings to fund that growth. That fits an asset-light business, or earnings that are already net of the reinvestment you believe. If growth needs reinvestment, lower the payout."
    ]
  },
  "warnings": [
    "Payout is at or above 95% while growth is above the terminal rate. The model does not use retained earnings to fund that growth. That fits an asset-light business, or earnings that are already net of the reinvestment you believe. If growth needs reinvestment, lower the payout."
  ]
}
```

## JSON value

```bash
python -m whats_priced_in value --growth 0.06 -f examples/synth.yaml --json
```

```text
{
  "model": "two_stage_fcfe_gordon",
  "version": "0.1.0",
  "mode": "value",
  "formula": "E_t = E_0*(1+g)^t; CF_t = payout*E_t; V = sum_{t=1..N} CF_t/(1+r)^t + CF_N*(1+g_T)/((r-g_T)*(1+r)^N)",
  "growth": 0.06,
  "equity_value": 137.59603536209121,
  "key_assumptions": {
    "basis": "FCFE",
    "payout": "100.00%",
    "terminal": "Gordon 4.00%",
    "timing": "end of year",
    "tax": "21.00% disclosed, not applied",
    "scale": "USD per share",
    "cost of equity": "11.00%",
    "explicit years": "10",
    "earnings": "$8.00",
    "price": "$150.00"
  },
  "target": 150.0,
  "explicit_pv": 62.631793867890536,
  "terminal_pv": 74.96424149420068,
  "terminal_share": 0.544813964275412,
  "year_n_earnings": 14.326781572342837,
  "assumptions": {
    "currency": "USD",
    "scale": "unit",
    "earnings": 8.0,
    "cost_of_equity": 0.11,
    "terminal_growth": 0.04,
    "years": 10,
    "payout": 1.0,
    "earnings_basis": "fcfe",
    "discount_convention": "end_of_year",
    "ticker": "SYNTH",
    "name": "Synthetic Holdings",
    "price": 150.0,
    "shares": null,
    "market_cap": null,
    "revenue": 40.0,
    "revenue_growth": null,
    "tax_rate": 0.21,
    "notes": "Fictional company used in the documentation. Not a security and not a recommendation."
  },
  "disclosure": {
    "items": [
      {
        "key": "basis",
        "title": "Basis",
        "text": "The starting figure is free cash flow to equity, before the payout scalar. Payout then scales it. At 100%, that FCFE is discounted as given. A lower payout haircuts it."
      },
      {
        "key": "payout",
        "title": "Payout",
        "text": "Payout is 100.00% of each year's earnings, treated as cash flow to equity. This is not a dividend forecast. Nothing is retained inside the model."
      },
      {
        "key": "terminal",
        "title": "Terminal",
        "text": "Terminal value is a Gordon growth perpetuity. The cash flow in year 10 grows once more at 4.00% and is capitalised at cost of equity minus terminal growth (11.00% - 4.00%). There is no fade inside the perpetuity."
      },
      {
        "key": "timing",
        "title": "Timing",
        "text": "Cash flows are dated at each year-end and discounted for that many full years. The terminal value is dated at the same final year-end."
      },
      {
        "key": "tax",
        "title": "Tax",
        "text": "Tax is not applied inside the model. The earnings input is taken as already after tax. A tax rate of 21.00% is disclosed and not reapplied. Changing it does not move the value."
      },
      {
        "key": "scale",
        "title": "Scale",
        "text": "Per-share mode. Price and earnings are per share, in USD. Scale is unit (one currency unit; use this for per-share figures). No share count was applied."
      }
    ],
    "warnings": [
      "Payout is at or above 95% while growth is above the terminal rate. The model does not use retained earnings to fund that growth. That fits an asset-light business, or earnings that are already net of the reinvestment you believe. If growth needs reinvestment, lower the payout."
    ]
  },
  "warnings": [
    "Payout is at or above 95% while growth is above the terminal rate. The model does not use retained earnings to fund that growth. That fits an asset-light business, or earnings that are already net of the reinvestment you believe. If growth needs reinvestment, lower the payout."
  ]
}
```

## JSON sensitivity

```bash
python -m whats_priced_in sens -f examples/synth.yaml --parameter cost_of_equity --values 0.09,0.13 --json
```

```text
{
  "model": "two_stage_fcfe_gordon",
  "version": "0.1.0",
  "mode": "sens",
  "key_assumptions": {
    "basis": "FCFE",
    "payout": "100.00%",
    "terminal": "Gordon 4.00%",
    "timing": "end of year",
    "tax": "21.00% disclosed, not applied",
    "scale": "USD per share",
    "cost of equity": "11.00%",
    "explicit years": "10",
    "earnings": "$8.00",
    "price": "$150.00"
  },
  "tables": [
    {
      "parameter": "cost_of_equity",
      "kind": "implied_growth",
      "base": 0.11,
      "target": 150.0,
      "rows": [
        {
          "value": 0.09,
          "implied_growth": 0.02678363240885029,
          "equity_value": 149.99999999999972,
          "versus_target": -1.887379141862766e-15,
          "note": ""
        },
        {
          "value": 0.13,
          "implied_growth": 0.1100594825279545,
          "equity_value": 150.0000000000002,
          "versus_target": 1.3322676295501878e-15,
          "note": ""
        }
      ]
    }
  ],
  "disclosure": {
    "items": [
      {
        "key": "basis",
        "title": "Basis",
        "text": "The starting figure is free cash flow to equity, before the payout scalar. Payout then scales it. At 100%, that FCFE is discounted as given. A lower payout haircuts it."
      },
      {
        "key": "payout",
        "title": "Payout",
        "text": "Payout is 100.00% of each year's earnings, treated as cash flow to equity. This is not a dividend forecast. Nothing is retained inside the model."
      },
      {
        "key": "terminal",
        "title": "Terminal",
        "text": "Terminal value is a Gordon growth perpetuity. The cash flow in year 10 grows once more at 4.00% and is capitalised at cost of equity minus terminal growth (11.00% - 4.00%). There is no fade inside the perpetuity."
      },
      {
        "key": "timing",
        "title": "Timing",
        "text": "Cash flows are dated at each year-end and discounted for that many full years. The terminal value is dated at the same final year-end."
      },
      {
        "key": "tax",
        "title": "Tax",
        "text": "Tax is not applied inside the model. The earnings input is taken as already after tax. A tax rate of 21.00% is disclosed and not reapplied. Changing it does not move the value."
      },
      {
        "key": "scale",
        "title": "Scale",
        "text": "Per-share mode. Price and earnings are per share, in USD. Scale is unit (one currency unit; use this for per-share figures). No share count was applied."
      }
    ],
    "warnings": [
      "Payout is at or above 95% while growth is above the terminal rate. The model does not use retained earnings to fund that growth. That fits an asset-light business, or earnings that are already net of the reinvestment you believe. If growth needs reinvestment, lower the payout."
    ]
  },
  "warnings": [
    "Payout is at or above 95% while growth is above the terminal rate. The model does not use retained earnings to fund that growth. That fits an asset-light business, or earnings that are already net of the reinvestment you believe. If growth needs reinvestment, lower the payout."
  ]
}
```

## JSON diff

```bash
python -m whats_priced_in diff examples/diff/pre.yaml examples/diff/post.yaml --json
```

```text
{
  "model": "earnings_assumption_diff",
  "version": "0.1.0",
  "changes": [
    {
      "field": "earnings",
      "before": 8.0,
      "after": 8.8,
      "affects_implied_growth": true
    },
    {
      "field": "revenue",
      "before": 40.0,
      "after": 44.0,
      "affects_implied_growth": false
    }
  ],
  "implied_growth_before": 0.07174705988709829,
  "implied_growth_after": 0.05877389163835012,
  "delta_implied_growth": -0.012973168248748168,
  "key_assumptions_before": {
    "basis": "FCFE",
    "payout": "100.00%",
    "terminal": "Gordon 4.00%",
    "timing": "end of year",
    "tax": "21.00% disclosed, not applied",
    "scale": "USD per share",
    "cost of equity": "11.00%",
    "explicit years": "10",
    "earnings": "$8.00",
    "price": "$150.00"
  },
  "key_assumptions_after": {
    "basis": "FCFE",
    "payout": "100.00%",
    "terminal": "Gordon 4.00%",
    "timing": "end of year",
    "tax": "21.00% disclosed, not applied",
    "scale": "USD per share",
    "cost of equity": "11.00%",
    "explicit years": "10",
    "earnings": "$8.80",
    "price": "$150.00"
  },
  "reference_growth": 0.07174705988709829,
  "value_before": 149.99999999999972,
  "value_after": 164.9999999999997,
  "delta_value": 14.999999999999972,
  "values_comparable": true,
  "target_before": 150.0,
  "target_after": 150.0,
  "disclosure_before": {
    "items": [
      {
        "key": "basis",
        "title": "Basis",
        "text": "The starting figure is free cash flow to equity, before the payout scalar. Payout then scales it. At 100%, that FCFE is discounted as given. A lower payout haircuts it."
      },
      {
        "key": "payout",
        "title": "Payout",
        "text": "Payout is 100.00% of each year's earnings, treated as cash flow to equity. This is not a dividend forecast. Nothing is retained inside the model."
      },
      {
        "key": "terminal",
        "title": "Terminal",
        "text": "Terminal value is a Gordon growth perpetuity. The cash flow in year 10 grows once more at 4.00% and is capitalised at cost of equity minus terminal growth (11.00% - 4.00%). There is no fade inside the perpetuity."
      },
      {
        "key": "timing",
        "title": "Timing",
        "text": "Cash flows are dated at each year-end and discounted for that many full years. The terminal value is dated at the same final year-end."
      },
      {
        "key": "tax",
        "title": "Tax",
        "text": "Tax is not applied inside the model. The earnings input is taken as already after tax. A tax rate of 21.00% is disclosed and not reapplied. Changing it does not move the value."
      },
      {
        "key": "scale",
        "title": "Scale",
        "text": "Per-share mode. Price and earnings are per share, in USD. Scale is unit (one currency unit; use this for per-share figures). No share count was applied."
      }
    ],
    "warnings": [
      "Payout is at or above 95% while growth is above the terminal rate. The model does not use retained earnings to fund that growth. That fits an asset-light business, or earnings that are already net of the reinvestment you believe. If growth needs reinvestment, lower the payout."
    ]
  },
  "disclosure_after": {
    "items": [
      {
        "key": "basis",
        "title": "Basis",
        "text": "The starting figure is free cash flow to equity, before the payout scalar. Payout then scales it. At 100%, that FCFE is discounted as given. A lower payout haircuts it."
      },
      {
        "key": "payout",
        "title": "Payout",
        "text": "Payout is 100.00% of each year's earnings, treated as cash flow to equity. This is not a dividend forecast. Nothing is retained inside the model."
      },
      {
        "key": "terminal",
        "title": "Terminal",
        "text": "Terminal value is a Gordon growth perpetuity. The cash flow in year 10 grows once more at 4.00% and is capitalised at cost of equity minus terminal growth (11.00% - 4.00%). There is no fade inside the perpetuity."
      },
      {
        "key": "timing",
        "title": "Timing",
        "text": "Cash flows are dated at each year-end and discounted for that many full years. The terminal value is dated at the same final year-end."
      },
      {
        "key": "tax",
        "title": "Tax",
        "text": "Tax is not applied inside the model. The earnings input is taken as already after tax. A tax rate of 21.00% is disclosed and not reapplied. Changing it does not move the value."
      },
      {
        "key": "scale",
        "title": "Scale",
        "text": "Per-share mode. Price and earnings are per share, in USD. Scale is unit (one currency unit; use this for per-share figures). No share count was applied."
      }
    ],
    "warnings": [
      "Payout is at or above 95% while growth is above the terminal rate. The model does not use retained earnings to fund that growth. That fits an asset-light business, or earnings that are already net of the reinvestment you believe. If growth needs reinvestment, lower the payout."
    ]
  },
  "growth_inputs": [
    "cost_of_equity",
    "discount_convention",
    "earnings",
    "market_cap",
    "payout",
    "price",
    "shares",
    "terminal_growth",
    "years"
  ]
}
```

## SVG growth card

```bash
python -m whats_priced_in card -f examples/synth.yaml -o synth-card.svg
```

```text
what's priced in · SYNTH
Synthetic Holdings
Fictional company used in the documentation. Not a security and not a recommendation.

E_t = E_0*(1+g)^t; CF_t = payout*E_t; V = sum_{t=1..N} CF_t/(1+r)^t + CF_N*(1+g_T)/((r-g_T)*(1+r)^N)

Implied constant growth  7.17%
Target                   $150.00 per share
Model value              $150.00
Explicit-period PV       $66.30
Terminal PV              $83.70
Terminal share           55.80%
Year-10 earnings         $16.00

Key assumptions
basis           FCFE
payout          100.00%
terminal        Gordon 4.00%
timing          end of year
tax             21.00% disclosed, not applied
scale           USD per share
cost of equity  11.00%
explicit years  10
earnings        $8.00
price           $150.00

Recorded, not used in this solve
Revenue          $40.00
Trailing margin  20.00%

Disclosure
  basis     The starting figure is free cash flow to equity, before the payout scalar. Payout then scales it. At 100%, that FCFE is discounted as given. A lower payout haircuts it.
  payout    Payout is 100.00% of each year's earnings, treated as cash flow to equity. This is not a dividend forecast. Nothing is retained inside the model.
  terminal  Terminal value is a Gordon growth perpetuity. The cash flow in year 10 grows once more at 4.00% and is capitalised at cost of equity minus terminal growth (11.00% - 4.00%). There is no fade inside the perpetuity.
  timing    Cash flows are dated at each year-end and discounted for that many full years. The terminal value is dated at the same final year-end.
  tax       Tax is not applied inside the model. The earnings input is taken as already after tax. A tax rate of 21.00% is disclosed and not reapplied. Changing it does not move the value.
  scale     Per-share mode. Price and earnings are per share, in USD. Scale is unit (one currency unit; use this for per-share figures). No share count was applied.
Warnings
  Payout is at or above 95% while growth is above the terminal rate. The model does not use retained earnings to fund that growth. That fits an asset-light business, or earnings that are already net of the reinvestment you believe. If growth needs reinvestment, lower the payout.

Not a recommendation. One model, read backwards.
Card written to synth-card.svg
```

SVG file `synth-card.svg`:

```xml
<svg xmlns="http://www.w3.org/2000/svg" width="960" height="586" viewBox="0 0 960 586" role="img">
  <title>What's priced in — SYNTH 7.17%</title>
  <desc>Reverse two-stage FCFE reading. 7.17% constant growth. Not a recommendation.</desc>
  <rect width="960" height="586" fill="#f3efe6"/>
  <rect width="8" height="586" fill="#9c3418"/>
  <text x="48" y="46" fill="#9c3418" font-family="Helvetica, Arial, sans-serif" font-size="13" letter-spacing="2.4">WHAT'S PRICED IN</text>
  <text x="912" y="46" fill="#5e584e" font-family="Helvetica, Arial, sans-serif" font-size="13" text-anchor="end">USD · per share</text>
  <text x="48" y="108" fill="#1c1915" font-family="Palatino, 'Palatino Linotype', Georgia, serif" font-size="42">SYNTH</text>
  <text x="48" y="138" fill="#5e584e" font-family="Palatino, 'Palatino Linotype', Georgia, serif" font-size="16">Synthetic Holdings</text>
  <text x="48" y="230" fill="#1c1915" font-family="Palatino, 'Palatino Linotype', Georgia, serif" font-size="84">7.17%</text>
  <text x="48" y="262" fill="#5e584e" font-family="Palatino, 'Palatino Linotype', Georgia, serif" font-size="16">constant earnings growth the price assumes</text>
  <g font-family="Helvetica, Arial, sans-serif" font-size="11" fill="#5e584e"><line x1="560" y1="229.9" x2="900" y2="229.9" stroke="#1f6b4a" stroke-dasharray="3 3"/><polyline fill="none" stroke="#1c1915" stroke-width="1.6" points="560.0,261.7 581.2,258.3 602.5,254.5 623.8,250.5 645.0,246.1 666.2,241.4 687.5,236.4 708.8,230.9 730.0,225.0 751.2,218.7 772.5,211.8 793.8,204.4 815.0,196.5 836.2,188.0 857.5,178.8 878.8,168.9 900.0,158.3"/><circle cx="712.5" cy="229.9" r="4.5" fill="#9c3418"/><text x="560" y="286">0%</text><text x="900" y="286" text-anchor="end">16%</text><text x="900" y="142" text-anchor="end">value vs growth</text></g>
  <line x1="48" y1="300" x2="912" y2="300" stroke="#d9d2c5"/>
  <text x="48" y="334" fill="#5e584e" font-family="Helvetica, Arial, sans-serif" font-size="12">PRICE</text>
  <text x="48" y="360" fill="#1c1915" font-family="Palatino, 'Palatino Linotype', Georgia, serif" font-size="20">$150.00</text>
  <text x="300" y="334" fill="#5e584e" font-family="Helvetica, Arial, sans-serif" font-size="12">EARNINGS NOW</text>
  <text x="300" y="360" fill="#1c1915" font-family="Palatino, 'Palatino Linotype', Georgia, serif" font-size="20">$8.00</text>
  <text x="560" y="334" fill="#5e584e" font-family="Helvetica, Arial, sans-serif" font-size="12">YEAR 10</text>
  <text x="560" y="360" fill="#1c1915" font-family="Palatino, 'Palatino Linotype', Georgia, serif" font-size="20">$16.00</text>
  <text x="780" y="334" fill="#5e584e" font-family="Helvetica, Arial, sans-serif" font-size="12">TERMINAL SHARE</text>
  <text x="780" y="360" fill="#1c1915" font-family="Palatino, 'Palatino Linotype', Georgia, serif" font-size="20">55.80%</text>
  <line x1="48" y1="390" x2="912" y2="390" stroke="#d9d2c5"/>
  <text x="48" y="422" fill="#1c1915" font-family="Helvetica, Arial, sans-serif" font-size="14">Explicit $66.30 · terminal $83.70</text>
  <text x="48" y="448" fill="#1c1915" font-family="Helvetica, Arial, sans-serif" font-size="13">Key assumptions</text><text x="48" y="468" fill="#5e584e" font-family="Helvetica, Arial, sans-serif" font-size="13">basis FCFE · payout 100.00% · terminal Gordon 4.00%</text><text x="48" y="488" fill="#5e584e" font-family="Helvetica, Arial, sans-serif" font-size="13">timing end of year · tax 21.00% disclosed, not applied · scale USD per share</text><text x="48" y="508" fill="#5e584e" font-family="Helvetica, Arial, sans-serif" font-size="13">cost of equity 11.00% · explicit years 10 · earnings $8.00</text>
  <text x="48" y="534" fill="#9c3418" font-family="Helvetica, Arial, sans-serif" font-size="13">Flag: growth is not funded by retained cash in this model.</text>
  <text x="48" y="558" fill="#1c1915" font-family="Helvetica, Arial, sans-serif" font-size="13">Not a recommendation. One model, read backwards.</text>
</svg>
```

## SVG diff card

```bash
python -m whats_priced_in diff examples/diff/pre.yaml examples/diff/post.yaml --card diff-card.svg
```

```text
what's priced in · earnings assumption diff

SYNTH · Synthetic Holdings

field                 before                after                 change            role
earnings              $8.00                 $8.80                 +$0.80            moves implied growth
revenue               $40.00                $44.00                +$4.00            disclosed only

implied growth        7.17%                 5.88%                 -1.30 pp
value at 7.17%        $150.00               $165.00               +$15.00

Key assumptions
assumption      before                         after
basis           FCFE                           FCFE
payout          100.00%                        100.00%
terminal        Gordon 4.00%                   Gordon 4.00%
timing          end of year                    end of year
tax             21.00% disclosed, not applied  21.00% disclosed, not applied
scale           USD per share                  USD per share
cost of equity  11.00%                         11.00%
explicit years  10                             10
earnings        $8.00                          $8.80
price           $150.00                        $150.00

Value is the model at the pre-earnings implied growth, under each set's own other assumptions. Revenue is not an input to that solve. The model is linear in the earnings base, so the value moves with earnings when the other growth inputs stay put.

Disclosure (same on both sides)
  basis     The starting figure is free cash flow to equity, before the payout scalar. Payout then scales it. At 100%, that FCFE is discounted as given. A lower payout haircuts it.
  payout    Payout is 100.00% of each year's earnings, treated as cash flow to equity. This is not a dividend forecast. Nothing is retained inside the model.
  terminal  Terminal value is a Gordon growth perpetuity. The cash flow in year 10 grows once more at 4.00% and is capitalised at cost of equity minus terminal growth (11.00% - 4.00%). There is no fade inside the perpetuity.
  timing    Cash flows are dated at each year-end and discounted for that many full years. The terminal value is dated at the same final year-end.
  tax       Tax is not applied inside the model. The earnings input is taken as already after tax. A tax rate of 21.00% is disclosed and not reapplied. Changing it does not move the value.
  scale     Per-share mode. Price and earnings are per share, in USD. Scale is unit (one currency unit; use this for per-share figures). No share count was applied.
Warnings
  Payout is at or above 95% while growth is above the terminal rate. The model does not use retained earnings to fund that growth. That fits an asset-light business, or earnings that are already net of the reinvestment you believe. If growth needs reinvestment, lower the payout.

Not a recommendation. A diff of two assumption sets, not a reaction to a headline.
Card written to diff-card.svg
```

SVG file `diff-card.svg`:

```xml
<svg xmlns="http://www.w3.org/2000/svg" width="960" height="540" viewBox="0 0 960 540" role="img">
  <title>What changed — SYNTH 7.17% to 5.88%</title>
  <desc>Earnings assumption diff. Not a recommendation.</desc>
  <rect width="960" height="540" fill="#f3efe6"/>
  <rect width="8" height="540" fill="#9c3418"/>
  <text x="48" y="46" fill="#9c3418" font-family="Helvetica, Arial, sans-serif" font-size="13" letter-spacing="2.4">WHAT CHANGED</text>
  <text x="48" y="108" fill="#1c1915" font-family="Palatino, 'Palatino Linotype', Georgia, serif" font-size="42">SYNTH</text>
  <text x="48" y="140" fill="#5e584e" font-family="Palatino, 'Palatino Linotype', Georgia, serif" font-size="16">Synthetic Holdings</text>
  <text x="48" y="210" fill="#1c1915" font-family="Palatino, 'Palatino Linotype', Georgia, serif" font-size="28">7.17%  →  5.88%</text>
  <text x="520" y="210" fill="#9c3418" font-family="Palatino, 'Palatino Linotype', Georgia, serif" font-size="28">-1.30 pp</text>
  <text x="48" y="248" fill="#1c1915" font-family="Helvetica, Arial, sans-serif" font-size="13">Key assumptions</text><text x="48" y="268" fill="#5e584e" font-family="Helvetica, Arial, sans-serif" font-size="13">basis FCFE · payout 100.00% · terminal Gordon 4.00%</text><text x="48" y="288" fill="#5e584e" font-family="Helvetica, Arial, sans-serif" font-size="13">timing end of year · tax 21.00% disclosed, not applied · scale USD per share</text><text x="48" y="308" fill="#5e584e" font-family="Helvetica, Arial, sans-serif" font-size="13">cost of equity 11.00% · explicit years 10 · earnings $8.00 → $8.80</text>
  <text x="48" y="344" fill="#1c1915" font-family="Helvetica, Arial, sans-serif" font-size="16">earnings   8  →  8.8   moves the growth</text><text x="48" y="372" fill="#1c1915" font-family="Helvetica, Arial, sans-serif" font-size="16">revenue   40  →  44   disclosed only</text>
  <text x="48" y="408" fill="#5e584e" font-family="Helvetica, Arial, sans-serif" font-size="14">Value at 7.17%: $150.00 → $165.00</text>
  <text x="48" y="452" fill="#1c1915" font-family="Helvetica, Arial, sans-serif" font-size="13">Not a recommendation. Implied growth under each assumption set.</text>
</svg>
```

## Library

The README library snippet, plus `print` of `value_growth`, `solve_margin`, `solve_years`, `implied_dividend`, and `diff_assumptions`.

```python
from whats_priced_in import (
    Assumptions,
    diff_assumptions,
    implied_dividend,
    load_assumptions,
    load_example,
    solve_growth,
    solve_margin,
    solve_years,
    value_growth,
)
from whats_priced_in.dividend import load_dividend_example

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
print("result.implied_growth")
print(result.implied_growth)
print()
print("result.key_assumptions")
for key, value in result.key_assumptions.items():
    print(f"{key}: {value}")
print()
print("print(result)")
print(result)
print()
print("print(value_growth(0.06, load_example('synth')))")
print(value_growth(0.06, load_example("synth")))
print()
print("print(solve_margin(load_example('synth'), revenue_growth=0.06))")
print(solve_margin(load_example("synth"), revenue_growth=0.06))
print()
print("print(solve_years(load_example('synth'), growth=0.12))")
print(solve_years(load_example("synth"), growth=0.12))
print()
print("print(implied_dividend(load_dividend_example()))")
print(implied_dividend(load_dividend_example()))
print()
print("print(diff_assumptions(pre, post))")
print(diff_assumptions(
    load_assumptions("examples/diff/pre.yaml"),
    load_assumptions("examples/diff/post.yaml"),
))
```

```text
result.implied_growth
0.07174705988709829

result.key_assumptions
basis: FCFE
payout: 100.00%
terminal: Gordon 4.00%
timing: end of year
tax: 21.00% disclosed, not applied
scale: USD per share
cost of equity: 11.00%
explicit years: 10
earnings: $8.00
price: $150.00

print(result)
what's priced in · SYNTH

E_t = E_0*(1+g)^t; CF_t = payout*E_t; V = sum_{t=1..N} CF_t/(1+r)^t + CF_N*(1+g_T)/((r-g_T)*(1+r)^N)

Implied constant growth  7.17%
Target                   $150.00 per share
Model value              $150.00
Explicit-period PV       $66.30
Terminal PV              $83.70
Terminal share           55.80%
Year-10 earnings         $16.00

Key assumptions
basis           FCFE
payout          100.00%
terminal        Gordon 4.00%
timing          end of year
tax             21.00% disclosed, not applied
scale           USD per share
cost of equity  11.00%
explicit years  10
earnings        $8.00
price           $150.00

Disclosure
  basis     The starting figure is free cash flow to equity, before the payout scalar. Payout then scales it. At 100%, that FCFE is discounted as given. A lower payout haircuts it.
  payout    Payout is 100.00% of each year's earnings, treated as cash flow to equity. This is not a dividend forecast. Nothing is retained inside the model.
  terminal  Terminal value is a Gordon growth perpetuity. The cash flow in year 10 grows once more at 4.00% and is capitalised at cost of equity minus terminal growth (11.00% - 4.00%). There is no fade inside the perpetuity.
  timing    Cash flows are dated at each year-end and discounted for that many full years. The terminal value is dated at the same final year-end.
  tax       Tax is not applied inside the model. The earnings input is taken as already after tax. A tax rate of 21.00% is disclosed and not reapplied. Changing it does not move the value.
  scale     Per-share mode. Price and earnings are per share, in USD. Scale is unit (one currency unit; use this for per-share figures). No share count was applied.
Warnings
  Payout is at or above 95% while growth is above the terminal rate. The model does not use retained earnings to fund that growth. That fits an asset-light business, or earnings that are already net of the reinvestment you believe. If growth needs reinvestment, lower the payout.

Not a recommendation. One model, read backwards.

print(value_growth(0.06, load_example('synth')))
what's priced in · SYNTH
Synthetic Holdings
Fictional company used in the documentation. Not a security and not a recommendation.

Forward value at growth 6.00%.
E_t = E_0*(1+g)^t; CF_t = payout*E_t; V = sum_{t=1..N} CF_t/(1+r)^t + CF_N*(1+g_T)/((r-g_T)*(1+r)^N)

Growth              6.00%
Model value         $137.60
Explicit-period PV  $62.63
Terminal PV         $74.96
Terminal share      54.48%
Year-10 earnings    $14.33
Target              $150.00
Gap to target       -$12.40

Key assumptions
basis           FCFE
payout          100.00%
terminal        Gordon 4.00%
timing          end of year
tax             21.00% disclosed, not applied
scale           USD per share
cost of equity  11.00%
explicit years  10
earnings        $8.00
price           $150.00

Disclosure
  basis     The starting figure is free cash flow to equity, before the payout scalar. Payout then scales it. At 100%, that FCFE is discounted as given. A lower payout haircuts it.
  payout    Payout is 100.00% of each year's earnings, treated as cash flow to equity. This is not a dividend forecast. Nothing is retained inside the model.
  terminal  Terminal value is a Gordon growth perpetuity. The cash flow in year 10 grows once more at 4.00% and is capitalised at cost of equity minus terminal growth (11.00% - 4.00%). There is no fade inside the perpetuity.
  timing    Cash flows are dated at each year-end and discounted for that many full years. The terminal value is dated at the same final year-end.
  tax       Tax is not applied inside the model. The earnings input is taken as already after tax. A tax rate of 21.00% is disclosed and not reapplied. Changing it does not move the value.
  scale     Per-share mode. Price and earnings are per share, in USD. Scale is unit (one currency unit; use this for per-share figures). No share count was applied.
Warnings
  Payout is at or above 95% while growth is above the terminal rate. The model does not use retained earnings to fund that growth. That fits an asset-light business, or earnings that are already net of the reinvestment you believe. If growth needs reinvestment, lower the payout.

Not a recommendation. One model, read forwards at a growth rate you chose.

print(solve_margin(load_example('synth'), revenue_growth=0.06))
what's priced in · SYNTH
Synthetic Holdings
Fictional company used in the documentation. Not a security and not a recommendation.

Constant margin, with revenue growing at 6.00%. Earnings in each year are that year's revenue times the margin.

Constant margin                                                      21.80%
Revenue growth                                                       6.00%
Target                                                               $150.00
Model value                                                          $150.00
Trailing margin                                                      20.00%
Trailing margin is earnings / revenue. It is not the solved margin.

Key assumptions
basis           FCFE
payout          100.00%
terminal        Gordon 4.00%
timing          end of year
tax             21.00% disclosed, not applied
scale           USD per share
cost of equity  11.00%
explicit years  10
earnings        $8.00
price           $150.00
revenue growth  6.00%

Margin path
Year 1   revenue $42.40  margin 21.80%  earnings $9.24
Year 2   revenue $44.94  margin 21.80%  earnings $9.80
Year 3   revenue $47.64  margin 21.80%  earnings $10.39
Year 4   revenue $50.50  margin 21.80%  earnings $11.01
Year 5   revenue $53.53  margin 21.80%  earnings $11.67
Year 6   revenue $56.74  margin 21.80%  earnings $12.37
Year 7   revenue $60.15  margin 21.80%  earnings $13.11
Year 8   revenue $63.75  margin 21.80%  earnings $13.90
Year 9   revenue $67.58  margin 21.80%  earnings $14.73
Year 10  revenue $71.63  margin 21.80%  earnings $15.62

Disclosure
  basis     The starting figure is free cash flow to equity, before the payout scalar. Payout then scales it. At 100%, that FCFE is discounted as given. A lower payout haircuts it.
  payout    Payout is 100.00% of each year's earnings, treated as cash flow to equity. This is not a dividend forecast. Nothing is retained inside the model.
  terminal  Terminal value is a Gordon growth perpetuity. The cash flow in year 10 grows once more at 4.00% and is capitalised at cost of equity minus terminal growth (11.00% - 4.00%). There is no fade inside the perpetuity.
  timing    Cash flows are dated at each year-end and discounted for that many full years. The terminal value is dated at the same final year-end.
  tax       Tax is not applied inside the model. The earnings input is taken as already after tax. A tax rate of 21.00% is disclosed and not reapplied. Changing it does not move the value.
  scale     Per-share mode. Price and earnings are per share, in USD. Scale is unit (one currency unit; use this for per-share figures). No share count was applied.
Warnings
  Payout is at or above 95% while growth is above the terminal rate. The model does not use retained earnings to fund that growth. That fits an asset-light business, or earnings that are already net of the reinvestment you believe. If growth needs reinvestment, lower the payout.

Not a recommendation. The margin is what the price assumes, given the revenue growth you set.

print(solve_years(load_example('synth'), growth=0.12))
what's priced in · SYNTH
Synthetic Holdings
Fictional company used in the documentation. Not a security and not a recommendation.

No integer horizon hits the target exactly. Closest is 3 years. The model first clears the target at 4 years.

Growth held fixed       12.00%
Closest horizon         3 years
Model value at closest  $146.53
Gap to target           -$3.47
Horizon that clears     4 years
Direction               increasing

Key assumptions
basis              FCFE
payout             100.00%
terminal           Gordon 4.00%
timing             end of year
tax                21.00% disclosed, not applied
scale              USD per share
cost of equity     11.00%
explicit years     searched 1 through 20
earnings           $8.00
price              $150.00
growth held fixed  12.00%

Horizon grid
1 year    $128.00   gap -$22.00
2 years   $137.23   gap -$12.77
3 years   $146.53   gap -$3.47
4 years   $155.93   gap +$5.93
5 years   $165.40   gap +$15.40
6 years   $174.96   gap +$24.96
7 years   $184.61   gap +$34.61
8 years   $194.35   gap +$44.35
9 years   $204.17   gap +$54.17
10 years  $214.08   gap +$64.08
11 years  $224.08   gap +$74.08
12 years  $234.17   gap +$84.17
13 years  $244.36   gap +$94.36
14 years  $254.63   gap +$104.63
15 years  $265.00   gap +$115.00
16 years  $275.46   gap +$125.46
17 years  $286.01   gap +$136.01
18 years  $296.66   gap +$146.66
19 years  $307.40   gap +$157.40
20 years  $318.24   gap +$168.24

Disclosure
  basis     The starting figure is free cash flow to equity, before the payout scalar. Payout then scales it. At 100%, that FCFE is discounted as given. A lower payout haircuts it.
  payout    Payout is 100.00% of each year's earnings, treated as cash flow to equity. This is not a dividend forecast. Nothing is retained inside the model.
  terminal  Terminal value is a Gordon growth perpetuity. The cash flow in year 10 grows once more at 4.00% and is capitalised at cost of equity minus terminal growth (11.00% - 4.00%). There is no fade inside the perpetuity.
  timing    Cash flows are dated at each year-end and discounted for that many full years. The terminal value is dated at the same final year-end.
  tax       Tax is not applied inside the model. The earnings input is taken as already after tax. A tax rate of 21.00% is disclosed and not reapplied. Changing it does not move the value.
  scale     Per-share mode. Price and earnings are per share, in USD. Scale is unit (one currency unit; use this for per-share figures). No share count was applied.
Warnings
  Payout is at or above 95% while growth is above the terminal rate. The model does not use retained earnings to fund that growth. That fits an asset-light business, or earnings that are already net of the reinvestment you believe. If growth needs reinvestment, lower the payout.

Not a recommendation. Horizons are integers. The gap is the honesty.

print(implied_dividend(load_dividend_example()))
what's priced in · yield · WHARF
Wharf Synthetic REIT
Fictional REIT-style case. Price, promised dividend, and FFO only. Not a security.

Forward yield             6.50%
Coverage                  1.23x
Payout                    81.25%
Implied perpetual growth  3.50%
Flat perpetuity value     $65.00

Key assumptions
basis           FFO
payout          81.25%
terminal        growing perpetuity, no explicit horizon
timing          next dividend (D1)
tax             not applied; this reading has no tax rate
scale           USD per share
cost of equity  10.00%
dividend        $6.50
price           $100.00

Scenarios hold the entered dividend as D1. D1 is $6.50.

growth      model value       vs price      note
0.00%       $65.00            -35.00%       
2.00%       $81.25            -18.75%       
3.00%       $92.86            -7.14%        
3.50%       $100.00           0.00%         implied by the price
4.00%       $108.33           +8.33%        

Disclosure
  basis     The earnings figure is FFO. Coverage divides that figure by the dividend you supplied. Periods are not aligned for you.
  payout    Payout is 81.25%, the dividend divided by the earnings figure. It is a coverage identity, not the payout scalar of the two-stage earnings model.
  terminal  There is no explicit horizon. The terminal assumption is the perpetual growth itself. Next dividend D1 is the distribution you entered, held fixed across scenarios. Value at a growth rate g is D1 / (r - g). Implied growth is r - D1 / price.
  timing    The dividend is treated as next period's distribution (forward yield = dividend / price). Growth applies after that distribution, not before it.
  tax       Tax is not applied. Coverage and yield use the dividend and the earnings figure as supplied. No tax rate is an input of this reading.
  scale     Per-share figures in USD. Scale is unit (one currency unit; use this for per-share figures). The dividend and the price are in that currency. Nothing is converted.
Warnings
  none

Not a recommendation. A yield reading of one perpetuity, not a credit opinion on the dividend.

print(diff_assumptions(pre, post))
what's priced in · earnings assumption diff

SYNTH · Synthetic Holdings

field                 before                after                 change            role
earnings              $8.00                 $8.80                 +$0.80            moves implied growth
revenue               $40.00                $44.00                +$4.00            disclosed only

implied growth        7.17%                 5.88%                 -1.30 pp
value at 7.17%        $150.00               $165.00               +$15.00

Key assumptions
assumption      before                         after
basis           FCFE                           FCFE
payout          100.00%                        100.00%
terminal        Gordon 4.00%                   Gordon 4.00%
timing          end of year                    end of year
tax             21.00% disclosed, not applied  21.00% disclosed, not applied
scale           USD per share                  USD per share
cost of equity  11.00%                         11.00%
explicit years  10                             10
earnings        $8.00                          $8.80
price           $150.00                        $150.00

Value is the model at the pre-earnings implied growth, under each set's own other assumptions. Revenue is not an input to that solve. The model is linear in the earnings base, so the value moves with earnings when the other growth inputs stay put.

Disclosure (same on both sides)
  basis     The starting figure is free cash flow to equity, before the payout scalar. Payout then scales it. At 100%, that FCFE is discounted as given. A lower payout haircuts it.
  payout    Payout is 100.00% of each year's earnings, treated as cash flow to equity. This is not a dividend forecast. Nothing is retained inside the model.
  terminal  Terminal value is a Gordon growth perpetuity. The cash flow in year 10 grows once more at 4.00% and is capitalised at cost of equity minus terminal growth (11.00% - 4.00%). There is no fade inside the perpetuity.
  timing    Cash flows are dated at each year-end and discounted for that many full years. The terminal value is dated at the same final year-end.
  tax       Tax is not applied inside the model. The earnings input is taken as already after tax. A tax rate of 21.00% is disclosed and not reapplied. Changing it does not move the value.
  scale     Per-share mode. Price and earnings are per share, in USD. Scale is unit (one currency unit; use this for per-share figures). No share count was applied.
Warnings
  Payout is at or above 95% while growth is above the terminal rate. The model does not use retained earnings to fund that growth. That fits an asset-light business, or earnings that are already net of the reinvestment you believe. If growth needs reinvestment, lower the payout.

Not a recommendation. A diff of two assumption sets, not a reaction to a headline.
```

## Live fetchers

Nothing in `whats_priced_in.fetchers` calls the network. Each stub raises `LiveDataNotImplemented`. The message says this MVP does not call the network. Captured class names, without quoting the stub text:

```text
fetch_nse_quote('NARMADA') -> LiveDataNotImplemented; message mentions network: True
fetch_edgar_companyfacts('0000000000') -> LiveDataNotImplemented; message mentions network: True
fetch_dfm_quote('CREEK') -> LiveDataNotImplemented; message mentions network: True
```

NSE, EDGAR, and DFM are the three stubs. The caller passes price, earnings, currency, and scale.

## License

The MIT license is the file [LICENSE](../LICENSE) at the repository root. Copyright (c) 2026 Manoj.
