# FIG-P602-01 R103 SA3 fresh isolated：composite-parent gate

- HANDOFF_ID：`C-FIG-P602-01-R103-SA3-FRESH-ISOLATED-V1`
- reviewer：`/root/sa3_fig_p602_r103_fresh_isolated`
- reviewed native view：`figure_crop_300dpi.png`，1810×1564 px，未缩放计数；同时逐项对照 `machine_text_run_coverage.csv`、`machine_glyph_inventory.csv` 与图源。
- 规则：同一 TikZ node 不是合并理由。具有独立语义行、独立 bbox、可独立发生裁切/碰撞的标题、变量、动作、比较、赋值、caption label 均拆分；只保留单一连续语义行或不可分割数学断言为一个父对象。

| 父对象 ID | 精确可见内容 | PDF text-run 数 | native bbox `[x0,y0,x1,y1]` | 人工 composite 裁决 |
|---|---|---:|---|---|
| T01_CURRENT_NODE_TITLE | 当前状态 | 1 | [678,33,832,68] | 保留为独立标题行；已与下一行变量拆分。 |
| T02_CURRENT_NODE_VARIABLE | 状态变量 $X_t$ | 3 | [651,81,854,122] | 保留为独立变量说明；中文与数学 span 共同组成同一行，不再按字体 run 拆语义。 |
| T03_CANDIDATE_NODE_ACTION | 按提议核抽取候选 | 1 | [595,218,911,253] | 保留为独立动作行；已与候选变量行拆分。 |
| T04_CANDIDATE_NODE_VARIABLE | 候选变量 $Y$ | 2 | [656,266,849,301] | 保留为独立变量说明；中文与数学 span 属同一不可分割短句。 |
| T05_RATIO_HEADER | 计算接受率（未规范化目标记为 $\pi_{\mathrm u}$ 且正向流为正） | 4 | [316,415,1187,457] | 保留为单一连续说明行；四个 PDF runs 仅源于中西文/数学字体切换，句法上没有可独立关系。 |
| T06_RATIO_FORMULA | $\alpha_t(Y)$ 取 $\min\{1\text{ 与 }\pi_{\mathrm u}(Y)q(X_t\mid Y)/[\pi_{\mathrm u}(X_t)q(Y\mid X_t)]\}$ | 20 | [406,470,1101,578] | 保留为一个数学断言；分子、分母、上下标和定界符是同一公式内部排版，不套独立 TEXT–TEXT 门。独立绘制的分数线已另列 M01。 |
| T07_DECISION_DRAW | 抽取区间 [0 到 1] 的均匀变量 $U$ | 8 | [468,771,1038,811] | 保留为独立抽样动作行；已与下一行比较判定拆分。 |
| T08_DECISION_COMPARE | 并判定 $U\le\alpha_t(Y)$？ | 5 | [567,819,941,860] | 保留为独立比较公式行；可独立碰撞/裁切，故不与 T07 合并。 |
| T09_ACCEPT_NODE_ACTION | 接受候选 | 1 | [178,1007,335,1041] | 保留为独立分支动作行；已与赋值行拆分。 |
| T10_ACCEPT_NODE_ASSIGNMENT | $X_{t+1}$ 取 $Y$ | 4 | [175,1055,337,1097] | 保留为独立状态赋值公式；可独立碰撞/裁切。 |
| T11_REJECT_NODE_ACTION | 拒绝并记录旧状态 | 1 | [1091,1007,1408,1041] | 保留为独立分支动作行；已与赋值行拆分。 |
| T12_REJECT_NODE_ASSIGNMENT | $X_{t+1}$ 保持 $X_t$ | 5 | [1141,1055,1354,1097] | 保留为独立状态赋值行；中文与数学 runs 共同构成一个赋值关系。 |
| T13_PROPOSAL_LABEL | 提议 | 1 | [782,151,860,186] | 原子 edge label；独立于对应箭线与上下节点。 |
| T14_CALCULATE_LABEL | 计算 | 1 | [783,338,859,373] | 原子 edge label；独立于对应箭线与上下节点。 |
| T15_DECISION_LABEL | 判定 | 1 | [782,612,860,647] | 原子 edge label；独立于对应箭线与上下节点。 |
| T16_ACCEPT_LABEL | 接受 | 1 | [278,891,356,926] | 原子 branch label；独立于分支箭线与菱形/接受框。 |
| T17_REJECT_LABEL | 拒绝 | 1 | [1151,891,1228,926] | 原子 branch label；独立于分支箭线与菱形/拒绝框。 |
| T18_SELFLOOP_LABEL | 拒绝后保持旧状态 | 1 | [1091,1412,1408,1447] | 原子 self-loop label；独立于自环曲线与拒绝节点。 |
| T19_CAPTION_LABEL | 图 32.5 | 2 | [305,1479,426,1517] | figure label 的字重、bbox 与裁切风险独立，已从 caption sentence 拆出。 |
| T20_CAPTION_TEXT | Metropolis–Hastings 单次更新中的提议判定及拒绝自环。 | 2 | [469,1480,1479,1523] | 保留为单一 caption sentence；两个 runs 只因 Latin/CJK 字体切换，无第二个独立句子。 |

## 最终冻结

- 文字/公式/label/caption 前景父对象：20。
- node border：6。
- directed LINE_ARROW：5。
- SELF_LOOP_ARROW：1。
- 独立 MATH_RULE：1。
- 最终 `N=33`；完整无序 pair 分母 `C(33,2)=528`。
- 65 个图内/caption PDF text runs 均映射到上述 20 个父对象；194 个非空格可见 glyph 均唯一映射；8 个空格因无可见墨迹排除。
- 本门完成后方开始 528 行人工 pair ledger；此前没有写入 pair 人工裁决。
