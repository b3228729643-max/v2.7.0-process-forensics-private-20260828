RESULT: FAIL

# FIG-P186-01 — SA1 strict R1B independent recheck

This is an independent, read-only SA1 result. It is not a candidate PASS.

## Scope and native basis

- Official input: physical page 200 of the assigned continuous full-book PDF.
- Native extraction: 300 dpi, 2481 x 3508 px, unrotated RGB; see `renders/official_p200_300dpi.png`.
- Source/reading context: only the assigned figure source and the assigned chapter insertion/caption/read-sentence context.
- Standalone source-build: successful XeLaTeX evidence build under `build/`; it imports the live source without modifying it.
- All geometry values below come from 1:1 native pixels or source coordinates transformed and checked against those pixels. The fit-page image is visual-review-only.

## Blocking findings

1. **Effective source type size fails.** Direct labels T01--T03 and the normal label T04 explicitly use `\fontsize{9.2pt}{11pt}\selectfont`; the minimum is 9.5 pt. Four figure text elements therefore fail the absolute effective-size hard gate.
2. **Boundary-label clearance fails.** Native measurement of `w^T x+b=0` (T03) to the separator is **1.000 px**, below the required 3 px. The key 1:1 ROI is `roi/boundary_label_native_1x.png`.
3. **A negative sample is on the positive side.** For the source separator `y=-0.68x+0.2`, take `g(x)=0.68x+y-0.2`. The source's teal triangle `(2.10,-1.05)` yields `g=+0.178`, not `<0`; its centre is **25.110 native px** into the positive side. The key 1:1 ROI is `roi/misclassified_triangle_native_1x.png`.

## Checks completed

- All six text elements, axes, normal arrow, separator, two region fills, all five blue disks, and all five teal triangles were enumerated.
- Pixel-category checks resolve the CJK characters at 34 px, lower-case math at 19 px, natural superscripts at 19--25 px, `0` at 25 px, and base operators at 22--24 px. The hard failure is the explicit 9.2 pt source size.
- Same-role source-size ratios are 1.000; blue-disk and teal-triangle same-class ratios meet the required `[0.92,1.08]` interval. There is one panel, so cross-panel checks are N/A.
- Region-fill and separator endpoint margins are 8.526 px (>=6); normal/axis text-to-arrow gaps are 20.000, 32.202, and 27.203 px; minimum text-to-text gap is 111.328 px.
- The normal vector passes independent direction verification: cross product `-0.000600`, positive dot product `1.762600` with the separating-line normal.
- Caption and adjacent reading sentence are present and page placement is clean in local 100%, full-page 100%, fit-page, and native grayscale review. The wrong teal triangle nevertheless contradicts the caption/body geometric explanation.

## Required correction before any recheck

Raise the direct/normal label font declaration to at least 9.5 pt; move the boundary label sufficiently away from the separator to create at least a 3 px native gap; and relocate or reclassify `(2.10,-1.05)` so its score is negative (for example, at fixed `x=2.10`, use `y<-1.228`). Then perform a fresh independent render-and-measure review.

See `01_scope_and_standalone_build.md` through `05_evidence_index.md` and the `metrics/` CSV files for the complete R1B evidence set.
