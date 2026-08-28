# FIG-P556-03｜STRICT R1｜SA1 正式验收

RESULT: FAIL

NEXT_ROLE: SA2

冻结 R93 最终 PDF 被独立定位到物理第 602/813 页。取证覆盖 114 个可见 glyph、16 个语义文字组件、25 个线/箭头/marker/node-border/fill 组件、120 个 TEXT--TEXT、304 个 TEXT--graphic 与 16 个 TEXT--edge 关系。原生视图为 200dpi 整页、300dpi 固定全页网格、裁图、standalone 和灰度。

| Gate | Observed | Required | Status |
|---|---:|---:|---|
| SOURCE_FONT_PASS | false | true | FAIL |
| SOURCE_FONT_FAILURE_COUNT | 84 glyphs / 14 components | 0 | FAIL |
| SOURCE_ROLE_FONT / SOURCE_CROSS_PANEL_FONT | true / true | true / true | PASS |
| PIXEL_HEIGHT_PASS | false (13 glyphs / 6 components) | true | FAIL |
| SAME_CLASS_RATIO_PASS | false | true | FAIL |
| ROLE_RATIO_PASS | false | true | FAIL |
| OVERLAP / CLIP | 0 / 0 | 0 / 0 | PASS |
| MIN_TEXT_CLEARANCE_PX | text/text raw=35.125, bbox=20.721; text/graphic=7.000; edge=19.000 | 4 / 3(or 5 node) / 6 | PASS |
| CLEARANCE_PASS | true | true | PASS |
| VISUAL_HARMONY_PASS / FONT_VISUAL_HARMONY_PASS | false / false | true / true | FAIL |
| MATH / PROBABILITY / TEXT | true / true / true | all true | PASS |

硬失败：图源局部明确声明的普通 9.4pt、9.2pt 与 8.8pt 文字均低于 9.5pt。共同 `every node=\small` 不改变这些局部样式；`FONT_VISUAL_HARMONY_PASS=false`。逐字形 raw H_ink（包括 `=`, 逗号、全角冒号、下标 `2` 等）及失败诊断均在 CSV 和 `critical/` 中。数学上，详细平衡可推出平稳性；$A=I_2$ 反例确实不连通且平稳分布不唯一，图文语义正确。

任一硬门失败即不能送 SA3。本轮只能 **FAIL → SA2**。

机器终检：`MACHINE_EVIDENCE_INTEGRITY_PASS=true`；它仅表示证据闭合，质量结论仍为 `FAIL`。
