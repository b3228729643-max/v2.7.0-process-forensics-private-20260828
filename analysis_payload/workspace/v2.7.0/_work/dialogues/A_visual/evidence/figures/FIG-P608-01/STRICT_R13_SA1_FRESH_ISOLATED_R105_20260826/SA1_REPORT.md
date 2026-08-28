# Strict R105 fresh isolated SA1 report — FIG-P608-01

## Assignment and identity

- `HANDOFF_ID=A-R105-P608-SA1-FRESH-ISOLATED-20260826`
- UID: `FIG-P608-01`
- Role: single fresh isolated SA1; no second UID or role was launched.
- Business mode: read-only review. No TeX engine was started and no source/build/main file was edited.
- Official candidate: `main_full.pdf`, physical page 661, 817 A4 pages, 4,967,209 bytes.
- Official PDF SHA256: `F86E89047BA09FEA72FD8F79BF524A04DA367BFF3057806A879106A1032626A1`.
- PDF page geometry: 595.276 × 841.890 pt; native 300 dpi grid 2481 × 3508 px.
- Figure crop: full-page native integer coordinates `[500,930,1460,860]`.
- Current goal service response at audit start: no active goal (`goal=null`).

## Mandatory views

The official PDF supplied every view. No standalone build or historical artifact was used.

- `full_page_200dpi.png`: 1654 × 2339 px.
- `figure_crop_300dpi.png`: 1460 × 860 px; direct cropped render from the official page, no resize.
- `standalone_300dpi.png`: 1520 × 870 px; direct cropped render from the official page, no resize.
- `grayscale_300dpi.png`: 1460 × 860 px; direct grayscale cropped render from the official page, no resize.
- `page_661_300dpi_native.png`: 2481 × 3508 px, the measurement source.

All four required views were manually opened. The standalone crop contains the entire figure and no clipped caption fragment.

## Source typography audit

The source declares a 9.6 pt base and tick/annotation text, 10.8 pt labels and titles, and no graphics scaling. Natural TeX subscripts derive from those compliant base formulas and render at the extracted 7.532 pt script level. No arbitrary whole-formula scriptstyle reduction occurs. All general visible text therefore has source effective size at least 9.5 pt; only natural subscript material is smaller.

Native measurements confirm:

- hard height failures: 0;
- ordinary numeric tick ink heights: 26–27 px;
- 9.6 pt CJK annotation ink heights: 34–35 px;
- 10.8 pt CJK title ink heights: 39–40 px;
- natural-script ink heights: 18–21 px, above the 15 px gate;
- commas, ellipses, and decimal points have nonempty pure masks and same-codepoint peer height/area ratios of exactly 1.000.

The complete source list and manual harmony result are in `after_font_audit.csv`.

## Object denominator and glyph/rule closure

- Visible glyph objects: 68.
- Graphic objects: 15, including axes/ticks/arrows, curves/markers, warm-up boundaries, target line, two hatch fields, and six visible math-rule components.
- Frozen total denominator: `N=83`.
- Nonempty masks: 83; empty masks: 0.
- PDF drawing paths within the figure: 45; mapped paths: 45; unmapped paths: 0.
- Whitespace characters excluded as nonvisible: 6.
- Review objects requiring contact sheets: 74 (68 glyphs + 6 math-rule components).
- Contact sheets opened: 25 of 25.
- Manual review rows: 74 unique rows; missing or duplicate rows: 0; non-PASS rows: 0.

Each item has an ID-safe ordinary filename, 1x mask/context evidence, 8x nearest-neighbour ORIGINAL/TARGET OVERLAY/MASK ONLY evidence, and a manual reviewer row. No colon-bearing ID was used as a filename.

The custom equal signs each comprise two independent rule masks. Their semantic aggregates measure 23 px high and read correctly. The two overline rule masks are nonempty and correctly associated.

## Complete unordered-pair and hard gates

- Frozen unordered-pair denominator: `C(83,2)=3,403`.
- Pair rows present: 3,403; missing/duplicate pairs: 0.
- Hard-relation overlap pixels: 0.
- Hard clearances below threshold: 0.
- Object clip count: 0.
- Minimum text/graphic clearance: 14 px (gate 3 px).
- Minimum independent text/text clearance: 24 px (gate 4 px).
- Minimum cross-panel reader-element clearance: 154 px (gate 8 px).
- Minimum glyph/crop-edge clearance: 23 px (gate 6 px).

The 12 nearest hard-gate relations have separated A/B raw masks, blank intersection panels, native 1x ROIs, and 8x nearest-neighbour counterevidence. Every one was opened manually after generation. Four additional endpoint/crop-edge pairs of views were opened and show intact final markers, paths, labels, axes, and arrowheads.

There are no node boxes, legends, independent annotation arrows, or panel-border constructs in this figure; those taxonomies are inapplicable rather than unknown. Plot-internal curve/reference and curve/hatch geometry is semantically intentional and does not create a text collision.

## Content, grayscale, and page integration

The upper panel accurately shows the fixed t=1..20 trace and a boundary at t=5.5, with warm-up t=1..5 and retained t=6..20. Independent recalculation of all 15 retained running means matches the source values through t=20, whose mean is exactly 2.0000. The lower title/label overlines, the target value 2 line, and the diagnostic-only caveat are semantically correct.

The grayscale view preserves differentiation of hatch, curve, target/reference line, markers, and annotation hierarchy. The full-page view shows a stable reading path and proportionate integration with surrounding text.

## R168 and decision

R168 was applied as directed. No missing/tofu/wrong codepoint, wrong math semantics, unreadability, visibly severe imbalance, genuine clipping, or real illegal overlap exists. Micro-ratios, taxonomy subtleties, and absolute-small but clear natural scripts are advisory only; none changes the hard result.

`SA1_RESULT=PASS`.

This report does not claim `A_LOCAL_PASS`. PASS authorizes only a separate future fresh isolated SA3 review; FAIL/SA2 routing is not invoked.
