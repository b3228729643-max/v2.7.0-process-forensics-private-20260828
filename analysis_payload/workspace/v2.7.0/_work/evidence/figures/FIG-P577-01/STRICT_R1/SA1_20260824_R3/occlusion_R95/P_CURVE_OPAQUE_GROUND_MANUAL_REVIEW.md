# R95 native p(y) opaque-label-ground review

The source p(y) path was independently recovered from R95 vector paint sequence 26 and reconstructed before later paint on the native 300dpi grid. Every listed white label/card fill is an R95 post-curve, opacity-1 ground. For each object, the directory contains original 1×, pre-occlusion curve mask, opaque-ground mask, final-visible curve mask, covered-pixel XOR mask, and annotated overlay; every one has an 8× nearest-neighbour companion.

A positive `COVERED_PRE_CURVE_PX` is a data-curve occlusion hard failure. It is not a text-mask colour-projection issue. The native 1× and 8× files were opened for each positive-coverage relation before this review was written.

| Ground | PRE ∩ opaque ground | post-paint raw-blue absent | post-paint raw-blue present but non-semantic | semantic final curve within ground | Decision |
|---|---:|---:|---:|---:|---|
| P_LEGEND_BLUE_GROUND | 302 | 223 | 79 | 0 | FAIL |
| P_LEGEND_TEAL_GROUND | 0 | 0 | 0 | 0 | PASS |
| P_MIN_GAP_GROUND | 304 | 298 | 6 | 0 | FAIL |
| P_FILL_ANNOTATION_GROUND | 609 | 594 | 15 | 0 | FAIL |
| P_ACCEPT_CARD_GROUND | 1571 | 1571 | 0 | 0 | FAIL |
| P_REJECT_CARD_GROUND | 1039 | 1039 | 0 | 0 | FAIL |

## Set definitions and count closure

- `PRE` is the R95 vector p(y) stroke rasterised before later paint at effective contrast >=20/255: 11,609 pixels.
- `GROUND` is the union of the six later opacity-1 white label/card fills. `COVERED_XOR = PRE XOR (PRE minus GROUND) = PRE ∩ GROUND`: 3,825 pixels. The six per-ground covered counts sum to exactly 3,825, so their covered sets do not overlap.
- `SEMANTIC_FINAL` is not a subset of `PRE`: it is strict native source-blue ink within a one-pixel dilation of PRE, after excluding GROUND, to accommodate the independent vector-vs-Poppler antialias registration. It contains 8,042 pixels; 566 are in its registration halo outside PRE, while 4,133 PRE pixels are not in SEMANTIC_FINAL (3,825 opaque-ground covered + 308 uncovered-edge source-blue absences).
- Therefore the scalar count subtraction `11,609 - 8,042 = 3,567` is neither a set difference nor an occlusion metric. It must not be compared to 3,825. The literal set difference `PRE minus SEMANTIC_FINAL` is 4,133.
- Within the 3,825 covered pixels, 3,725 have no post-paint raw-blue trace. The other 100 satisfy the colour predicate only through later blue label ink and/or antialias boundary pixels (79 under the blue legend ground, 6 under the min-gap ground, 15 under the fill-annotation ground); semantic final curve pixels inside every ground are exactly zero by direct paint order and explicit ground exclusion.

Conclusion: final-visible p(y) is materially covered by the failing opaque grounds. This violates the data-curve visibility/occlusion gate even though the background has no text-contour contamination.
