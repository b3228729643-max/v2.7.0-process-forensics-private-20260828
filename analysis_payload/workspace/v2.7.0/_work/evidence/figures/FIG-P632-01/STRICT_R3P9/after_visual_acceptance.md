# FIG-P632-01 最终视觉验收（R3.9，已关闭）

- CANDIDATE_ID: `FIG-P632-01-R3.9`
- SOURCE_FONT_PASS: `true`
- PIXEL_HEIGHT_PASS: `true`
- SAME_CLASS_RATIO_PASS: `true`
- ROLE_RATIO_PASS: `true`
- OVERLAP_PIXEL_COUNT: `0`
- CLIP_PIXEL_COUNT: `0`
- MIN_TEXT_CLEARANCE_PX: `14`
- TEXT_TEXT_CLEARANCE_PASS: `true`
- TEXT_GRAPHIC_CLEARANCE_PASS: `true`
- NODE_BORDER_CLEARANCE_PASS: `true`
- EDGE_CLEARANCE_PASS: `true`
- CROSS_PANEL_CLEARANCE_PASS: `true`
- VISUAL_HARMONY_PASS: `true`
- MATH_SEMANTICS_PASS: `true`
- TEXT_CONSISTENCY_PASS: `true`
- GRAYSCALE_PASS: `true`
- PAGE_INTEGRATION_PASS: `true`
- SA1_RESULT: `PASS`
- SA3_RESULT: `PASS`
- ROOT_RESULT: `PASS`

独立 SA1、隔离 SA3 与根线程均已 PASS；本候选可复制到 `STRICT_FINAL`。

## 证据路径

- full_page_200dpi: `full_page_200dpi.png`（连续版物理页 680）
- full_page_300dpi: `fullbook_page_300dpi.png`（连续版物理页 680）
- figure_crop_300dpi: `figure_crop_300dpi.png`
- standalone_300dpi: `standalone_300dpi.png`
- grayscale_300dpi: `grayscale_300dpi.png`
- fullbook_grayscale_300dpi: `fullbook_page_grayscale_300dpi.png`
- font_audit: `after_font_audit.csv`
- pixel_measurements: `after_pixel_measurements.csv`
- overlap_report: `after_overlap_report.csv`
- measurement_overlay: `after_text_measurement_overlay_300dpi.png`
- continuous_page_pdf: `fullbook_page_680.pdf`

## 通过依据与未关闭项

- 59/59 字号源级记录 PASS；59/59 原生像素高度记录 PASS；31/31 重叠/裁切检查 PASS。
- 非法重叠像素 0，裁切像素 0；最小净空 14 px，对应 C23 `x_1`—联合图横轴箭头头部。
- CJK/Latin与数字/x-height/基准数学/天然脚本的最小实墨高度依次为 34/25/18/22/19 px。
- 同角色与跨面板字号、像素比例均在严格门内；根线程未见字号突兀或因缩小导致的可读性损失。
- 连续页面中图题、后续正文与例题正常衔接。
- 闭环：全新 SA1 与隔离 SA3 均已独立 PASS；根线程已完成最终验收。后续若图源或页面集成发生变化，必须新建候选并重新走完整闭环。
- 书级旁路问题：连续版末尾 FIG-P756-01 触发 `Float(s) lost`，故整书构建仍为 FAIL；该问题不改变本页实测数据，但阻止最终发布验收。
