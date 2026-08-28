# FIG-P525-01 根线程复核｜STRICT R1

结论：**FAIL → SA2**。本记录只签发失败事实，不授予最终 PASS。

## 根线程独立回读

- 冻结对象为官方 R93 物理第 571 页；图源、相邻正文、原生 300 dpi 图裁、灰度、整页融合、测量 overlay 与四个关键 1:1/8× ROI 均已查看。
- `after_font_audit.csv` 共 112 行：普通 node/公式由公共 `every node/.append style={font=\small}` 覆盖为 10.0pt，旧 9.4pt 普通节点失败计数已清零；仅两段显式 8.8pt 图例失败，共 19 glyph / 2 组件。图例/基准角色比为 0.8800，字号协调失败。
- `after_pixel_measurements.csv` 共 112 行，其中 `PIXEL_HEIGHT_PASS=false` 为 11 行；综合源字号与像素/比例后的行级 `PASS_FAIL=FAIL` 为 28 行，两种计数口径没有矛盾。
- `after_overlap_report.csv` 共 301 对，四对真实失败：`φ_{:1}`×outer-edge-3=88px、`φ_{:2}`×outer-edge-2=126px、`φ_{:3}`×outer-edge-2=170px、`θ_{2j}`×document-diamond=3px。双方 raw mask 未膨胀，净空均为 0，clip 总数为 0；四个文字 bbox 彼此不交，故 pair-sum=unique=387、duplicate=0。
- 独立数值复算得到 `det(Phi)=0.4288`、`theta=(0.3,0.45,0.25)`、重构残差约 0。固定且仿射独立的当前 `Phi` 下系数唯一；相邻正文无条件写“同一点可多解”缺少退化主题、联合参数化或置换等限定，因此数学/图文一致性失败。
- `final_consistency_check.json` 的 14/14 项均为 true；必需证据无 UNKNOWN/MISSING。该一致性 PASS 只表示失败证据闭合，不改变图的严格 FAIL。

## SA2 边界

只可定向修复本图源及上述直接相邻正文：提升两段图例字号、移开三个主题标签与 `theta_{2j}`、修正文句的唯一性条件；不得整体缩放、修改公共样式或中央状态。修复后必须生成新官方候选并重新执行全新 SA1、隔离 SA3 与根验收。
