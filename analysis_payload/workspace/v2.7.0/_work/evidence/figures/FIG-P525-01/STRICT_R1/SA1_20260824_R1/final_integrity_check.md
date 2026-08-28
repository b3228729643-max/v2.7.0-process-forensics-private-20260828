# FIG-P525-01｜STRICT R1｜SA1 证据闭合核验

| 项目 | 观察 | 状态 |
|---|---:|---|
| 必需交付物 | 22/22 个核心文件存在（含公共样式字号上下文、overlap reconciliation JSON/CSV、最终一致性 JSON 和本闭合核验记录） | PASS |
| glyph 清单 | 112，逐项含 PDF bbox 与 raw no-dilation mask | PASS |
| 语义组件清单 | 14，题注为一个语义父段 | PASS |
| 图形组件清单 | 15，覆盖 fill、6 条边、3 marker、3 spoke、node border | PASS |
| mask manifest | 141 = 112 glyph + 14 semantic + 15 graphic | PASS |
| 视觉临界/失败对 | 9/9 均有 raw ROI、A/B 分离 mask、overlap、overlay、8x | PASS |
| 数学语义发现 | 1 项独立的相邻正文命题复算；非空间成对关系，证据为 `math_semantics_recheck.md`、`adjacent_source_context.tex`、`critical/MATH_UNQUALIFIED_NONUNIQUENESS_*` | PASS |
| JSON/CSV 一致性 | pixel、源字号、overlap、最终状态均与八栏报告和 `SA1_RESULT.md` 一致；overlap unique=pair-sum=387、duplicate=0 | PASS |
| 终检 | `final_consistency_check.json` 的 14/14 跨文件检查均为 true | PASS |
| 字号覆盖复核 | 普通 node=10.0pt（`shared_style_font_context.tex:276`）；失败仅显式 8.8pt 图例 19 glyph/2 components | PASS |
| unknown/missing 硬门 | 0 | PASS |
| 严格总验收 | 至少一个硬门为 FAIL（实际多个） | FAIL |

结论：证据闭合；严格结论只能是 **FAIL**，下一角色为 **SA2**。
