# Render review

All listed views were generated directly from the exact official R114 PDF and actually opened by this reviewer.

- `renders/full_page_200dpi.png`: complete physical page, 1654 x 2339 px.
- `renders/full_page_native_300dpi.png`: complete physical page, 2481 x 3508 px.
- `renders/figure_crop_native_300dpi.png`: direct 300 dpi PDF clip, 2021 x 679 px, with no post-render resizing.
- `renders/figure_crop_grayscale_300dpi.png`: direct grayscale 300 dpi clip, 2021 x 679 px.
- `renders/semantic_object_overlay_300dpi.png`: final tightened 16-object overlay, 2021 x 679 px; it was reopened after the boxes were tightened to PDF-native span/vector coordinates.
- `renders/key_roi_native1x_300dpi.png`: direct 300 dpi ROI containing the smallest probability labels and the predictive formula.
- `renders/key_roi_nearest_neighbor_8x.png`: exact 8x nearest-neighbor enlargement of the preceding ROI, used only for pixel inspection.

Observed result:

- Full-page scale: the figure is immediately readable at ordinary page view and does not dominate or disappear relative to the following example.
- Native 300 dpi: Chinese, Latin, digits, Greek letters, fractions, subscripts, arrows, borders, and hatching are intact; no tofu, wrong codepoint, broken glyph, or clipped foreground is visible.
- Grayscale: category numbers, fractions, outline grouping, and the hatch for the new class-2 observation preserve the intended distinctions without relying solely on color.
- ROI: `4/9`, `3/9`, `2/9` and every base/script component of the predictive formula remain readable at native 1x; the 8x nearest-neighbor view confirms continuous glyph strokes and absence of glyph substitution.
- Page integration: the caption is complete on the same page, the following example begins with normal separation, and there is no orphaning, collision, abnormal blank region, or page-edge clipping.

R168 was applied: legacy point-size, pixel-height, and ratio thresholds are advisory and were not used as stand-alone failure grounds. The decision is based on the current PDF's actual glyph integrity, readability, balance, clipping, visible-ink relationships, geometry, and mathematical meaning.

