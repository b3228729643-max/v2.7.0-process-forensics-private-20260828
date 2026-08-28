# FIG-P608-01 — ROOT APPLY R3

- timestamp: `2026-08-22T23:07:41+08:00`
- owner: `/root`（wrapper、清单、数值清单、证据与状态单写者）
- RESULT: **PASS_LOCAL**
- SPLIT_REQUIRED: **NO**
- FINAL_ACCEPTANCE: **PENDING_FRESH_SA1_AND_BLIND_SA3**

## 本轮应用

1. 完整回读 `R2/FIG-P608-01-SA2-R2.md`、当前图源及 `V5-C03.tex` 相邻正文；SA2 的限域结论为 `FIXED / NO SPLIT`。
2. 保留 SA2 对固定轨迹、运行均值、字号、直接标签、短题注、首次引用、`\FloatBarrier` 和图后读图句的修复。
3. 同步 `v260_FIG-P608-01_standalone.tex` 与 `v260_FIG-P608-01_page.tex`：metadata 改为 v2.7.0；page wrapper 按冻结总册 AUX 设为页 643、图 32.8，并复制正式章节的首次引用、图输入、`\FloatBarrier` 与专属读图句。
4. 同步 V5-C03 `figure_sources.json`、中央 `figure_manifest.csv` 与 `figure_numeric_manifest_v16.json`；中央总体验收保持待独立复核，没有提前放行。

## 数值与图文一致性

- 固定轨迹为 20 个确定值；舍弃 `t=1,...,5` 后，按
  `\overline X_{6:t}=(t-5)^{-1}\sum_{s=6}^{t}X_s` 复算 `t=6,...,20`。
- 图源和数值清单均含 15 个保留样本运行均值点；根线程复算为 `15/15` 一致、`NUMERIC_MISMATCH=0`。
- 关键末三点为 `t=18: 2.0077`、`t=19: 2.0071`、`t=20: 2.0000`；四位小数最大舍入误差为 `0.0000428571`，小于声明容差 `0.00005`。
- 上面板明确给出轨迹、前 5 步预热段和后 15 步保留样本；下面板明确使用 `\overline X_{6:t}`，并以点划线标出目标值 2。图、正文、wrapper、JSON 与 CSV 的对象和结论一致。

## 字号、布局与像素验收

- 普通图内文字、刻度和直接标签为源级 9.6pt；面板标题与轴名为 10.8pt。低于 9.5pt 的显式字号命中为 0。
- 图源对 `resizebox`、`scalebox`、`adjustbox`、`transform shape` 与 `scale=` 的最终命中均为 0。
- 阴影预热段、虚线分界、点划目标线、轨迹圆标记和运行均值方标记提供颜色之外的冗余编码。
- 根线程亲自查看以下当前 R3 证据：
  - `p608_root_r3_standalone_300dpi.png`
  - `p608_root_r3_full_page_200dpi.png`
  - `p608_root_r3_page_300dpi.png`
  - `p608_root_r3_gray_page_300dpi.png`
  - `p608_root_r3_figure_caption_guide_crop_300dpi.png`
- 结果：两面板标题、轴名、刻度、直接标签与曲线清晰；无重叠、穿字、裁切、越界或异常断行。灰度下各段、线型与点型仍可区分；首次引用位于图前，题注与图后读图句连续且没有分页孤立。

## 构建、身份与顺序

- 使用 TeX Live 2026 LuaLaTeX 与既有已填充缓存 `C:\Users\ASUS\AppData\Local\Temp\statlearn-v2.7.0-texmf-cache` 定向构建。
- `p608_root_r3_standalone.pdf`：1 页 A4，32,428 bytes，metadata v2.7.0。
- `p608_root_r3_page.pdf`：1 页 A4，60,026 bytes，metadata v2.7.0，可见页码 643。
- 两份最终日志的 LaTeX/Package error、undefined control/reference/citation、fatal/emergency、missing character、font substitution、multiply defined、overfull/underfull 与待重跑引用硬诊断均为 0。
- page AUX 唯一记录 `fig:V5-C03-trace-running-mean = 图 32.8 / 页 643`。
- `pdftotext -layout` 的实际位置索引为：首次引用 178、短题注 936、读图句 984，故 `178 < 936 < 984`。
- 冻结整书仍为 805 页、4,851,007 bytes；本轮遵守精简执行约束，没有重复全书 L1，汇总构建时再统一确认最终物理分页。

## 清单与边界

- V5-C03 `figure_sources.json` 与中央 numeric manifest 均可解析，目标源、label 与 numeric record 各唯一命中 1 条。
- 中央 CSV 可解析为 99 行 × 19 列、99 个 `canonical_uid` 唯一，P608 唯一命中 1 条；总体验收保持 `待R3独立复审`。
- `Tagged: no` 是公共模板当前能力的非阻断事实；现行权威验收条款没有把 PDF/UA 或实际 Alt tagging 规定为本图硬门，本轮未扩大公共样式范围。

## 根线程局部决定

FIG-P608-01 当前数学、数值、图文、字号、自然宽度、页面融合、灰度冗余、metadata、日志、身份链与阅读顺序局部门均通过，且双面板共享同一轨迹、同一预热分界和同一目标，拆图会削弱对照关系，故 `SPLIT_REQUIRED=NO`。该结论不是最终放行；下一步必须由不读取 R1/R2/本报告的全新 SA1 独立复核，通过后再进入盲审 SA3。
