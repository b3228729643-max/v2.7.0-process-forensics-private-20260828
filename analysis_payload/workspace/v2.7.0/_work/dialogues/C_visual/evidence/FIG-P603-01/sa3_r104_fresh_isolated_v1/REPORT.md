# FIG-P603-01 / R104 / SA3 fresh-isolated report

## Conclusion

`PASS — C_LOCAL_PASS_ONLY — WAIT_MAINLINE`

This is a local isolated SA3 finding. It does not assert global PASS, does not update a central state or inventory, does not request a source writer, and does not execute TeX. The source and official PDF remained read-only.

## Instance identity and isolation

- HANDOFF_ID: `C-FIG-P603-01-R104-SA3-FRESH-ISOLATED-V1`
- UID / role / round: `FIG-P603-01` / `SA3` / `R104`
- Evidence root: `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\C_visual\evidence\FIG-P603-01\sa3_r104_fresh_isolated_v1`
- Root state at dispatch: absent; created only for this review.
- TeX execution: `DISABLED`; LuaLaTeX, latexmk, texlua, and all TeX engines were not run.
- Source writer: `NONE`.
- Delegation: none.
- Central state/inventory writes: none.

The business inputs were limited to the official R104 PDF, the current FIG-P603-01 drawing source, the goal objective, the strict pixel/typography protocol, the strict figure evidence schema, and only the necessary surrounding V5-C03 body passage. The accepted SA1 root, older P603 evidence and role roots, central reports/state/inventory/routing, other UID evidence, other agents' outputs, chat/git history, and all other forbidden inputs were not read, listed, or hashed. No page, denominator, conclusion, or hash was inherited from SA1 or any prior evidence.

## Independent PDF location and identity

The figure was located from the official PDF itself by the current rendered caption/figure number, then checked against the whitelisted current label.

- Official PDF: `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\build\strict_current_r104_fullbook\main_full.pdf`
- Bytes: `4,967,222`
- SHA256: `E5C871642FBDDBEC6508BE1B61BD911FE281CA5ACFBD16B0449B13357770A641`
- Pages: `817`
- Page size: A4, `595.276 × 841.890 pt`
- Physical PDF page: `655` (zero-based index `654`)
- Printed page: `642`
- Rendered figure number: `32.6`
- Source label: `fig:V5-C03-acceptance-function`

The full native 300 dpi page is `2481 × 3508 px`. The integer-coordinate figure crop is `[250,2100,2184,2871]`, yielding `1934 × 771 px`. The standalone crop is `[454,2100,1980,2738]`, yielding `1526 × 638 px`. Both 300 dpi crops came directly from the official PDF without resize. The 200 dpi full page is view-only, never used for pixel counts.

## Source and semantic consistency

The current source declares a single acceptance-function graph with:

- x ticks `0,1,2,3` and y ticks `0,0.5,1`;
- a rising curve from `(0,0)` to `(1,1)`;
- a plateau at `alpha=1` from `r=1` onward;
- dashed guides at `r=1` and `alpha=1`;
- a breakpoint marker and label `折点`;
- annotations `r<1：按比例接受` and `r≥1：必然接受`;
- the general ratio `r=pi(y)q(y,x)/[pi(x)q(x,y)]`;
- the independent-proposal simplification `r=w(y)/w(x)`.

The caption states that MH acceptance is the truncated function `alpha=min{1,r}` and repeats both ratios. The necessary body passage says the figure displays the two sides of one and that truncation at one comes from the probability bound rather than a numerical patch. The rendered geometry, formulas, caption, and body therefore agree.

## Rendered views actually reviewed

The reviewer opened:

1. `full_page_200dpi.png` — page integration, surrounding text, caption flow, and page-edge condition;
2. `figure_crop_300dpi.png` — native figure-plus-caption readability and collision review;
3. `standalone_300dpi.png` — native graph/card geometry and text review;
4. `grayscale_300dpi.png` and `standalone_grayscale_300dpi.png` — non-color distinguishability;
5. `after_text_measurement_overlay_300dpi.png` — complete object mapping;
6. all 15 glyph contact sheets — 150 cells total;
7. both graphic contact sheets — 15 cells total;
8. all 14 critical-pair contact sheets — 53 native 1x / nearest-neighbor 8x cells total.

The full page is visually balanced. The figure does not crowd the surrounding paragraph or caption. The native figure and standalone render keep all ticks, labels, curve segments, guides, marker, formulas, border, and caption readable. Grayscale preserves the distinction between the data curve, threshold guide, marker, and text.

## Object closure

The machine inventory maps `165` objects:

- `150` individual glyphs;
- `15` graphical objects, including two independent fraction rules;
- `13` foreground graphics with nonempty masks;
- `2` visible background fills that are explicitly mapped but excluded from foreground collision masks.

Every glyph has a unique safe filename, semantic parent, bbox, native raw mask, evidence image, codepoint, role, and contact-sheet cell. Every visible foreground drawing/path is assigned to a graphic object. The formula-card border is isolated from its fill; the two fraction rules are separate `MATH_RULE` objects. No foreground mask is empty.

All `C(165,2)=13,530` unordered pairs occur exactly once in the machine pair inventory. This includes glyph-glyph, glyph-graphic, and graphic-graphic relationships, internal-layout exclusions, and the 53 pairs selected for manual native/8x review.

## Per-glyph and per-graphic manual decisions

`manual_glyph_review.csv` contains 150 unique reviewer-authored rows, one for each `GLYPH-001..150`. The reviewer inspected the ORIGINAL, TARGET OVERLAY, and MASK ONLY panels for each ID. Every row records:

- correct visible outline/codepoint;
- complete overlay coverage;
- pure mask-only isolation;
- `missing_stroke_px=0`;
- `foreign_pixel_px=0`;
- actual readability;
- no clipping;
- no hard R168 font issue.

`manual_graphic_review.csv` contains 15 per-ID rows. Axes, ticks, arrowheads, rising and plateau curves, dashed guide, marker, card border, and both fraction rules are geometrically correct and complete. GRAPHIC-007 and GRAPHIC-013 are the two mapped background-fill exclusions; they are not silently missing or treated as foreground.

No tofu box, wrong CJK glyph, wrong mathematical codepoint, missing punctuation, broken delimiter, formula-rule loss, or actual unreadability was observed.

## Overlap and clearance adjudication

Machine results before human interpretation:

- all pair rows: `13,530`;
- critical manual rows: `53`;
- raw nonzero-overlap pairs: `17`;
- raw candidate pixels across those pairs: `259`;
- glyph-glyph nonzero intersections: `0`;
- glyph-graphic nonzero intersections: `0`.

The first 36 critical rows are close independent reader relationships and all have blank native intersection panels. Their measured minima are:

- independent text-text: `28.1548 px` against a `4 px` requirement;
- text-to-line/graphic: `16.0 px` against a `3 px` requirement;
- formula text-to-card border: `26.0 px` against a `5 px` requirement.

The remaining 17 rows are graphic-graphic contacts. Each was judged individually in `manual_pair_review.csv`. They are necessary axis/tick crossings, shaft/arrowhead joins, curve/origin joins, guide/axis joins, guide/tick crossings, or the curve/threshold connection. None obscures unrelated content. The raw 259 pixels remain recorded; after semantic adjudication the canonical illegal collision count is:

`OVERLAP_PIXEL_COUNT=0`.

## Clip review

`machine_clip_inventory.csv` contains a containment row for every object. All 165 objects lie within both the official page and figure crop. All standalone-eligible objects lie within the standalone crop.

- minimum figure-crop margin for any object: `10 px`;
- minimum standalone-crop margin for any eligible object: `4 px`;
- minimum figure-crop edge margin for text: `10 px`;
- minimum standalone-crop edge margin for text: `18 px`.

The 4 px standalone minimum belongs to non-text graphics and is positive; direct visual review shows the corresponding ink is complete. Per-object clip fields in both glyph and graphic ledgers are `NO`. Thus:

`CLIP_PIXEL_COUNT=0`.

## R168 font treatment

The source contains 8.5 pt tick labels and 9.2 pt other figure text, with graphics scale 1 and no resizebox/scalebox/transform-shape reduction. These declared sizes would be below an older metadata-only 9.5 pt threshold. Under the controlling R168 instruction, point metadata, peer taxonomy, small ratio differences, and 1–2 px effects are advisory unless they manifest as tofu/wrong glyph or codepoint, mathematical corruption, actual unreadability, clearly severe font imbalance, real clipping, or illegal overlap.

The native renders show none of those hard defects. Tick labels are smaller by design yet clearly readable. Annotations, formula block, caption, and page text have a natural hierarchy. The 32 peer/role rows contain six advisories caused by rotated antialiasing or grouping punctuation/operators with intrinsically different outlines; individual glyph review confirms that every affected object is complete and readable. Consequently:

- `FONT_VISUAL_HARMONY_PASS=true`;
- R168 hard font failure count: `0`;
- point-size/peer observations: advisory only.

## Hard-gate matrix

| Gate | Result | Evidence |
|---|---:|---|
| Tofu / missing glyph | PASS | 150 native/8x glyph rows |
| Wrong codepoint / math glyph | PASS | glyph and math ledgers |
| Actual readability | PASS | all rendered views and glyph sheets |
| Clearly severe font imbalance | PASS | 32 peer/role rows and full-page view |
| Glyph mask completeness | PASS | missing stroke pixels 0 |
| Glyph mask purity | PASS | foreign/contamination pixels 0 |
| Geometry and relationships | PASS | 15 graphics and 17 topology rows |
| Formula semantics | PASS | two rules, formulas, curve, caption, body |
| Object/text content | PASS | all 165 objects mapped |
| Caption/body consistency | PASS | source label/caption and necessary V5-C03 passage |
| Illegal overlap | PASS | `OVERLAP_PIXEL_COUNT=0` |
| Real clipping | PASS | `CLIP_PIXEL_COUNT=0` |
| Actual render/view | PASS | full/figure/standalone/grayscale/overlay and all contact sheets |

## Machine terminal state

The machine terminal check reports:

- object IDs `165`, glyphs `150`, graphics `15`;
- expected/actual/unique pair keys `13,530 / 13,530 / 13,530`;
- glyph masks/evidence `150 / 150`, all decodable;
- graphic masks/evidence `15 / 15`, all decodable;
- glyph/graphic contact sheets `15 / 2`, all decodable;
- critical pair evidence/contact sheets `53 / 14`, all decodable;
- cache and pyc entries `0`.

NTFS alternate streams, ordinary-file coverage, final hashes, timestamps, and read-only sealing are checked by the final seal operation and captured in `MANIFEST.csv`; the marker is deliberately excluded and created last.

## Final disposition

The isolated SA3 result is `PASS` within local C authority only. The sealed evidence is handed back as `C_LOCAL_PASS_ONLY` and must wait for mainline acceptance. No central inventory/state was changed and no global PASS is claimed.
