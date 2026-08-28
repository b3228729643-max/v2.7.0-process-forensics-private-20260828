# Static projection and regression boundary

The original boundary/label collision is removed by draw order rather than by changing geometry. The convex-set path is drawn first. The domain-label node is drawn later with `fill=white`, `fill opacity=1`, and `text opacity=1`; therefore boundary ink underneath the label node is fully occluded and cannot share rendered pixels with the `C` glyph or any other glyph in that node.

The `inner sep=1.2pt` creates an opaque protection band outside the text box. At native 300 dpi, `1.2 TeX pt × 300 / 72.27 = 4.98 px`, so the predicted minimum protective band is approximately five pixels on each side of the text box.

Regression boundary:

- unchanged node coordinate `(3.20,1.86)` and `anchor=north east`;
- unchanged label text `凸可行域 $C$`, font `9.2pt/11.2pt`, and text color;
- unchanged convex-set path coordinates, fill, stroke, and segment;
- unchanged points/markers, interpolation formula, statement box/formula, caption, chapter prose, labels, numbering, shared macros, and build entry;
- no coordinate displacement, global scaling, font reduction, or change to mathematical semantics.

This is a static projection only. A new standalone PDF must verify the old critical pair, all label glyphs, visible boundary continuity, neighboring objects, grayscale, caption, and page integration before any PASS claim.
