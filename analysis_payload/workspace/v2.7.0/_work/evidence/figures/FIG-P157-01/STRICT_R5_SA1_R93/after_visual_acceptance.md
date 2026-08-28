# FIG-P157-01 — SA1 strict visual acceptance on official R93

RESULT = PASS

SOURCE_FONT_PASS = true
PIXEL_HEIGHT_PASS = true
SAME_CLASS_RATIO_PASS = true
ROLE_RATIO_PASS = true
OVERLAP_PIXEL_COUNT = 0
CLIP_PIXEL_COUNT = 0
MIN_TEXT_CLEARANCE_PX = 15.000
MIN_INDEPENDENT_TEXT_TEXT_CLEARANCE_PX = 44.283180
MIN_INDEPENDENT_TEXT_TEXT_BBOX_CLEARANCE_PX = 36.541667
MIN_TEXT_GRAPHIC_CLEARANCE_PX = 15.000
MIN_PAGE_EDGE_CLEARANCE_PX = 266
MIN_TEXT_PAGE_EDGE_CLEARANCE_PX = 334
MIN_TEXT_FIGURE_CROP_EDGE_CLEARANCE_PX = 54
MIN_TEXT_STANDALONE_EDGE_CLEARANCE_PX = 39
VISUAL_HARMONY_PASS = true
MATH_SEMANTICS_PASS = true
TEXT_CONSISTENCY_PASS = true
GRAYSCALE_PASS = true
PAGE_INTEGRATION_PASS = true

## Native-render identity

- Frozen candidate: `strict_current_r93_fullbook/main_full.pdf`.
- Caption search found exactly one matching figure on physical PDF page 170 (printed page 157, Figure 10.1).
- PDF page: A4, 595.276 x 841.89 pt.
- Native Poppler 300 dpi page: 2481 x 3508 pixels; no resize was applied.
- The 200 dpi page is used only for whole-page overview. Pixel decisions use the native 300 dpi page and native 1:1 ROIs.

## Hard-gate summary

- 12 unique visible text elements were audited, including plot text and the caption label/text.
- Minimum effective source size is 9.856 pt (`T06`--`T08` region labels), above the 9.5 pt floor.
- CJK ink heights are 35--41 px, all >=30 px. Caption digits are 28 px, >=24 px. The figure contains no lowercase/Greek, formula-operator, or natural-script element requiring the other pixel classes.
- Within-role same-class maximum pixel drift is 36/35 = 1.028571, below 1.08. Same-role source-size ratios are all 1.000 with 0 pt absolute drift. There is one panel, so cross-panel gates are not applicable and cannot conceal a mismatch.
- With repeated region annotations as the no-tick BASE (median 35 px), direct annotations have role-median ratio 38.5/35 = 1.100000, axis titles 41/35 = 1.171429, and explicit key annotations 39/35 = 1.114286. Direct and axis roles are inside their prescribed bands. Key-role eligibility is not post-hoc: source line 2 predeclares protection of the key-label size/stroke hierarchy, lines 8--9 define its style, and lines 49--52 bind only the validation minimum and selected complexity to it. `KEY_ROLE_PREDECLARATION.md` records the chain; 1.114286 is inside [0.90,1.25].
- 150 text/text-graphic rows were recomputed against independent semantic masks: 65 independent text-text gates, one measured intra-composite caption-script relation, and 84 text-graphic gates. Pair failures = 0 and summed illegal overlap = 0.
- All 65 independent text-text PDF/vector bbox gaps were computed explicitly. Minimum bbox gap is 36.541667 px and minimum independent foreground gap is 44.283180 px, both above 4 px. `图` and `10.1` are CJK/digit sub-elements of one caption-label parent and are split only for script-specific pixel floors, not incorrectly treated as independent semantic text objects.
- Global text-graphic minimum is 15 px (`T03_MINIMUM_KEY` to `G04_MINIMUM_MARKER`), above 3 px.
- `after_edge_clip_report.csv` traces all 19 current text/graphic objects. No object mask touches an image boundary: overall full-page/crop/standalone minima are 266/35/35 px; text-only minima are 334/54/39 px. All exceed 6 px, all rows pass, and summed `CLIP_PIXEL_COUNT` is 0.

## Four-view and semantic acceptance

- `full_page_200dpi.png`: figure/caption/body/example form a balanced page; no orphaned caption, abnormal gap, or page overflow.
- `figure_crop_300dpi.png`: all labels are legible and subordinate to the curves; the selection label is visibly clear of the x-axis.
- `standalone_300dpi.png`: curves, marker, reference, axes, region labels, and both direct labels remain unambiguous.
- `grayscale_300dpi.png`: solid training curve and dashed validation curve remain distinguishable; the filled minimum marker and dashed vertical reference preserve the selection encoding without colour.
- Mathematical semantics pass: the training curve `0.36+3.35 exp(-0.34x)` is strictly decreasing; the validation curve `1.08+0.105(x-5.25)^2` has its unique minimum at `(5.25,1.08)`; the marker/reference/selection label agree with that minimum; the selected point lies in the central appropriate-complexity region.
- Caption and adjacent prose agree with the drawn solid/dashed curves, the gold filled point, the vertical reference line, and the rule that selection uses validation rather than continuing to reduce training error.

## Superseded preflight value

The first preflight `T03_MINIMUM_KEY`--`G04_MINIMUM_MARKER` value (4 overlap pixels, 0 px clearance) was an object-mask construction error, not a rendered overlap. It is explicitly withdrawn in `SUPERSEDED_T03_G04_MASK_CONTAMINATION.md`. The corrected current masks have intersection 0, nearest points `(1350,927)` and `(1350,942)`, and 15.000 px clearance. All current CSVs, ROIs, overlays, summary counts, and this decision use only the corrected masks.

## Font harmony decision

Typography is visually coordinated: region labels are the smallest repeated role, direct/key labels form the middle tier, and axis titles form the upper tier without dominating the data. No label appears anomalously large or small. Although local font reduction is generally allowed when every hard floor remains satisfied, no reduction is recommended here: the smallest role is already 9.856 pt, only 0.356 pt above the 9.5 pt hard floor, and the present balance passes every role and pixel gate.
