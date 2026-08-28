# FIG-P640-01｜根线程应用与局部门（R3）

- FIGURE_ID: `FIG-P640-01`
- ROUND: `R3`
- ROOT_RESULT: `PASS_LOCAL`
- SPLIT_REQUIRED: `NO`
- BLOCKERS: `NONE`
- FINAL_ACCEPTANCE: `PENDING_INDEPENDENT_SA1_AND_SA3`

## 根线程应用范围

根线程完整回读 `FIG-P640-01-SA2-R2.md` 后，核验并单写同步当前图源身份、page/standalone wrapper、V5-C04 `figure_sources.json`、数值清单与中央 `figure_manifest.csv`；未改公共宏、全局编号、构建入口或已关闭的 P630/P634。

当前正文和 page wrapper 均保持“首次引用 → 图 → `\FloatBarrier` → 专属读图句”。page wrapper 使用当前整书身份：图 33.7、印刷页 671、v2.7.0。

## 数学与教学语义

- 左面板三条轮末 ACF 曲线的底数仍为 `.9025=.95^2`、`.49=.70^2`、`.04=.20^2`；独立复算 `.95^24=0.291989024338772`。
- 右面板为渐近比例 $(1-\rho^2)/(1+\rho^2)$；在 $|\rho|=.5$ 时为 `.6`。
- 合法绘图区止于 `.99`；端点为 `(.99,.010)`，精确值 `0.010049997474875`，不再把 `.99` 伪标为 `1` 或画成零。
- 图内另以 $|\rho|\to1^-$、$N_{\rm eff}/N\to0$ 表达边界极限，并由正文明确 $|\rho|=1$ 不是可取的退化相关系数。
- 两面板分别题为“(a) 轮末 ACF：$\rho^{2k}$”和“(b) 渐近 ESS 比例：$(1-\rho^2)/(1+\rho^2)$”；题注也保留“轮末 / 渐近”限定。

## 字号、布局与视觉门

- 当前图源可见显式字号为 9.6pt 或 9.8pt，最小 9.6pt；无 `resizebox`、`scalebox`、`adjustbox`、`transform shape` 或整体 `scale=`。
- 根线程亲自查看最终 `p640_root_r3_page_300dpi.png`、`p640_root_r3_gray_page_300dpi.png` 与 `p640_root_r3_standalone_300dpi.png`。图体、两面板标题、图例、题注和读图句均无重叠、穿字、裁切、越界或异常换行。
- 首次视觉检查发现 `.99` 的正确非零点因纵轴尺度近似贴零，仍可能被误读；根线程增加 `(.99,.010)` 直接标签。第二次检查又发现曲线轻触末位，最终加入 1pt 白底留白后重建，彩色与灰度证据均清楚显示非零端点，且不遮挡端点空心标记。
- 灰度下三条 ACF 曲线仍由实线、密虚线、点划线与直接图例区分；右图只有一条解析曲线，并由端点数值、极限文字和面板标题提供冗余语义。
- 单图的两面板共同表达“相关衰减变慢 → 渐近 ESS 比例下降”的同一教学链，当前密度适中，无需拆图。

## 构建、身份与原始证据

- 最终 standalone：`p640_root_r3_standalone.pdf`，40,372 bytes，A4、1页。
- 最终 page：`p640_root_r3_page.pdf`，68,100 bytes，A4、1页；AUX 将标签解析为图 33.7、页 671、`figure.caption.1`。
- 两份最终 LOG 对 `!`、LaTeX Error、Emergency/Fatal、Undefined control sequence、Runaway、No pages、File ended while scanning、Overfull、Underfull、未定义引用与重跑提示的计数均为 0。
- 两份 FLS 分别从当前 `v260_FIG-P640-01_standalone.tex` / `v260_FIG-P640-01_page.tex` 输入，并均只命中当前 `fig_v5_c04_mixing_rho_comparison.tex`；PDF 字体均嵌入且为 Unicode 编码。
- page PDF 文本顺序索引为：首次引用 131、面板标题 211、`.99` 端点 1249、题注 1802、读图句 1922，阅读链正确。
- 首次构建时 PowerShell 的变量型 `-outdir` 被原样传给 latexmk，产物误落到合并总册下字面量 `$evidenceDir` 临时目录；该目录经绝对路径、父目录和叶名三重校验后删除。随后使用显式绝对输出路径重建，最终 R3 证据均位于本目录，源码身份未受影响。

## 根线程局部裁决

`FIG-P640-01` 当前候选通过根线程 R3 数学、身份、日志、彩色、灰度、字号、阅读顺序与页面融合局部门。

ROOT_RESULT: **PASS_LOCAL**  
SPLIT_REQUIRED: **NO**  
BLOCKERS: **NONE**  
NEXT_ACTION: **由全新独立 SA1 与隔离 SA3 只读复核当前源和 R3 原始证据；双 PASS 前不作最终接受。**
