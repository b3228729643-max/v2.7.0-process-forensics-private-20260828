# FIG-P142-01 strict R1 visual acceptance

Official object: `main_full.pdf`, physical page 152.

Raw measurement input: `official_page_152_300dpi.png` (2481×3508, direct 300 dpi render; no resizing or resampling).

SOURCE_FONT_PASS = false
PIXEL_HEIGHT_PASS = false
SAME_CLASS_RATIO_PASS = true
ROLE_RATIO_PASS = false
OVERLAP_PIXEL_COUNT = 0
CLIP_PIXEL_COUNT = 0
MIN_TEXT_CLEARANCE_PX = 3.48
VISUAL_HARMONY_PASS = false
MATH_SEMANTICS_PASS = true
TEXT_CONSISTENCY_PASS = true
GRAYSCALE_PASS = true
PAGE_INTEGRATION_PASS = true

## Measurement outcome

- Source effective-size failure: all node labels and both phase labels are 9.2pt; both feedback labels are 8.6pt. All are below the 9.5pt reader-text floor. The `new` subscript is 6.42pt and cannot qualify as legal natural script because its base `x` is only 9.2pt.
- Pixel-height failure: `T18_NEW_SUBSCRIPT` measures 13px at the required raw 300 dpi, below the 15px script floor.
- Role-ratio failure: feedback-label median = 31px; ordinary node-text base median = 33px; ratio = 0.9394, below the 0.95 lower bound for a normal annotation.
- Geometry pass: the complete matrix records 0 text-text overlap pixels, 0 text-graphic overlap pixels, 0 clipping pixels, and all pair-specific clearances pass. The global 3.48px minimum is a text-to-line case whose 3px floor is met; text-text and node-text/border rows meet their 4px and 5px floors.
- The whole-page, raw figure crop, 1:1 local ROIs, and grayscale image are retained in this directory. Pixel height/class-ratio values are in `after_pixel_measurements.csv`; every text-text and text-graphic comparison is in `after_overlap_report.csv`.

## Visual / semantic review

- Information flow is semantically coherent: training data and learning algorithm produce the shared model; evaluation supplies supervised or unsupervised feedback; new input enters the same model and leads to a reportable result.
- Caption and immediately following reading sentence agree with this closed-loop interpretation and correctly warn that feedback from testing turns it into development information.
- The solid/dashed structural distinction remains legible in grayscale, and the page has normal caption/body integration.
- These strengths cannot override the source-font, script-pixel-height, and feedback-role-ratio hard failures. The undersized feedback annotation also reduces visual harmony.

## Required repair direction (no edits made)

1. Raise normal node/phase-label and feedback-label effective text to at least 9.5pt.
2. Rebalance feedback labels after enlargement so their raw median reaches at least 0.95 of the normal node-text base without exceeding the 1.25 emphasis ceiling; recheck clearances after placement.
3. Re-run every source, pixel, ratio, collision, clipping, ROI, grayscale, semantic and page-integration check from a new candidate PDF.

RESULT: FAIL
