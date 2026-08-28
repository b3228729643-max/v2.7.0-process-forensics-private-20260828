# FIG-P756-01 严格视觉验收（R3，已关闭）

- CANDIDATE_ID: `FIG-P756-01-R3`
- SOURCE_FONT_PASS: `true`
- PIXEL_HEIGHT_PASS: `true`
- SAME_CLASS_RATIO_PASS: `true`
- ROLE_RATIO_PASS: `true`
- OVERLAP_PIXEL_COUNT: `0`
- CLIP_PIXEL_COUNT: `0`
- MIN_TEXT_CLEARANCE_PX: `12`
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

根线程候选取证、独立 SA1 与隔离 SA3 均已通过；根线程复核后允许固化为 `STRICT_FINAL`。

## 证据路径

- full_page_200dpi: `full_page_200dpi.png`（连续版物理页 801，印刷页 788）
- full_page_300dpi: `full_page_300dpi.png`
- figure_crop_300dpi: `figure_crop_300dpi.png`
- standalone_300dpi: `standalone_300dpi.png`
- grayscale_300dpi: `grayscale_300dpi.png`
- font_audit: `after_font_audit.csv`
- pixel_measurements: `after_pixel_measurements.csv`
- overlap_report: `after_overlap_report.csv`
- measurement_overlay: `after_text_measurement_overlay_300dpi.png`
- continuous_page_pdf: `fullbook_page_801.pdf`

## 根线程候选结论

- 39/39 字号源级记录 PASS，39/39 原生像素高度记录 PASS，67/67 重叠、净空与裁切检查 PASS。
- 一般图中文字最低有效字号为 9.5641pt；面板标题为 10.1619pt，图注为 9.9626/10.0618pt。未使用整体缩放规避字号门，未见突兀放大或不可读缩小。
- 非法重叠 0px，裁切 0px；全体记录中的最小净空为 12px。用户重点关注的图内文字—线条、文字—边框、图例—图注、图注—后续正文均满足对应硬门。
- 图例—图注净空 27px，图注—读图检查净空 75px，图裁边缘净空 19px；彩色、灰度与连续页均保持可辨层级。
- 全书构建已消除 `Float(s) lost`；AUX 含 `fig:V5-C08-course-map`，图 37.8 实际落在连续版物理页 801。该构建是本图页面集成候选，不代表当前整书最终发布构建。

## 关闭结论

- 全新独立 SA1 已在原生 300dpi/1:1 下回读全部 CSV、overlay、四种视图和 67 个 ROI并给出 PASS。
- 隔离 SA3 已逐项检查全部 67 个 ROI，并独立重测得到 overlap=0、clip=0、最小净空 12px；当前官方连续页逐像素一致。
- 根线程确认全部硬门与三角色顺序满足新 Goal，FIG-P756-01 当前候选严格关闭。
- 后续任何图源或页面集成变化均使本候选失效，必须重新取证。
