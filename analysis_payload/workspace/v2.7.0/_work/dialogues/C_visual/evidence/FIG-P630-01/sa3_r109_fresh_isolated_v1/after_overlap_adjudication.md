# FIG-P630-01 R109 independent overlap adjudication

- Reviewer: SA3_FRESH_ISOLATED (`gpt-5.6-sol`, `xhigh`)
- Official page: physical PDF page 680, printed page 667
- Denominator: 17 visible semantic objects (`O01`-`O17`)
- Unordered-pair closure: 136/136 pairs (`P001`-`P136`) manually observed after opening the native 300 dpi crop, semantic overlay, text overlay, native1x ROI sheet, and nearest-neighbor 8x ROI sheet.
- Machine tables contain geometry only. All reviewer observations, decisions, booleans, and notes are authored in `after_overlap_report.csv`; the builder has no manual decision fields and never writes this file.

## Result

No unordered pair shows a true illegal collision. Fourteen pairs are intentional topological endpoint attachments: `P014`, `P024`, `P029`, `P038`, `P039`, `P052`, `P053`, `P065`, `P066`, `P069`, `P077`, `P078`, `P088`, and `P099`. They connect a leader or directed edge to its declared source/target node boundary; the native1x and nearest8x ROIs show that none touches label ink or creates an ambiguous direction.

All remaining 122 pairs are visibly disjoint. The tightest non-topological object separation is `P108` (boundary banner to caption), with 13.14 native-300-dpi pixels between vector bounding boxes and clean raster whitespace. The tightest reader-text pair is the two-line full-conditional label (`T06`/`T07`): thresholded ink rows end at y=1701 and begin at y=1705, so the actual ink clearance is exactly 4 px and meets the text-text minimum.

No mask contamination cluster and no unresolved cluster exists. Native 300 dpi inspection shows complete arrowheads, borders, formulas, and caption glyphs. Nearest8x views show normal antialiasing only; R168 treats low-outline/micro-raster metadata as advisory, but no advisory discrepancy is needed to excuse a substantive defect here.

OVERLAP_CANDIDATE_PIXEL_COUNT = 0

MASK_CONTAMINATION_PIXEL_COUNT = 0

OVERLAP_PIXEL_COUNT = 0

PIXEL_ADJUDICATION_STATUS = CLEAR

CLIP_PIXEL_COUNT = 0

MIN_TEXT_CLEARANCE_PX = 4

PIXEL_DISPUTE_REQUIRED = false
