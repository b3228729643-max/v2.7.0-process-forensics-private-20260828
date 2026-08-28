# Decisive final-view opening ledger

All entries below were actually opened from the final machine-evidence generation before the manual ledgers and verdict were closed.

| View | Manual observation |
|---|---|
| `full_page_300dpi.png` | Physical page 713 is complete; figure, caption, following derivation, theorem, header, footer, and margins are integrated without clipping or severe imbalance. |
| `full_page_grayscale_native_300dpi.png` | Page hierarchy survives grayscale; warning/result distinction and figure/text separation remain readable. |
| `full_page_figure_location_overlay_300dpi.png` | Red frame encloses exactly the current figure and caption and excludes following body derivation. |
| `figure_caption_native_300dpi.png` | Final color crop shows the complete two-panel figure and both caption lines. |
| `figure_caption_grayscale_native_300dpi.png` | Native grayscale preserves titles, formulas, arrow, borders, note, and warning hierarchy. |
| `object_bbox_overlay_300dpi.png` | O01–O22 boxes cover every visible semantic object in the frozen denominator. |
| `semantic_role_overlay_300dpi.png` | Text/formula, geometry, background container, divider, result, warning, and caption categories correspond to visible roles. |
| `text_measurement_overlay_300dpi.png` | E01–E18 boxes track the final ink; no measured text is missing or cut by its mapped box. |
| `reading_order_overlay_300dpi.png` | The intended left 1–6, right 7–12, caption 13–15 order is recoverable and agrees with the figure's structure. |
| `closest_pair_numeric_risk_overlay_300dpi.png` | The only logical-bbox shortfall is localized to derivative O15 versus result border O16; no visible overlap is present. |
| `text_union_mask_300dpi.png` | Reader-text/formula foreground is cleanly separated and complete. |
| `geometry_union_mask_300dpi.png` | Brace, divider, arrow, and both bordered containers are continuous and separate from text. |
| `visible_object_union_mask_300dpi.png` | Union mask contains every denominator object without crop-edge contact. |
| `rois/R01_brace_note_native1x.png` | Brace note reads cleanly at native raster scale. |
| `rois/R01_brace_note_nearest8x.png` | Note and brace have intact outlines and visible blank separation. |
| `rois/R02_left_term_content_native1x.png` | All three term boxes and their formulas are readable as a balanced group. |
| `rois/R02_left_term_content_nearest8x.png` | Indicator, Delta, K-1, eta/alpha subscripts, and sufficient-statistic subscripts are intact. |
| `rois/R03_right_derivation_native1x.png` | Log-partition, arrow, derivative, result border, and expected-log formula form an unambiguous chain. |
| `rois/R03_right_derivation_nearest8x.png` | O15/O16 retain seven blank native pixels; no collision, tofu, or clipping. |
| `rois/R04_warning_formula_native1x.png` | Warning is readable and its red box is intact. |
| `rois/R04_warning_formula_nearest8x.png` | Not-equal sign, expectations, Theta glyphs, and subscripts are exact and separated. |
| `rois/R05_caption_math_native1x.png` | Caption label and both lines are readable with correct wrapping. |
| `rois/R05_caption_math_nearest8x.png` | Mixed CJK/math codepoints, identity, punctuation, and warning phrase are intact. |

No decisive view or ROI remains unopened.
