# FIG-P715-01 — ROOT APPLY / LOCAL VALIDATION R3

- timestamp: `2026-08-22T19:43:47+08:00`
- owner: `/root`（公共源、中央清单与证据单写者）
- result: **ROOT_R3_LOCAL_VALIDATION=PASS**
- figure acceptance: **PENDING_NEW_SA1_AND_SA3**
- split: **NO**

## R3 变更边界

独立 `FIG-P715-01-SA1-R2` 对 R2 的数学、矩阵、状态推进、字号、视觉、灰度、日志和包装器均判通过；唯一硬阻塞是正式章节中的“先—再—最后”读图句位于图源输入之前，不满足图后阅读顺序门。

R3 仅调整正式章节 `V5-C07.tex` 中该段的位置：保留首次引用和输入说明在图前，将专属 `\textbf{读图。}` 三步说明移到 `web_random_walk.tex` 输入之后。图源、题注、两个 wrapper、边集、`A/c/M/P`、numeric manifest 和所有数值均未改变。R2 的失败报告和全部 R2 产物原样保留，没有覆盖或改写。

## 正文顺序门

定向回读得到：

```text
first reference = 179
figure input    = 181
reading guide  = 183
179 < 181 < 183 = true
```

图前保留四条边与 `c=(1,2,1)` 的输入说明；图后读图句依次要求读者从箭头写 `A`、按 `c_j` 得到列随机 `M`、再核对 `P=M^T` 及两种状态推进。

## 构建与日志

使用项目权威默认链路 `TeX Live 2026 / latexmk -g -lualatex` 和 ASCII 临时字体缓存，在独立 R3 目录重建两个 wrapper：

| wrapper | PDF | pages | hard diagnostics |
|---|---:|---:|---:|
| `v260_FIG-P715-01_standalone.tex` | 40,878 bytes | 1 | 0 |
| `v260_FIG-P715-01_page.tex` | 62,234 bytes | 1 | 0 |

两份 PDF 均为 A4，Producer 为 `LuaTeX-1.24.0`，Title/Subject 均保持 v2.7.0。硬诊断扫描覆盖 LaTeX/Package Error、Undefined control sequence、Emergency stop、Fatal、overfull、underfull、未定义引用、重复定义和需再次交叉引用运行，计数均为 0。

## 像素与源级定向验证

本轮新生成并逐一实看：

- `current_standalone_300dpi.png` — 177,273 bytes
- `current_full_page_200dpi.png` — 211,577 bytes
- `current_figure_crop_300dpi.png` — 146,926 bytes
- `current_gray_page_300dpi.png` — 326,581 bytes

彩色、灰度、整页和局部证据均无裁切、越界、文字/公式重叠或箭头穿字；图后读图段在正式页清晰可见。图源禁用小字号命令、整体 `resizebox/scalebox` 和显式小于 9.5pt 字号的扫描命中为 0。

## 数学证据沿用边界

R3 未改变图源、边集、矩阵或 numeric manifest，因此不重复 R2 的精确复算。R2 已从边集独立生成并验证 `A/c/M/P`，全部矩阵残差、列和残差、行和残差均为 0，悬挂结点数为 0，verification status 为 `passed`；该证据继续有效。

## 根线程结论

R3 已消除 SA1-R2 的唯一阻塞，根线程局部验证 **PASS**。这不是最终图件接受：中央清单总体验收状态继续保持待复核，下一步必须由不读取旧 SA/根报告的全新独立 SA1 审查当前原始对象；其通过后，再启动全新盲审 SA3。两者均通过后方可签署最终接受。
