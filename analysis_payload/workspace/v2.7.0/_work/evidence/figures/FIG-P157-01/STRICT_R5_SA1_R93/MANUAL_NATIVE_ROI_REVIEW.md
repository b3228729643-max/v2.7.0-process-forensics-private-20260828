# Manual native 1:1 ROI review — FIG-P157-01 R93

All ROIs listed below are direct crops of the 2481 x 3508 Poppler 300 dpi page. They were not resized. Red/blue nearest-point overlays are supplemental; the `raw_1to1_300dpi` crops were inspected as the visual authority.

| Pair | Overlap | Clearance (px) | Manual native-pixel finding |
|---|---:|---:|---|
| T02 validation label / G02 validation curve | 0 | 163.865799 | White-backed label is fully separated from the dashed curve. |
| T04 training label / G05 leader | 0 | 26.570661 | Leader terminates below-left of the label; it does not enter any glyph. |
| T04 training label / G01 training curve | 0 | 59.539903 | Solid curve remains well below the label. |
| T03 minimum label / G04 marker | 0 | 15.000000 | A clean background row separates gold text from the filled point; exact nearest pixels are visible in the overlay. |
| T03 minimum label / G02 validation curve | 0 | 15.524175 | Dashed curve remains below the label; no dash enters the glyphs or their white backing. |
| T05 selection label / G03 reference line | 0 | 24.738634 | Dashed reference ends at the x-axis; label starts below it with clear white space. |
| T05 selection label / G06 x-axis arrow | 0 | 21.000000 | Visible gap between the x-axis stroke and top ink of the selection label. |
| T09 x-axis title / G06 x-axis arrow | 0 | 201.000000 | Title is separated by the selection and region-label tiers; no crowding. |
| T01 y-axis title / G07 y-axis arrow | 0 | 31.000000 | Rotated CJK title has a clear gutter from the vertical axis. |
| T06 underfit label / G06 x-axis arrow | 0 | 111.000000 | Clear vertical separation. |
| T07 appropriate label / G06 x-axis arrow | 0 | 111.000000 | Clear vertical separation; nearby selection label is also non-overlapping. |
| T08 overfit label / G06 x-axis arrow | 0 | 111.000000 | Clear vertical separation. |

The mask-diagnostic raw ROI was also inspected. The four superseded coordinates `(1352,941)`--`(1355,941)` sit on the top antialias edge of the marker, not in the T03 glyph mask. Corrected current overlap is empty.

