# Codex review brief — Pack D: whats-priced-in launch post (copy only) — rev4
Review post-draft.md + thread-alt.md. Verdict APPROVED / NEEDS FIXES with numbered findings.

## Criteria
1. Numbers match the approved fictional calc: $150 / $8 FCFE/share / 11% CoE / 4% terminal g / 10y / 100% payout → 7.17%/yr; $66.30 explicit + $83.70 terminal (55.8%). Labelled fictional.
2. No overclaim on live data: fetchers are stubs; copy says the user supplies inputs.
3. (finding 3, revised) Every product claim must match docs/LAUNCH_RECEIPTS.md (embedded at evidence/LAUNCH_RECEIPTS.md; copy of Origin draft main). Claim → post map:
   - C1 reverse-DCF CLI (`wpi` / `python -m whats_priced_in`), price in → assumption out: primary, t1, qt1
   - C2 other implied inputs (margin / horizon / yield solvers only): reply1, t3
   - C3 pre vs post earnings assumption diff: reply1, t3
   - C4 India ₹ crore + UAE AED examples: reply1, t3
   - C5 live market data not wired; user supplies inputs: reply1, t3
   - C6 setup in README: reply1
   - C7 Key assumptions block beside every answer: qt1, t4 — receipted on ALL README output paths (CLI solve/margin/horizon/yield/value/sensitivity/diff, JSON, SVG growth+diff cards, `card` stdout, library result.key_assumptions/print) in evidence/LAUNCH_RECEIPTS.md at evidence commit 76ea0aa359b2dec184bc595eee5fc7c93b7e3242 (stamp commit 23f5b76b03c1a7b780934422e9c97fecc6d9850c)
   - C8 six disclosures (basis, payout, terminal, timing, tax, scale): t4 — all six labels shown on every path above; pinned evidence SHA 76ea0aa359b2dec184bc595eee5fc7c93b7e3242
   - MIT: NOT claimed in copy; evidence/LICENSE now embedded (MIT, (c) 2026 Manoj) for reference.
4. RELEASE GATE: launch-state wording ("I open-sourced", "I put out") is conditional on a verified public repo; REPO_URL placeholder acceptable.
5. No investment advice / buy-sell-target language; "Not advice"/"not advice" present.
6. Voice first person, no slop. check.py ALL MATCH; raw and X-weighted ≤280 (URL=23).

## Cloud-agent evidence summary (bc-679e690a-6282-5bdb-9ed5-79265a442d05, Origin draft main)
Every listed claim verified true in code; C7 was missing and has been implemented (Key assumptions block on every output). Synthetic figures unchanged (7.17%, $66.30/$83.70, 55.80%). pytest green; repo check.py ALL MATCH. Cite file: docs/LAUNCH_RECEIPTS.md.

Out of scope: repo code review itself.

## Changelog
- 2026-10-27 rev4c: C7/C8 closed — receipts cover all output paths (card stdout fixed in code), evidence SHA pinned 76ea0aa…; 60 pytest pass; numbers unchanged.
- 2026-10-27 rev4: restored product claims per Manoj ("build what you claim"); finding-3 criterion changed from "no product claims" to "claims match receipts"; C7 reworded to "Key assumptions"; t4 adds six disclosure labels.
