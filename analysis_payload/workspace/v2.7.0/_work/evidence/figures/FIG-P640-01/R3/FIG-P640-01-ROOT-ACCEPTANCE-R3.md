# FIG-P640-01｜根线程最终验收（R3）

- FIGURE_ID: `FIG-P640-01`
- ROUND: `R3`
- ROOT_ACCEPTANCE: `PASS`
- OVERALL: `PASS`
- SPLIT_REQUIRED: `NO`
- BLOCKERS: `NONE`
- unresolved: `NONE`

## 验收依据

根线程已直接核验当前图源、正文邻域、standalone/page wrapper、R3 两份 PDF、三张 300 dpi PNG、最终 LOG/FLS/AUX、目标 source/numeric JSON 记录与中央清单唯一行，并完整回读以下三份相互独立的 R3 报告：

1. `FIG-P640-01-ROOT-APPLY-R3.md`：根线程局部构建与亲看为 `PASS_LOCAL / NO SPLIT`；
2. `FIG-P640-01-SA1-R3.md`：全新 SA1 独立复审为 `PASS / NO SPLIT / NONE`；
3. `FIG-P640-01-SA3-R3.md`：隔离历史结论的 SA3 盲审为 `PASS / NO SPLIT / NONE`。

三条证据链结论一致，未相互替代，也未把 99/99 初审覆盖或旧状态当作最终通过证据。

## 根线程复核结论

- 数学与边界：轮末 ACF 为 $\rho^{2k}$；渐近 ESS 比例为 $(1-\rho^2)/(1+\rho^2)$。右轴合法绘图区止于 $|\rho|=.99$，端点为 `(.99,.0100499975)`；$|\rho|\to1^-$ 仅表示从 $|\rho|<1$ 内逼近时的极限 0。
- 教学闭环：两面板标题、题注、首次引用、`\FloatBarrier` 与图后专属读图句一致，明确“先读轮末 ACF，再读渐近 ESS，最后辨认合法边界”。
- 字号与布局：全部显式可见字号为 9.6/9.8pt，无整体缩放；彩色整页、灰度整页与 standalone 均无碰撞、裁切、越界或曲线穿字。
- 灰度冗余：左图实线、密虚线、点划线与颜色共同编码；右图端点、曲线和极限文字在灰度证据中仍可辨。
- 技术与身份：standalone/page PDF 分别为 40,372/68,100 bytes、A4 单页；AUX 将标签解析为图 33.7、页 671；两份最终日志硬诊断与引用重跑项均为 0，FLS 指向当前 wrapper 与当前图源。
- 数值复算：`.95^24=0.291989024338772`；$|\rho|=.5$ 时 ESS 比例为 `.6`；`.99` 时为 `.010049997474875`，与图源和 numeric manifest 一致。
- 拆分判断：两面板构成“混合速度 → 统计效率”的连续教学链，当前密度与阅读顺序清楚，不拆图。

## 最终裁决

`FIG-P640-01` 已满足专属 SA2 修订、根线程 R3 应用、全新 SA1 独立复审和隔离 SA3 盲审的完整闭环，接受当前候选并关闭本图。

ROOT_ACCEPTANCE: **PASS**  
SPLIT_REQUIRED: **NO**  
BLOCKERS: **NONE**  
NEXT_ACTION: **中央清单更新为 `RESOLVED_EVIDENCE_CLEAR`；后续不再为本图重复构建。**
