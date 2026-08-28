# FIG-P715-01 — ROOT APPLY / LOCAL VALIDATION R2

- timestamp: `2026-08-22T19:29:01+08:00`
- owner: `/root`（公共源、中央清单与证据单写者）
- result: **ROOT_R2_LOCAL_VALIDATION=PASS**
- figure acceptance: **PENDING_NEW_SA1_AND_SA3**
- split: **NO**

## 本轮落地范围

按 `FIG-P715-01-SA2-R1.md` 落地并同步：

1. 图源改为无悬挂四边例 `i→j, j→i, j→h, h→i`，结点顺序固定为 `(i,j,h)`。
2. 显式给出邻接矩阵 `A`、出度 `c=(1,2,1)`、列随机矩阵 `M`、行随机矩阵 `P=M^T`。
3. 同时给出列向量推进 `p^(t+1)=Mp^(t)` 与行向量推进 `rho_(t+1)=rho_tP`。
4. 正文、题注、读图句、figure source metadata、numeric manifest、wrapper 身份与中央 figure manifest 同步为 v2.7.0 语义。
5. 首轮像素检查发现左栏底部三式横向挤压；经 SA2 定点复诊后，将列归一式、列和式与状态推进式分为两行，并把两栏面板底边下扩 0.5 cm。数学与字号未改变。

## 权威矩阵与独立复算

按来源列存边：

```text
A = [[0, 1, 1],
     [1, 0, 0],
     [0, 1, 0]]
c = [1, 2, 1]
M = [[0, 1/2, 1],
     [1,   0, 0],
     [0, 1/2, 0]]
P = [[0,   1, 0],
     [1/2, 0, 1/2],
     [1,   0, 0]]
```

对 `figure_numeric_manifest_v16.json` 中 `fig:V5-C07-web-random-walk` 的对象重新由边集生成矩阵，结果为：

```text
TARGET_COUNT=1
A_RESIDUAL=0
C_RESIDUAL=0
M_RESIDUAL=0
P_RESIDUAL=0
COLUMN_SUM_RESIDUAL=0
ROW_SUM_RESIDUAL=0
DANGLING_COUNT=0
VERIFICATION_STATUS=passed
```

因此边集、邻接矩阵、按列归一、转置桥和两类随机性严格一致。

## 构建与日志

最终 R2 证据使用项目权威默认链路：

- engine: `LuaHBTeX 1.24.0 (TeX Live 2026)`
- driver: LuaLaTeX 直接 PDF
- font cache: 项目约定的 ASCII 临时 `TEXMFCACHE/TEXMFVAR`
- build mode: `latexmk -g -lualatex -interaction=nonstopmode -halt-on-error -file-line-error`

两个 wrapper 均为 A4 单页并成功收敛：

| wrapper | PDF | hard diagnostics |
|---|---:|---:|
| `v260_FIG-P715-01_standalone.tex` | 40,878 bytes | 0 |
| `v260_FIG-P715-01_page.tex` | 62,234 bytes | 0 |

硬诊断扫描包括 LaTeX/Package Error、Undefined control sequence、Emergency stop、Fatal、overfull、underfull、未定义引用、重复定义与需再次交叉引用运行；两份最终日志计数均为 0。

此前一次 XeLaTeX 诊断曾因 MiKTeX/TeX Live 混用及字体后端失败产生旧 `.xdv`。该文件不是验收产物；最终 PDF 与日志已由上述 LuaLaTeX 权威链路重建覆盖。

## 字号、身份与源级门

- 图源普通文字：`9.5pt`；标题：`10.4pt`；关键公式：`12pt`；矩阵单元：`10.2pt`。
- 禁用项扫描：小于 9.5pt 的显式字号、`tiny/scriptsize/footnotesize/small`、`resizebox/scalebox` 均为 0。
- PDF 图区提取：最小 span `9.46pt`，最大 `11.96pt`；关键下标/转置 span `11.46pt`，高于 `8.876pt` 门槛。
- source label 文件数：1；正文首次引用仍先于图源输入。
- 旧 `A^col/A^row` 与错误 `P=A^T`/列向量用 `P` 推进模式计数：0。
- wrapper PDF Title/Subject 均为 v2.7.0；page wrapper 印刷页为 743，图号为 36.2。

## 像素证据与视觉结论

本轮生成并逐一实看：

- `current_standalone_300dpi.png` — 177,273 bytes
- `current_full_page_200dpi.png` — 211,577 bytes
- `current_figure_crop_300dpi.png` — 146,926 bytes
- `current_gray_page_300dpi.png` — 326,581 bytes

视觉结论：

- 两栏自然宽度排版，无整体缩放；无裁切、越界、文字重叠或箭头穿字。
- 左栏三条底部等式已经分层，不再互相粘连或越过中央分隔；两栏末式与底边均有安全留白。
- 箭头方向、橙色重点边、边框粗细、矩阵框选与文字说明形成非颜色冗余；300 dpi 灰度下仍可辨。
- 题注完整，图后“先—再—最后”读图句完整，整页未出现异常断行或分页挤压。

## 中央清单策略

`figure_manifest.csv` 的颜色/线型、灰度和正文变量一致性三个局部字段已据 R2 证据改为“通过”。总体验收状态仍保持 `待R2复核`，不得把根线程局部验证冒充新的独立 SA1 或 SA3 放行。

## 下一步

由新的独立 SA1 实例只读审查当前源码、正文、中央清单、numeric manifest 与本目录像素/PDF/log 证据；SA1 PASS 后再由新的盲审 SA3 复核。两者均 PASS 后，根线程才可签署 FIG-P715-01 最终接受并更新总体验收状态。
