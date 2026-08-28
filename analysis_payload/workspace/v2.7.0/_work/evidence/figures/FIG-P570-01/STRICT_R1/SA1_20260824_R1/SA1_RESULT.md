# FIG-P570-01｜STRICT R1｜SA1 正式验收

RESULT: FAIL

NEXT_ROLE: SA2

独立 R94 定位：物理页 617/813（页内印刷页 604）。覆盖 161 个可见 glyph、10 个语义文字组件、37 个线/箭头/marker/node-border/fill/pre-halo 组件、666 个无序独立前景对象对；其中 TEXT--TEXT=45、TEXT--graphic=270、TEXT--edge=10、GRAPHIC--edge=27。四视图和 300dpi 固定网格均已落盘。

| Gate | Observed | Required | Status |
|---|---:|---:|---|
| SOURCE_FONT_PASS | false | true | FAIL |
| SOURCE_FONT_FAILURE_COUNT | 86 glyphs / 8 components | 0 | FAIL |
| SOURCE_ROLE_FONT / SOURCE_CROSS_PANEL_FONT | true / true | true / true | PASS |
| PIXEL_HEIGHT_PASS | false (10 glyphs / 4 components) | true | FAIL |
| SAME_CLASS_RATIO_PASS | false | true | FAIL |
| ROLE_RATIO_PASS | false | true | FAIL |
 | OVERLAP / CLIP | 0 / 0 | 0 / 0 | PASS |
 | RELATION / PAIR / CLEARANCE failures | 1 / 1 / 1 | 0 / 0 / 0 | FAIL |
 | MIN_TEXT_CLEARANCE_PX | text/text raw=42.105, bbox=21.415; text/graphic=0.000; edge=33.000 | 4 / 3(or 5 node) / 6 | FAIL |
| VISUAL_HARMONY_PASS / FONT_VISUAL_HARMONY_PASS | false / false | true / true | FAIL |
| MATH / PROBABILITY / TEXT | true / true / true | all true | PASS |

 硬失败：图源 L3/L7 的 9.2pt 普通 input/method/diagnostic 文字和 L31 的 8.6pt 注释低于 9.5pt；局部明确字体不由公共 `every node=\small` 覆盖。每个可见 glyph（含 `/`,`≤`,`–`,`|`、全角冒号/分号及所有下标/标点）均有独立 raw H_ink 与 mask。真实 text relation overlap=0、clip=0，但 `REL_0274` 的“接受--拒绝”节点文字与最终可见虚线右边框 raw 净空为 0px（要求 5px），故 relation/pair/clearance 各 1 项失败；节点 bbox 的包含关系不单独作为失败依据。IS 双线边框的 pre-occlusion/opaque-gap/final-visible 三套 mask 均保存，质量关系只使用 final-visible mask。数学、概率语义、箭头方向、题注与紧邻正文一致。

任何硬门失败均不得进入 SA3。本轮只能 **FAIL → SA2**。

机器终检：`MACHINE_EVIDENCE_INTEGRITY_PASS=true`；仅确认取证闭合，质量结论仍为 `FAIL`。
