# FIG-P020-01 严格视觉验收（R4，独立 SA1 已否决）

- CANDIDATE_ID: `FIG-P020-01-STRICT-R4-OFFICIAL-R89`
- SOURCE_FONT_PASS: `true`
- PIXEL_HEIGHT_PASS: `true`
- SAME_CLASS_RATIO_PASS: `true`
- ROLE_RATIO_PASS: `false`
- OVERLAP_PIXEL_COUNT: `0`
- CLIP_PIXEL_COUNT: `0`
- MIN_TEXT_CLEARANCE_PX: `14`
- TEXT_TEXT_CLEARANCE_PASS: `true`
- TEXT_GRAPHIC_CLEARANCE_PASS: `true`
- NODE_BORDER_CLEARANCE_PASS: `true`
- EDGE_CLEARANCE_PASS: `true`
- CROSS_PANEL_CLEARANCE_PASS: `not_applicable_single_panel`
- VISUAL_HARMONY_PASS: `false`
- MATH_SEMANTICS_PASS: `true`
- TEXT_CONSISTENCY_PASS: `true`
- GRAYSCALE_PASS: `true`
- PAGE_INTEGRATION_PASS: `true`
- SA1_RESULT: `FAIL_ROLE_RATIO_AND_HARMONY`
- SA3_RESULT: `NOT_STARTED_FAIL_ROUTE`
- ROOT_RESULT: `FAIL_ROUTE_SA2_R5`

## 证据路径

- official continuous page: `fullbook_page_17.pdf`
- full page 200/300 dpi: `full_page_200dpi.png`, `full_page_300dpi.png`
- figure crop: `figure_crop_300dpi.png`
- standalone: `standalone.pdf`, `standalone_300dpi.png`
- grayscale: `grayscale_300dpi.png`
- font/pixel evidence: `after_font_audit.csv`, `after_pixel_measurements.csv`
- overlap evidence: `overlap_evidence_manifest.json`, `after_overlap_report.csv`, `roi/`
- measurement overlay: `after_text_measurement_overlay_300dpi.png`

独立 SA1 发现局部 `\to` 有效字号 14.4458pt 对普通正文 9.9626pt 的角色比为 1.450003，且实墨 23px 对相邻 CJK 约 37px 的像素比仅 0.6216。故 R4 即使几何与像素下限通过，角色比例和视觉协调仍失败。本目录不得进入 SA3 或复制为 `STRICT_FINAL`；下一步必须由 SA2 产生 R5。
