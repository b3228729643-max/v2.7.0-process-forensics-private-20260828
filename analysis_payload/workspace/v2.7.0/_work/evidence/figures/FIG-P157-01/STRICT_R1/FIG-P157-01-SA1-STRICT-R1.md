RESULT: FAIL

# FIG-P157-01 — independent SA1 strict R1 recheck

## Scope and independence

- Official candidate: `v2.7.0/_work/source/v2.7.0/src/build/strict_current_r90_fullbook/main_full.pdf`, physical page 170, figure 10.1.
- Figure source: `src/绘图源码/第01册_数学基础与统计学习基本理论/V1-C10/fig_v1_c10_complexity.tex`.
- This review read the official page, relevant source/style definitions, and the adjacent source reading sentence only.  It did not read any earlier SA1/SA2/SA3/ROOT report, state, or verdict, and modified no source, wrapper, common file, inventory, or state.
- `official_page_170.pdf` was extracted directly from the official PDF.  Poppler direct rendering at 300 dpi produced `official_page_170_300dpi.png` at exactly **2481×3508 px**.  All reported geometry comes from that native raster and vector-bbox-to-pixel mapping at `300/72`; no measurement used a resized image.

## Complete object coverage

`element_inventory.csv` enumerates 12 reader-visible TEXT elements (`T01`–`T12`) and 7 native foreground graphics (`G01`–`G07`): two data curves, selection reference line, minimum marker, leader, and both axis arrows.  It also records that this is one panel and has no node border, enclosing panel border, or legend; those absent classes were not silently skipped.

The source and official vector display list were both reconciled with the inventory.  There are no visible tick labels, legend items, formula blocks, Latin/Greek labels, or multi-panel counterparts to audit here.

## A. Effective-font audit — PASS

`after_font_audit.csv` is the source-level record.  The apparent 8.8/9.2 pt local declarations are subject to the enclosing `every picture ... scale=1.12`; the rendered PDF font metrics independently confirm that cumulative scale.

| Role | Declared → effective source size | Result |
|---|---:|---|
| Curve labels and key annotations (T01–T04) | 9.2 → 10.304 pt | PASS |
| Region annotations (T05–T07) | 8.8 → 9.856 pt | PASS |
| Axis titles (T08–T09; later `slfig axis` `\small` wins) | 10.0 → 11.200 pt | PASS |
| Caption label/body (T10–T12) | 10.0 → 10.000 pt | PASS |

Every effective size is at least 9.5 pt.  Each same-role source-size ratio is 1.000, absolute difference 0.000 pt, and the figure has only P01, so cross-panel comparison is N/A rather than unmeasured.

## B. Native 300 dpi text measurement and hierarchy — PASS except collision row

`after_pixel_measurements.csv` contains the required per-element pixel coordinates, class medians, ratios, overlaps, and clearances.  It uses the least measured full-size character per element rather than a favourable maximum.

- CJK ink heights are 36–42 px (all ≥30 px); the `10.1` digit element is 27 px (≥24 px).
- Same-role/same-script ratios are within `[0.92,1.08]`: curve labels 0.973–1.027, key annotations 0.974–1.026, region annotations 0.973–1.000, and axis titles 0.988–1.012.
- Using curve-label median 37 px as BASE, key annotations are 1.027, region annotations 1.000, and axis titles 1.122.  These meet the mandatory role ranges and no emphasis exceeds 1.25.
- Text–text overlap is 0.  The tightest text-bbox separation is 9.76 px (`图` to `10.1`), exceeding 4 px.  Outer-page clip count is 0 and the tightest text-to-image-edge distance is 334.11 px, exceeding 6 px.

The sole failing measurement row is T02, described below.  It makes the complete pixel-measurement gate FAIL despite the otherwise compliant font and ratio checks.

## C. Zero-overlap / clearance audit — FAIL

`after_overlap_report.csv` covers every TEXT–TEXT pair and every TEXT–graphic pair, with the path from the official PDF used only to locate the object and the native 300 dpi foreground mask used to count pixels.

| Pair | Native finding | Required | Result |
|---|---:|---:|---|
| T01–T12 text pairs | 0 overlap; minimum bbox gap 9.76 px | 0; ≥4 px | PASS |
| T02 `验证误差：先降后升` × G02 validation dashed curve | **134 overlap px; 0.00 px clearance** | 0; ≥3 px | **FAIL** |
| All other audited TEXT–curve/axis/reference/marker/leader pairs | 0 overlap; thresholds met | 0; ≥3 px | PASS |
| All figure objects × page edge | 0 clip px | 0; text edge ≥6 px | PASS |

The focused unresampled ROI `roi_05_validation_label_curve_conflict_100pct.png` marks the T02/G02 semantic-object intersection.  Source code places T02 at `(axis cs:6.5,2.05)` while the U-shaped validation curve rises through its label run.  The annotation’s 90% opaque white fill does not establish a valid text-to-curve clearance; it is not an exemption under §9.2.1-F.

## D. Mathematical semantics, data, caption, and adjacent prose — FAIL

The core plotted mathematics is correct:

- Training curve is `0.36+3.35 exp(-0.34x)`, with strictly negative derivative and descending endpoint values about 3.710 → 0.472.
- Validation curve is `1.08+0.105(x-5.25)^2`, with its minimum exactly at `(5.25,1.08)`; the plotted gold marker and vertical reference line use those coordinates.
- The underfit / suitable / overfit regions contain the selected minimum in the appropriate middle region.  The caption’s statement about decreasing training error and a U-shaped validation error agrees with the curves.

However, the adjacent reading sentence claims: “实线圆点表示训练误差，虚线三角表示验证误差”.  The source draws a solid training line and a dashed validation line, but it declares neither training circles nor validation triangles; the only plotted marker is the gold `mark=*` at the validation minimum.  This is a direct figure–prose inconsistency and independently requires FAIL.

## E. Visual acceptance and page fusion — FAIL

The four mandatory views are recorded in `after_visual_acceptance.md`.  The page generally integrates cleanly and grayscale preserves solid/dashed differentiation.  Nevertheless, the label-through-curve collision disrupts the reading path and the false marker description misleads grayscale reading.  Neither can be waived as “still readable”.

## Required repair before another SA1 review

1. Move T02 completely away from G02; a distinct empty upper-middle placement is preferable.  The regenerated official page must show overlap exactly 0 and ink-to-curve clearance at least 3 px at native 300 dpi.
2. Make the adjacent prose match the actual encoding.  The least cluttered fix is to say that solid and dashed lines identify training and validation errors, and that the solid point plus vertical reference line mark the selected complexity.  Alternatively add the claimed circle/triangle markers and re-audit the resulting density and overlaps.
3. Recompile the official full-book candidate and rerun the whole source-font, native-pixel, ratio, zero-overlap, semantic, and four-view evidence sequence.  This failed R1 evidence cannot be reused as a passing candidate.

This figure is not eligible for SA3/root sign-off in its current form.
