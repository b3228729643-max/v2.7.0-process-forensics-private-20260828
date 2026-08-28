# FIG-P660-01 independent context, mathematics, caption, alt, and glyph review

## Independent location

The exact current caption phrase was searched in the official R111 PDF. It occurs on PDF physical page 709 of 817 (one-based), whose printed page number is 696, as Figure 34.4. The historical UID token `P660` was not used as the page locator.

## Current-source and current-context consistency

The sole whitelisted figure source defines a three-vertex simplex, an interior point `theta=(0.2,0.3,0.5)`, three component guides, a closed-simplex formula, face classifications, a freedom-count conclusion, the caption, and the alt text. The narrowly read current V5-C05 chapter context states that a three-class probability vector has three components but only two degrees of freedom; immediately before the figure it defines the Dirichlet law on the `(K-1)`-dimensional simplex measure, and immediately after it gives the Gamma-normalization theorem. Those statements agree with the rendered figure.

The source caption and rendered caption are textually consistent: three-class probability vectors lie on a two-dimensional simplex; each vertex represents probability one for one class; an interior point's barycentric coordinates are the class probabilities; and the Dirichlet law has a two-dimensional support although written in three ambient coordinates. The alt text expresses the same object-relation-conclusion content and adds no contradictory claim.

## Independent mathematical recomputation

Using the source vertices `e1=(0,0)`, `e2=(7,0)`, `e3=(3.5,6.062)` and weights `(0.2,0.3,0.5)`, the weighted point is exactly `(3.85,3.031)`, identical to the source `th` coordinate. The weights sum to one and are all positive.

For an equilateral triangle, each barycentric component equals normalized perpendicular distance to the opposite edge. Independent projection gives distance ratios `0.2`, `0.3`, and `0.5` to edges `e2-e3`, `e1-e3`, and `e1-e2`, respectively, so all three dashed guides and labels are semantically correct. One affine constraint in ambient dimension three gives affine dimension two. The `0.2,0.4,0.6,0.8` grid is consistent with the probability-coordinate partition.

The face card is correct: all components positive describes the interior; one zero component describes an edge; and a vertex has one category probability equal to one. The top card correctly defines the closed simplex, which is the topological support closure for the three-class Dirichlet distribution; the chapter's density domain uses the open simplex for coordinates and does not conflict with this closure view.

## Glyphs and codepoints

The PDF exposes 259 glyph records across the 21 text elements. No record contains U+FFFD, U+25A1, or U+2610. Critical extracted symbols include mathematical italic theta U+1D703, mathematical italic `i` U+1D456, Greek capital delta U+0394, blackboard-bold R U+211D, element-of U+2208, ratio sign U+2236, greater-than-or-equal U+2265, and n-ary summation U+2211. The three basis labels extract as the intended mathematical italic `e` with ordinary numeric subscripts. Native1x, nearest8x, grayscale, and the glyph atlas show no tofu, substituted box, missing stroke, wrong sign, or wrong numeral.

## R168 advisory items

The three component labels are explicitly 8.7 pt in source and extract at 8.66749 pt for their base glyphs, below the older 9.5 pt declaration threshold. Their rendered groups are each 36 px high, have exact same-class ratio 1.0, remain sharply readable at native 300 dpi and page scale, and carry no missing or ambiguous glyph. Under R168 this numeric difference is advisory rather than a hard defect.

No mathematical, coordinate, caption, alt, current-context, or glyph/codepoint hard defect was found.
