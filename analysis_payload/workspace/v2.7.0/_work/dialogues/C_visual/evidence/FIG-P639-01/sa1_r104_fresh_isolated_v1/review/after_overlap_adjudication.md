# FIG-P639-01 R104 SA1 overlap adjudication

- reviewer_type: `AI_SA1_VISUAL_REVIEW`
- human_certification: `false`
- source: `fig_v5_c04_bivariate_normal_conditionals.tex` lines 16--30
- native evidence: `render/full_page_native_300dpi.png`, `render/figure_crop_native_300dpi.png`, `render/standalone_equivalent_native_300dpi.png`
- separated evidence: `masks/*_mask_native.png`, `pairs/all_unordered_pair_measurements.csv`, `pairs/critical_pair_inventory.csv`, `render/actual_object_overlay_native_300dpi.png`
- 1x/8x evidence: `crops_1x`, `crops_8x`, `pairs/PAIR-*_critical_1x.png`, `pairs/PAIR-*_critical_8x.png`

## Manual outcome

All 496 unordered object pairs were reviewed by ID. No text-text or text-graphic pair shares a native foreground pixel. The nearest reviewed text clearances are 12 px for T16/T17, 14 px for T19/T20, 16 px for the closest x-tick/tick-mark pairs, and 18--19 px for note text to G12 border. These exceed the applicable 4/3/5 px hard floors.

The mechanical all-pair scan reports 28 graphic-graphic pairs with 843 summed pairwise shared native pixels. Every one was individually inspected in `manual_critical_pair_review.csv`. They are direct vector/raster manifestations of intended geometry: tick-to-axis junctions, axis-to-arrowhead junctions, the orthogonal origin, filled-area baseline closure, near-zero density endpoints, mean-line starts at the baseline, one density-curve crossing, and mean-reference/curve intersections. None is a text collision, illegal obscuration, wrong relationship, or mask artifact.

Accordingly:

- MANDATORY_ILLEGAL_PAIR_OVERLAP_CANDIDATE_PIXEL_COUNT = 0
- ALL_UNORDERED_PAIR_NATIVE_SHARED_PIXEL_SUM = 843
- ALLOWED_GEOMETRIC_RELATION_SHARED_PIXEL_SUM = 843
- MASK_CONTAMINATION_PIXEL_COUNT = 0
- OVERLAP_PIXEL_COUNT = 0
- UNRESOLVED_PAIR_COUNT = 0
- PIXEL_ADJUDICATION_STATUS = CLEAR

No candidate was re-labeled as mask contamination; the shared pixels are real but lawful geometric relations. The detailed per-ID reason is retained rather than using a global/default PASS.
