# FIG-P573-01｜SA1 严格视觉／数学盲审（R94）

## 1. 冻结输入、定位与覆盖

- 冻结输入：`D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\build\strict_current_r94_fullbook\main_full.pdf`；只读。
- 以 R94 题注“蒙特卡罗积分把曲线下的面积…”独立定位：物理页 **620**、印刷页 **607**、图 **31.2**。
- 300dpi 固定整页网格为 `2481×3508`；整页后以整数像素裁切，无 resize。覆盖 18 个语义文字／公式对象、148 个逐字形记录、20 个矢量对象（16 个 non-halo final-visible，其中 15 个是跨对象 pair 组件；2 个 opaque halo）。

## 2. 源级有效字号

`SOURCE_FONT_PASS = false`。普通 PGFPlots tick label 为源码第 8 行 `8.6pt`，共 12 个独立刻度对象低于 9.5pt；其余图内 node／axis label／公式基准为 9.5pt，caption 由 11pt 文档的 `\small`（10pt）产生。自然数学 script 仅由 9.5pt 基公式产生，逐字形像素另验。

## 3. 原生 300dpi 字形与比例

`PIXEL_HEIGHT_PASS = false`（失败 24 个独立 glyph／字面语义项）；`SAME_CLASS_RATIO_PASS = false`（失败 2）；`ROLE_RATIO_PASS = false`（失败 3）。D 仅比较同面板、同 role、同 script class 的实际 independent raw H_ink；E 仅用可比 script 相对于 TICK base，不可比项记为 N/A。每个 CJK／全角字形仍按自身 30px 门，连续 CJK 语义组件仅作 D/E 可追溯聚合，绝不替代单字门。

## 4. 无膨胀 mask、重叠、净空与裁切

`PAIR_COUNT = 423 = C(18,2)+18×15`；`OVERLAP_PIXEL_COUNT = 0`（无重复 union，pair-sum=0，失败 pair=0）；`CLIP_PIXEL_COUNT = 0`；`MIN_TEXT_CLEARANCE_PX = 16.0`；`CLEARANCE_PASS = true`。节点文字—公式框只对 final-visible **border stroke**测 5px，不把白色 node fill／bbox 误记为 0px。V019 是 `\frac` 的内部分数线，已并入同一公式的 semantic foreground 作对外关系检查，绝不按外部 line／node-border 与其父公式自配对。所有 opaque halo 均保存 pre-occlusion、halo、final-visible mask。临界／失败 pair 共 0 包，均含 raw、A/B raw mask、intersection、overlay、1:1 和 8×NN。

## 5. 四视图、灰度与页面融合

四视图齐全：`full_page_200dpi.png`、`full_page_300dpi_native.png`、`figure_crop_300dpi.png`／`standalone_300dpi.png`、`grayscale_300dpi.png`。`GRAYSCALE_PASS = true`；曲线、样本 stem/marker、均值实线和积分虚线仍可由线型／点型区分。`READING_ORDER_PASS = true`；`PAGE_INTEGRATION_PASS = true`。

`FONT_VISUAL_HARMONY_PASS = false`。本项不能因“仍可辨认”放宽：8.6pt 刻度低于硬门，故不接受以缩小或局部可读性作为协调性通过理由。

## 6. 数学、文本与题注一致性

`MATH_SEMANTICS_PASS = true`。重算：$h(u)=\exp(-u^2/2)$、四点 $(0.1,0.4,0.7,0.8)$ 的均值为 0.8567456002，图示 0.8567；$\int_0^1h(u)\,du=0.8556243919$，图示 0.8556。对 $U_i\sim\mathrm U(0,1)$，$E[h(U)]=\int_0^1h$ 与图内 $\widehat\mu_N=N^{-1}\sum h(U_i)$ 一致；caption 的“竖线四个均匀样本、虚线参考值”与直接正文一致。

`TEXT_CONSISTENCY_PASS = true`。

## 7. 机器一致性与证据完整性

`EVIDENCE_INTEGRITY_PASS = true`。`final_consistency_check.json`逐行核对 VECTOR_ID、DRAWING_INDEX、CATEGORY、OWNER、pre/halo/final mask 路径、pair B_CATEGORY／阈值、pair 数、临界包和报告数字；`machine_terminal_check.csv/json/md`再交叉核对非空 mask、全部失败／临界包的 8 件证据、relation/pair/clearance 计数、字号／像素／D/E 失败数和最终 RESULT。任何未知或错配即 integrity FAIL。

## 8. 判定与下一角色

**RESULT: FAIL → SA2。** 直接阻断项至少包括 `SOURCE_FONT_PASS=false`（8.6pt tick）以及所有逐字形像素门的失败项；即使其他视觉／数学项通过，§9.2.1 要求全门为 true 才能转 SA3。
