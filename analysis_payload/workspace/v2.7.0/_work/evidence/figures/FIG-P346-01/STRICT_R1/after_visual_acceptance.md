# FIG-P346-01 SA1 strict visual acceptance (R1)

RESULT = FAIL

SOURCE_FONT_PASS = false

PIXEL_HEIGHT_PASS = false

SAME_CLASS_RATIO_PASS = false

ROLE_RATIO_PASS = false

OVERLAP_PIXEL_COUNT = 50

CLIP_PIXEL_COUNT = 0

MIN_TEXT_CLEARANCE_PX = 0.0000

MIN_TEXT_TEXT_BBOX_CLEARANCE_PX = 22.1158

VISUAL_HARMONY_PASS = false

FONT_VISUAL_COORDINATION_PASS = false

MATH_SEMANTICS_PASS = true

TEXT_CONSISTENCY_PASS = false

GRAYSCALE_PASS = true

PAGE_INTEGRATION_PASS = false

READING_ORDER_PASS = true

CAPTION_CONSISTENCY_PASS = true

SA3_ALLOWED = false

## Frozen candidate and views

- Official candidate: `strict_current_r93_fullbook/main_full.pdf`, physical page 375, printed page 362, caption `图 20.1 可复算的相切下界`.
- `full_page_200dpi.png`: whole-page integration view only.
- `figure_crop_300dpi.png`: lossless native 300 dpi crop from the official page.
- `standalone_300dpi.png`: lossless native 300 dpi content crop from the independently compiled source-only PDF `v260_FIG-P346-01_standalone.pdf`.
- `grayscale_300dpi.png`: native-size grayscale view of the official figure crop.
- No title, panel label, legend, panel border, or second panel exists in this figure; those roles are not applicable, not unknown.

## Hard failures

1. Source font: 46 of 50 token-level elements have a base effective source size below 9.5 pt. The only source-font passes are the four axis-title tokens at 9.5 pt. Exact IDs and source lines are in `after_font_audit.csv`.
2. Pixel height: `T05H1_BOUND_CJK_1` (`：`) is 20 px < 30 px; `T06D_TANGENCY_4` (`；`) is 26 px < 30 px; `T07E_FORMULA_MINUS1` and `T07S_FORMULA_MINUS2` are 4 px < 22 px; `T07L_FORMULA_EQUALS` is 13 px < 22 px.
3. Same-role/class pixel ratio: formula operators `T07E`, `T07L`, `T07S`, and `T07W` have ratios 0.1081, 0.3514, 0.1081, and 0.8378 against the 37 px operator median, outside `[0.92,1.08]`.
4. Role hierarchy against the 24 px tick BASE fails for annotation (32 px, 1.3333 > 1.10), axis title (35 px, 1.4583 > 1.18), and direct label (29 px, 1.2083 > 1.10). Formula block is 27 px, 1.1250 and passes its role band. See `role_ratio_report.csv`.
5. Independent native masks prove `L05_BOUND_LABEL` versus `G07_BOUND_CURVE` has 50 illegal foreground-overlap pixels, 0 px clearance, intersecting vector bboxes, and coincident nearest foreground coordinates `(1648,1018)` on the official page raster. The raw ROI and independent text/curve/overlap masks are under `roi/`.
6. Direct body text `V3-C04.tex:256` says the reader will see five objects including an old point, a new point, and an ascent arrow. The frozen figure has one tangency point, no distinct old/new pair, and no ascent arrow. The caption itself agrees with the plotted lower-bound identity, but the directly following body sentence does not.

## Passing measurements that do not override the failure

- Text-text foreground minimum is 50.4480 px and PDF/vector text-text bbox minimum is 22.1158 px, both above the 4 px gate.
- `L02_X_AXIS_LABEL` versus the formula-note border has 0 overlap and 9.0000 px actual foreground clearance; its font bbox intersects the border bbox, so the PASS is based on independent foreground masks, not bbox alone.
- Formula text to its own node border has 24.0000 px foreground clearance, above the 5 px gate.
- Full-page edge minimum is 502.6244 px and all tracked objects have `CLIP_PIXEL_COUNT=0`; this is a single vector panel, so cross-panel clearance is not applicable.
- Solid/dashed curve coding, tangent point, and tangent line remain distinguishable in grayscale.

## Font visual coordination

The STIX Two mathematical glyphs and Noto Serif CJK glyphs are stylistically compatible, and no ordinary label is abnormally oversized. The hierarchy still fails: the 8.5 pt tick is too small as BASE; the 9.2 pt curve labels, 9.0 pt annotation, and 9.0 pt formula are all below the absolute source floor; their measured ink ratios then make axis/annotation/direct-label roles visually too large relative to that undersized BASE. The dashed lower-bound curve also cuts through its own label, so the label cannot be accepted as visually coordinated even though the surrounding layout has ample space.

## Math and text judgment

The plotted mathematics is internally correct: at `theta=2`, both curves equal 2.675; `ell'(2)=0.9`; `B'(2)=0.9`; and `ell(theta)-B(theta,2)=0.16(theta-2)^2>=0`. The gold line uses the matching tangent slope and point. This mathematical PASS cannot compensate for font, pixel, ratio, overlap, and direct-body consistency failures.

## Required repair direction

1. Raise the tick, direct-label, annotation, and formula base sizes to at least 9.5 pt; do not shrink any of these already undersized roles. If space becomes tight, shorten/re-anchor text or move explanation to prose, then remeasure every token and role band.
2. Move/re-anchor `B(theta,2)：下界` or give it a deliberate opaque halo/background so the dashed curve has zero overlap and at least 3 px foreground clearance without covering a key curve segment.
3. Recompose or move the in-figure identity if its operator glyphs cannot meet the 22 px operator gate while retaining the role band; a merely larger but visually dominant formula is not acceptable.
4. Rewrite the direct body sentence to describe only objects actually drawn, or explicitly add and verify the old point/new point/ascent arrow.
5. After repair: independently compile again, regenerate native 300 dpi views, repeat the complete source/pixel/ratio/overlap audit, and obtain a new SA1 PASS before any SA3 review.
