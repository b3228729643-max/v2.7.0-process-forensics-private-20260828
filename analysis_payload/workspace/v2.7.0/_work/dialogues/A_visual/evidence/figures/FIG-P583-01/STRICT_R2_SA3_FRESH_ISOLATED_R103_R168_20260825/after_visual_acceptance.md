# FIG-P583-01 - Fresh Isolated SA3 Visual Acceptance

## Identity and isolation

- HANDOFF_ID: `A-R103-P583-SA3-FRESH-ISOLATED-20260825`
- Instance: `/root/p583_r103_fresh_sa3`
- Model/effort: `gpt-5.6-sol/xhigh`
- Role: completely fresh isolated SA3 for FIG-P583-01
- Candidate: frozen official R103 full book, physical page 633
- Candidate PDF: `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\build\strict_current_r103_fullbook\main_full.pdf`
- PDF identity: 817 pages; 4,967,184 bytes; SHA-256 `9379A489E0C2A57A7DA670C98029BB27B3F1A385BF8E4C3BD14FE9B606AA0F23`
- Source inspected read-only: `fig_v5_c02_rmse_rate.tex`
- Isolation boundary: no prior P583 evidence, reports, handoffs, role verdicts, acceptance history, state, inventory, task packets, model-route logs, git history, diffs, or P654 evidence were read. No build engine was started or managed. The PDF, source, main tree, and central state remained read-only.

## Render identity and crop geometry

All measurement images are direct page-633 renders of the official PDF. The 300 dpi images were integer-cropped only, with no resize or interpolation.

| Item | Value |
|---|---|
| PDF page size | 595.276 x 841.890 pt |
| Native whole page | 2481 x 3508 px at 300 dpi |
| Whole-page context | 1654 x 2339 px at 200 dpi |
| Figure float rectangle | [60.0, 62.0, 525.0, 255.0] pt |
| Figure crop rectangle | [250, 258, 2188, 1063] px |
| Figure crop size | 1938 x 805 px |
| Plot-only rectangle | [140.0, 65.0, 443.0, 220.0] pt |
| Standalone crop rectangle | [583, 270, 1846, 917] px |
| Standalone size | 1263 x 647 px |

The required page, context, figure, standalone, grayscale, and measurement-overlay views were opened. Every final contact sheet, pair matrix, and critical/relationship overlay was also opened and visually inspected. The human opened-artifact ledger contains 34/34 PASS rows.

## Source typography audit and R168 interpretation

The current source declares a 9.2 pt base figure font, 8.6 pt tick labels, 9.6 pt axis labels, a 9.6 pt rate formula, 9.2 pt triangle annotation text, and 9.2 pt condition text. The formula's exponent is a natural TeX script derived from the 9.6 pt base formula. No `resizebox`, `scalebox`, `scale`, or `transform shape` is present.

For this R168 adjudication, the legacy 9.5 pt floor, `[0.92,1.08]` ratios, fine role/script taxonomy, readable absolute-min metadata, peer/metadata comparisons, and 1-2 px raster differences are advisory only. The font hard gates are missing/tofu, wrong glyph or codepoint/math semantics, genuine unreadability, obvious severe visible imbalance, and real clipping/overlap.

Observed at native page, figure crop, standalone, grayscale, 1x contact-cell, and 8x nearest mask detail:

- no missing or tofu glyph;
- no wrong glyph, codepoint, or mathematical semantics;
- no genuinely unreadable visible glyph;
- no obvious severe visible imbalance;
- no real clipping or illegal overlap.

`FONT_VISUAL_HARMONY_PASS=TRUE`. Tick labels, axis titles, formula, annotations, condition text, and caption form a readable hierarchy without a visually dominant or anomalously small object. The advisory measurements remain preserved in `machine/after_font_audit.csv`, `machine/after_pixel_measurements.csv`, and `machine/role_script_advisory.csv`; they do not override the R168 visual hard-gate result.

## Complete object and pair denominators

The independent reconstruction produced the following closed denominator from the official page:

| Denominator | Count |
|---|---:|
| Visible glyph objects | 119 |
| Visible graphic components | 23 |
| Total visible objects N | 142 |
| All unordered pairs C = N(N-1)/2 | 10,011 |
| Figure PDF drawing paint operations | 10 |
| Assigned path-item ledger rows | 340 |
| Critical or relationship pair rows | 328 |
| Consolidated critical/relationship overlays | 8 |

The drawing/path audit assigns every visible chart foreground drawing component used by the denominator. There is no visible formula accent or math-rule path left unassigned. The 23 graphics include the curve, axes, tick segments, arrowheads, triangle segments, and the final-visible condition border.

Every one of the 119 glyph masks and 23 graphic masks is nonempty. The visible PDF character stream has zero unmapped target glyphs. The ID-to-safe-filename map is unique and uses ordinary files rather than NTFS alternate data streams.

## Human per-ID adjudication

The manual per-ID ledger was written only after actual observation. It contains 142 unique rows, exactly one for each of T0001-T0119 and the 23 graphic IDs. Each row records a reviewer, the opened contact sheet and cell, original-match, overlay-complete, mask-only-pure, missing-stroke count, foreign-pixel count, a decision, and an individualized observation note.

- Human denominator observed: 142/142
- Original match: 142/142 TRUE
- Overlay complete: 142/142 TRUE
- Mask-only pure: 142/142 TRUE
- Missing stroke pixels: 0 total
- Foreign pixels: 0 total
- Manual per-ID decisions: 142 PASS, 0 FAIL, 0 pending

All 15 glyph contact sheets and all 3 graphic contact sheets were opened. The low-profile caption punctuation, natural exponent script, triangle-note glyphs, rotated `RMSE`, curve and axis connections, and rounded final-visible node border were inspected explicitly. No script generated or overwrote reviewer, manual boolean, decision, or note fields.

## Geometry, overlap, clipping, and clearance

All 10,011 unordered object pairs are represented once. Machine direction is `NO_MACHINE_HARD_FAILURE_DETECTED`.

| Hard gate | Result |
|---|---|
| Illegal overlap pixels | 0 - PASS |
| Clip pixels | 0 - PASS |
| Empty glyph masks | 0 - PASS |
| Empty graphic masks | 0 - PASS |
| Independent text-text minimum | 39.8121 px >= 4 px - PASS |
| Text/formula-line minimum | 6 px >= 3 px - PASS |
| Node text-border minimum | 14 px >= 5 px - PASS |
| Reader glyph to crop edge minimum | 11 px >= 6 px - PASS |
| Machine hard pair failures | 0 - PASS |

The eight consolidated critical/relationship overlays were individually opened. The curve-to-y-axis/top-tick endpoint is an intentional geometric connection. The triangle diagonal follows the rate curve; the horizontal leg encodes sample size x4 and the vertical leg encodes error divided by 2. The triangle labels remain clear of the legs, the `O(N^-1/2)` label remains clear of the curve, condition text remains clear of the final-visible rounded border, and the crop retains the complete figure and caption.

## Semantic, caption, grayscale, and page checks

- Axes and ticks: log-log axes; x ticks 1, 4, 16, 64, 256, 1024; y ticks 1/32, 1/16, 1/8, 1/4, 1/2, 1.
- Curve: `x^(-.5)`, connecting RMSE 1 at N=1 to RMSE 1/32 at N=1024.
- Rate formula: `O(N^-1/2)` is correct and readable.
- Triangle: N 16 to 64 is x4; RMSE 1/4 to 1/8 is divided by 2; its diagonal aligns with the rate curve.
- Condition: iid and finite variance.
- Caption/object consistency: the caption states the theoretical root-mean-square-error rate under independent identical sampling with finite variance and correctly warns that correlated or infinite-variance cases cannot directly reuse the line.
- Grayscale: curve, axes, annotation triangle, condition box, labels, and caption remain distinguishable.
- Page integration: the float is balanced with surrounding page content and has no page-level collision, crop, or readability defect.

All semantic, object-content, caption, grayscale, and page-integration hard gates PASS.

## Final SA3 verdict

`PASS`

Route: `SA3_PASS_READY_FOR_MAIN_A_LOCAL_PASS_ACCEPTANCE`

This SA3 package does not write or claim `A_LOCAL_PASS`. The root single writer must independently validate the sealed package and decide any main acceptance state.
