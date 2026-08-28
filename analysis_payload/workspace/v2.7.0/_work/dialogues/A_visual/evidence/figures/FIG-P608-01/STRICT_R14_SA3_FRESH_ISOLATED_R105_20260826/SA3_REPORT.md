# FIG-P608-01 — R105 fresh isolated SA3 terminal review

## Assignment and independence

- `HANDOFF_ID=A-R105-P608-SA3-FRESH-ISOLATED-20260826`
- Role: the single fresh isolated SA3 reviewer for `FIG-P608-01`.
- Review kind: read-only terminal review. No TeX engine was started and no source, main, build, central state, or Git object was modified.
- Inputs were limited to the official R105 full-book PDF, the current figure source, the current Goal query, and the two authorized protocol/schema files. The active Goal query returned no current Goal object.
- No old P608 evidence, role report, handoff, state, inventory, chat history, Git history, or old P608 build artifact was read.

## Official-candidate lock

- PDF: `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\build\strict_current_r105_fullbook\main_full.pdf`
- Size: `4,967,209` bytes.
- SHA-256: `F86E89047BA09FEA72FD8F79BF524A04DA367BFF3057806A879106A1032626A1`.
- Page count and media box: 817 pages; page 661 is A4 `595.276 × 841.890 pt`.
- Target identity: physical page 661, printed page 648, Figure 32.8, source `fig_v5_c03_trace_running_mean.tex`.
- Native page grids: 200 dpi `1654 × 2339`; 300 dpi `2481 × 3508`.
- Figure crop page coordinates: `[292,917,2146,1867]`, yielding `1854 × 950` pixels.
- Standalone audit crop page coordinates: `[479,917,1959,1784]`, yielding `1480 × 867` pixels.
- The crop products are unresized integer crops from the same official Poppler 300 dpi page. No standalone build or prior-round PDF was mixed in.

## Complete denominator and native masks

The independently rebuilt denominator contains 128 foreground objects:

- 68 visible text glyphs, each with `CHAR ↔ contour ↔ parent ↔ bbox ↔ raw mask` mapping;
- 58 in-scope PDF drawing paths exposed by the current page, including four axes, four arrowheads, four tick-path groups, two data curves, 35 markers, three reference lines, four equals-sign bars, and two overlines;
- two visible tiling-pattern hatch regions that PyMuPDF does not expose as ordinary page drawing paths, retained as two semantic final-visible foreground pattern groups.

All `128 choose 2 = 8,128` unordered pairs are present exactly once in `all_unordered_pairs.csv`. All 128 ordinary mask PNGs have unique safe filenames, open successfully, and contain ink. IDs use ordinary filenames only; no colon-bearing ADS path was used.

The 68 glyph rows are distributed across 12 complete contact sheets. I opened every sheet and reviewed each row individually. Every `original`, `target overlay`, and `mask only` view matches; `missing_stroke_px=0` and `foreign_pixel_px=0` on all 68 manual rows. The six path-based math rules have matching native 1x/8x evidence and six manual rows.

## Typography and R168

Source inventory found 9.6 pt base/tick/annotation text, 10.8 pt labels/titles, no `resizebox`, `scalebox`, graphic `scale`, or `transform shape`, and two explicitly scripted y-label `t` glyphs. PDF extraction is 9.564 pt and 10.760 pt respectively (`D/E=0.9963`); script extraction is 7.532 pt against the expected 7.56 pt (`0.9963`).

Native ink medians/ranges include:

- 9.6 pt CJK annotation: 34–35 px;
- 10.8 pt CJK title: 38–40 px;
- 9.6 pt digits: 26–27 px;
- 10.8 pt base math `X`: 30 px;
- natural or explicitly scripted math glyphs: 18–22 px;
- xlabel `t`: 28 px.

The title/annotation CJK median ratio is about 1.114, matching the intended hierarchy. The cross-panel title medians differ by only about 1.3%. Commas, ellipses, and decimal points have exact same-codepoint, same-font, same-color, same-size peers: all comma peers are `H=10/area=42`, both ellipses are `H=6/area=74`, and all decimal points are `H=6/area=27`.

Under R168, the explicitly scripted y-label `t` is advisory rather than a hard failure because it is complete, visually clear at 21 px, and does not create imbalance. There is no missing glyph, tofu, wrong codepoint, unreadable glyph, or visibly severe typography imbalance. `FONT_VISUAL_HARMONY_PASS=true` was set manually after opening the evidence.

## Geometry, relationships, overlap, clearance, endpoints, and clipping

- Illegal `OVERLAP_PIXEL_COUNT=0`.
- `CLIP_PIXEL_COUNT=0`.
- No text-involved mask intersection occurs in any of the 8,128 pair rows.
- Seventy-one pair rows have nonzero designed geometry intersections: axis-arrow/tick/junction connections, divider-axis junctions, curve-marker connections, reference-line/data crossings, and hatch-background relations. These are not illegal reader-object overlaps.
- Minimum independent text-text clearance: 35.235 px (`>=4`).
- Minimum text-axis clearance: 21 px; text-arrowhead: 16.117 px; text-reference line: 27 px; text-data curve: 51 px; text-marker: 43.777 px; tick text-tick stroke: 13 px; text-hatch: 23 px (all `>=3`).
- Minimum text-to-audit-crop edge: 13 px (`>=6`).
- Minimum cross-panel reader clearance: 34 px (`>=8`).
- The overline-to-own-`X` clearance is 6 px and belongs to a single formula; the overlines do not touch glyph ink or any unrelated object.

All four axes and arrowheads are complete. The upper curve contains 20 source points and 19 joined segments; the lower curve contains 15 retained-mean points and 14 joined segments. First/last points, both x=5.5 dividers, the y=2 target line, and all 35 endpoint markers were visually and numerically checked. Source `clip=false` agrees with the zero-clipping evidence.

## Formula and content semantics

The upper trace contains 20 points. Discarding t=1…5 leaves exactly 15 points t=6…20. Independent recomputation of every retained running mean matches the 15 source coordinates to the stated four-decimal rounding; the largest absolute rounding difference is `0.00004286`, and the final mean is exactly `2.0000`.

Visible semantics agree among source, formulas, annotations, curves, and caption:

- upper panel is `X_t` and marks warm-up `t=1,…,5` versus retained `t=6,…,20`;
- lower title and y-label use overlined `X_{6:t}`;
- target line and annotation are value 2;
- caption accurately states that the running mean fluctuates near 2 and that the graphic is diagnostic, not a convergence proof.

The four custom path bars visibly form two correct equals signs; the two overline paths are centered over the intended `X` glyphs. No formula rule is missing from the object denominator.

## Cross-check and decision

`machine_crosscheck.json` reports zero integrity errors: 128 unique objects, 8,128 complete unordered pairs, 68 glyph/manual rows, 6 math-rule/manual rows, 128 ordinary masks opened, zero text intersections, zero illegal overlap, zero clip pixels, and consistent source semantics.

Final manual decision: `SA3_PASS_READY_FOR_MAIN_A_LOCAL_PASS_ACCEPTANCE`.

This decision authorizes only the root thread to consider main A-local acceptance. It does not claim or write central `A_LOCAL_PASS`.
