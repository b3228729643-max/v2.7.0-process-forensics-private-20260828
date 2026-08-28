# FIG-P609-01｜根线程最终验收（R3）

- FIGURE_ID: `FIG-P609-01`
- ROUND: `R3`
- ROOT_ACCEPTANCE: `PASS`
- OVERALL: `PASS`
- SPLIT_REQUIRED: `NO`
- BLOCKERS: `NONE`
- unresolved: `NONE`

## 三条独立证据链

根线程已直接核验当前图源、V5-C03 邻文与公式、正式 wrappers、数值与图源清单、两份 R3 PDF、四张 PNG、LOG/FLS/AUX，并完整读取：

1. `FIG-P609-01-ROOT-APPLY-R3.md`：根线程局部构建、数值复算与视觉亲看为 `PASS_LOCAL / NO SPLIT`；
2. `FIG-P609-01-SA1-R3.md`：全新 SA1 独立取证为 `PASS / NO SPLIT / NONE`；
3. `FIG-P609-01-SA3-R3.md`：隔离旧报告和状态的 SA3 盲审为 `PASS / NO SPLIT / NONE`。

三者均从当前原始对象与 R3 原始证据得出结论，没有用中央清单的流程状态替代证据。

## 根线程最终复核

- 数学语义统一为有限样本加权诊断：
  $\widehat\tau_{K,n}=1+2\sum_{k=1}^{K}(1-k/n)\widehat\rho_k$，
  $\widehat N_{\mathrm{eff}}=n/\widehat\tau_{K,n}$，并要求 $\widehat\tau_{K,n}>0$。
- 图中 $K=6<n$，只纳入 $k=1,\ldots,6$；$k=0$ 仅作 ACF 基准点，后续滞后明确为未绘出且未纳入。未指定 $n$，所以不报告伪数值 ESS。
- 独立复算一致：$\sum\widehat\rho_k=3.66$，$\sum k\widehat\rho_k=11.21$，$\widehat\tau_{6,n}=8.32-22.42/n$；最小允许 $n=7$ 时分别为 5.1171428571 与 1.3679508654。
- A–I 全部通过；普通读者文字最低 9.6pt、轴标签 9.8pt、标题 10.4pt，无整体缩放。ACF stem/圆点、窗口、截断虚线/文字与方向箭头在灰度下仍有冗余编码。
- 页面阅读链为“首引 → 左侧经验 ACF → 箭头 → 右侧有限样本加权 ESS → 单结论题注 → 读图顺序”；无重叠、裁切、溢出或题注/导读孤行。
- 两份 TeX Live 2026 日志硬诊断为 0；FLS 指向正式 wrapper、中央版本源与当前图源；AUX/LoF 为图 32.9、印刷页 644。局部 PDF 物理页为 1，不与印刷页身份混淆。
- 当前对象共同承担“正相关 → 方差权重增大 → 同长度 ESS 减小”的单一任务，左右角色已经视觉分离，继续拆分会割裂结论。

## B56 串项说明

独立 SA1 指出：B56 的身份、图源、类型和主要硬门属于 P609，但其中个别“轨迹/运行均值/预热段/目标值 2”句子误混入 P608 文案。按权威顺序及当前源、邻文、附录 A 和清单的一致交集，该串项不应驱动 P609 返工；当前图级验收无未决项。原始主提示词保持只读，此事实留在本验收证据中供最终问题汇总。

## 最终裁决

`FIG-P609-01` 已满足根线程、全新 SA1 与隔离 SA3 三重门，接受当前候选并关闭本图。

ROOT_ACCEPTANCE: **PASS**  
SPLIT_REQUIRED: **NO**  
BLOCKERS: **NONE**  
NEXT_ACTION: **更新中央清单为 `RESOLVED_EVIDENCE_CLEAR`；后续不为本图重复构建。**
