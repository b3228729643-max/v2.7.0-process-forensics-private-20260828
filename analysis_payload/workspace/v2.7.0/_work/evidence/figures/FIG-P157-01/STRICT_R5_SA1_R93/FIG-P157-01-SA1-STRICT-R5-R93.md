# FIG-P157-01 — independent SA1 strict review on official R93

RESULT: PASS

FIGURE_ID: FIG-P157-01

OFFICIAL_ARTIFACT: `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\build\strict_current_r93_fullbook\main_full.pdf`

OFFICIAL_PAGE: physical page 170 / printed page 157 / Figure 10.1

SOURCE_READ_ONLY: `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\绘图源码\第01册_数学基础与统计学习基本理论\V1-C10\fig_v1_c10_complexity.tex`

BLOCKERS: none

MATH_SEMANTICS: PASS. The source training curve is `0.36+3.35 exp(-0.34x)`, whose derivative is negative on the displayed domain. The source validation curve is `1.08+0.105(x-5.25)^2`, whose unique minimum is `(5.25,1.08)`. The filled marker, dashed reference, minimum label, selection label, and central region all agree with those values. Axis directions and underfit/appropriate/overfit ordering are correct.

TEXT_CONSISTENCY: PASS. The caption states the single reading conclusion: training error usually decreases as complexity rises while validation error may first decrease and then increase. The directly adjacent prose correctly identifies solid training, dashed validation, the filled gold point, and the vertical reference as the selection encoding, and correctly reserves selection for validation information.

READING_ORDER: PASS. The reader can follow axes and two curves, then the labelled validation minimum, then the reference to the selected complexity, and finally the three complexity regions. The training leader attaches to the training curve without crossing text.

SOURCE_FONT_AUDIT: PASS. Twelve visible elements were assigned unique IDs. Direct/key labels resolve to 10.304 pt, region labels to 9.856 pt, axis titles to 11.20 pt, and caption text/label to 10.0 pt. All are >=9.5 pt. For direct/key/region labels the final PDF text-matrix values (10.27/10.27/9.82 bp) independently match declared TeX size x 1.12 x 72/72.27. The axis option cascade resolves to a 10 pt base and the final PDF matrix is 11.16 bp, matching 10 x 1.12 x 72/72.27. Same-role effective-size ratios are 1.000 and absolute differences are 0 pt.

PIXEL_HEIGHT_AUDIT: PASS. Native page size is exactly 2481 x 3508 at 300 dpi. CJK ink heights are 35--41 px (floor 30); caption digits are 28 px (floor 24). No lowercase/Greek, formula-operator, or natural-script element is present in the figure.

SAME_CLASS_RATIO_AUDIT: PASS. Within-role ratios to the role median range from 0.987013 to 1.028571, inside [0.92,1.08]. The maximum same-role height ratio is 36/35 = 1.028571. This is a one-panel figure; cross-panel ratio is not applicable.

ROLE_RATIO_AUDIT: PASS. With the repeated region annotations as the no-tick BASE (35 px), the direct-annotation role median is 38.5 px (1.100000), the axis-title median is 41 px (1.171429), and the explicit key-annotation median is 39 px (1.114286). Direct annotations and axis titles lie in their prescribed bands. Eligibility for the key emphasis band is predeclared in the frozen source, not assigned after measurement: line 2 explicitly plans to protect the key-label size/stroke hierarchy; lines 8--9 define the dedicated key style; lines 49--52 apply it only to `最低验证误差` and `选择复杂度`, the two decision outputs. `KEY_ROLE_PREDECLARATION.md` records this line-by-line chain. Therefore 1.114286 is assessed against the predeclared [0.90,1.25] band and passes.

OVERLAP_PIXEL_COUNT: 0 across all 150 current pair rows (65 independent text-text gates, one measured intra-composite caption-script relation, and 84 text-graphic gates). Every curve, reference, marker, leader, and axis arrow uses its own semantic foreground mask. `T10_CAPTION_LABEL_CJK` and `T11_CAPTION_LABEL_DIGITS` share parent `TCAP_LABEL_COMPOSITE`; they are split only to apply CJK and digit pixel floors and are explicitly excluded from the independent-object 4 px gate. Intentional graphic junctions (leader-to-training-curve, marker/reference-to-validation minimum, and axis origin) are not misclassified as illegal text overlap.

CLIP_PIXEL_COUNT: 0. `after_edge_clip_report.csv` contains 19 object rows. Overall full-page / no-resize figure-crop / no-resize standalone minimum edge clearances are 266 / 35 / 35 px. Text-only minima are 334 / 54 / 39 px. Every applicable edge is >=6 px, no row fails, and summed clip count is 0. The figure crop and standalone crop retain all intended plot text and arrows; caption sub-elements are intentionally absent only from the standalone plot crop.

MIN_TEXT_CLEARANCE_PX: 15.000 overall, set by the minimum label to marker text-graphic pair (floor 3). Across the 65 independent text-text relations, minimum foreground clearance is 44.283180 px and minimum axis-aligned final-PDF/vector bbox clearance is 36.541667 px (floor 4); bbox intersections/touches = 0. The caption label's CJK and digit sub-elements share one parent and are not counted as two independent text objects. Other critical values include selection label to x-axis 21 px, selection label to reference 24.738634 px, training label to leader 26.570661 px, and y-axis title to y-axis 31 px.

VISUAL_HARMONY: PASS. Region labels are the small base tier, direct/key annotations the middle tier, and axis titles the upper tier. Their relative sizes are restrained and consistent; ordinary text does not displace or dominate the curves. Font reduction is not recommended because the smallest tier is already 9.856 pt, close to the 9.5 pt hard floor.

FONT_AND_DENSITY: PASS. CJK typography is consistent in weight and density; labels are readable at page scale and at native 1:1. White label backing is used only where it protects curve readability and does not create an oversized visual block.

LAYOUT: PASS. No text, curve, arrow, marker, caption, or page object is clipped or crowded. The selection label is visibly separated from both the x-axis and the dashed reference. The closest key-label relations retain 15 px or more foreground clearance.

GRAYSCALE: PASS. Solid versus dashed curve style remains clear; the filled minimum marker and dashed vertical reference preserve the selected-complexity cue. Region labels remain readable by text and position without reliance on colour.

CAPTION: PASS. It contains one concise reading conclusion. Selection mechanics and data-use qualifications remain in the adjacent body paragraph.

PAGE_INTEGRATION: PASS. The 200 dpi whole-page overview shows a balanced upper figure, attached caption, adjacent explanatory paragraph, and following example. There is no orphan, abnormal blank area, overlap, or page overflow.

TECHNICAL: PASS for the frozen artifact inspected. The 813-page PDF opens, the target page renders at both 200 and 300 dpi, vector text/drawing objects are accessible, the caption is present once, and the printed figure/page identifiers are stable. No source or build artifact was modified in this review.

REQUIRED_FIXES: none

SUPERSEDED_EVIDENCE: The first preflight T03/G04 value of 4 overlap pixels was caused by a padded same-colour object mask and is withdrawn. `SUPERSEDED_T03_G04_MASK_CONTAMINATION.md` gives the exact four false coordinates, old/current mask construction, and corrected 0-overlap / 15.000 px result. All current CSVs, current masks, ROIs, overlays, summaries, and this PASS use the corrected masks only.

EVIDENCE_USED:

- `full_page_200dpi.png`
- `full_page_300dpi.png`
- `figure_crop_300dpi.png`
- `standalone_300dpi.png`
- `grayscale_300dpi.png`
- `after_font_audit.csv`
- `after_pixel_measurements.csv`
- `after_overlap_report.csv`
- `after_edge_clip_report.csv`
- `after_text_measurement_overlay_300dpi.png`
- `semantic_masks_overlay_figure_1to1_300dpi.png`
- independent `mask_G01`--`mask_G07` native 300 dpi PNGs
- independent `mask_T01`--`mask_T12` native 300 dpi PNGs
- twelve critical raw/nearest native 1:1 ROI pairs
- `MANUAL_NATIVE_ROI_REVIEW.md`
- `SUPERSEDED_T03_G04_MASK_CONTAMINATION.md`
- `KEY_ROLE_PREDECLARATION.md`

BLIND_REVIEW_COMPLIANCE: No previous FIG-P157-01 R1/R2/R3/R4, SA2, SA3, ROOT, inventory, status, prior CSV/JSON, prior mask, or prior ROI was read. Only the authorized Goal section, AGENTS.md, R93 frozen PDF, current figure source, and directly adjacent V1-C10 text were used. The review wrote only this isolated `STRICT_R5_SA1_R93` directory.

SOURCE_MODIFICATION: none
