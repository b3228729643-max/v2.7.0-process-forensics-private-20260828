# Native raster and four-view protocol

## Official page extraction

The assigned `main_full.pdf` physical page 200 was extracted directly with Poppler at 300 dpi. PDF metadata reports an unrotated A4 page (595.276 x 841.89 pt). The resulting authoritative raster is:

- `renders/official_p200_300dpi.png`
- 2481 x 3508 pixels, RGB, 299.9994 dpi in both axes.

No geometry measurement uses a resized image. All bounding boxes, gaps, component sizes, and affine checks use this native page or pixel-exact crops from it.

## Required review views

| View | Artifact | Geometry use |
|---|---|---|
| Whole page at 100% | `renders/official_p200_300dpi.png` | Yes |
| Local 100% | `roi/figure_and_caption_native_1x.png`, `roi/plot_native_1x.png`, `roi/labels_and_normal_native_1x.png`, `roi/boundary_samples_native_1x.png` | Yes |
| Key native 1:1 ROIs | `roi/boundary_label_native_1x.png`, `roi/misclassified_triangle_native_1x.png` | Yes |
| Fit-page | `renders/official_p200_fitpage_review_only.png` | No; visual review only |
| Grayscale native | `renders/official_p200_300dpi_grayscale_native.png` | Yes; no resampling |

The fit-page review is not used to relax a hard gate. Since hard gates do not all pass, no reduced-size readability concession is applied.
