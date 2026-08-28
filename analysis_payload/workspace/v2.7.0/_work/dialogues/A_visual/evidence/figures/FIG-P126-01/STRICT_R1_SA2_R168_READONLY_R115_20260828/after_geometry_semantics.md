# Geometry, mathematics, caption, chapter, grayscale, and page integration

## Coordinate-descent geometry and mathematics

The current source draws four ellipses as `(a*cos(t), b*sin(t))` with no rotation. Their principal axes are exactly the displayed `x_1` and `x_2` axes. The current chapter, immediately before and after the figure, says the zig-zag diagnoses coordinate-system mismatch and specifically attributes frequent zig-zagging to an appreciable angle between the ellipse principal axes and the coordinate axes. The rendered figure therefore contradicts its defining chapter explanation.

The chapter also defines the displayed method by exact one-coordinate minimization,
`x_j <- argmin_z f(x_1,...,z,...,x_d)`. For a centered strictly convex quadratic having the displayed axis-aligned elliptical level sets, an exact `x_2` update from `q0=(-3.20,1.75)` would set `x_2=0`, not the displayed `q1=(-3.20,0.85)`, and the next exact `x_1` update would set `x_1=0`, not the displayed `q2=(-1.65,0.85)`. The seven-step path is thus not the exact coordinate-minimization trajectory of the contours it overlays.

The caption alone correctly states that each drawn substep changes only one coordinate and that the path approaches the optimum. That local truth does not repair the source/chapter geometric contradiction. `MATH_SEMANTICS_PASS=false` and `TEXT_CONSISTENCY_PASS=false` are hard under R168.

## Glyphs, readability, balance, and clipping

All extracted visible glyphs/codepoints match the source: mathematical italic x is U+1D465, the optimum asterisk is U+2217, digits and subscripts are correct, both Chinese legend labels are complete, and the full Chinese caption is complete. No tofu, missing glyph, wrong codepoint, or clip was observed. `CLIP_PIXEL_COUNT=0`.

The source-declared 8.6/9.2/9.4 pt values and machine ink-height/ratio numbers are retained as advisory evidence only. At native page scale and in every 8x ROI the labels remain actually readable, and there is no severe role imbalance attributable solely to size. R168 therefore does not turn those legacy numeric values into a separate hard failure.

## Grayscale

The plot body retains a visible solid-horizontal versus dashed-vertical distinction. The legend does not: final PDF drawing sequences 33 and 34 each contain two adjacent collinear segments with no gap, and both have the same grayscale intensity. Thus the source-declared dash for the `更新 x_2` legend swatch does not survive as a reader-visible legend distinction. `GRAYSCALE_PASS=false`.

## Page integration

The target is uniquely located on R115 physical page 137, printed page 124. The figure, legend, caption, following explanatory paragraph, and next section occupy the page cleanly. No figure/caption clipping, overflow, page imbalance, or disruptive whitespace was observed. `PAGE_INTEGRATION_PASS=true`.

