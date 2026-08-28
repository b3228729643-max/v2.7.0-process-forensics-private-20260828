# FIG-P547-01 — ROOT FINAL ACCEPTANCE R3

- timestamp: `2026-08-22T21:18:00+08:00`
- owner: `/root`（最终接受与中央清单单写者）
- result: **ROOT_ACCEPTANCE=PASS**
- split: **NO**
- final manifest status: **通过**

## 三角色结论

| 角色 | 正式证据 | 结论 |
|---|---|---|
| 专属 SA2 | `R1/FIG-P547-01-SA2-R1.md` | FIXED / NO SPLIT |
| 根线程局部门 | `R3/FIG-P547-01-ROOT-APPLY-R3.md` | PASS / pending independent review |
| 全新独立 SA1 | `R3/FIG-P547-01-SA1-R3.md` | PASS / NO SPLIT |
| 全新盲审 SA3 | `R3/FIG-P547-01-SA3-R3.md` | PASS / NO SPLIT |

两名独立审校者均被禁止读取任何旧 SA、SA2、根报告、状态摘要和 R1/R2 目录，只从当前 TeX、wrapper、JSON/CSV、AUX 与 R3 原始 PDF/log/fls/PNG 按权威 A--I、附录 A 本图条款和 B33 独立取证。根线程已完整回读两份正式报告；SA1 为 9,926 bytes，SA3 清理转义控制字符后为 12,724 bytes。

## 接受依据

1. 数学：
   `A=[[0.7,0.3],[0.2,0.8]]` 行随机，`P=A^T=[[0.7,0.2],[0.3,0.8]]` 列随机；`a12=P21=.3`、`a21=P12=.2`，自环亦逐项一致。三方均独立确认任意行状态 `rho_t A` 与列状态 `P p^(t)` 互为转置，物理边方向与概率不变。
2. 图文与阅读：
   图内、章节、题注、两个 wrapper、`figure_sources.json`、numeric manifest、中央 CSV 与 `main_full.aux` 一致；正式章节顺序为首次引用183、图输入184、图后专属读图句186。
3. 字号与布局：
   源级普通可见字号下限9.6pt，关键公式11.6--12.0pt；无整体缩放。节点、箭头端点、标签、矩阵和中央转置桥无穿字、交叉、重叠、裁切或越界，左右同屏对照是本图唯一教学任务，拆图反而削弱逐边对应。
4. 灰度与编码：
   重点 `.3` 同时由更粗跨边、带框标签、粗体数值与矩阵单元框选编码，300dpi灰度实看不依赖颜色。
5. 构建与身份：
   TeX Live 2026 LuaLaTeX 的 standalone/page 均为A4单页，分别37,811/65,877 bytes；两份最终日志硬诊断、未定义引用、盒溢出与缺字均为0。Title/Subject/Keywords均为v2.7.0；page可见页码578、图号30.2，与AUX一致。
6. 像素：
   200dpi彩色整页、300dpi standalone、300dpi图+题注+读图句联合裁切、300dpi灰度整页均已由根线程和两名独立角色实看通过。

SA3 初次写入时，Markdown 中少数 `\rho`/`\boldsymbol` 的反斜杠被转义成 U+000D/U+0008。该代理只做原文等价字符恢复，未改证据或结论；根线程复核 U+0008 与非行尾 U+000D 均为0。此为报告编码清理，不是图件返工。

`Tagged: no` 是如实保留的非阻塞事实；权威 A--I、附录 A 与 B33 未把 tagged-PDF/PDF-UA/实际 Alt tagging 规定为本图硬门，不据此扩大公共模板范围。

## 最终决定

FIG-P547-01 已满足权威 A--I、附录 A、B33、全新独立 SA1、全新盲审 SA3 与根线程最终复核，现正式接受并关闭该图当前修订闭环。中央 `figure_manifest.csv` 的本图 `验收状态` 更新为 `通过`。

按精简执行约束，本次最终接受不触发新的整书 L1；当前805页、4,851,007-byte整书基线继续有效，待多个图件形成公共批次或最终验收阶段再统一重建。
