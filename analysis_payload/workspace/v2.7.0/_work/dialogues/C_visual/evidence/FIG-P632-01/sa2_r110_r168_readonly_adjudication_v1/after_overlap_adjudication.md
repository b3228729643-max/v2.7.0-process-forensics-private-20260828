# FIG-P632-01 R110 / R168 overlap adjudication

- HANDOFF_ID: `C-FIG-P632-01-R110-SA2-R168-READONLY-ADJUDICATION-V1`
- Actual instance: `/root/sa2_fig_p632_r110_r168_readonly_adjudication_v1`
- Reviewer: `gpt-5.6-sol`, reasoning `xhigh`
- Visible-object denominator: 31 objects (`O01`--`O31`)
- Complete unordered-pair denominator: 465 pairs (`P001`--`P465`)
- Manual judgments present: 465 unique pair IDs
- Machine nonzero candidate pairs: 19
- Pairwise candidate pixels: 8,196
- Unique multiassigned pixels: 7,079
- Manually confirmed mask-contamination / role-alias pixels: 8,196
- Confirmed true illegal collision pixels: 0
- Unresolved candidate pairs: 0
- PIXEL_ADJUDICATION_STATUS: `MASK_CONTAMINATION_CONFIRMED`

The role-agnostic masks deliberately over-call pixels when two coarse semantic regions share a color or when valid topology requires contact. Every nonzero pair was opened in the native 300 dpi figure and the applicable nearest-neighbor 8x ROI before manual classification. `manual_pair_judgments.csv` records every pair ID, including the 446 zero-candidate pairs, and `mechanical_pixel_pair_candidates.csv` preserves the unedited machine counts.

| Pair | Pixels | Manual adjudication |
|---|---:|---|
| P031 O02--O03 | 651 | Permitted coordinate-axis origin contact. |
| P116 O05--O07 | 1,942 | Intended horizontal-slice / middle-contour crossing. |
| P143 O06--O09 | 771 | Intended vertical-slice / inner-contour crossing. |
| P145 O06--O11 | 472 | Coarse blue-region reassignment; 8x native view shows no illegal contour/marker collision. |
| P146 O06--O12 | 106 | Coarse blue-region reassignment; label leader clears the contour. |
| P172 O07--O14 | 234 | Intended continuous horizontal mapping route. |
| P213 O09--O10 | 85 | Intended vertical-slice / top-leader join. |
| P214 O09--O11 | 358 | Intended slice / marked-point contact. |
| P215 O09--O12 | 17 | Intended marked-point / leader attachment. |
| P224 O09--O21 | 47 | Intended continuous vertical mapping route. |
| P239 O10--O15 | 30 | Coarse black-region reassignment; labels are separate in native view. |
| P256 O11--O12 | 87 | Intended marker / leader attachment. |
| P278 O12--O15 | 195 | Coarse black-region reassignment; labels are separate in native view. |
| P302 O13--O21 | 1,663 | Coarse same-blue reassignment; dedicated 8x ROI shows the arrow clearing the final rho glyph. |
| P375 O18--O19 | 817 | Intended upper density / mean-guide peak contact. |
| P376 O18--O20 | 105 | Coarse green-region reassignment; mean fraction is below and clear of the axis. |
| P388 O19--O20 | 105 | Coarse guide-region reassignment; fraction has a visible gap below the baseline. |
| P445 O25--O26 | 444 | Intended lower density / mean-guide peak contact. |
| P451 O26--O27 | 67 | Coarse guide-region reassignment; fraction has a visible gap below the baseline. |

No candidate was classified from a bbox alone. Native pixels, text/object/semantic overlays, vector coordinates, mask contact sheet, complete-page integration, and the relevant 8x ROI were all used. R168 treats raster micro-differences and mask taxonomy as advisory; none of the candidate pixels represents missing content, wrong codepoint, unreadable text, clipping, illegal overlap, or wrong mathematical geometry.
