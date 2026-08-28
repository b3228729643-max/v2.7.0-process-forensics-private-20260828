# FIG-P547-01 — ROOT APPLY / LOCAL VALIDATION R3

- timestamp: `2026-08-22T20:46:59+08:00`
- owner: `/root`（公共包装器、中央清单、状态与证据单写者）
- result: **ROOT_R3_LOCAL_VALIDATION=PASS**
- figure acceptance: **PENDING_NEW_SA1_AND_SA3**
- split: **NO**

## R3 变更边界

初始 `FIG-P547-01-SA1-R1` 判定图 30.2 的字号、矩阵命名、转置桥和图后阅读句未达门。专属 SA2 随后仅修改权威图源与 `V5-C01.tex`：统一为行随机 `A=(a_{ij})`、列随机 `P=A^{\mathsf T}`，明确同一物理边满足 `a_{ij}=P_{ji}`，同时给出行向量与列向量两种等价推进，并把普通可见文字提升到至少 9.6pt、关键公式提升到 11.6--12.0pt。

根线程按单写者约束同步两个 wrapper、`figure_sources.json`、`figure_numeric_manifest_v16.json` 和中央 `figure_manifest.csv`。R2 产物的时间戳早于 wrapper 更新，旧 PDF 因而仍显示页码 696 且缺少图后读图句；该旧证据原样保留，不覆盖、不冒充当前结果。R3 使用全新目录、全新 jobname 和中央源码目录中的真实入口强制重建。

## 正文顺序与身份门

定向回读正式章节得到：

```text
first reference = 183
figure input    = 184
reading guide  = 186
183 < 184 < 186 = true
```

新 page wrapper 明确使用印刷页 578；PDF 文本同时出现页码 `578`、图 30.2 及图后“读图顺序”。page 与 standalone 的 Title、Subject、Keywords 均为 v2.7.0，均为 A4 单页，Producer 为 `LuaTeX-1.24.0`。

## 构建与日志

使用项目权威链路 `TeX Live 2026 / latexmk -g -lualatex`，并复用已填充缓存 `C:\Users\ASUS\AppData\Local\Temp\statlearn-v2.7.0-texmf-cache`：

| wrapper | PDF | pages | hard diagnostics |
|---|---:|---:|---:|
| `v260_FIG-P547-01_standalone.tex` | 37,811 bytes | 1 | 0 |
| `v260_FIG-P547-01_page.tex` | 65,877 bytes | 1 | 0 |

硬诊断扫描覆盖 LaTeX/Package Error、Undefined control sequence、Emergency stop、Fatal、overfull、underfull、未定义引用、重复定义和需再次交叉引用运行；两份最终日志计数均为 0。

## 像素与版面验证

本轮新生成并逐一实看：

- `root_p547_standalone_r3_300dpi.png` — 132,171 bytes
- `root_p547_full_page_r3_200dpi.png` — 232,711 bytes
- `root_p547_figure_crop_r3_300dpi.png` — 218,941 bytes
- `root_p547_gray_page_r3_300dpi.png` — 362,977 bytes

彩色整页、standalone、300 dpi 联合裁切和 300 dpi 灰度证据均无裁切、越界、文字/公式重叠或箭头穿字；图、题注和图后读图句连续可见。`.3` 同时由较粗金色物理边、标签框和矩阵框选编码，灰度下仍可区分。图源中 `resizebox`、`scalebox`、`adjustbox`、`transform canvas` 和整体 `scale=` 命中均为 0；普通可见字号源级下限 9.6pt，关键公式为 11.6--12.0pt。

## 数学、清单与结构门

独立复算采用

```text
A = [[0.7, 0.3], [0.2, 0.8]]
P = [[0.7, 0.2], [0.3, 0.8]] = A^T
```

- `A` 两个行和残差：`0, 0`；`P` 两个列和残差：`0, 0`。
- `P-A^T` 四个元素残差：全部 `0`。
- `a12-P21` 与 `a21-P12`：均为 `0`。
- 平稳行向量 `(0.4,0.6)A-(0.4,0.6)` 与列向量 `P(0.4,0.6)^T-(0.4,0.6)^T` 的最大浮点残差为 `5.55111512312578e-17`，按精确十进制分数计算为 `0`。

两个 JSON 均解析通过；中央 `figure_manifest.csv` 为 99 行 × 19 列，`FIG-P547-01` 恰有一行。根线程仅把局部字号/灰度/变量字段据当前 R3 证据更新为通过，总体验收保持“待独立复核”。

## 根线程结论

R3 已消除旧产物污染，并通过当前对象所需的数学、正文顺序、身份、构建、日志、字号、彩色/灰度和清单局部门，故 `ROOT_R3_LOCAL_VALIDATION=PASS`、`SPLIT_REQUIRED=NO`。

这不是最终图件接受。下一步必须由不读取旧 SA、SA2、根报告和状态摘要的全新独立 SA1 从当前原始对象复核权威 A--I/B33 门；其通过后再启动另一全新盲审 SA3。两者均通过后，根线程方可签署最终接受并把中央清单改为“通过”。
