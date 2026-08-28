# RUN6 evidence superseded

Status: **SUPERSEDED — not terminal evidence**.

Root review of the previous contact sheets found that glyph masks were formed by
cropping every non-white final-page pixel in each broad PDF character bbox. This
admitted underlying hatch, curve, and texture ink into text masks, notably in
E026 (`纹理缺失区：q_L=0<p`). Consequently the former glyph mapping PASS count,
pixel-height counts, D/E ratios, relationship calculations, and active-package
indexes are invalidated rather than silently reused.

`RUN7_TEXT_ISOLATION/` will replay the frozen PDF's text operators into a
text-only layer at native 300 dpi, intersect that layer with the official final
300-dpi page for final visibility, subtract and account for later opaque
occlusion, and then perform an all-record contamination gate and manual review.
The independent E016 source-order / opaque-halo finding remains open and is not
erased by this evidence correction.
