# FIG-P552-01｜SA1 严格视觉验收（冻结 R93）

RESULT: **FAIL**  
NEXT_ROLE: **SA2**

冻结输入为 `main_full.pdf`；图位于物理 PDF 第 596 页、印刷第 583 页，图号 30.3。权威测量网格为最终 PDF整页直接 rasterize 至原生 300 dpi，随后只作像素切片得到图裁，不 resize。任何 direct-clip 结果均标记为 `SUPERSEDED`，不进入以下结论。

| 硬门 | 结果 | 证据 |
|---|---:|---|
| SOURCE_FONT_PASS | FAIL（38/41 对象低于 9.5 pt） | `after_font_audit.csv` |
| PIXEL_HEIGHT_PASS | FAIL（10/154 可见字形） | `after_pixel_measurements.csv` |
| SAME_CLASS_RATIO_PASS | FAIL（34/154 raw-H_ink 比例行） | `same_class_ratio_audit.csv` |
| ROLE_RATIO_PASS | FAIL | `role_ratio_audit.csv` |
| OVERLAP_PIXEL_COUNT | FAIL（**221 unique px；4 unique pair**） | `after_overlap_report.csv`、`measurement_consistency.json` |
| CLIP_PIXEL_COUNT | PASS（0） | `after_edge_clip_report.csv` |
| FONT_VISUAL_HARMONY_PASS | **FAIL** | 见下文 |
| 数学/正文、阅读顺序、灰度、页面融合 | PASS | 四视图与 `SA1_STRICT_R1_REPORT.md` |

已人工核看 `full_page_200dpi.png`、`full_page_300dpi.png`、`figure_crop_300dpi.png` / `standalone_300dpi.png`、`grayscale_300dpi.png` 与 `after_text_measurement_overlay_300dpi.png`。31 个临界/失败关系均有原图、双方无膨胀 mask、交集、overlay，以及明示的 8× nearest-neighbour 原图/overlay/交集检查图；逐项索引见 `critical_pair_index.csv` 与 `critical_pair_manifest.md`。8×图只供像素核看，不参与测量。

`FONT_VISUAL_HARMONY_PASS: false`。普通读者角色落在 8.6--10.0 pt：刻度 8.6 pt、注记 8.8 pt、节点/区间/结论 9.2 pt、面板标题 9.4 pt，仅时间轴 `$t$` 与题注约 10 pt。基于实际 raw H_ink，节点正文 BASE=30 px，时间轴标题=26 px（0.867，低于 [1.00,1.18]）、刻度=25 px（0.833，低于 [0.95,1.10]）、题注=37 px（1.233，高于 [0.95,1.10]）。同类 actual-H_ink 也有 34 行超出 [0.92,1.08]，跨面板 annotation 的 lower/operation/script 比分别为 1.160 / 1.361 / 1.174。当前不允许再缩小；任何后续缩小只在全部字号、像素、比例、净空和整页阅读门重新通过后才可能成立。

独立 PDF 矢量 raw mask 的 unique 计数为 **22 + 55 + 33 + 111 = 221 px**，恰为四个 unique failure pair：上区间文字--区间箭头 22；下方注记--节点 1 边框 55；下区间文字--区间箭头 33；下方注记--下区间箭头 111。`MIN_TEXT_CLEARANCE_PX=0`，`CLIP_PIXEL_COUNT=0`；所有其他非失败 pair 的最小正 raw 净空为 9.591 px，页面边缘最小 bbox 净空为 259.845 px。计数去重口径和 full-page grid 方法固定于 `measurement_consistency.json`。
