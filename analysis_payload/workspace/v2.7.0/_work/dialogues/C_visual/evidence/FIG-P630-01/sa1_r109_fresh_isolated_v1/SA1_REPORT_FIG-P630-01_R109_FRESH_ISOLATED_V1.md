# Isolated SA1 review report — FIG-P630-01 against official R109

RESULT: `SA1_PASS_READY_FOR_FRESH_ISOLATED_SA3`

HANDOFF_ID: `C-FIG-P630-01-R109-SA1-FRESH-ISOLATED-V1`  
ACTUAL_INSTANCE: `/root/sa1_fig_p630_r109_fresh_isolated_v1`  
MODEL: `gpt-5.6-sol`  
REASONING_EFFORT: `xhigh`  
FORK_TURNS: `none`  
STARTUP_ABSENT: `true`  
FIGURE_ID / CANONICAL_UID: `FIG-P630-01`  
OFFICIAL_PDF_PHYSICAL_PAGE: `680`  
PRINTED_PAGE: `667`

## Authoritative identities

- Official R109 PDF: 4,967,054 bytes; 817 A4 pages; SHA256 `936162A637DCE09EE02B3F83CB1C21A61A87EFBB9A7C8DDE2FB11A326EB552A9`.
- Current figure source: 2,342 bytes; SHA256 `746163570B90750C1BE9731029C450B2F800D43296075FC22D71B9D9F72F2E43`.
- R109 page location was independently established from the exact caption and node vocabulary, not inherited from a prior conclusion.

## Review result

BLOCKERS: none.  
MATH_SEMANTICS: The chain is correct: joint target/local factors → full conditional given `x_{-j}` → single-coordinate kernel `K_j` updating only `x_j` → systematic/random scan → related samples → MCSE/ESS/trajectory diagnostics. The correctness and mixing side boxes are advisory leaders, not generation-time arrows.  
TEXT_CONSISTENCY: Every node, formula, caption phrase, and the adjacent V5-C04 reading-order paragraph agree. `π_j(·|x_{-j})`, `K_j`, `x_j`, `x_{-j}`, and `≠` are correct and fully rendered.  
READING_ORDER: One serpentine directed route (right, right, down, left, left) is unambiguous. Plain side leaders do not compete with the route.  
SOURCE_FONT_AUDIT: Core/side text is declared at 9.6 pt with graphics scale 1.0; boundary text is 10.0 pt; no resizebox/scalebox/transform shrinkage exists. Legal TeX scripts are source-derived from the 9.6 pt base.  
PIXEL_HEIGHT_AUDIT: Pure Chinese base ink height is 32--34 px; mixed base lines are 34--46 px; boundary/caption are 39--40 px; legal scripts are 28--29 px. No key glyph is below its class threshold.  
SAME_CLASS_RATIO_AUDIT: Core pure-Chinese labels have max/min 34/32=1.0625; side pure-Chinese labels 33/32=1.03125; comparable mixed core lines 46/45=1.0223. All are within 1.08.  
ROLE_RATIO_AUDIT: All ordinary roles share the 9.6 pt source base. The 10 pt bold boundary statement is an explicit semantic emphasis; its 39/32=1.21875 ink ratio remains below the 1.25 emphasis ceiling. Whole-line formula height includes legal subscripts and is not substituted for base-glyph size. No text is actually or obviously imbalanced under R168.  
OVERLAP_CANDIDATE_PIXEL_COUNT: `0`  
MASK_CONTAMINATION_PIXEL_COUNT: `0`  
OVERLAP_PIXEL_COUNT: `0`  
PIXEL_ADJUDICATION_STATUS: `CLEAR`  
CLIP_PIXEL_COUNT: `0`  
MIN_TEXT_CLEARANCE_PX: `4` actual text-text ink; text/line conservative minimum 6 px; text/node-border minimum 8.96 px.  
VISUAL_HARMONY: Main chain has highest weight; side conditions are visually subordinate; boundary statement is proportionate; density is comfortable.  
FONT_AND_DENSITY: Readable at full-page 200 dpi and native 300 dpi; no microtype hard defect.  
LAYOUT: Node geometry is balanced; arrowheads stop at borders; no crossings, illegal overlap, clipping, overflow, or cramped region.  
GRAYSCALE: Structure, arrow directions, side leaders, and emphasis remain distinguishable without color.  
CAPTION: One concise readout conclusion; the method caveat and reading instructions are correctly moved to adjacent prose.  
PAGE_INTEGRATION: The figure sits between the chapter map and the reading-order paragraph; no orphan, collision, abnormal break, or obviously imbalanced whitespace is present.  
REQUIRED_FIXES: none.

## Manual acceptance matrix

- `SA1_MODEL = gpt-5.6-sol`
- `SA1_REASONING = xhigh`
- `SOURCE_FONT_PASS = true`
- `PIXEL_HEIGHT_PASS = true`
- `SAME_CLASS_RATIO_PASS = true`
- `ROLE_RATIO_PASS = true`
- `VISUAL_HARMONY_PASS = true`
- `MATH_SEMANTICS_PASS = true`
- `TEXT_CONSISTENCY_PASS = true`
- `GRAYSCALE_PASS = true`
- `PAGE_INTEGRATION_PASS = true`
- `PIXEL_ARBITER_MODEL = NOT_USED`
- `PIXEL_ARBITER_REASONING = NOT_USED`

SA2/SA3 routing metadata is outside this fresh isolated SA1's authorized read scope and was neither read nor inferred; under the supplied R168 rule that peer/font metadata is advisory, it does not alter the hard visual decision.

## Evidence used

Required views actually opened: `full_page_300dpi.png`, `full_page_200dpi.png`, `figure_crop_native300dpi_1x.png`, `figure_caption_native300dpi_1x.png`, `figure_crop_grayscale_native300dpi_1x.png`, `text_measurement_overlay_native300dpi.png`, `object_overlay_native300dpi.png`, `semantic_overlay_native300dpi.png`, and all four `roi_*_nearest8x.png` files. Machine tables and the two manual adjudication notes provide traceable denominator, pixel, clearance, and pair coverage.

This is only an isolated SA1 result. It does not claim C_LOCAL, global, integrated, or final acceptance.
