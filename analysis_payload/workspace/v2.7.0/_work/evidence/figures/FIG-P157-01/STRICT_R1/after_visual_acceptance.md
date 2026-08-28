RESULT: FAIL

# FIG-P157-01 — four-view visual acceptance record

Scope: official `main_full.pdf`, physical page 170, figure 10.1 only.  This is an independent SA1 record.  Review used the direct, unresampled Poppler outputs below; any display proxy was not used for geometric measurement.

| Required view | Evidence | Native inspection finding |
|---|---|---|
| Full page / fit | `full_page_200dpi.png` | Page hierarchy and surrounding reading order are stable; no figure/caption overflow into the paragraph or example block. |
| Full page / 100% coordinates | `official_page_170_300dpi.png` (2481×3508) | Pixel work used this exact file, not a screenshot or resized preview. |
| Figure-only / 100% | `figure_crop_300dpi.png`, `standalone_300dpi.png`, and `roi_01`–`roi_05` | The validation-curve label crosses the rising dashed curve; `roi_05_validation_label_curve_conflict_100pct.png` marks the 134 independently located collision pixels in red. |
| Grayscale / 100% | `figure_grayscale_300dpi.png` | Solid training curve and dashed validation curve remain distinguishable, but the label/curve collision is still visible and breaks the intended clean reading path. |

## Hierarchy and page fusion

- The single-panel chart has a clear left-to-right complexity axis and a plausible low-to-high error range.  Caption placement and the immediately following reading sentence are visually integrated with the page.
- Axis titles are more prominent than the curve labels, but their measured 1.122 role ratio is inside the prescribed `[1.00,1.18]` range; no isolated oversized ordinary label was found.
- All ordinary CJK labels remain readable at native size.  The figure does not rely on colour alone: solid versus dashed curves survive grayscale.

## Blocking visual finding

`FIG-P157-01-T02` (`验证误差：先降后升`) and `FIG-P157-01-G02` (validation-error dashed curve) have zero native-pixel clearance and 134 foreground intersection pixels under the §9.2.1 threshold.  The white annotation plate is only 90% opaque and does not create the required 3 px ink-to-curve separation.  This is an illegal text–data-curve collision, not an acceptable label overlay.

Therefore the visual result is FAIL.  Reposition the T02 label to a genuinely empty plot region, then regenerate the official page and all 300 dpi evidence; no current view is accepted as a final visual candidate.
