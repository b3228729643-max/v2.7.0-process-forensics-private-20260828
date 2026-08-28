# FIG-P092-01 fresh isolated SA3 visual acceptance

## Identity

- HANDOFF_ID: `A-R114-P092-SA3-FRESH-ISOLATED-20260828`
- CANONICAL_INSTANCE: `/root/p092_r114_fresh_sa3`
- FIGURE_UID: `FIG-P092-01`
- MODEL: `gpt-5.6-sol`
- REASONING: `xhigh`
- REVIEW_MODE: `read-only; current official PDF and current source only`
- OFFICIAL_PDF_SHA256: `C3BB9B1C7FC9D7AF9178CD33F227F24899AA505FAB81840DB6E3AD8BD6CE78A6`
- SOURCE_SHA256: `EA3FB7B92ED3B7B2755D513B5F3DEECF7D7114E8DC711F3AB2FE50E9C7EE8608`
- INDEPENDENTLY_LOCATED_PAGE_INDEX0: `95`
- INDEPENDENTLY_LOCATED_PHYSICAL_PAGE: `96`

## Independent coverage

- Reader-visible denominator: `13/13` IDs, frozen in `object_registry_mechanical.csv` and manually reviewed in `manual_element_ledger.csv`.
- Unordered text-pair denominator: `78/78`, mechanically frozen and individually adjudicated in `manual_pair_ledger.csv`.
- Opened views: `11/11`, including full-page 200 dpi, official native full-page 300 dpi, figure crop 300 dpi, grayscale 300 dpi, object overlay 300 dpi, and native1x/nearest8x peak/left/right critical ROIs.
- Math checks: `6/6` manual claims plus independent numeric samples.
- Semantic checks: `8/8` manual checks covering axes, ticks, extrema, endpoints, symmetry, caption, adjacent prose, and reading path.

## R168 hard-fail matrix

- CURRENT_PDF_MISSING: `false`
- TOFU_OR_WRONG_CODEPOINT: `false`
- MATH_MEANING_ERROR: `false`
- ACTUAL_UNREADABILITY: `false`
- OBVIOUS_VISUAL_IMBALANCE: `false`
- TRUE_CLIPPING: `false`
- ILLEGAL_VISIBLE_INK_OVERLAP: `false`
- SEMANTIC_OR_GEOMETRIC_ERROR: `false`

Legacy numeric font, pixel, ratio, taxonomy, microgrid, and clearance thresholds were recorded as diagnostics only. In particular, the conservative color-mask proximity of 1 px near the maximum-label/peak region is not shared ink; native1x and nearest8x inspection shows a readable separation. R168 therefore does not convert that advisory proximity into a hard failure.

## Required result fields

- SA3_MODEL = `gpt-5.6-sol`
- SA3_REASONING = `xhigh`
- SOURCE_FONT_PASS = `true`
- PIXEL_HEIGHT_PASS = `true`
- SAME_CLASS_RATIO_PASS = `true`
- ROLE_RATIO_PASS = `true`
- OVERLAP_CANDIDATE_PIXEL_COUNT = `0`
- MASK_CONTAMINATION_PIXEL_COUNT = `0`
- OVERLAP_PIXEL_COUNT = `0`
- PIXEL_ADJUDICATION_STATUS = `CLEAR`
- PIXEL_ARBITER_MODEL = `NOT_USED`
- PIXEL_ARBITER_REASONING = `NOT_USED`
- PIXEL_DISPUTE_REQUIRED = `false`
- CLIP_PIXEL_COUNT = `0`
- MIN_TEXT_CLEARANCE_PX = `1` (`advisory conservative color-mask proximity; no shared visible ink`)
- VISUAL_HARMONY_PASS = `true`
- MATH_SEMANTICS_PASS = `true`
- TEXT_CONSISTENCY_PASS = `true`
- GRAYSCALE_PASS = `true`
- PAGE_INTEGRATION_PASS = `true`

## Verdict

- RESULT: `PASS`
- BLOCKERS: `none`
- REQUIRED_FIXES: `none`
- OUTCOME: `SA3_PASS_AWAIT_MAIN_A_LOCAL_PASS_ACCEPTANCE`

