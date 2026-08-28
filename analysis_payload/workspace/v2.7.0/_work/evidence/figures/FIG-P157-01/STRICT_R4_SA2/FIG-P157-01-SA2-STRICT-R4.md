RESULT: FIXED

# FIG-P157-01 — SA2 STRICT-R4 targeted axis-clearance repair

## assigned_scope

- Reproduce the official R92 `T04_SELECTION_KEY` (`选择复杂度`) ↔ `G06_X_AXIS_ARROW` failure, then modify only T04 positioning/anchoring.
- Preserve every curve, point, reference line, axis, other label, caption, font, scale, body sentence, shared style, central inventory, build entry and project-state file.
- Write all local evidence only under `FIG-P157-01/STRICT_R4_SA2`.

## completed

- Recomputed the official-R92 baseline from the two independent native 300 dpi semantic masks: overlap `0px`, nearest foreground-center distance `2.2361px`, foreground clearance `1.2361px`; see `r92_baseline_reproduction.json`.
- Changed only T04's y coordinate from `(axis cs:5.25,-.02)` to `(axis cs:5.25,-.07)`. `anchor=north`, text, style, font, scale and x coordinate are unchanged.
- Independently compiled the standalone figure and one-page local context twice, rendered direct native 300 dpi images without resizing, regenerated all five standard artifacts, independent T04/G06 masks and a 1:1 nearest-pixel ROI.
- Regressed all 12 reader-visible text elements, all 7 independent graphic objects, all 162 mandatory matrix rows, and the four required visual views.

## files_changed

- Authorized source: `v2.7.0/_work/source/v2.7.0/src/绘图源码/第01册_数学基础与统计学习基本理论/V1-C10/fig_v1_c10_complexity.tex` — one coordinate literal only.
- Evidence-only wrappers, scripts, PDFs, logs, direct renders, masks, ROIs, CSV/JSON and reports under `v2.7.0/_work/evidence/figures/FIG-P157-01/STRICT_R4_SA2/`.
- No body source, common style, curve function, point, reference line, axis, other label, caption, central inventory, state file or shared build was modified.

## root_cause

At y=`-.02`, the north-anchored T04 text foreground sat immediately below the x-axis/arrow foreground. The two objects did not overlap, but only `1.2361px` of blank foreground clearance remained, below the 3px hard gate and the requested 8px repair target.

## patch_summary

The single y-coordinate adjustment moves T04 downward while preserving the visual selection/reference alignment. The new independent-mask result is overlap `0px`, center distance `20.0000px`, foreground clearance `19.0000px`; both the `>=8px` target and `>=3px` hard gate pass.

Critical T04 regressions all pass:

| counterpart | overlap px | foreground clearance px | gate |
| --- | ---: | ---: | --- |
| G06 x-axis/arrow | 0 | 19.00 | >=8 target / >=3 hard |
| G03 vertical reference line | 0 | 23.35 | >=3 |
| G04 minimum marker | 0 | 227.14 | >=3 |
| T06 nearest region label `合适` | 0 | 49.99 | >=4 text-text |
| T12 nearest caption body | 0 | 226.00 | >=4 text-text |
| figure crop edge | 0 | 293.00 | >=6 |

## validation

- STANDALONE_BUILD: PASS — `build/standalone_wrapper.pdf`, one A4 page, 38,442 bytes.
- PAGE_BUILD: PASS — `build/page_wrapper.pdf`, one A4 local context page, 66,403 bytes; stabilized on the second run.
- BUILD_LOGS: PASS — final standalone/page logs contain 0 fatal, LaTeX-error, undefined-reference/control-sequence, overfull, underfull, lost-float or rerun hard-pattern hits.
- NATIVE_RENDER: PASS — `standalone_300dpi.png` and `local_page_300dpi.png` are direct `2481×3508` 300 dpi Poppler renders; `full_page_200dpi.png` is a direct `1654×2339` render; crops and grayscale views were not resized.
- FONT_AUDIT_RESULT: PASS — 12/12; effective font range `9.819–11.158pt`, all `>=9.5pt`; same-role source ratio/delta gates pass.
- PIXEL_MEASUREMENT_RESULT: PASS — CJK glyph medians `36.5–42px` (`>=30px`); caption number `27px` (`>=24px`); same-class ratios `0.9865–1.0191`; role ratios are compliant.
- OBJECT_REGRESSION: PASS — 12 text masks and 7 non-empty independent graphic masks; 66 text-text + 84 text-graphic + 12 figure-edge rows = 162/162 PASS.
- OVERLAP_PIXEL_COUNT: `0`.
- CLIP_PIXEL_COUNT: `0`.
- MIN_TEXT_TEXT_CLEARANCE_PX: `14.00` (required `>=4`).
- MIN_TEXT_GRAPHIC_CLEARANCE_PX: `13.04` (required `>=3`).
- MIN_FIGURE_EDGE_CLEARANCE_PX: `28.00` (required `>=6`).
- T04_G06_CLEARANCE_PX: `19.0000` (target `>=8`, hard gate `>=3`).
- VISUAL_HARMONY/GRAYSCALE/PAGE_INTEGRATION: PASS — `full_page_200dpi.png`, `figure_crop_300dpi.png`, `standalone_300dpi.png` and `grayscale_300dpi.png` preserve hierarchy, reading order, solid/dashed distinction, region spacing, caption separation and page fit.
- MATH_SEMANTICS/TEXT_CONSISTENCY/CAPTION: PASS — equations, minimum `(5.25,1.08)`, marker/reference meaning, axis labels, three regions, caption and adjacent prose are unchanged and mutually consistent.

## new_evidence

Five required standard artifacts:

- `after_font_audit.csv`
- `after_pixel_measurements.csv`
- `after_overlap_report.csv`
- `after_text_measurement_overlay_300dpi.png`
- `after_visual_acceptance.md`

Focused independent evidence:

- `masks/T04_selection_key_text_mask_300dpi.png`
- `masks/G06_x_axis_arrow_foreground_mask_300dpi.png`
- `roi/T04_selection_vs_xaxis_raw_1to1_300dpi.png`
- `roi/T04_to_G06_x_axis_nearest_segment_1to1_300dpi.png`
- `focused_nearest_pixel_segments.json`
- `audit_summary.json`

## decisions

- Selected y=`-.07` because it is the smallest simple coordinate move with a substantial native-pixel margin over the 8px target while keeping `选择复杂度` visually associated with the vertical reference and comfortably separated from `合适`, the x-axis title and the caption.
- Retained `anchor=north`; no font, style or geometry outside T04 required alteration.

## unresolved / remaining_risks

- No local-candidate hard-gate failure remains.
- This is an SA2 `FIXED` handoff, not a final figure PASS. Root must integrate the one-line source patch into a new official continuous full-book build, then assign a fresh independent SA1. Only after SA1 PASS may root start isolated SA3 and final root qualification.

## next_action

Stop SA2 writes and return source ownership to root. Root should build the next official continuous PDF and re-run the independent SA1 → isolated SA3 sequence on its physical P157 page.
