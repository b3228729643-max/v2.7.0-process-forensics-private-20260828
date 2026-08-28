# FIG-P570-01｜ROOT VALIDATION｜STRICT R1／R94

结论：`FAIL → SA2`。不得进入 SA3，也不得沿用历史“已完成/通过”。

## 官方对象与根验范围

- 官方候选：`src/build/strict_current_r94_fullbook/main_full.pdf`，物理页 617／813、印刷页 604、图 31.1。
- 根线程回读了 `SA1_RESULT.md`、全部核心 CSV/JSON、对象与 mask 清单，并实际查看彩色、灰度、文字 overlay，以及 `REL_0274` 的原图、双方独立 mask、交集与 8× nearest overlay。
- 300 dpi 整页网格为 `2481×3508px`。8× 图仅用于人工看清像素，全部计数仍取原生 1:1 mask。

## 独立复算

- 对象：161 glyph + 10 语义文字组件 + 37 图形组件 = 208 个唯一对象；208 个 mask 链接均存在，根线程逐 PNG 复算空 mask 为 0。
- 前景 pair：10 个语义文字 + 27 个最终可见图形 = 37 个前景对象，`C(37,2)=666`；`pair_universe.csv` 为 666 行。
- 必查关系：45 text-text + 270 text-graphic + 10 text-edge + 27 graphic-edge = 352 行。
- 源字号失败 86 glyph／8 组件；实际字高失败 10 glyph／4 组件；D 同类比例失败 8／20 组；E 角色比例失败 1／20 组；字体视觉协调失败。
- 非法 overlap 总像素 0，clip 总像素 0；但 relation/pair/clearance 各有 1 个失败。

## 原生像素裁决

唯一几何失败是 `REL_0274`：`SEM_METHOD_REJECTION` 的最右“绝”字与 `GRAPHIC_METHOD_REJECTION_BORDER` 的最终可见虚线右边框没有交叠像素，但原生双方 mask 的最小净空为 `0px`，硬门要求节点内文字到边框至少 `5px`。8× nearest 图显示红色文字墨迹与绿色边框像素相贴；这不是节点外框 bbox 包含造成的假阳性。

IS 双边框的 pre-occlusion、真实白缝 halo/background 与 final-visible mask 已分开，质量关系只使用 final-visible 边框。数学、概率语义、箭头方向、题注、相邻正文、灰度与页面融合均通过，不能抵消字号、像素、比例、净空及协调性硬失败。

## 证据完整性

SA1 最终机器终检为 PASS：28／28 必需文件存在；208 对象 ID 唯一且 mask 非空；352 relations、666 pairs、93 组失败/临界证据闭合；底层 CSV、JSON、Markdown 一致记录 `relation_fail=1`、`pair_fail=1`、`clearance_fail=1` 和最终 `FAIL`。

下一角色只能是专属 SA2：提高 9.2pt/8.6pt 普通文字到硬门以上，结构化解决像素与 D/E/字体协调，并为接受—拒绝节点增加真实右侧净空；不得靠整体缩小或降低阈值。
