# Formal report — FIG-P608-01 R104 fresh isolated SA1

## Disposition

`SA1_PASS_READY_FOR_FRESH_ISOLATED_SA3`

This is an SA1-only result. It does not start SA3 and does not claim `A_LOCAL_PASS`.

## Reviewer identity and isolation

- `HANDOFF_ID=A-R104-P608-SA1-FRESH-ISOLATED-20260826`
- role: one fresh isolated read-only SA1 instance
- official PDF: R104 `main_full.pdf`
- current source: `fig_v5_c03_trace_running_mean.tex`
- evidence root did not exist at startup and was created for this role
- no R8 SA2 adjudication, old P608 evidence/SA/root/handoff, `_work/state`, inventory, `CURRENT_STATE`, `MODEL_ROUTE_LOG`, `TASK_PACKET`, chat-derived conclusion, or Git history was read
- no TeX engine, LaTeX build, source modification, commit, SA3, second UID, or second role was performed

## Independent candidate lock

The target was located from R104 PDF text and current-source labels rather than an inherited page number. The unique page containing the required figure title/labels/caption is physical page `661`, printed page `648`, figure `32.8`. Page size is `595.2760 × 841.8900 pt`; native renders are `1654 × 2339` at 200 dpi and `2481 × 3508` at 300 dpi.

The native integer crops are:

- figure crop: `[250,895,2180,1876]` → `1930 × 981`
- standalone graph: `[437,916,1980,1780]` → `1543 × 864`

## Denominators and machine closure

The standalone graph contains `68` visible glyph objects and `21` semantic graphic/background objects. The `21` graphic objects cover all `58` PDF drawing records exactly once and include `6` independently masked math-rule paths plus the two source-declared hatch backgrounds. Total objects are `89`; all `3916` unordered pairs are present exactly once.

Machine closure reports zero empty masks, zero glyph hard-threshold failures, zero failed pair gates, zero non-whitelisted illegal-overlap pixels, zero clip pixels, `89` unique portable mask filenames/files, and a passing semantic recomputation. The final machine crosscheck also validates every manual-ledger denominator and referenced ROI file.

## Manual review closure

The reviewer actually opened:

- the full page, 300 dpi color figure crop, 300 dpi standalone graph, 300 dpi grayscale crop, and all-glyph overlay;
- five glyph contact sheets covering `68/68` cells with original, unique target overlay, and mask-only evidence;
- the six-cell math-rule contact sheet;
- six full relation-evidence sheets covering all `23` actual-intersection or critical formula-rule relationships and every raw/A/B/intersection/1×/8× file.

The hand-written ledgers contain `68` glyph PASS rows, `6` math-rule PASS rows, `23` relationship PASS rows, `5` view PASS rows, and `23` panel/role/script PASS rows. Every row has a reviewer, sheet/cell or view, explicit booleans, a decision, and an individual note.

## Hard-gate results

- effective source sizes: ordinary `9.6 pt`; axis/panel title `10.8 pt`; only natural TeX scripts below `9.5 pt`
- minimum native glyph heights pass all applicable `30/24/17/22/15 px` gates
- each custom equals-sign composite is `23 px` high; both overlines are nonempty and clean
- same-codepoint punctuation calibration ratios are exactly `1.0` for height and area
- independent text–text minimum clearance: `20 px`
- text/formula–graphic minimum clearance: `13 px`
- cross-panel reader-element minimum clearance: `154 px`
- text-to-image-edge minimum clearance: `20 px`
- non-whitelisted illegal overlap: `0 px`
- clip count: `0 px`
- font visual harmony: PASS
- grayscale: PASS
- page integration: PASS
- glyph/codepoint/readability: PASS
- math and data semantics: PASS

All positive intersections are individually recorded and manually reviewed as intended geometry: axis/tick construction, data/reference-line crossings, the first `t=1` data point at the declared `xmin=1` boundary, or plotted/axis geometry over the two explicitly designated hatch backgrounds. No text or formula participates in an illegal intersection.

## Semantic reconstruction

The 20 trace values, warm-up split `1–5`, retained interval `6–20`, all 15 running-mean points, final mean `2.0000`, target value `2`, labels, overlines, and custom equals relations agree with the current source and page prose. The visible mathematical-colon glyph maps to STIX math `U+2236`, which is the correct rendered semantics of the source math colon.

## R168 advisory items

Two observations remain advisory only and are not hard failures:

1. PDF-extracted font metadata differs from the source declarations by about `0.036–0.040 pt` because of the final graphics transform; no visible imbalance or threshold breach results.
2. Ratios computed across different low-profile punctuation contours or different natural-script glyph shapes are not valid same-contour comparisons. The same-codepoint groups and manual review are exact and passing.

## Final statement

No real hard failure or evidence gap remains in this SA1 package. The correct next state is exactly:

`SA1_PASS_READY_FOR_FRESH_ISOLATED_SA3`

