# FIG-P639-01 SA1 R105 fresh isolated visual acceptance

- HANDOFF_ID: `MAIN-R105-P639-SA1-FRESH-ISOLATED-REPLACEMENT-20260826`
- reviewer: `SA1_R105_FRESH`
- manual record time: `2026-08-25T22:54:32.938Z`
- candidate: `strict_current_r105_fullbook/main_full.pdf`, physical page 689
- current source: `fig_v5_c04_bivariate_normal_conditionals.tex`

## Manual views actually opened

The reviewer actually opened the native full-page 200/300 dpi views, figure crop, standalone crop, grayscale crop, labeled measurement overlay, all 13 glyph contact sheets, and the single critical native 1x/8x relation ROI before writing the manual ledgers.

## R168 hard-defect review

- missing/tofu/wrong glyph/codepoint: PASS; the visible text and math glyphs match the source and caption.
- mathematical semantics: PASS; the two displayed normal densities have variance 0.64 and means 0.45/0.60, consistent with rho=0.6, a=1, b=0.75 and the adjacent explanation.
- unreadable or gross visible imbalance: PASS; no such defect is visible in color or grayscale.
- crop: PASS; `CLIP_PIXEL_COUNT=0` and all reader text clears its applicable crop edge by at least 6 native pixels.
- illegal overlap: PASS; `OVERLAP_PIXEL_COUNT=0` for independent objects.
- page fusion: PASS; the figure, caption, preceding lead-in and following Figure 33.7 lead-in form a coherent reading sequence on physical page 689.
- font pixel/proportion details: ADVISORY only under R168. The source uses 9.2pt labels/notes and 8.5pt tick labels; these are below the legacy 9.5pt target but remain readable and visually balanced, so they are not elevated to hard defects.

## Strict geometry result

FAIL. Relation `R00008` (`G001` U+2212 minus in x-axis tick `−2` versus `G009` y-axis tick `0`) has `PDF_BBOX_CLEARANCE_PX=0.0`, below the independent TEXT-TEXT minimum of 4px. Their final-visible raw ink masks do not overlap (`INTERSECTION_PX=0`) and have 28.0689px raw-mask clearance, but the authoritative geometry protocol explicitly gates independent text by PDF/vector bbox clearance.

## Verdict

`FAIL_TO_SA2`

Recommended minimal repair scope: separate the y=0 tick label and the x-axis `−2` tick label so their final PDF/vector bboxes have at least 4 native pixels of clearance while preserving curve semantics and R168 visual balance. No other hard defect was found.
