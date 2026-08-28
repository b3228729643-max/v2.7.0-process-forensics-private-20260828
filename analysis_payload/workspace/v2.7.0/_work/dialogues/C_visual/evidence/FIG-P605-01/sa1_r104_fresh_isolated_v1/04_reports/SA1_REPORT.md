# FIG-P605-01 — R104 fresh-isolated SA1 report

## Disposition

- `HANDOFF_ID`: `C-FIG-P605-01-R104-SA1-FRESH-ISOLATED-V1`
- reviewer instance: `SA1 fresh isolated`
- result: **PASS**
- next action: request one completely fresh isolated SA3 review.
- scope limit: this is an SA1 result only. It does not assert `C_LOCAL_PASS` or any global pass.
- TeX execution: `DISABLED`; LuaLaTeX, latexmk, texlua and all other TeX engines were not invoked.
- source writer: `NONE`; PDF, figure source and main text remained read-only.
- subagents: none.

## Isolation and allowed inputs

Only the following business inputs were used: the official R104 PDF; the current single P605 figure source; `goal-objective.md`; `STRICT-PIXEL-TYPOGRAPHY-PROTOCOL.md`; and `STRICT_FIGURE_EVIDENCE_SCHEMA.md`. The optional current chapter source was not needed and was not read. No old P605 evidence, other UID evidence, central report/state/inventory/routing, current-state/task packet, other-agent output, chat history or Git history was read.

The only output root is:

`D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\C_visual\evidence\FIG-P605-01\sa1_r104_fresh_isolated_v1`

## Candidate identity and independent location

- official PDF: `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\build\strict_current_r104_fullbook\main_full.pdf`
- PDF bytes: `4,967,222`
- PDF SHA-256: `E5C871642FBDDBEC6508BE1B61BD911FE281CA5ACFBD16B0449B13357770A641`
- PDF: 817 A4 pages; native page size 595.276 × 841.890 pt.
- independent current-caption search: physical PDF page `658`; printed page `645`; figure `32.7`.
- current label: `fig:V5-C03-componentwise-sweep`.
- figure source SHA-256: `53AE215D7E7CBB423ED4A7D14806A6CAEB68FDE56B70217F8A87AF914B982C7F`.

The location was derived from the R104 PDF itself by searching its current caption. A stale page reference in an allowed task card was not inherited.

## Native render set actually reviewed

- full page at native 200 dpi: 1654 × 2339 px.
- full page at native 300 dpi: 2481 × 3508 px; no post-render resize.
- figure-with-caption crop at 300 dpi: full-page box `[292,250,2237,1063]`, size 1945 × 813 px.
- standalone figure crop at 300 dpi: full-page box `[354,250,2171,921]`, size 1817 × 671 px.
- grayscale figure at 300 dpi.
- all four review views were actually opened and manually inspected. Full-page integration, figure/caption margins, standalone structure and grayscale distinction are all clear.

## Complete inventory and mapping

- visible glyphs: `150`; whitespace excluded as nonvisible.
- text objects: `15`; graphic objects: `17`; total objects: `32`.
- unordered object pairs: `C(32,2) = 496`; machine rows `496`; manual rows `496`; IDs unique and exact.
- PDF figure drawings: `23`; mapped `23`; unmapped `0`.
- ordinary glyph masks/cells: `150 / 150`; empty glyph masks `0`.
- ordinary object masks: `32`; empty object masks `0`.
- contact sheets: `8`; opened and manually reviewed `8 / 8`.
- critical pair ROI sets: `14`; each includes the original, both masks, intersection, 1× overlay and nearest-neighbour 8× overlay.
- math-rule paths within the figure: `0`; all visible mathematics is represented by PDF glyph objects and was reviewed glyph-by-glyph and semantically.
- explicitly excluded non-visible backgrounds: page background, panel fill, node fill, annotation-card fill and choice-diamond fill. Final-visible strokes, borders, arrows and text remain included.

## Glyph and typography adjudication under R168

Every visible glyph was reviewed by ID against the original, overlay, mask-only view and 8× view. Results: missing-stroke pixels `0`; foreign pixels `0`; tofu/wrong glyph/codepoint `0`; mathematical-glyph semantic substitutions `0`; actually unreadable glyphs `0`; severe macro-level size imbalance `0`.

Peer/role calibration was also checked:

- panel-title colons: equal 27 px heights and equal 82 px areas.
- ellipses: both 5 px high; areas 64 and 62 px; ratio 0.969; each has all three dots.
- caption full stops: both 11 px high; areas 26 and 28 px; ratio 0.929.
- the annotation colon has no same-font-size duplicate within the candidate; its actual mark is intact and readable.

Advisories that do not trigger a hard failure under R168:

- source default/node size is 9.2 pt rather than legacy 9.5 pt; headings are 9.8 pt; graphics scale is exactly 1.0000. The 1× native render is readable and has no severe imbalance.
- natural script glyphs include `GLY-006-004` at 13 px and `GLY-013-002..004` at 13 px.
- selected naturally short operators include `GLY-013-010` lower-limit equals at 9 px, a base equality sign at 12 px and a relation tilde at 7 px. Each contour is complete and semantically unmistakable.

These are legacy micro-size/ratio observations only. R168 treats them as advisory because there is no actual unreadability, wrong glyph, tofu, semantic error or severe size imbalance.

## Geometry, clipping and pair adjudication

- crop-edge touch/clip pixels: `0` for every inventoried object.
- real clipping: `0`; illegal overlap: `0`.
- minimum text-to-text clearance: `41 px`.
- minimum annotation-to-node/card border clearance: `15 px`.
- minimum text-to-line/arrow clearance: `19 px`.
- minimum text-to-panel-border clearance: `25 px`.
- nearest cross-panel reader-text clearance: `321 px`.
- caption-to-panel clearance: `25 px`.

Across all 496 pairs the raw candidate-intersection total is `86 px`. Manual ROI review partitions it as:

- intended node/arrow design connections: `80 px` (`PAIR-0394`: 42 px; `PAIR-0408`: 38 px).
- mask-colour contamination: `6 px` (`PAIR-0483`: 3 px; `PAIR-0485`: 3 px). Original render and source geometry show the outer branches target K_1 and K_d; the apparent K_j contact exists only in the colour-derived masks.
- true illegal overlap: `0 px`.

Ten relationship pairs are manually classified as intentional design connections or arrivals, two as confirmed mask contamination, and the remaining 484 as clear and separate. Every pair has its own reviewer, decision and note; no default or bulk PASS was generated by the machine script.

## Content, relationships and mathematical semantics

- left panel accurately represents fixed ordered composition: `K_sys = K_1 K_2 ⋯ K_d`.
- right panel accurately represents coordinate choice `J ∼ ω` and the fixed weighted mixture `K_rand = Σ_{j=1}^{d} ω_j K_j`.
- the diagram distinguishes sequential composition from randomized coordinate choice through its arrows and grouping.
- the statement that fixed ordered composition is usually not reversible is correctly qualified.
- the statement that a fixed-weight mixture of coordinate kernels reversible with respect to π remains reversible is correct and matches the source.
- figure number, label, caption, node labels, summation limits and weights match between current source and R104 PDF.

## Hard-gate matrix

| R168 hard gate | Finding |
|---|---:|
| tofu / wrong codepoint / wrong math glyph | 0 |
| actually unreadable text or math | 0 |
| obvious severe size imbalance | 0 |
| real clipping | 0 |
| illegal overlap | 0 |
| geometry / relationship error | 0 |
| formula-semantic error | 0 |
| object-content or caption/source inconsistency | 0 |

## Final SA1 result

`PASS` — no hard failure was found under R168. This result only requests a separate completely fresh isolated SA3 audit. The SA3 instance must independently locate and judge the current candidate and must not inherit this SA1 conclusion as evidence.
