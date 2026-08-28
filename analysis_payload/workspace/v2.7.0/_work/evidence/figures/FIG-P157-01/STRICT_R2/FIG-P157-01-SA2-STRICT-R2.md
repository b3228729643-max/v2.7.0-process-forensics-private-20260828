RESULT: FIXED

# FIG-P157-01 — SA2 STRICT-R2 targeted repair report

assigned_scope:
- Repair only the two independent R1 failures for physical P157 / figure 10.1: the validation-label collision and the false solid-circle/dashed-triangle prose claim.
- Modify only the authorized figure source and its directly adjacent chapter reading sentence; write all local evidence only under `FIG-P157-01/STRICT_R2`.

completed:
- Reproduced the R1 failure from the native 1:1 ROI and accepted the measured baseline: T02 `验证误差：先降后升` crossed G02 validation curve at 134 illegal pixels with 0 px clearance.
- Moved only T02 from `(axis cs:6.5,2.05)` to `(axis cs:3.9,2.2)`, preserving its font, color, fill, anchor, and all curve mathematics.
- Replaced only the inaccurate grayscale-reading clause. It now says solid line = training error, dashed line = validation error, and the gold filled point plus vertical reference line jointly mark the selected complexity.
- Independently compiled a standalone candidate and a local context page, rendered direct native 300 dpi and 200 dpi views, and rebuilt the complete font/pixel/ratio/overlap/clip evidence set.

files_changed:
- `v2.7.0/_work/source/v2.7.0/src/绘图源码/第01册_数学基础与统计学习基本理论/V1-C10/fig_v1_c10_complexity.tex`
- `v2.7.0/_work/source/v2.7.0/src/讲义源码/第01册_数学基础与统计学习基本理论/chapters/V1-C10.tex`
- Evidence-only wrappers, audit script, renders, CSV/JSON, ROIs, logs, local PDFs, and reports under `v2.7.0/_work/evidence/figures/FIG-P157-01/STRICT_R2/`.

decisions:
- Chose `(3.9,2.2)` because it is a genuinely empty upper-middle region and is the lowest-disturbance source change. Native measurement gives T02–G02 overlap 0 and 164.12 px ink clearance, far above the required 3 px.
- Corrected prose to the encoding already implemented instead of adding dense, nonexistent series markers. This preserves the existing curves, sample count, selected point `(5.25,1.08)`, reference line, regions, caption, effective sizes, and enclosing scale.
- Did not alter any public style, wrapper/build entry, central CSV/JSON, project status, other figure, or unrelated teaching content.

unresolved:
- No local-candidate hard-gate failure remains.
- Final qualification remains intentionally unresolved: root must build a new official continuous PDF, then send that official page to a fresh independent SA1 and, only after SA1 PASS, an isolated SA3. SA2 does not sign final PASS.

validation:
- STANDALONE_BUILD: PASS — `build/standalone_wrapper.pdf`, 1 A4 page; direct `standalone_page_300dpi.png` is 2481×3508 px.
- PAGE_BUILD: PASS — `build/page_wrapper.pdf`, 1 A4 local context page; `\cref` stabilized after rerun; direct `local_page_300dpi.png` is 2481×3508 px.
- BUILD_LOGS: PASS — final standalone/page logs have 0 combined hard-pattern matches.
- FONT_AUDIT_RESULT: PASS — 12/12; effective 9.856–11.200 pt, all at least 9.5 pt.
- PIXEL_MEASUREMENT_RESULT: PASS — 12/12; CJK 35–43 px, digit 27 px; same-class ratios 0.973–1.027; role ratios compliant.
- OVERLAP_PIXEL_COUNT: 0 — 151/151 required pair/clip rows PASS; no visible text, curve, axis, reference line, marker, leader, or arrowhead collision.
- CLIP_PIXEL_COUNT: 0.
- MIN_TEXT_CLEARANCE_PX: 9.76 px overall reader-object minimum (TEXT–TEXT threshold 4 px).
- MIN_TEXT_GRAPHIC_CLEARANCE_PX: 14.04 px (threshold 3 px).
- T02_VALIDATION_CURVE_CLEARANCE_PX: 164.12 px, with overlap 0.
- MATH_SEMANTICS: PASS — both functions, sample count, minimum `(5.25,1.08)`, marker/reference line, and three regions unchanged and mutually consistent.
- TEXT_CONSISTENCY: PASS — new extracted page text matches the actual solid/dashed/filled-point/reference-line encoding and contains neither false marker claim.
- GRAYSCALE/PAGE_INTEGRATION: PASS for the local candidate; the required views show stable line-type differentiation, clean hierarchy, and no context-page overflow.

next_action:
- Freeze these two source edits. Root should build the next official continuous full-book PDF outside this evidence directory, regenerate official P157 evidence from its physical page, and assign a fresh independent SA1; proceed to isolated SA3 only after SA1 PASS.

## Goal-template summary

- FIGURE_ID: FIG-P157-01
- ROOT_CAUSE: T02 was placed on the rising dashed curve; adjacent prose described series markers that were never drawn.
- PATCH_SUMMARY: one coordinate replacement plus one adjacent prose-clause replacement.
- NEW_EVIDENCE: `after_font_audit.csv`, `after_pixel_measurements.csv`, `after_overlap_report.csv`, `after_text_measurement_overlay_300dpi.png`, `after_visual_acceptance.md`, native page/standalone/grayscale views, five 1:1 ROIs, and this report.
- REMAINING_RISKS: only official continuous-page rebuild and independent SA1/SA3/root qualification remain.
