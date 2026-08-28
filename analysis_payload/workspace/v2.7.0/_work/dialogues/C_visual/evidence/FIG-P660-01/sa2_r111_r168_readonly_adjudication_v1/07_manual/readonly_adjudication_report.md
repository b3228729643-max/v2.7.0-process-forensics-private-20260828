# FIG-P660-01 R111/R168 independent read-only adjudication

## Identity and current location

- HANDOFF_ID: `C-FIG-P660-01-R111-SA2-R168-READONLY-ADJUDICATION-V1`
- current source UID: `FIG-P660-01`
- official input: R111 `main_full.pdf`, 4,967,076 bytes, SHA-256 `DAB1062500E39DD2C34C6B4A9FF51CAC2BE0A4C84B2F45F5FB8E645C4BC012D6`
- current figure source: `fig_v5_c05_simplex_geometry.tex`, 3,445 bytes, SHA-256 `B1EBE40A22D8A39C983C1BD70F208907B413F611EE0D40601AE44B6F4B66A224`
- independently located current output: R111 physical PDF page 709, printed page 696, Figure 34.4
- adjudicated subject: three-category probability simplex geometry

The stale task-card sentence about Gamma normalization was not adopted as a conclusion and was not counted as a defect. Current source, rendered figure, caption, alt text, and the necessary adjacent V5-C05 context all concern the simplex.

## Evidence actually opened

I opened the page-integration views for physical pages 708, 709, and 710; the full page 709 at 300 dpi; the native 300 dpi figure-plus-caption crop; grayscale; text/object overlays; separated masks and their composite; the complete unordered-pair contact matrix; and every native1x plus nearest-neighbor8x ROI R01 through R11. Manual findings were written only after the corresponding evidence IDs had been opened. The per-object ledger is `manual_object_findings.csv`; the per-candidate-pair ledger is `manual_pair_adjudication.csv`.

## Mathematical and geometric adjudication

The source vertices are `e_1=(0,0)`, `e_2=(7,0)`, and `e_3=(3.5,6.062)`. Their three side lengths are 7.000000, 6.999846, and 6.999846 source units, so the intended equilateral construction is preserved to the written-coordinate precision.

Solving the affine system for the plotted point `(3.85,3.031)` yields barycentric weights `(0.2,0.3,0.5)`, with sum exactly 1 in the machine calculation and minimum weight 0.2. The same values are recovered independently as normalized perpendicular distances from the point to the three opposite edges. Thus the point is strictly interior, the three component labels are assigned to the correct opposite edges, and the displayed coordinate `theta=(0.2,0.3,0.5)` is geometrically correct.

The one-hot vertex labels are correct: left `e_1=(1,0,0)`, right `e_2=(0,1,0)`, and top `e_3=(0,0,1)`. The constraint card correctly gives `Delta^2={theta in R^3: theta_i>=0, sum_i theta_i=1}` and `dim(Delta^2)=2`. The region card correctly distinguishes interior (all components positive), edge (one component zero), and vertex (one category probability equal to 1). The grid, component rays, and marker form a coherent barycentric reading path without introducing a false axis or coordinate convention.

## Text, caption, alt, and current context

The current alt semantic string and caption semantic string are an exact normalized match of 81 characters. Both state the same single conclusion: a ternary probability vector lies on a two-dimensional simplex; vertices represent one-hot categories; an interior point's barycentric coordinates are the category probabilities; and the Dirichlet support is two-dimensional despite the three-coordinate representation.

The adjacent current chapter sentence introduces the figure by saying that the three-component classification-probability vector has only two degrees of freedom. The following Gamma-normalization theorem is a separate next object on the same page. The figure does not claim that the plotted simplex itself is a Gamma-normalization construction.

## Glyphs and codepoints

Native1x and nearest8x evidence show complete glyphs without tofu or replacement boxes. PDF text extraction identifies the critical rendered characters as:

- `Delta`: U+0394 GREEK CAPITAL LETTER DELTA;
- `R`: U+211D DOUBLE-STRUCK CAPITAL R;
- `sum`: U+2211 N-ARY SUMMATION;
- `>=`: U+2265 GREATER-THAN OR EQUAL TO;
- math italic `e`: U+1D452, three occurrences;
- math italic `theta`: U+1D703, seven occurrences.

No U+FFFD replacement character or square/tofu codepoint occurs in the current figure/caption extraction. Subscript spans are separately measurable: the three 8.7 pt component-label subscripts have native ink heights 18, 18, and 19 px; other scripts in vertex/constraint formulas measure 19–27 px. The constraint operators, membership sign, double-struck R, summation, subscripts, punctuation, Latin `Dirichlet`, digits, and Chinese glyphs all render with the intended shapes.

## Readability, scale, and visual hierarchy under R168

The figure has no whole-object `scale`, `transform shape`, `resizebox`, or `scalebox`; graphics scale is 1.0. Ordinary nodes are declared at 9.5 pt. The three component labels are explicitly declared at 8.7 pt, and the style line also contains a 9.2 pt declaration. Under the controlling R168 policy, those declarations and the older numeric thresholds are advisory and cannot alone cause failure.

The native evidence does not show the hard phenomena that could convert that advisory difference into failure. The three component-label object ink heights are all 35 px, with ratio 1.0000; their theta glyphs are 28 px and their subscripts 18–19 px. Vertex-coordinate object heights are all 48 px; the three vertex-meaning lines are all 34 px. Region-statement ink heights are 36, 36, and 35 px. The conclusion lines are 38, 36, and 35 px; the 1.0857 max/min ink ratio comes from different Chinese glyph compositions on identically declared 9.5 pt lines and does not create a visible size change or imbalance in the opened native and grayscale views.

The geometry retains the highest visual priority: the boundary is strongest, component rays are dashed and darker than the auxiliary grid, and the selected point is salient. The three explanatory cards align on the right, have consistent widths and padding, and remain subordinate to the simplex. Color is not the only encoding; grayscale preserves boundary/grid/ray/marker/card hierarchy.

## Overlap, clearance, and clipping

The frozen denominator contains 30 objects and the machine table enumerates all 435 unordered pairs. Nineteen near/contact rows were manually adjudicated after their evidence was opened. Intended simplex construction contacts account for 355 shared mask pixels. Four extracted-bbox duplication rows account for 458 candidate pixels and are confirmed mask contamination because native ROIs show distinct readable baselines. One additional near-line pair has no overlap. No candidate is unresolved and canonical true illegal overlap is zero.

The native crop's 1 px and 6 px edge strips contain zero denominator foreground. Object margins to the crop edges are 30.675 px left, 47.592 px top, 35.136 px right, and 26.496 px bottom. The full-page view likewise shows complete strokes and glyphs. No text, formula, boundary, grid segment, component ray, marker, card, or caption character is truly clipped.

## Page integration

On physical page 708, the preceding definition and short bridge introduce the geometry naturally. Physical page 709 begins with the complete figure and caption, then proceeds to Theorem 34.2 and its proof without an orphan line, collision, forced overflow, or conspicuous empty block. Physical page 710 continues the proof and next figure normally. Figure width, caption wrapping, surrounding whitespace, running header, and footer navigation are balanced and readable.

## Independent disposition

No native evidence shows a missing glyph/tofu, wrong codepoint, wrong mathematics, unreadability, visibly obvious imbalance, true clipping, illegal overlap, or semantic/geometric error. No source edit or rebuild is warranted by this SA2 adjudication.

`DISPOSITION = SA2_NO_SOURCE_CHANGE_READY_FOR_FRESH_SA1`
