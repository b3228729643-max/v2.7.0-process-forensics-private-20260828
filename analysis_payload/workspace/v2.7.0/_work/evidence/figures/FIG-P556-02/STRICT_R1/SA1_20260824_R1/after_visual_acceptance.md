# FIG-P556-02｜SA1 visual acceptance

冻结输入 `main_full.pdf` 的真实图位是物理第 602 页、印刷第 589 页、图30.5。300 dpi 的唯一有效口径为整页直出固定网格后切片；不使用 resize 或 direct clip。

| Gate | Result | Evidence |
|---|---|---|
| SOURCE_FONT_PASS | FAIL (10/14 source objects) | `after_font_audit.csv` |
| PIXEL_HEIGHT_PASS | FAIL (17/167 glyphs) | `after_pixel_measurements.csv` |
| SAME_CLASS_RATIO_PASS | FAIL (36 actual raw-H rows) | `same_class_ratio_audit.csv` |
| ROLE_RATIO_PASS | FAIL (3 actual raw-H rows) | `role_ratio_audit.csv` |
| OVERLAP_PIXEL_COUNT | PASS (0, 0 pairs) | `after_overlap_report.csv` |
| CLIP_PIXEL_COUNT | PASS (0) | `after_edge_clip_report.csv` |
| FONT_VISUAL_HARMONY_PASS | FAIL | four-view inspection + source/raw-H audit |
| MATH_SEMANTICS_PASS | PASS | `math_text_semantics_audit.json` |
| CAPTION/TEXT CONSISTENCY | FAIL | `math_text_semantics_audit.json` |

There are 0 collision-failure pairs; the 12 nearest critical pairs nevertheless have separate raw masks, overlap, overlay and nearest-neighbour 8x ROI. The result is **FAIL → SA2**.
