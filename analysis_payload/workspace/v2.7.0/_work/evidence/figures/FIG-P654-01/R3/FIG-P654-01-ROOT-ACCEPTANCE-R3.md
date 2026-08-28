# FIG-P654-01 — ROOT FINAL ACCEPTANCE R3

- timestamp: `2026-08-22T22:47:36+08:00`
- owner: `/root`（最终接受与中央清单单写者）
- result: **ROOT_ACCEPTANCE=PASS**
- split: **NO**
- final manifest status: **通过**

## 三角色结论

| 角色 | 正式证据 | 结论 |
|---|---|---|
| 专属 SA2 | `R2/FIG-P654-01-SA2-R2.md` | FIXED / NO SPLIT |
| 根线程局部门 | `R3/FIG-P654-01-ROOT-APPLY-R3.md` | PASS_LOCAL / pending independent review |
| 全新独立 SA1 | `R3/FIG-P654-01-SA1-R3.md` | PASS / NO SPLIT |
| 全新盲审 SA3 | `R3/FIG-P654-01-SA3-R3.md` | PASS / NO SPLIT |

SA1 与 SA3 均从空历史启动，并被禁止读取 P654 的 R1/R2、旧代理报告、SA2、根线程报告及状态摘要；两者只从当前 TeX、wrapper、JSON/CSV、AUX/FLS 与 R3 原始 PDF/log/PNG 独立取证。根线程已完整回读两份正式报告，结论一致且均无阻断、新回归或未解决项。

## 接受依据

1. **数学语义**：先验核与多项似然核相乘得到
   `\operatorname{Dir}(\boldsymbol\alpha+\boldsymbol n)`；单步预测为后验均值
   `(\alpha_i+n_i)/(\alpha_0+N)`，全类别归一化为 1。图内条件变量、章节、wrapper、JSON 与 CSV 逐符号一致。
2. **对象—关系—结论**：四条实线有向边构成“前置线索→似然/先验→共轭后验→预测”主链；两条无箭头细线仅表示参数解释关联；一条虚线有向边只表示主题模型应用出口，没有虚构同等推导或反向前置。
3. **阅读顺序**：正式章节和 page wrapper 均为首次引用→图与短题注→`\FloatBarrier`→专属“先看—再看—最终”读图句；PDF 实际文本位置为 `90 < 804 < 832`。
4. **字号与布局**：普通节点及“应用”均为 9.6pt，后验/预测关键公式均为 11.8pt；`resizebox`、`scalebox`、`adjustbox`、`transform shape` 和 `scale=` 最终命中为 0。箭头停边，无穿字、交叉、重叠、裁切、越界或异常断行。
5. **灰度与页面融合**：实线有箭头、细实线无箭头、虚线有箭头以及节点边框/填充共同编码；300dpi 灰度证据不依赖颜色即可区分。首引、图、短题注和导读形成连续教学单元，局部 wrapper 页尾留白不冒充生产页回归。
6. **构建与身份**：TeX Live 2026 LuaLaTeX 的 standalone/page 均为 A4 单页、v2.7.0，分别 40,918/59,977 bytes；page 为页 685、图 34.1。两份最终日志的 LaTeX/Package error、fatal、未定义引用、缺字、字体替代和盒溢出硬诊断均为 0。
7. **证据与清单**：standalone、彩色整页、灰度整页及图+题注+读图句联合裁切均由根线程、SA1 和 SA3 实看通过。V5-C05 JSON 声明/实际均为 10 且目标唯一；中央 CSV 为 99 行×19列、99 个 UID 唯一、P654 唯一；本解析关系图无绘图数值数据，numeric manifest 目标为 0 合理。

`Tagged: no` 是公共模板当前能力的如实记录；v2.7.0 权威 A--I 与 B66 未将 PDF/UA 或实际 Alt tagging 规定为本图硬门，因此不据此扩大公共样式范围。

## 最终决定

FIG-P654-01 已满足 v2.7.0 权威 A--I、B66、全新独立 SA1、全新盲审 SA3 与根线程最终复核，现正式接受并关闭当前修订闭环。中央 `figure_manifest.csv` 的本图 `验收状态` 更新为 `通过`，`v240_resolution_status` 更新为 `RESOLVED_EVIDENCE_CLEAR`。

按 `codex-lean-execution` 的精简执行约束，本次接受不重复运行整书 L1；805 页、4,851,007-byte 整书基线继续作为汇总构建前基线，当前全书物理页 698／印刷页 685 的映射待批次或最终构建统一更新。
