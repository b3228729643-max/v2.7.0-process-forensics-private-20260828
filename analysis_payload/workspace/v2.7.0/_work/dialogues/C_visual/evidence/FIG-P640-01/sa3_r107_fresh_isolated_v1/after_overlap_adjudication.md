# FIG-P640-01 SA3 overlap adjudication

REVIEWER = SA3-R107-FRESH-ISOLATED-V1  
OFFICIAL_PDF = R107 physical page 690 / printed 677 / Figure 33.7  
NATIVE_GRID = 2481x3508 at direct 300 dpi  
OVERLAP_CANDIDATE_PAIR_COUNT = 12  
OVERLAP_CANDIDATE_PIXEL_COUNT = 5843  
MASK_CONTAMINATION_PIXEL_COUNT = 5843  
OVERLAP_PIXEL_COUNT = 0  
UNRESOLVED_PIXEL_COUNT = 0  
PIXEL_ADJUDICATION_STATUS = MASK_CONTAMINATION_CONFIRMED  
PIXEL_ARBITER_MODEL = NOT_USED  
PIXEL_ARBITER_REASONING = NOT_USED

All 12 candidates were opened individually at native 1x and 8x nearest-neighbour scale. Each evidence image contains the unchanged original ROI, separated A-red and B-blue raw masks, and a magenta intersection pane. The machine detector intentionally compares every independent semantic leaf; therefore backgrounds and intended line-line/data-marker connections enter its candidate total. For the canonical illegal-overlap count these are false positives and are recorded as `MASK_CONTAMINATION` with a more precise subtype in `after_overlap_report.csv`.

| Pair | Raw px | Classification | Evidence-specific adjudication |
|---|---:|---|---|
| PAIR-0010 | 2 | MASK_CONTAMINATION / opaque background edge | The real white backing from source lines 47-48 covers the curve from line 41 at the rectangle edge; no independent final foregrounds share pixels. |
| PAIR-0021 | 2070 | MASK_CONTAMINATION / background-text composition | Limit text is intentionally painted on its own documented white node fill; the fill is background rather than a border or foreground object. |
| PAIR-0036 | 15 | MASK_CONTAMINATION / opaque background edge | Endpoint backing from lines 44-46 covers the gold line at the label edge; text-to-final-curve clearance is assessed separately as 8.944 px for the tighter endpoint relation. |
| PAIR-0048 | 1382 | MASK_CONTAMINATION / background-text composition | Endpoint coordinate ink is intentionally painted atop its white backing; neither element is mis-mapped. |
| PAIR-0054 | 2203 | MASK_CONTAMINATION / intentional line-line geometry | The rho=.20 curve begins at (0,1) and rapidly reaches the native y=0 raster floor; these are valid chart-line contacts. |
| PAIR-0055 | 51 | MASK_CONTAMINATION / intentional line-line geometry | The rho=.70 curve begins at (0,1) and approaches the x-axis; no text or unrelated object is touched. |
| PAIR-0056 | 5 | MASK_CONTAMINATION / intentional line-line geometry | The rho=.95 curve shares only its exact ACF(0)=1 start with the frame. |
| PAIR-0079 | 55 | MASK_CONTAMINATION / intentional data coincidence | The .20 and .70 analytic curves share ACF(0)=1 and near-zero native raster positions; their identities remain visually distinct. |
| PAIR-0080 | 1 | MASK_CONTAMINATION / intentional data coincidence | The .20 and .95 curves share one exact start pixel and immediately diverge. |
| PAIR-0103 | 2 | MASK_CONTAMINATION / intentional data coincidence | The .70 and .95 curves share two start pixels and immediately diverge. |
| PAIR-0208 | 1 | MASK_CONTAMINATION / intentional line-line geometry | ESS(0)=1 lies exactly at the B y-axis start; this is the intended mathematical coordinate. |
| PAIR-0226 | 56 | MASK_CONTAMINATION / intentional curve-marker connection | Source lines 41-43 place the open marker on the curve at (.99,.0100499975); its ring and white center remain recognizable. |

The 5843 classified pixels equal the machine candidate sum exactly. No candidate is unresolved, no candidate contains a true illegal collision, and no arbiter escalation is triggered.
