# Strict SA1 R3/R93 report — FIG-P634-01

## Result

RESULT: FAIL

The frozen candidate fails the non-negotiable direct 300 dpi operator/punctuation-height gate and one same-class fullwidth-comma ratio class.  Source effective sizes, semantic consistency, foreground overlap, clipping, role hierarchy, visual harmony, grayscale, and page integration pass.  Under §9.2.1, either remaining hard failure prevents PASS.

## Frozen-input discovery

- Frozen input: `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\build\strict_current_r93_fullbook\main_full.pdf`
- PDF page count: 813
- Independently discovered PDF physical page: 682
- Printed page read from the page header: 669
- Figure number read from final PDF: 图 33.3
- Native final-PDF raster: 2481×3508 at 300 dpi; no post-render resize.
- Assigned source audited: `src/绘图源码/第05册_采样方法主题模型与图排序/V5-C04/fig_v5_c04_coordinate_sweep.tex`.

## Source-size recovery

PASS.  The local figure declares 9.6pt normal reader labels, 10.6pt title, 10.0pt formula card, and 9.8pt note card with graphics scale 1.0000.  The caption is recoverable through its actual source dependency chain: local `fig:32` sets width; `src/讲义源码/common/statlearnbook.sty:305` sets `font={small,stretch=1.12}`; `src/讲义源码/合并总册/main.tex:8` selects 11pt `ctexbook`; therefore caption effective base size is 10.0pt (final PDF extracted about 9.96pt).  All 129 text/substrings have recoverable source effective size and pass `SOURCE_FONT_PASS`.

## Semantic / text consistency check

PASS.  The final PDF, assigned source, and adjacent V5-C04 text agree on all required meanings:

1. sequence `1, 2, …, j−1, j, j+1, …, d` proceeds left to right;
2. the left side of `x^[j]` uses same-round `x_1^(t), …, x_j^(t)` while the right uses previous-round `x_(j+1)^(t−1), …, x_d^(t−1)`;
3. `x^[j]` is explicitly a within-sweep state; only `x^[d]=x^(t)` is called the end-of-sweep sample;
4. title, arrow, hatch/solid/dotted structural encoding, caption, and the adjacent reading-order prose agree.

## Four-view inspection

- Full page 200 dpi: readable and integrated; no abnormal page break or blank region.
- Full page native 300 dpi: figure and caption fully present.
- Standalone native 300 dpi crop: order arrow, eight boxes, two explanatory cards, and all labels visible.
- Grayscale native 300 dpi: hatch/solid/dotted border plus textual status preserves the intended order coding.

## Hard-gate outcomes

SOURCE_FONT_PASS = true
PIXEL_HEIGHT_PASS = false
SAME_CLASS_RATIO_PASS = false
ROLE_RATIO_PASS = true
OVERLAP_PIXEL_COUNT = 0
CLIP_PIXEL_COUNT = 0
MIN_TEXT_CLEARANCE_PX = 14.00
MIN_PAGE_EDGE_CLEARANCE_PX = 317
FONT_VISUAL_HARMONY_PASS = true
VISUAL_HARMONY_PASS = true
MATH_SEMANTICS_PASS = true
TEXT_CONSISTENCY_PASS = true
GRAYSCALE_PASS = true
PAGE_INTEGRATION_PASS = true

## Failure evidence

- `SYM_FIG_TITLE_FULLWIDTH_COLON_01` / `：`: H_ink=29px, threshold=30px (FULLWIDTH); base effective_pt >= 9.5; independent '：' H_ink=29px < 30px
- `SYM_SEQ_ELLIPSIS_1_ELLIPSIS_01` / `⋯`: H_ink=5px, threshold=22px (MATH_OPERATOR); base effective_pt >= 9.5; independent '⋯' H_ink=5px < 22px
- `SYM_SEQ_J_MINUS_1_MINUS_01` / `−`: H_ink=3px, threshold=22px (MATH_OPERATOR); base effective_pt >= 9.5; independent '−' H_ink=3px < 22px
- `SYM_SEQ_ELLIPSIS_2_ELLIPSIS_01` / `⋯`: H_ink=5px, threshold=22px (MATH_OPERATOR); base effective_pt >= 9.5; independent '⋯' H_ink=5px < 22px
- `SYM_NODE_J_MINUS_1_MINUS_01` / `−`: H_ink=3px, threshold=15px (NATURAL_SCRIPT_SYMBOL); natural TeX script/script-script derivative of a >=9.5 pt base formula; independent '−' H_ink=3px < 15px
- `SYM_NODE_J_PLUS_1_MINUS_01` / `−`: H_ink=3px, threshold=15px (NATURAL_SCRIPT_SYMBOL); natural TeX script/script-script derivative of a >=9.5 pt base formula; independent '−' H_ink=3px < 15px
- `SYM_NODE_ELLIPSIS_2_ELLIPSIS_01` / `⋯`: H_ink=5px, threshold=22px (MATH_OPERATOR); base effective_pt >= 9.5; independent '⋯' H_ink=5px < 22px
- `SYM_NODE_D_MINUS_01` / `−`: H_ink=3px, threshold=15px (NATURAL_SCRIPT_SYMBOL); natural TeX script/script-script derivative of a >=9.5 pt base formula; independent '−' H_ink=3px < 15px
- `SYM_NODE_ELLIPSIS_1_ELLIPSIS_01` / `⋯`: H_ink=5px, threshold=22px (MATH_OPERATOR); base effective_pt >= 9.5; independent '⋯' H_ink=5px < 22px
- `SYM_FORMULA_STATE_EQUALS_01` / `=`: H_ink=11px, threshold=22px (MATH_OPERATOR); base effective_pt >= 9.5; independent '=' H_ink=11px < 22px
- `SYM_FORMULA_STATE_COMMA_01` / `,`: H_ink=10px, threshold=22px (MATH_OPERATOR); base effective_pt >= 9.5; independent ',' H_ink=10px < 22px
- `SYM_FORMULA_STATE_ELLIPSIS_01` / `…`: H_ink=5px, threshold=22px (MATH_OPERATOR); base effective_pt >= 9.5; independent '…' H_ink=5px < 22px
- `SYM_FORMULA_STATE_COMMA_02` / `,`: H_ink=10px, threshold=22px (MATH_OPERATOR); base effective_pt >= 9.5; independent ',' H_ink=10px < 22px
- `SYM_FORMULA_STATE_COMMA_03` / `,`: H_ink=10px, threshold=22px (MATH_OPERATOR); base effective_pt >= 9.5; independent ',' H_ink=10px < 22px
- `SYM_FORMULA_STATE_MINUS_01` / `−`: H_ink=3px, threshold=15px (NATURAL_SCRIPT_SYMBOL); natural TeX script/script-script derivative of a >=9.5 pt base formula; independent '−' H_ink=3px < 15px
- `SYM_FORMULA_STATE_COMMA_04` / `,`: H_ink=10px, threshold=22px (MATH_OPERATOR); base effective_pt >= 9.5; independent ',' H_ink=10px < 22px
- `SYM_FORMULA_STATE_ELLIPSIS_02` / `…`: H_ink=5px, threshold=22px (MATH_OPERATOR); base effective_pt >= 9.5; independent '…' H_ink=5px < 22px
- `SYM_FORMULA_STATE_COMMA_05` / `,`: H_ink=10px, threshold=22px (MATH_OPERATOR); base effective_pt >= 9.5; independent ',' H_ink=10px < 22px
- `SYM_FORMULA_STATE_MINUS_02` / `−`: H_ink=3px, threshold=15px (NATURAL_SCRIPT_SYMBOL); natural TeX script/script-script derivative of a >=9.5 pt base formula; independent '−' H_ink=3px < 15px
- `SYM_NOTE_TEXT_FULLWIDTH_EQUALS_01` / `＝`: H_ink=10px, threshold=30px (FULLWIDTH); base effective_pt >= 9.5; independent '＝' H_ink=10px < 30px
- `SYM_NOTE_TEXT_FULLWIDTH_SEMICOLON_01` / `；`: H_ink=26px, threshold=30px (FULLWIDTH); base effective_pt >= 9.5; independent '；' H_ink=26px < 30px
- `SYM_NOTE_TEXT_FULLWIDTH_EQUALS_02` / `＝`: H_ink=10px, threshold=30px (FULLWIDTH); base effective_pt >= 9.5; independent '＝' H_ink=10px < 30px
- `SYM_NOTE_TEXT_FULLWIDTH_SEMICOLON_02` / `；`: H_ink=26px, threshold=30px (FULLWIDTH); base effective_pt >= 9.5; independent '；' H_ink=26px < 30px
- `SYM_NOTE_TEXT_FULLWIDTH_EQUALS_03` / `＝`: H_ink=10px, threshold=30px (FULLWIDTH); base effective_pt >= 9.5; independent '＝' H_ink=10px < 30px
- `SYM_NOTE_TEXT_FULLWIDTH_SEMICOLON_03` / `；`: H_ink=26px, threshold=30px (FULLWIDTH); base effective_pt >= 9.5; independent '；' H_ink=26px < 30px
- `SYM_NOTE_MATH_EQUALS_01` / `=`: H_ink=11px, threshold=22px (MATH_OPERATOR); base effective_pt >= 9.5; independent '=' H_ink=11px < 22px
- `SYM_CAPTION_LABEL_DOT_01` / `.`: H_ink=6px, threshold=22px (MATH_OPERATOR); base effective_pt >= 9.5; independent '.' H_ink=6px < 22px
- `SYM_CAPTION_LINE_1_FULLWIDTH_COLON_01` / `：`: H_ink=25px, threshold=30px (FULLWIDTH); base effective_pt >= 9.5; independent '：' H_ink=25px < 30px
- `SYM_CAPTION_LINE_1_FULLWIDTH_COMMA_01` / `，`: H_ink=14px, threshold=30px (FULLWIDTH); base effective_pt >= 9.5; independent '，' H_ink=14px < 30px
- `SYM_CAPTION_LINE_1_FULLWIDTH_COMMA_02` / `，`: H_ink=11px, threshold=30px (FULLWIDTH); base effective_pt >= 9.5; independent '，' H_ink=11px < 30px
- `SYM_CAPTION_MATH_EQUALS_01` / `=`: H_ink=11px, threshold=22px (MATH_OPERATOR); base effective_pt >= 9.5; independent '=' H_ink=11px < 22px

Caption source-size recovery passes: `statlearnbook.sty:305` supplies `font={small,stretch=1.12}` and the actual merged main uses the 11pt `ctexbook` class, yielding a recoverable 10.0pt caption base (about 9.96pt in the final PDF).  No source-size element is unresolved.

### Literal operator/punctuation H_ink (not parent-formula substituted)

Every visible punctuation/operator has an independent `SYM_*` ID and raw/mask/overlay under `symbols/`; the following is the direct final-PDF 300dpi result (`H_ink/threshold`, each item literal-specific):

- `−`: `SYM_SEQ_J_MINUS_1_MINUS_01`=3/22 FAIL; `SYM_NODE_J_MINUS_1_MINUS_01`=3/15 FAIL; `SYM_NODE_J_PLUS_1_MINUS_01`=3/15 FAIL; `SYM_NODE_D_MINUS_01`=3/15 FAIL; `SYM_FORMULA_STATE_MINUS_01`=3/15 FAIL; `SYM_FORMULA_STATE_MINUS_02`=3/15 FAIL
- `+`: `SYM_SEQ_J_PLUS_1_PLUS_01`=24/22 PASS; `SYM_NODE_J_PLUS_1_PLUS_01`=18/15 PASS; `SYM_FORMULA_STATE_PLUS_01`=24/15 PASS
- `=`: `SYM_FORMULA_STATE_EQUALS_01`=11/22 FAIL; `SYM_NOTE_MATH_EQUALS_01`=11/22 FAIL; `SYM_CAPTION_MATH_EQUALS_01`=11/22 FAIL
- `＝`: `SYM_NOTE_TEXT_FULLWIDTH_EQUALS_01`=10/30 FAIL; `SYM_NOTE_TEXT_FULLWIDTH_EQUALS_02`=10/30 FAIL; `SYM_NOTE_TEXT_FULLWIDTH_EQUALS_03`=10/30 FAIL
- `⋯`: `SYM_SEQ_ELLIPSIS_1_ELLIPSIS_01`=5/22 FAIL; `SYM_SEQ_ELLIPSIS_2_ELLIPSIS_01`=5/22 FAIL; `SYM_NODE_ELLIPSIS_2_ELLIPSIS_01`=5/22 FAIL; `SYM_NODE_ELLIPSIS_1_ELLIPSIS_01`=5/22 FAIL
- `…`: `SYM_FORMULA_STATE_ELLIPSIS_01`=5/22 FAIL; `SYM_FORMULA_STATE_ELLIPSIS_02`=5/22 FAIL
- `,`: `SYM_FORMULA_STATE_COMMA_01`=10/22 FAIL; `SYM_FORMULA_STATE_COMMA_02`=10/22 FAIL; `SYM_FORMULA_STATE_COMMA_03`=10/22 FAIL; `SYM_FORMULA_STATE_COMMA_04`=10/22 FAIL; `SYM_FORMULA_STATE_COMMA_05`=10/22 FAIL
- `，`: `SYM_CAPTION_LINE_1_FULLWIDTH_COMMA_01`=14/30 FAIL; `SYM_CAPTION_LINE_1_FULLWIDTH_COMMA_02`=11/30 FAIL
- `；`: `SYM_NOTE_TEXT_FULLWIDTH_SEMICOLON_01`=26/30 FAIL; `SYM_NOTE_TEXT_FULLWIDTH_SEMICOLON_02`=26/30 FAIL; `SYM_NOTE_TEXT_FULLWIDTH_SEMICOLON_03`=26/30 FAIL
- `：`: `SYM_FIG_TITLE_FULLWIDTH_COLON_01`=29/30 FAIL; `SYM_CAPTION_LINE_1_FULLWIDTH_COLON_01`=25/30 FAIL
- `.`: `SYM_CAPTION_LABEL_DOT_01`=6/22 FAIL

`+` passes in all three measured instances (24/22 base, 18/15 natural script, and 24/15 natural script).  All other listed FAIL entries remain FAIL at their own literal threshold.  Complete per-instance evidence, including brackets/parentheses and all PASS entries, is `operator_height_audit.csv`; no parent formula height is used for any symbol.

### Same-class ratio failure (exact, legal comparison only)

- `OP_FULLWIDTH_COMMA` / `FULLWIDTH` / `CAPTION_PARAGRAPH`: class median 12.50px; max/min=1.2727; `SYM_CAPTION_LINE_1_FULLWIDTH_COMMA_01` H=14px, ratio=1.1200; `SYM_CAPTION_LINE_1_FULLWIDTH_COMMA_02` H=11px, ratio=0.8800.

This is a same literal/fullwidth punctuation role inside the same caption reading flow and same recovered 10.0pt base, so it is a valid comparable class.  It is not a cross-role, cross-size, cross-script, or natural-script-bracket comparison.  Natural scripts were emitted as their own literal components; their separately applicable same-class rows pass.

## Geometry / clipping

- Independent semantic objects: 144 (129 text/substrings, 15 vectors/textures).
- Pair rows: 10296 total: 8633 independent geometry pairs, 136 same-caption-flow rows, 961 same-composite math/node rows, and 566 texture rows.
- All independent masks have overlap 0.  Same-flow/composite rows also have true foreground overlap 0; no natural caption wrap is falsely scored as an independent text-text pair.
- Minimum TEXT–TEXT bbox clearance: 30.00px (required ≥4px).
- Minimum TEXT–LINE/ARROW/NODE_BORDER clearance: 14.00px (required ≥3px or ≥5px for node border), at `STATE_DONE_TEXT` ↔ `VEC_FORMULA_CARD_BORDER` (also `STATE_CURRENT_TEXT` and `STATE_OLD_TEXT`); all are PASS.
- No final foreground reaches a PDF page edge; clip count is 0 and the minimum page-edge bbox clearance is 317px (required ≥6px).
- One panel only, therefore cross-panel threshold is not applicable.

## Visual / typography judgment

`FONT_VISUAL_HARMONY_PASS = true` and `VISUAL_HARMONY_PASS = true`: all four required views show a coherent title-to-node-to-note hierarchy, intact reading order, adequate page integration, and status encoding that remains intelligible in grayscale.  These perceptual passes do not relax the independent literal H_ink and same-class-ratio hard gates.

## Required action / next role

NEXT_ROLE: SA2

SA2 must retain the semantic structure but alter the typography/notation so every independently measurable operator/punctuation glyph (`−`, `+`, `=`, ellipses, commas, fullwidth equals/punctuation, colon, semicolon and dot) passes its own direct 300dpi threshold, and ensure the two same-role caption fullwidth commas are within [0.92,1.08] of their class median.  The caption source-size chain is already recovered and does not require repair.  Produce a fresh final-PDF candidate for a new independent SA1 audit.  Do not close this figure or advance to SA3.
