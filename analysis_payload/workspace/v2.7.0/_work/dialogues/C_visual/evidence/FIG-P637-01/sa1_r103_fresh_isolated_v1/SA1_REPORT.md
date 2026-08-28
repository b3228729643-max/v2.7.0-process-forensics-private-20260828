# FIG-P637-01 — R103 fresh isolated SA1 report

## Verdict

`RESULT: PASS`

- `C_LOCAL_PASS: NOT_DECLARED`
- `GLOBAL_PASS: NOT_DECLARED`
- `NEXT: REQUEST_FRESH_ISOLATED_SA3`
- Failure IDs: none.

This is an SA1-only decision under user R168. It does not replace an independent fresh isolated SA3 or aggregate into a global result.

## Identity and isolation

- Instance: `/root/sa1_fig_p637_r103_fresh_isolated`
- HANDOFF_ID: `C-FIG-P637-01-R103-SA1-FRESH-ISOLATED-V1`
- Evidence root: `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\C_visual\evidence\FIG-P637-01\sa1_r103_fresh_isolated_v1`
- TeX: `DISABLED`; no LuaLaTeX, latexmk, texlua, or other TeX process was run.
- Source writer: `NONE`; the official PDF, current figure source, and all mainline/state material stayed read-only.
- Prior P600/P602/P637 evidence, conclusions, roles, handoffs, state, inventory, routing logs, chat/git history, and other agent output were not read or inherited.
- No child agent or second SA1 was started.

## Candidate identity and independent location

The sole candidate is the official R103 full-book PDF:

- Pages: 817.
- Bytes: 4,967,184.
- SHA-256: `9379A489E0C2A57A7DA670C98029BB27B3F1A385BF8E4C3BD14FE9B606AA0F23`.
- Independent full-book searches for `固定教学示意`, `二维Gibbs`, and `轴向短步` converged on one unique physical page: 687 (printed page text `674`). No page number from prior evidence was used.
- Page size: 595.2760009765625 × 841.8900146484375pt.
- Native 300dpi page: 2481 × 3508px; 200dpi page: 1654 × 2339px.
- Figure-plus-caption crop: `[58.3619995, 59.1808319, 525.5735474, 346.4978943]pt`, mapping to `[243,246,2190,1444]px`, dimensions 1947 × 1198px.
- Standalone plot crop: `[151.4606323, 59.1808319, 431.0722961, 314.3513489]pt`, mapping to `[631,246,1797,1310]px`, dimensions 1166 × 1064px.

## Rebuilt denominator

The denominator was rebuilt from the located official PDF, not copied from any earlier result.

- Raw PDF drawings on page: 39.
- Drawings mapped to the figure region: 31; drawings explicitly excluded as outside the figure: 8.
- Mapped background-only fill exclusions: 2 (pale ellipse interior and white information-node interior).
- Independent visible text objects: 16.
- Independent visible graphic objects: 21.
- Total pair objects: `n = 37`.
- Complete unordered-pair enumeration: `C(37,2) = 666`; actual rows: 666.
- Pair class counts: 120 text-text, 336 text-graphic, 210 graphic-graphic.
- Visible glyphs: 131; nonempty glyph masks: 131; manual glyph rows: 131.
- Whitespace exclusions: 3, each recorded rather than silently treated as a glyph.
- Clip rows: 37; manual clip decisions: 37.

Every mapped drawing contributes to an inventoried graphic object or an explicit background exclusion. Every independent visible text span contributes to an object, and every visible glyph contributes to a per-glyph mask/card/decision.

## Render and card coverage

Review used the official PDF only and produced no TeX-derived candidate.

- Full page: native 200dpi and native 300dpi.
- Figure plus caption: native 300dpi.
- Standalone plot: native 300dpi.
- Grayscale standalone: native 300dpi.
- Object measurement overlay: native 300dpi.
- Exact nearest-neighbor 8x quadrants: 4 standalone plus 4 figure-plus-caption.
- Glyph review: 131 exact-8x original/target-overlay/mask-only cells across 11 sheets.
- Graphic review: 21 original/target-overlay/mask-only cards.
- Critical pair review: 42 one-x cards and 42 exact-8x nearest cards; every nonzero pair has its own manual row.

All 46 top-level/manual view rows passed. The page composition, standalone plot, grayscale view, every 8x quadrant, every glyph sheet, and every graphic card were opened and visually inspected.

## Typography and glyph findings under R168

Read-only source inspection found explicit 9.2pt figure text and 8.8pt state numerals, with no resizebox, scalebox, general scale, or transform-shape text scaling. The 8.8/9.2 ratio is 0.9565. The official PDF exposes caption glyph metadata near 9.96–9.99pt and general figure glyph metadata near 9.165pt; that small role/metadata difference is advisory under R168.

Hard typography outcomes:

- Tofu or missing glyphs: 0.
- Wrong glyphs/codepoints: 0.
- Missing-stroke pixels across manual glyph decisions: 0.
- Foreign-ink pixels across manual glyph decisions: 0.
- Actual unreadable items: 0.
- Obvious severe font imbalance: 0.
- Mathematical semantic defects: 0.

Natural subscripts are smaller by design. Low-profile punctuation and sparse characters such as `一` have short ink boxes by shape. The rotated long-axis annotation has a taller projected box than the horizontal short-axis annotation while using the same source size and visual weight. These are not hard failures under R168.

Advisories only:

1. The 9.2pt/8.8pt source sizes are below a legacy absolute numerical preference but remain fully readable and balanced.
2. Caption-versus-figure observed PDF metadata differs by roughly 8.7–9.0%, with no severe visual imbalance.
3. The two-line caption is dense but fully contained and readable.

## Pair, overlap, and clearance findings

- Text-text raw intersections: 0 pixels across 120 pairs.
- Text-graphic raw intersections: 0 pixels across 336 pairs.
- Minimum raw isolated-mask clearance across all text-related pairs: 10.198px.
- Zero-intersection pairs: 624.
- Nonzero exact-mask pairs flagged for manual review: 42.
- Total raw pixels in those designed intersections: 1,731.
- Individually reviewed designed intersections: 42.
- Illegal overlap pairs: 0; illegal overlap pixels: 0.

The 42 intersections are coordinate-axis crossings, contour/axis/guide/trajectory crossings, state-marker endpoint connections, or the intended crossing of the long and short principal-axis guides. Each exact 8x card was judged independently in `manual/manual_critical_pair_review.tsv`. No intersection covers text, conceals arrow direction, creates a false state/junction, or changes mathematical meaning. The 624 mechanically separated pairs retain `UNSET_BY_MACHINE` manual fields; no bulk/default/global human PASS was generated.

## Geometry, semantics, clipping, and integration

- Geometry: three nested tilted contours, coordinate axes, long/short target axes, seven state markers, and six alternating Gibbs moves are coherent.
- Relationship semantics: green horizontal moves update x1; dark-blue vertical moves update x2; states progress 0→1→2→3→4→5→6.
- Caption semantics agree with the visible diagram and explicitly identify the fixed teaching path rather than a simulated random trace.
- Clip pixel count: 0 across 37 objects.
- Minimum assigned-viewport ink margin: 9px, belonging to the complete information-node border.
- Grayscale: essential topology survives through orientation, contour nesting, arrowheads, marker shapes, and line weight.
- Page integration: no bad whitespace, orphaned label, real crop, caption overflow, or collision with the following paragraph.

## Manual ledgers and machine separation

Machine-created artifacts are limited to inventories, masks, pair enumeration, clearances, and renders; their manual fields remain `UNSET_BY_MACHINE`. Human decisions were authored separately:

- `manual/manual_glyph_review.tsv`: 131 per-ID glyph decisions.
- `manual/manual_critical_pair_review.tsv`: 42 per-ID nonzero-pair decisions.
- `manual/manual_clip_review.tsv`: 37 per-object clipping decisions.
- `manual/manual_view_review.tsv`: 46 per-view/card-group decisions.
- `manual/manual_role_script_review.tsv`: 7 role and 5 script decisions plus the R168 advisory.
- `manual/manual_hard_gate_review.tsv`: 16 named hard-gate decisions.

No script generated, filled, or overwrote a reviewer name, boolean, decision, or note.

## Final SA1 disposition

All R168 hard gates pass. There are no failure IDs. The result is `PASS` for this fresh isolated SA1 recordset only. Request one separate completely fresh isolated SA3. Do not declare `C_LOCAL_PASS` or global PASS from this recordset alone.
