# FIG-P598-02 fresh isolated SA1 visual acceptance

- HANDOFF_ID: `A-R104-P598-02-SA1-FRESH-20260826`
- instance: `/root/p598_02_r104_fresh_sa1`
- model/effort: `gpt-5.6-sol/xhigh`
- candidate: official frozen R104 `main_full.pdf`, physical page 650
- PDF identity: 4,967,222 bytes; SHA-256 `E5C871642FBDDBEC6508BE1B61BD911FE281CA5ACFBD16B0449B13357770A641`; 817 pages
- native page: 595.276001 x 841.890015 pt; 300 dpi 2481 x 3508 px; 200 dpi 1654 x 2339 px
- figure body crop: page px `[471,272,2056,807]`, native 1585 x 535 px
- standalone crop: page px `[294,272,2234,940]`, native 1940 x 668 px

## Machine closure

- `NATIVE_300DPI_DIRECT_RENDER=true`
- `LOWER_RES_WHOLE_PAGE_CONTEXT_PRESENT=true`
- `GLYPH_COUNT=137`
- `GRAPHIC_COUNT=26`
- `OBJECT_COUNT_N=163`
- `ALL_UNORDERED_PAIR_COUNT_C=13203`
- `EXPECTED_C=13203`
- `CRITICAL_RELATIONSHIP_COUNT=22`
- `HARD_APPLICABLE_PAIR_COUNT=9836`
- `HARD_APPLICABLE_PAIR_FAIL_COUNT=0`
- `EMPTY_MASK_COUNT=0`
- `OVERLAP_PIXEL_COUNT=0`
- `CLIP_PIXEL_COUNT=0`
- `HARD_CLEARANCE_FAIL_COUNT=0`
- `FIGURE_BODY_CROP_CLEARANCE_MIN_PX=11`
- `STANDALONE_CROP_CLEARANCE_MIN_PX=11`
- `MATH_RULE_GRAPHIC_COUNT=2`
- `PDF_DRAWING_PATH_COVERAGE_COUNT=30/30`
- `ORDINARY_PNG_OPEN_COUNT=288`
- `ADS_NON_DEFAULT_STREAM_COUNT=0`
- `PYC_OR_CACHE_FILE_COUNT=0`

The pre-occlusion ownership ledger records 15 intended design-shared relations totaling 261 raster pixels. Paint-order/final-visible ownership is explicit; the quality denominator uses the final reader-visible masks, whose unordered-pair intersection count is zero.

## Manual observation closure

- `GLYPH_CONTACT_SHEETS_OPENED=12/12`
- `GLYPH_MANUAL_ROWS=137/137`
- `GRAPHIC_CONTACT_SHEETS_OPENED=7/7`
- `GRAPHIC_MANUAL_ROWS=26/26`
- `CRITICAL_OVERLAY_SHEETS_OPENED=4/4`
- `CRITICAL_RELATIONSHIP_MANUAL_ROWS=22/22`
- `VIEW_MANUAL_ROWS=15/15`
- `PANEL_ROLE_SCRIPT_MANUAL_ROWS=24/24`
- `R168_FONT_GATE_MANUAL_ROWS=6/6`
- `SEMANTIC_MANUAL_ROWS=13/13`
- `ALL_ORIGINAL_MATCH=true`
- `ALL_OVERLAY_COMPLETE=true`
- `ALL_MASK_ONLY_PURE=true`
- `MISSING_STROKE_OR_GRAPHIC_PIXEL_COUNT=0`
- `FOREIGN_PIXEL_COUNT=0`
- `FONT_VISUAL_HARMONY_PASS=true`
- `GRAYSCALE_PASS=true`
- `PAGE_INTEGRATION_PASS=true`

I opened the native figure, standalone, grayscale, 200 dpi whole-page and 300 dpi whole-page views; all twelve glyph contact sheets; all seven graphic contact sheets; the complete unordered-pair matrix; the text-index overlay; the semantic and page-integration overlays; and all four critical-relationship overlays. Every per-ID manual row was entered only after the corresponding final sheet or overlay had been observed.

## R168 font adjudication

The source-level 8.6/9.2/9.4 pt roles and four fine raster threshold shortfalls are advisory under R168. The four advisory pixel cases are the base equality in `pi K = pi`, the subscript comma in `I-hat_{m,n}`, the base equality in the estimator, and the natural-script equality in the lower summation limit. At native 300 dpi and in 8x nearest-neighbor cells, all are intact and readable.

- `MISSING_OR_TOFU=false`
- `WRONG_GLYPH_CODEPOINT_OR_MATH_SEMANTICS=false`
- `GENUINELY_UNREADABLE=false`
- `OBVIOUS_SEVERE_VISIBLE_IMBALANCE=false`
- `REAL_CLIPPING_OR_OVERLAP=false`
- `R168_HARD_FONT_FAIL_COUNT=0`

## Semantic and geometry adjudication

The figure visibly contains three ordered cards and exactly two inter-card flow arrows. Step 1 states `pi K = pi` and shows x/y with bidirectional kernel arrows. Step 2 shows a continuous chain trace, hatched warm-up region, dashed divider, and separately labeled retained segment. Step 3 shows seven retained-sample dots and the ergodic average `I-hat_{m,n}=1/n sum_{t=m+1}^{m+n} h(X_t)`. The caption states that the workflow estimates `E_pi[h(X)]`. Cards, arrows, curve, pattern, divider, dots, formula rules, crop, clearance, continuity, and full-page integration all pass.

## SA1 conclusion

- `VISUAL_ACCEPTANCE=true`
- `SA1_DECISION=SA1_PASS_AWAIT_FRESH_ISOLATED_SA3`
- No source edit, TeX invocation, commit, state/inventory write, second UID, or business-writer action occurred.

