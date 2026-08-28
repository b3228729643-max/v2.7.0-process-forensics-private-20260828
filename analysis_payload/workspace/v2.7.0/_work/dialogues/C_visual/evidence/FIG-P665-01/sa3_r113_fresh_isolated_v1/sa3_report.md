# Fresh isolated SA3 report: FIG-P665-01

## Identity and location

- Handoff: `C-FIG-P665-01-R113-SA3-FRESH-ISOLATED-V1`
- Official input PDF identity: 4,967,121 bytes; SHA-256 `6B48D215721463EA2A9B94EFA54200F8D767B609E47714A70D9B441328F2BB9D`.
- Current main figure source identity: 2,800 bytes; SHA-256 `65F9C440D3058569C920F8C2E7E7B50545241EDAA6B6DAD4AA27EEF858324E6B`.
- Independent semantic match: official R113 physical PDF page 713, printed page 700, figure label `图 34.6`.

## Independent findings

The figure correctly decomposes a Dirichlet density into base measure, natural parameter, sufficient statistic, and log-partition function. Differentiating the stated `A(alpha)=log B(alpha)` gives the displayed expected log moment, and the red warning correctly rejects replacing expectation of log by log of expectation. Figure, caption, and necessary current V5-C05 prose agree.

The native full-page, figure/caption, grayscale, overlay, mask, and risk-ROI views show complete glyphs, stable two-panel reading order, intact borders/arrows, and no hard clipping, illegal visible-ink overlap, unreadability, severe imbalance, or semantic/geometric error. The 22-object denominator and all 231 unordered pairs are closed. Separated collision masks overlap on zero pixels. One PDF logical-bbox clearance trigger was manually inspected and has seven blank final-raster pixels; it is an R168 advisory only.

## Required return fields

`RESULT: SA3_PASS_AWAIT_MAIN_C_LOCAL_PASS_ACCEPTANCE`

`FIGURE_ID: FIG-P665-01`

`INDEPENDENT_FINDINGS: mathematics, caption, codepoints, reading order, native/grayscale rendering, denominator, all-pairs geometry, clipping, and page integration are clear under R168`

`SOURCE_FONT_AUDIT: numeric 9.2 pt and 8.5 pt advisories recorded; no final-pixel hard defect`

`PIXEL_HEIGHT_AUDIT: clear; machine measurements and opened nearest8x ROIs retained`

`SAME_CLASS_RATIO_AUDIT: clear`

`ROLE_RATIO_AUDIT: clear`

`OVERLAP_CANDIDATE_PIXEL_COUNT: 0`

`MASK_CONTAMINATION_PIXEL_COUNT: 0`

`OVERLAP_PIXEL_COUNT: 0`

`PIXEL_ADJUDICATION_STATUS: CLEAR`

`CLIP_PIXEL_COUNT: 0`

`MIN_TEXT_CLEARANCE_PX: 7`

`VISUAL_HARMONY: clear in color and grayscale`

`NEW_REGRESSIONS: none found within this isolated review scope`

`BLOCKERS: none`

`REQUIRED_FIXES: none`

`EVIDENCE_USED: files enumerated by the sealed manifest; decisive views listed in manual_object_ledger.md and risk_roi_index_machine.csv`
