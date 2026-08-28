# FIG-P020-01 R107 fresh isolated SA3 visual acceptance

- HANDOFF_ID: `A-R107-P020-SA3-FRESH-ISOLATED-20260826`
- INSTANCE: `/root/p020_r107_fresh_sa3`
- FORK_TURNS: `none`
- SA3_MODEL: `gpt-5.6-sol`
- SA3_REASONING: `xhigh`
- OFFICIAL_CANDIDATE: `R107`
- PHYSICAL_PAGE: `17`
- PRINTED_PAGE: `4`
- REVIEWER: `SA3-R107`

## Independent denominator closure

The current R107 PDF character stream and the independently frozen figure crop were used directly. No old role denominator, object list, page/crop, candidate, decision, or conclusion was read.

- FIGURE_BODY_GLYPH_COUNT: `65`
- CAPTION_GLYPH_COUNT: `43`
- CAPTION_INCLUDED_IN_N: `true`
- TOTAL_VISIBLE_GLYPH_COUNT: `108`
- FOREGROUND_GRAPHIC_COMPONENT_COUNT: `14`
- VISIBLE_DRAWING_PATH_COUNT: `16`
- BACKGROUND_PATH_COMPONENTS_EXCLUDED_FROM_FOREGROUND_N: `2`
- BACKGROUND_EXCLUSION: outer pale rounded backing fill; opaque white annotation backing rectangle
- MATH_RULE_OBJECT_COUNT: `0`
- N: `122`
- EXPECTED_C_N_2: `7381`
- ACTUAL_UNORDERED_PAIRS: `7381`
- UNIQUE_PAIR_IDS: `7381`

The earlier pre-manual provisional denominator `N=79, C=3081` excluded the visible caption and is withdrawn. Before any manual ledger or seal, the caption was closed character by character (`图1.1` = 4 glyphs; caption sentence = 39 glyphs), N was corrected to 122, and all 7,381 unordered pairs were rerun from the corrected object set.

## Machine gates

- SOURCE_FONT_PASS: `true`
- PIXEL_HEIGHT_PASS: `true`
- SAME_CLASS_RATIO_PASS: `true`
- ROLE_RATIO_PASS: `true`
- EMPTY_MASK_COUNT: `0`
- TOFU_OR_WRONG_CODEPOINT_COUNT: `0`
- PDF_CHARACTER_MAPPING_PASS: `true`
- PDF_DRAWING_PATH_COVERAGE_PASS: `true`
- OVERLAP_CANDIDATE_PIXEL_COUNT: `0` for independent objects
- DESIGN_CONNECTION_PAIR_COUNT: `5`
- DESIGN_CONNECTION_INTERSECTION_PIXEL_SUM: `517`
- MASK_CONTAMINATION_PIXEL_COUNT: `0`
- OVERLAP_PIXEL_COUNT: `0`
- PIXEL_ADJUDICATION_STATUS: `CLEAR`
- PIXEL_ARBITER_MODEL: `NOT_USED`
- PIXEL_ARBITER_REASONING: `NOT_USED`
- CLIP_PIXEL_COUNT: `0`
- MIN_TEXT_TEXT_BBOX_CLEARANCE_PX: `24.000000`
- MIN_TEXT_NODE_BORDER_CLEARANCE_PX: `15.000000`
- MIN_TEXT_LINE_ARROW_CLEARANCE_PX: `12.928388`
- MIN_ARROWHEAD_TEXT_CLEARANCE_PX: `13.317821`
- MIN_TEXT_CLEARANCE_PX: `12.928388`

The five nonzero intersections are only each arrow shaft with its own arrowhead: inline mapping arrow, three main-chain arrows, and the reverse-return arrow. Their 1x and 8x evidence shows the intersection confined to the intended continuous shaft-head joint; they are not independent-object overlaps.

## R168 application

R168 was applied exactly as the later adjudication rule:

- micro `[0.92,1.08]` ratios: advisory only;
- font metadata differences: advisory only;
- single-horizontal-stroke CJK pixel height: advisory only;
- 1-2 px raster differences: advisory only.

Accordingly, the intact single-stroke caption glyph `一` (`T091`, U+4E00, 5x38 px) and low-profile punctuation are not hard failures. They are nonempty, codepoint-correct, complete, pure, unclipped, and readable. No missing/tofu/wrong-codepoint or meaning, unreadability, severe visible imbalance, real clipping, illegal overlap, or geometric/semantic error is present.

## Manual evidence review

After final visual machine artifacts were fixed, I actually opened:

- `full_page_200dpi.png`, `figure_crop_300dpi.png`, `standalone_300dpi.png`, `grayscale_300dpi.png`, and `after_text_measurement_overlay_300dpi.png`;
- all 11 final 8x-nearest glyph contact sheets and both final graphic contact sheets;
- all 22 critical/closest relation images at both 1x and 8x-nearest.

Only after those opens, I hand-authored `manual_glyph_review.csv` (108 row-specific glyph reviews), `manual_graphic_review.csv` (14 row-specific path reviews), `manual_critical_relation_review.csv` (22 row-specific relation reviews), and `manual_view_role_review.csv` (view/role/script-specific reviews).

- FONT_VISUAL_HARMONY_PASS: `true`
- VISUAL_HARMONY_PASS: `true`
- MATH_SEMANTICS_PASS: `true`
- TEXT_CONSISTENCY_PASS: `true`
- GRAYSCALE_PASS: `true`
- PAGE_INTEGRATION_PASS: `true`
- READING_PATH_PASS: `true`
- CAPTION_PASS: `true`

The four equal nodes form a clear left-to-right dependency chain; the inline `定义域 -> 值域` arrow is legible; the dashed return path correctly travels from the task node back toward the object node; the note and caption agree with the current source and the neighboring body text. The title/body ratio is visually natural (CJK medians 35 px vs 33 px, ratio 1.0606), the subdued return note remains readable, and grayscale preserves the solid-main-chain versus dashed-return distinction.

## Manual verdict

- SA3_FINAL_VERDICT: `PASS`
- REQUIRED_OUTCOME: `SA3_PASS_READY_FOR_MAIN_A_LOCAL_PASS_ACCEPTANCE`

This SA3 does not write `A_LOCAL_PASS`.
