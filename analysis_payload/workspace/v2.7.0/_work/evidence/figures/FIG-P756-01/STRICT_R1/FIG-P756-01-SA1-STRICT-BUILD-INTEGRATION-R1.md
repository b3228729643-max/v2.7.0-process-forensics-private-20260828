# FIG-P756-01｜独立 SA1 严格全书集成复核（R1）

- ROLE: `SA1`
- MODEL: `gpt-5.6-terra / max`
- RESULT: **FAIL**
- NEXT_ROLE: `SA2`
- SOURCE_WRITE: `NONE`

## 硬阻断

FIG-P756-01 当前没有真实落入连续全书 PDF，不能以单图/page wrapper 成功替代全书集成。

- 源码链：`main_full.tex:3 -> main.tex:155 -> V5-C08.tex:825 -> full_course_synthesis_map.tex`。
- 图源自身在第 6--85 行使用 `figure[htbp]`，题注在第 83 行、标签 `fig:V5-C08-course-map` 在第 84 行。
- 章节第 804--830 行把该输入放在 `solution` 内；公共样式第 497--507 行把 `solution` 定义为 `enhanced,breakable` 的 `tcolorbox`。
- 当前全书日志读取图源后，在 `main.tex:157` 报 `LaTeX Error: Float(s) lost.`；诊断构建虽写出 813 页 PDF，日志仍为失败。
- 当前 AUX 不含 `fig:V5-C08-course-map`。物理页 801／印刷页 788 只有“图 37.8”的正文引用、读图检查和后续练习，没有真实图形或题注；该编号来自旧 AUX，不是当前候选的有效落版证据。

## 严格门

| 项目 | 结果 |
|---|---|
| 候选身份、图源、章节引用链 | PASS |
| 源码标签与题注一致性预检 | PASS |
| `figure` 外层环境可安全落版 | FAIL |
| 全书日志无致命浮动错误 | FAIL |
| AUX 含当前图标签 | FAIL |
| 最终 PDF 真实落图与题注 | FAIL |
| `PAGE_INTEGRATION_PASS` | FAIL |
| 字号／像素／比例／重叠／裁切／净空 | FAIL：严格最终证据缺失或 UNKNOWN |
| 灰度与视觉协调 | FAIL：旧 wrapper 图不等于当前全书最终证据 |

`STRICT_FINAL/` 不存在，第 9.2.1 节要求的九类核心产物未齐；旧 R3 图只能表明 wrapper 候选大致可读，不能证明当前连续版集成。

## SA2 白名单建议

只修改 `src/讲义源码/第05册_采样方法主题模型与图排序/chapters/V5-C08.tex`：在 holdout 例题解答结论后立即关闭 `solution`，再让既有图、`FloatBarrier` 与读图检查处于普通垂直流中，并删除原图后的重复 `end{solution}`。不得改图源、数学结论、题注、标签、编号、公共样式、索引或构建入口。

修复后必须重新连续全书构建并证明日志无 `Float(s) lost`、AUX 有当前标签、PDF 有真实图和题注；随后生成本图完整 300 dpi 严格证据，再走全新 SA1 与隔离 SA3。
