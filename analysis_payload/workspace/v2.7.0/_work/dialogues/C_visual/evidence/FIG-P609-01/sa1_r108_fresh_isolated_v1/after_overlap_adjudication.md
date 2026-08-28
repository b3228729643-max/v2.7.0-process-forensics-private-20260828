# Pair and overlap adjudication

- Semantic visible-object denominator: `N=32`.
- Exhaustive unordered pairs: `C(32,2)=496`; every pair appears once in `all_unordered_pairs.csv`.
- Broad-phase bbox intersections: 14.
- Actual independent semantic foreground-mask pixel candidates after native 300 dpi inspection: 0.
- `OVERLAP_CANDIDATE_PIXEL_COUNT=0`.
- `MASK_CONTAMINATION_PIXEL_COUNT=0`.
- `OVERLAP_PIXEL_COUNT=0`.
- `PIXEL_ADJUDICATION_STATUS=CLEAR`.
- `CLIP_PIXEL_COUNT=0`.

The 14 bbox intersections are not foreground collision candidates:

| Pair(s) | Manual classification and evidence |
|---|---|
| T16-G03 | Text over a designated pale background fill; background is excluded from illegal foreground overlap. |
| T16-G04 | Coarse series bbox only. Native 1x and nearest8x show the callout above the k=4..6 stems/markers with no ink sharing. |
| T18/T19/T20/T21/T22/T23-G06 | Interior containment in the right-panel bbox. The nearest8x border ROIs show text/formula ink separated from the border. |
| G01-G02 | Intended x/y-axis junction, not reader text overlap. |
| G01-G03 | Axis boundary adjacent to background fill; the fill is not independent foreground. |
| G01-G04 | Intended data stems meeting the zero baseline; no text or formula is involved. |
| G01-G05 | Intended cutoff line meeting the x-axis baseline; no text or formula is involved. |
| G03-G04 | Data series drawn over its designated window background. |
| G03-G05 | Cutoff boundary drawn at the edge of its designated background. |

The smallest positive vector bbox gap is T19-T20 at 3.25 px, 0.75 px below the nominal 4 px text-bbox target. Direct native-raster measurement finds 20 completely white raster rows between their actual ink and a 49.4 px nearest-ink Euclidean distance. Under the supplied R168 rule, this sub-pixel-to-one-pixel bbox-metadata shortfall is advisory only; it is not a true collision, clipping event, or readability defect. The next-smallest positive text/graphic gaps are 10.71 px (tick to x-axis) and 16.00 px (y tick to y-axis), both above their 3 px requirement. T21-T22 and T22-T23 have 13.92 px and 14.62 px bbox gaps. T16-G05 has 25.42 px.

All 496 pair rows were reviewed through the exhaustive pair table plus the object/span overlays. The 14 intersections and the smallest positive-gap neighborhood were individually rechecked in native and nearest8x views; all remaining pairs have larger separation and no forbidden semantic relationship.

