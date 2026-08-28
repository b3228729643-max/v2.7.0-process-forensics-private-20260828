# FIG-P067-01 — fresh isolated R112 SA3 visual acceptance

`HANDOFF_ID=A-R112-P067-SA3-FRESH-ISOLATED-20260827`

## Identity and evidence

- Official candidate: `strict_current_r112_fullbook/main_full.pdf`
- Independent location: physical page 69 / printed page 56
- PDF page size: `595.276 x 841.890 pt`
- Native full page at 300dpi: `2481 x 3508 px`
- Figure crop: `[100,64,485,220] pt` -> `1605 x 651 px`
- Standalone crop: `[100,64,485,200] pt` -> `1605 x 568 px`
- Frozen visible denominator: `130 = 95 text glyphs + 35 foreground graphic paths`
- Frozen unordered pairs: `8,385 = 130*129/2`
- Actual-open evidence: six final views, eight text contact sheets, nine graphic contact sheets.
- Manual object ledger: `130/130` rows completed after the final evidence was opened.

## R168 hard gates

- Missing glyph/tofu/wrong code: `PASS`
- Actual readability: `PASS`
- Obvious visual imbalance: `PASS`
- Real clipping: `PASS`
- Final-visible illegal overlap: `PASS` (0 illegal pairs after manual final-visible reconciliation)
- Coordinate axes and PMF geometry: `PASS`
- Probability masses and cumulative marker values: `PASS`
- CDF connecting path, right continuity, and PMF/CDF relation: `FAIL`
- Caption truth relative to the actual drawn curve: `FAIL`
- Font and micro-grid observations: advisory only; no hard failure.

## Decision

`SA3_FAIL_RETURN_TO_SA2`

The hard failure is `GFX-007`: the CDF staircase is shifted one support interval to the left, so the path contradicts the correct open/closed endpoint markers and the intended right-continuous cumulative distribution.
