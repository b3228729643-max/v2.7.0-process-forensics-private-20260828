# FIG-P660-01 SA1 individualized visible-object review

Reviewer identity: `C-FIG-P660-01-R111-SA1-FRESH-ISOLATED-V1` (`gpt-5.6-sol`, `xhigh`).

Review order: the reviewer first opened the R111 native-300-dpi page, 200-dpi page-integration view, native-300-dpi local/standalone views, grayscale view, object/text overlays, foreground/text/geometry masks, glyph atlas, native1x critical ROIs, their nearest-neighbor8x versions, and the six latest critical-pair sheets. The following judgments were written only afterward. Object identities are frozen by `machine/frozen_visible_object_denominator.csv`.

- `G01` — simplex interior fill: the pale triangular field is continuous, bounded by the three intended sides, and remains subordinate to grid, guides, marker, and text. Judgment: acceptable.
- `G02` — left boundary: the edge joins `e1` to `e3` without a break, overshoot, clipping, or contact with either vertex label. Judgment: acceptable.
- `G03` — right boundary: the edge joins `e3` to `e2` cleanly and leaves the point-vector label outside with generous clearance. Judgment: acceptable.
- `G04` — bottom boundary: the baseline is continuous and separated from `theta3`, both bottom vertex labels, and the caption. Judgment: acceptable.
- `G05` — grid family A at 0.2: the segment terminates on the intended simplex sides and participates in the regular 0.2 lattice without text contact. Judgment: acceptable.
- `G06` — grid family B at 0.2: the horizontal level is straight, consistently light, and intersects only lattice geometry by construction. Judgment: acceptable.
- `G07` — grid family C at 0.2: the diagonal is aligned with the equilateral grid and has no label or marker collision. Judgment: acceptable.
- `G08` — grid family A at 0.4: the diagonal reaches its two intended endpoints and keeps the foreground hierarchy below the dashed guides. Judgment: acceptable.
- `G09` — grid family B at 0.4: the horizontal is evenly rendered and its geometry-only crossings are unambiguous. Judgment: acceptable.
- `G10` — grid family C at 0.4: the diagonal has the expected parallel family orientation and no illegal foreground contact. Judgment: acceptable.
- `G11` — grid family A at 0.6: the segment remains within the simplex and is visually distinct from the component guides. Judgment: acceptable.
- `G12` — grid family B at 0.6: the horizontal level is regular, light, and does not obscure the central point. Judgment: acceptable.
- `G13` — grid family C at 0.6: the diagonal is complete and participates only in intended lattice crossings. Judgment: acceptable.
- `G14` — grid family A at 0.8: the short upper segment is present, aligned, and visibly connected to its correct sides. Judgment: acceptable.
- `G15` — grid family B at 0.8: the upper horizontal is present and separated from the top vertex description. Judgment: acceptable.
- `G16` — grid family C at 0.8: the short upper diagonal is present and has no clipping or accidental text contact. Judgment: acceptable.
- `G17` — `theta1` projection guide: the dashed segment runs from the marker toward edge `e2-e3`; the recomputed normalized distance is exactly 0.2 and the `theta1` label is clear. Judgment: acceptable.
- `G18` — `theta2` projection guide: the dashed segment runs from the marker toward edge `e1-e3`; the recomputed normalized distance is exactly 0.3 and the `theta2` label is clear. Judgment: acceptable.
- `G19` — `theta3` projection guide: the vertical dashed segment reaches the bottom edge; the recomputed normalized distance is exactly 0.5 and the lower label remains separate. Judgment: acceptable.
- `G20` — theta marker: the dark blue disk is fully rendered, centered at the three guide origins, and is the intended geometric focal point. Judgment: acceptable.
- `G21` — definition card: the rounded border is complete; measured text-to-border clearance is 32 px or more for both formula lines. Judgment: acceptable.
- `G22` — face-classification card: the border is complete; all three statements remain inside with measured minimum edge clearance 23 px. Judgment: acceptable.
- `G23` — conclusion card: the border is complete; its three lines remain inside with measured minimum edge clearance 34 px and retain hierarchy in grayscale. Judgment: acceptable.
- `T01` — `theta2=.3`: native1x and nearest8x show the exact mathematical glyphs, a legible 36-px group height, and 34.482-px ink-bbox clearance from its guide. Judgment: readable and correct under R168.
- `T02` — `theta1=.2`: native1x and nearest8x show the correct codepoints, a legible 36-px group height, and 41.725-px clearance from its guide. Judgment: readable and correct under R168.
- `T03` — `theta3=.5`: the lower component label is fully visible, 36 px high as a group, and 48.795 px from its guide bbox. Judgment: readable and correct under R168.
- `T04` — `theta=(0.2,0.3,0.5)`: the tuple is exact, fully rendered, and separated from both marker and right boundary; its value sums to one. Judgment: acceptable.
- `T05` — `e3=(0,0,1)`: the top-vertex formula has the correct basis vector and no glyph loss; the two-line ROI shows a real empty raster gap before `T06`. Judgment: acceptable.
- `T06` — `category 3 certain`: the Chinese description is exact, 35 px high, and five wholly empty native rows separate it from `T05`. Judgment: acceptable.
- `T07` — `e1=(1,0,0)`: the left-vertex formula matches the barycentric basis and remains 30 px from the nearest boundary bbox. Judgment: acceptable.
- `T08` — `category 1 certain`: the description is exact, visually distinct, and six wholly empty native rows separate it from `T07`. Judgment: acceptable.
- `T09` — `e2=(0,1,0)`: the right-vertex formula matches the barycentric basis and remains 30 px from the nearest boundary bbox. Judgment: acceptable.
- `T10` — `category 2 certain`: the description is exact, visually distinct, and six wholly empty native rows separate it from `T09`. Judgment: acceptable.
- `T11` — closed-simplex definition: `Delta^2`, membership in `R^3`, nonnegativity, and sum-to-one are all rendered with the correct mathematical symbols and no tofu. Judgment: mathematically and typographically correct.
- `T12` — `dim(Delta^2)=2`: the dimension statement follows from one affine constraint in ambient dimension three; four wholly empty native rows separate it from `T11`. Judgment: acceptable.
- `T13` — interior statement: the text correctly identifies strictly positive components and is 36 px high. Judgment: acceptable.
- `T14` — edge statement: the text correctly identifies one zero component and is separated from adjacent lines by visible blank raster rows. Judgment: acceptable.
- `T15` — vertex statement: the text correctly identifies one category probability equal to one; no truncation or line collision is visible. Judgment: acceptable.
- `T16` — conclusion line 1: the first clause is complete, 37 px high, and remains subordinate to the geometric focal point. Judgment: acceptable.
- `T17` — conclusion line 2: the freedom-count and triangle-position clause is complete, 36 px high, with 10-px ink-bbox separation from `T16`. Judgment: acceptable.
- `T18` — conclusion line 3: `barycentric coordinates` closes the claim accurately, is 34 px high, and has 11-px ink-bbox separation from `T17`. Judgment: acceptable.
- `T19` — caption tag `Figure 34.4`: the tag is bold, complete, correctly numbered, and 43 px from the nearest bottom description. Judgment: acceptable.
- `T20` — caption line 1: the rendered text exactly matches the first part of the current source caption and is fully inside the page. Judgment: acceptable.
- `T21` — caption line 2: the rendered text exactly completes the current source caption, including `Dirichlet`, and is separated from `T20` by 14 px at the ink-bbox level. Judgment: acceptable.

Object denominator result: all 44 frozen visible objects were individually reviewed; no missing object, wrong glyph, unreadable object, true clipping, illegal overlap, or semantic/geometry defect was found.
