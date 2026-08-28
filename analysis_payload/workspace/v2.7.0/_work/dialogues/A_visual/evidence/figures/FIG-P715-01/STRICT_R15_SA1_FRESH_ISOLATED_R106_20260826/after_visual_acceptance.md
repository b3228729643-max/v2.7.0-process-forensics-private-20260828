# FIG-P715-01 — R106 fresh isolated SA1 visual acceptance

## Identity and scope

- HANDOFF_ID: `A-R106-P715-SA1-FRESH-ISOLATED-20260826`
- Reviewer role: single fresh isolated read-only SA1.
- Decision: **FAIL**. Route to SA2; do not start SA3 and do not claim `A_LOCAL_PASS`.
- Official candidate: `main_full.pdf`, SHA256 `0FA4A5A0B35D2566D71B5472B49E9B4A8A60CBAE76B3FA744B92783AFC6BC31A`, 4,967,249 bytes, 817 pages.
- Independently located page: physical page **765**, printed page **752**, unique caption match count 1; no inherited mapping was used.
- Page size: 595.276001 × 841.890015 pt. Native full-page grids: 2481 × 3508 px at 300 dpi and 1654 × 2339 px at 200 dpi.
- Source: `web_random_walk.tex`, SHA256 recorded in `machine/candidate_identity.json`.
- TeX engines were never started; source and official PDF remained read-only.

## Views opened

The reviewer opened the final full-page 200 dpi view, the figure-plus-caption 300 dpi crop, the guarded standalone 300 dpi view, and the grayscale 300 dpi view. The standalone crop uses full-page integer coordinates `[280,280,2153,1126]`, adding a three-native-pixel guard around the source bounding box; the 1873 × 846 px crop has no antialias-edge clipping. The figure-plus-caption crop is `[258,283,2175,1200]`, 1917 × 917 px.

All four views are readable. There is no tofu, missing glyph, wrong codepoint, semantic substitution, or severe global imbalance. Caption and page placement are coherent. Grayscale preserves the distinction among node borders, selected paths, matrix borders, and text. These positive observations cannot override the hard geometry failures below.

## Source hierarchy and semantics

The current source has no `resizebox`, `scalebox`, `transform shape`, `tiny`, `scriptsize`, `footnotesize`, `small`, or explicit graphics scale. Effective parent sizes are 9.5 pt for the global default, notes, and edge notes; 10.2 pt for node and matrix-cell text; 10.4 pt for panel titles; and 12 pt for formulas. Natural TeX scripts originate from 12 pt formula parents. The minimum reader-facing effective size is therefore 9.5 pt.

The graph and matrices are mathematically consistent:

- edges are `i→j`, `j→i`, `j→h`, and `h→i`;
- outdegree tuple is `(1,2,1)`;
- the displayed `A` uses source columns;
- `M` is column-normalized and satisfies `1^T M = 1^T`;
- `P=M^T`, `P_{ji}=M_{ij}`, and the row-vector update is consistent with the column-vector update.

There are no formula rules emitted as separate drawing paths: no fraction rule, radical bar, overline, underline, or accent path appears. Every visible formula mark is present in the PDF character stream. The 43 foreground drawing paths are exactly two panel borders, three node borders, four edge curves/segments, four arrowheads, 27 matrix-cell borders, and three focus borders.

## Denominator and manual review

- Visible non-space glyph objects: **216**.
- Foreground drawing/path objects: **43**.
- Total foreground objects: **259**.
- Complete unordered-pair denominator: **33,411**, matching `259×258/2`.
- Glyph contact sheets opened: **18**, covering all 216 glyph cells.
- Drawing contact sheets opened: **6**, covering all 43 path cells.
- Critical relationship sheets opened: **22**, covering all 260 automatically surfaced near/intersecting candidates.
- Hard-candidate native/8× ROI packages opened: **21**, each with original, A mask, B mask, intersection, native overlay, and 8× nearest overlay.

The glyph reviewer ledger has 216 explicit rows. One glyph evidence row, `TXT_G0081` (comma), is itself an evidence failure: its raw mask contains a disconnected 13-pixel foreign component. Pairs involving that mask are therefore not used as standalone hard-geometry proof. This evidence defect independently forbids PASS, but the decision does not depend on it because multiple other masks are pure and prove hard failures.

## Hard failures

The following are geometry/relationship failures under R168, not advisory micro-typography issues:

1. `PAIR_08396`: `TXT_G0035` (“矩”) versus `DRW_0004` (node `j` border) has **37 native intersection pixels**. The glyph is gray and the border is blue, so the separated masks and yellow 8× intersection are unambiguous. This is a real illegal overlap between an independent note glyph and a node border.
2. `PAIR_11633`: the right parenthesis of `(i,j,h)` has **3 px** white gap to the panel border, below the required 6 px.
3. `PAIR_12712`: independent formula-row glyphs have **0 px** white gap, below the required 4 px.
4. `PAIR_24218` and `PAIR_24754`: the two superscript `T` glyphs in the left conservation identity each intersect an M-matrix bottom cell border by **60 px**.
5. Eleven node-order-note versus P-matrix-top-border pairs (`PAIR_26499`, `26616`, `26732`, `26733`, `26848`, `26962`, `26963`, `27076`, `27188`, `27299`, `27409`) contain **25–97 px** intersections. The note is visibly laid across the matrix top border.
6. `PAIR_29229` and `PAIR_29412`: independent consecutive formula rows in the right panel intersect by **20 px** (`P`/`P`) and **22 px** (`M`/`M`).
7. `PAIR_29582`: the superscript `T` in `P=M^T` intersects the P-matrix bottom border by **60 px**.

Confirmed hard-relation intersection sum excluding the contaminated-comma pairs is **888 native pixels**. `CLIP_PIXEL_COUNT=0`. Category minima are: text–text 0 px (required 4), text/formula–line/arrow 13 px (required 3, pass), text/formula–node border 0 px (required 5), text/formula–panel border 3 px (required 6), and text/formula–matrix-cell border 0 px (required 5).

## R168 treatment

The ideograph `一`, arrow glyphs, equals signs, commas, and other low-profile or small visible marks were inspected at native 1× and 8×. They remain visually clear. Their micro height ratios, typography taxonomy, and small raster differences are recorded as advisory only and did not trigger this FAIL. The decision is based on large, visible illegal overlaps and missing mandatory clearances, including a clean 37-pixel node-border collision.

## Final gates

- Candidate identity: PASS.
- Source effective-size floor: PASS.
- Glyph/codepoint/math semantics: PASS.
- Font visual harmony: readable globally; FAIL overall because placement creates hard collisions.
- Grayscale: PASS for legibility.
- Page integration: PASS for placement/caption, FAIL for internal geometry.
- Mask evidence closure: FAIL due `TXT_G0081` foreign component.
- Illegal overlap gate: FAIL; confirmed overlap count is nonzero.
- Clearance gate: FAIL.
- Clipping gate: PASS (`0`).
- Overall SA1 result: **FAIL**.

## Required next action

Route FIG-P715-01 to SA2 for source repair. Increase the node-to-note horizontal separation, move the right-panel node-order note away from the P matrix, add vertical separation between matrix bottoms and superscript formulas, and add vertical separation between consecutive formula rows. After a new official build, discard this round for PASS purposes and run a new fresh isolated SA1 from the new candidate. SA3 is not authorized from this result.
