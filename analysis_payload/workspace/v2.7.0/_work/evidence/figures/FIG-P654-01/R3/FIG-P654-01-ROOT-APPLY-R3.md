# FIG-P654-01 — ROOT APPLY R3

- timestamp: `2026-08-22T22:27:48+08:00`
- owner: `/root`（wrapper、清单、证据与状态单写者）
- RESULT: **PASS_LOCAL**
- SPLIT_REQUIRED: **NO**
- FINAL_ACCEPTANCE: **PENDING_FRESH_SA1_AND_BLIND_SA3**

## 本轮应用

1. 完整回读 `R2/FIG-P654-01-SA2-R2.md`、当前图源和 `V5-C05.tex` 相邻正文；SA2 的限域结论为 `FIXED / NO SPLIT`。
2. 保留 SA2 的数学、字号、短题注、alt 字符串和图后读图句修复；把其 `scale=0.94` 等价吸收到八个节点坐标中并删除 `scale=`，几何位置不变，源码不再包含整体缩放写法。
3. 同步 `v260_FIG-P654-01_standalone.tex` 与 `v260_FIG-P654-01_page.tex`：metadata 改为 v2.7.0；page wrapper 设页 685、图 34.1，并复制正式章节的首次引用、`\FloatBarrier` 和专属读图句。
4. 同步 V5-C05 `figure_sources.json` 与中央 `figure_manifest.csv` 的短题注、教学目标、alt、真实页码、字号、变量一致性、冗余编码和待独立复核状态。旧 `v2.3.1_*` 清单保留为历史证据，不冒充当前页码。

## 数学与图文一致性

- 先验核 `\prod_i\theta_i^{\alpha_i-1}` 与多项似然核 `\prod_i\theta_i^{n_i}` 相乘，得到
  `\boldsymbol\Theta\mid\boldsymbol n,\boldsymbol\alpha\sim\operatorname{Dir}(\boldsymbol\alpha+\boldsymbol n)`。
- 令 `\alpha_0=\sum_i\alpha_i`、`N=\sum_i n_i`，后验均值给出
  `\Pr(Y_{N+1}=i\mid\boldsymbol n,\boldsymbol\alpha)=(\alpha_i+n_i)/(\alpha_0+N)`，各分量之和为 1。
- 图源、章节、page wrapper、JSON 与 CSV 均使用同一 `\operatorname{Dir}`、`\Pr`、`\boldsymbol n`、`\boldsymbol\alpha`、`\alpha_0` 与 `N`；主题模型只画成虚线应用出口，没有被宣称为本章推导前提。

## 字号、布局与像素验收

- 普通节点和“应用”均为源级 9.6pt；后验与预测关键公式均为 11.8pt。图源及两个 wrapper 对 `resizebox`、`scalebox`、`adjustbox`、`transform shape` 和 `scale=` 的最终命中均为 0。
- 主链为带箭头实线，解释支线为无箭头细实线，应用支线为带箭头虚线；颜色之外还有方向、线型、边框和填充冗余。
- 根线程亲自查看以下当前 R3 证据：
  - `p654_root_r3_standalone_300dpi.png`
  - `p654_root_r3_full_page_200dpi.png`
  - `p654_root_r3_gray_page_300dpi.png`
  - `p654_root_r3_figure_caption_guide_crop_300dpi.png`
- 结果：八节点阅读方向清楚，箭头均停在节点边界，无穿字、交叉、重叠、裁切、越界、公式断裂或异常换行；灰度下主链、解释支线和应用支线仍可分；题注位于图后且读图句紧随其后。

## 构建、身份与顺序

- TeX Live 2026 LuaLaTeX 使用已填充缓存
  `C:\Users\ASUS\AppData\Local\Temp\statlearn-v2.7.0-texmf-cache` 定向构建。
- `p654_root_r3_standalone.pdf`：1 页 A4，40,918 bytes，metadata v2.7.0。
- `p654_root_r3_page.pdf`：1 页 A4，59,977 bytes，metadata v2.7.0，可见页码 685。
- 两份最终日志中 LaTeX/Package error、undefined control/reference/citation、fatal/emergency、missing character、font substitution、multiply defined、overfull/underfull 和待重跑引用硬诊断均为 0。
- page AUX 唯一记录
  `fig:V5-C05-dependency-graph = 图 34.1 / 页 685`。
- `pdftotext -layout` 的实际位置索引为：首次引用 90、短题注 804、读图句 832，故 `90 < 804 < 832`。
- 当前冻结整书仍为 805 页、4,851,007 bytes；其全书物理页 698／印刷页 685 是本轮 wrapper 定位依据。本轮按精简执行约束不重复整书 L1，最终物理页在汇总构建时统一确认。

## 清单与数值边界

- V5-C05 `figure_sources.json` 可解析为 10 条，目标源/label 唯一命中 1 条。
- 中央 CSV 可解析为 99 行×19列，99 个 `canonical_uid` 唯一，P654 唯一命中 1 条；总体验收保持 `待独立复核`。
- 本图为解析关系图，没有坐标轴、数据点或绘图数值数据；`numeric_recomputation.required=false`，中央 numeric manifest 目标为 0 合理。

`Tagged: no` 是公共模板当前能力的非阻断事实；权威 A--I、附录 A 与 B66 未把 PDF/UA 或实际 Alt tagging 规定为本图硬门，因此本轮未扩大公共样式范围。

## 根线程局部决定

FIG-P654-01 当前数学、图文、字号、自然宽度、页面融合、灰度冗余、metadata、日志和身份链局部门均通过，且单图任务清楚，无需拆图。该结论不是最终放行；下一步必须由不读取 R1/R2/本报告的全新 SA1 独立复核，通过后再进入盲审 SA3。
