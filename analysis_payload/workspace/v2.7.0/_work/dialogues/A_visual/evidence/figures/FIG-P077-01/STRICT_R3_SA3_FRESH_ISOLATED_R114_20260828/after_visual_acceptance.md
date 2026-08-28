# FIG-P077-01 fresh isolated SA3 visual acceptance

- HANDOFF_ID = `A-R114-P077-SA3-FRESH-ISOLATED-20260828`
- FIGURE_ID = `FIG-P077-01`
- ROLE = `SA3_FRESH_ISOLATED`
- SA3_MODEL = `gpt-5.6-sol`
- SA3_REASONING = `xhigh`
- OFFICIAL_PDF_BYTES = `4967122`
- OFFICIAL_PDF_SHA256 = `C3BB9B1C7FC9D7AF9178CD33F227F24899AA505FAB81840DB6E3AD8BD6CE78A6`
- CURRENT_SOURCE_BYTES = `2603`
- CURRENT_SOURCE_SHA256 = `ED96F120CFF0815122B2914D7D94D12884FAC3DB328D30E883F93457C68484E4`
- INDEPENDENT_CURRENT_PDF_CAPTION_HITS = `1`
- INDEPENDENT_CURRENT_PDF_PHYSICAL_PAGE = `79`
- DENOMINATOR_N = `25`
- ALL_UNORDERED_PAIRS_EXPECTED = `300`
- ALL_UNORDERED_PAIRS_REVIEWED = `300`
- PAIR_DUPLICATES = `0`
- PAIR_MISSING = `0`
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
- CLIP_PIXEL_COUNT = `0`
- MIN_TEXT_CLEARANCE_PX = `7`
- VISUAL_HARMONY_PASS = `true`
- MATH_SEMANTICS_PASS = `true`
- TEXT_CONSISTENCY_PASS = `true`
- GRAYSCALE_PASS = `true`
- PAGE_INTEGRATION_PASS = `true`
- MISSING_TOFU_WRONG_CODEPOINT = `false`
- UNREADABILITY_OR_OBVIOUS_IMBALANCE = `false`
- TRUE_CLIPPING = `false`
- ILLEGAL_VISIBLE_INK_OVERLAP = `false`
- SEMANTIC_OR_GEOMETRIC_ERROR = `false`

## Independent findings

The standard-normal curve is solid, symmetric, centered at zero and peaks at approximately `1/sqrt(2*pi) ~= 0.399`; the `N(0,2^2)` curve is dashed, wider, centered at zero and peaks at approximately `1/(2sqrt(2*pi)) ~= 0.199`. Both plotted expressions are mathematically correct for their stated normal laws. The two area fills terminate on the same zero path, and the brace/caption accurately state that normalization is preserved.

The full-page view is balanced: the figure fits the surrounding proof and following section without crowding or anomalous whitespace. The grayscale view preserves the solid-versus-dashed distinction and peak hierarchy. All 14 text/formula elements are complete and readable at native scale. The only locally smaller item is the mathematically legitimate superscript `2`, which is clearly rendered at native1x and nearest8x.

Under R168, legacy source-size/pixel/ratio thresholds alone are advisory. They were recorded in the ledgers, but no current-PDF hard failure exists: no missing/tofu/wrong codepoint, unreadability/obvious imbalance, true clipping, illegal visible-ink overlap, or mathematical/semantic/geometric error was observed.

## Isolation statement

No SA1/SA2/old P077 page number, denominator, pair, pixel, metric, verdict, acceptance, evidence path, conclusion, report, handoff, or root was read or used. SA1/SA2 model and decision fields are intentionally absent from this SA3-only artifact rather than inferred.

## Result

`RESULT: PASS`

`RETURN_TOKEN: SA3_PASS_AWAIT_MAIN_A_LOCAL_PASS_ACCEPTANCE`
