# FIG-P020-01｜独立 SA1 严格复核（R4）

- RESULT: **FAIL**
- CANDIDATE: `FIG-P020-01-STRICT-R4-OFFICIAL-R89`
- ROUTE: `SA2_R5_REQUIRED`
- SOURCE_WRITES: `NONE`

## 独立结论

SA1 在不沿用根线程视觉结论的前提下复核了 R4 源码、官方物理页 17、standalone、原生 300 dpi 叠加图与全部 26 个 1:1 ROI。几何门通过，但关系节点中的 `\to` 被单独提升为 14.4458pt，普通正文为 9.9626pt，角色字号比为 `1.450003`，超过 Goal 的公式/普通文字角色上限和强调绝对上限。其实际箭头实墨 23px、相邻 CJK 正文约 37px，像素比仅 `0.6216`，视觉上既突兀增大源字号，又没有形成与正文协调的实墨高度。

## 硬门矩阵

| 门 | 结果 | 证据 |
|---|---|---|
| SOURCE_FONT | PASS | 最低普通文字 9.9626pt；箭头本身 14.4458pt |
| PIXEL_HEIGHT | PASS | 13/13 像素下限通过；箭头 23px |
| SAME_CLASS_RATIO | PASS | 同类正文一致 |
| ROLE_RATIO | **FAIL** | `14.4458/9.9626=1.450003` |
| VISUAL_HARMONY | **FAIL** | 箭头实墨/相邻 CJK 字高 `23/37=0.6216` |
| OVERLAP / CLIP | PASS | 26/26 ROI；非法重叠 0、裁切 0 |
| MIN_CLEARANCE | PASS | 独立复测最小 15.033px |
| MATH / TEXT | PASS | 四节点与连接语义一致 |
| GRAYSCALE / PAGE | PASS | 官方连续页与灰度视图可读 |

## 必须修复

不得继续通过放大文本字号解决箭头像素下限。SA2 应把局部 `\to` 改为与文字角色分离的 TikZ 线箭头/图形箭头，使普通文字保持统一字号，同时保证图形箭头与左右文字至少 3px 净空、非法重叠与裁切均为 0。修复后必须生成新 R5 证据并重新走独立 SA1；本 R4 不得进入 SA3 或 `STRICT_FINAL`。

## 证据

- `fullbook_page_17.pdf`
- `full_page_300dpi.png`
- `standalone_300dpi.png`
- `grayscale_300dpi.png`
- `after_font_audit.csv`
- `after_pixel_measurements.csv`
- `after_overlap_report.csv`
- `after_text_measurement_overlay_300dpi.png`
- `roi/`（26/26 原始 1:1）
