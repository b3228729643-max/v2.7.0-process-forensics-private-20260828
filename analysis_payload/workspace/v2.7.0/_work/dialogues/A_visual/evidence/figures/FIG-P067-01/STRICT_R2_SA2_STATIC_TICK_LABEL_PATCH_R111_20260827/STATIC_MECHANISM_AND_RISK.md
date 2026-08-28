# Static mechanism and risk account

## Mechanism

The automatic label at the unchanged 0.30 y-tick is suppressed, while the automatic tick itself remains in `ytick={0,.15,.30,.35}`. The same visible text `0.3` is replayed at the same axis coordinate `(axis cs:.45,.30)` with the existing 8.6/10.3 pt font and a local `yshift=-4.5pt`. The 0.35 automatic label and tick remain unchanged.

No PMF or CDF coordinate, probability value, cumulative level, axis meaning, panel order, open/closed endpoint, annotation, caption, font declaration, color, stroke, or unrelated geometry is changed.

## Native-clearance projection

The accepted R111 native-300-dpi boxes were:

- 0.35: vertical PDF interval 135.3163--143.8842 pt.
- 0.30: vertical PDF interval 139.8743--148.4422 pt.
- 0.15: vertical PDF interval 153.5383--162.1062 pt.

A 4.5 TeX-pt downward shift is approximately 4.48 PDF pt at the same engine scale. The projected 0.30 interval is therefore about 144.36--152.93 PDF pt. This gives approximately 0.48 PDF pt (about 2.0 native pixels) to 0.35 above and 0.61 PDF pt (about 2.5 native pixels) to 0.15 below. Both former overlap and lower-neighbour collision are statically projected absent. Rendering is still required to verify real ink clearance.

## Regression boundary

- Horizontal placement remains at the y-axis with a 2 pt label gap.
- The replayed label remains well inside the existing left page margin and does not move toward the caption.
- The change cannot alter the four PMF stems/markers, CDF staircase, guide lines, axes, or page geometry.
- This is a build-slot request, not a PASS claim.

