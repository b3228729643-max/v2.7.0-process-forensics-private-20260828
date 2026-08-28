# FIG-P556-01｜STRICT R1｜SA1 正式验收

RESULT: FAIL

NEXT_ROLE: SA2

## 输入与覆盖

- 冻结 R93 PDF 的独立物理定位：第 601/813 页；SHA-256 记录于 `render_manifest.json`。
- 图源 `fig_v5_c01_stationary_fixed_point.tex`；紧邻正文 `V5-C01.tex:624--625`；公共字号样式证据 `statlearnbook.sty:276`。
- 覆盖 124 glyph、21 个语义文字组件、25 个线/曲线/marker/axis/arrow/node-border/fill 组件；所有 TEXT--TEXT、TEXT--graphic 和 TEXT--edge 对均登记。
- 原生视图：`full_page_200dpi.png`、`full_page_300dpi_native.png`、`figure_crop_300dpi.png`、`standalone_300dpi.png`、`grayscale_300dpi.png`；300dpi 测量图未 resize。
- `full_page_300dpi_grid.json` 固定全页原生测量网格；`machine_terminal_check.csv/json/md` 对输出完整性与计数交叉一致性作终检。

## 硬门矩阵

| Gate | Observed | Required | Status |
|---|---:|---:|---|
| SOURCE_FONT_PASS | false | true | FAIL |
| SOURCE_FONT_FAILURE_COUNT | 76 glyphs / 20 components | 0 | FAIL |
| PIXEL_HEIGHT_PASS | false (30 failures) | true | FAIL |
| SAME_CLASS_RATIO_PASS | false | true | FAIL |
| ROLE_RATIO_PASS | false | true | FAIL |
| OVERLAP_PIXEL_COUNT | 30 | 0 | FAIL |
| CLIP_PIXEL_COUNT | 0 | 0 | PASS |
| MIN_CLEARANCE | text/text raw=28.000, bbox=14.412; line=0.000; border=6.000; edge=33.000 | 4/3/5/6 | FAIL |
| CROSS_PANEL_PASS | true | true | PASS |
| FONT_VISUAL_HARMONY_PASS | false | true | FAIL |
| MATH_SEMANTICS_PASS | true | true | PASS |
| PROBABILITY_SEMANTICS_PASS | true | true | PASS |
| TEXT_CONSISTENCY_PASS | false | true | FAIL |
| GRAYSCALE_PASS / PAGE_INTEGRATION_PASS | true / true | true / true | PASS |

## 强制发现

1. **字号与视觉协调 FAIL。** 图内刻度 8.7pt、曲线标签 9.3pt、轴/固定点标签 9.4pt、初值/说明框 9.2pt，均低于 9.5pt；公共 `every node=\small` 不覆盖这些局部显式字体。`FONT_VISUAL_HARMONY_PASS=false`。
2. **逐字形与比例门。** 各 literal 运算符/标点（含 `=`,`+`,`<`,小数点、映射箭头、星号）各自以 raw mask 测量；所有失败详见 `after_pixel_measurements.csv` 与 8x ROI。相同类比例结果见 `same_class_ratio_audit.csv`。
3. **符号一致性 FAIL。** 图内使用 $r^*$，题注使用 $r_\star$ 表示同一固定点却未声明等价；正文概率语义 $\rho=(0.4,0.6)$、映射、固定点和两条 cobweb 坐标均正确。

## SA1 结论

任一硬门 FAIL 即不得进入 SA3。本轮结论为 **FAIL**，下一角色为 **SA2**；SA2 应只修订指定图源/直接正文后重新冻结并接受全新 SA1 复审。

机器终检：`MACHINE_EVIDENCE_INTEGRITY_PASS=true`，其只确认取证完整/计数一致；质量结论仍为 `FAIL`。
