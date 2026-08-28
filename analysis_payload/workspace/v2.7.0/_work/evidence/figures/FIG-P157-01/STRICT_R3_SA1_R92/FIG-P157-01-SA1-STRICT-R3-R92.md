# FIG-P157-01-SA1-STRICT-R3-R92

SUPERSEDES: preliminary 21:49 local preflight; see `SUPERSEDED_2026-08-23_2149.md`.

RESULT: FAIL

Independent SA1 rebuilt evidence from the fixed official continuous R92 PDF only (813 pages, 4,933,704 bytes, physical page 170). No previous R1/R2/SA2/root conclusion or central inventory was used.

## Verdict summary

- Source-effective font gate: PASS; all 12 reader-visible figure/caption elements have an R92 native effective font size >=9.5pt after cumulative realization.
- 300dpi element-height gate: PASS; all CJK elements meet >=30px and the caption number meets >=24px.
- Same-class and role hierarchy gates: PASS; one coordinate panel only, so no artificial cross-panel claim is made.
- Illegal overlap: 0px; clipping: 0px; minimum reported mandatory clearance: 1.24px.
- Blocking item: `T04_SELECTION_KEY` (`选择复杂度`, `fig_v1_c10_complexity.tex:8-9,51-52`) ↔ `G06_X_AXIS_ARROW` (`fig_v1_c10_complexity.tex:24,59`), native bboxes `[299.283,285.745,350.610,296.739]` / `[97.414,280.876,530.815,284.768]`, overlap 0px but clearance `1.24px < 3.00px`. Minimal repair direction: move/reanchor the selection label down or shorten its visual extent while retaining all font gates.
- T02 `验证误差：先降后升` was separately measured against both curves, the gold point, vertical reference, leader and axes; native bboxes, pixel intersections and clearances are in `after_overlap_report.csv` and the explicit table in `after_visual_acceptance.md`.
- Semantic, figure/text, caption, grayscale and page-integration checks: PASS.

The hard failure above prevents a PASS. It is reported with its `ELEMENT_ID`, source lines, native bboxes, measured pixels and breached threshold; SA1 made no source modification.

## Evidence map

- Font/source audit: `after_font_audit.csv`
- Native pixel/bbox measurements: `after_pixel_measurements.csv`
- Mandatory pairwise overlap and clearance matrix: `after_overlap_report.csv`
- Measurement overlay: `after_text_measurement_overlay_300dpi.png`
- Acceptance matrix and T02 focused analysis: `after_visual_acceptance.md`
- Official direct renders and native ROIs/masks: files listed in `after_visual_acceptance.md`
