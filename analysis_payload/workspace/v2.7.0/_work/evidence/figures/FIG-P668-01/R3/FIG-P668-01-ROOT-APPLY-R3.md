# FIG-P668-01｜根线程应用与局部门（R3）

- FIGURE_ID: `FIG-P668-01`
- ROUND: `R3`
- ROOT_RESULT: `PASS_LOCAL`
- SPLIT_REQUIRED: `NO`
- BLOCKERS: `NONE`
- FINAL_ACCEPTANCE: `PENDING_INDEPENDENT_SA1_AND_SA3`

## 根线程应用范围

根线程完整核验联合设计、专属 SA2 报告和当前工作树，只同步当前 P668 图源、正文邻域、page/standalone wrapper、V5-C05 `figure_sources.json`、数值清单与中央 `figure_manifest.csv`。99 个 canonical UID 保持唯一；P668 与 P669 是原混合语义的逻辑再分配，不新增中央 UID。未改公共宏、构建入口、全局编号，也未触碰任何已关闭图。

正文与 page wrapper 均保持“段题 → 首次引用 → 图 → `\FloatBarrier` → 专属读图句”。page wrapper 使用当前整书身份：图 34.8、印刷页 665、v2.7.0。

## 数学与教学语义

- 三个同尺度单纯形依次绘制 $\operatorname{Dir}(2,2,2)$、$\operatorname{Dir}(1,1,1)$ 与 $\operatorname{Dir}(1/2,1/2,1/2)$ 的真实解析密度，不再以协方差椭圆代替密度边界行为。
- 密度分别为 $120\theta_1\theta_2\theta_3$、$2$、$1/(2\pi\sqrt{\theta_1\theta_2\theta_3})$；中心值为 `4.444444444444445 / 2 / 0.826993343132688`。
- `N=24` 的确定性重心网格每面板 576 个严格内点单元，共 1,728 个解析着色单元；最小重心坐标为 $1/72$，没有在边界上数值求值。
- 三面板共用对数密度范围 `[-1.224073476033, 2.777394473238]`。图内直接写明：全体 $\alpha_i>1$ 时面上趋零，等于 1 时恒为 2，小于 1 时面附近发散；这与正文的内点 MAP 条件一致。
- 根线程独立复算近面点 `(.01,.495,.495)` 的三值为 `.29403 / 2 / 3.215251375593845`，近顶点 `(.01,.01,.98)` 的半参数密度为 `16.07707707423404`，与图源及 numeric manifest 一致。

## 字号、布局与视觉门

- 默认可见字号 9.6pt，面板标题 10.1pt；无 `resizebox`、`scalebox`、`adjustbox`、`transform shape` 或整体 `scale=`。
- 根线程亲自查看最终彩色整页、灰度整页和 standalone 三份 300 dpi PNG。三角形、共同色阶、边界极限、题注和读图句均无重叠、穿字、裁切、越界或异常换行。
- 首轮视觉检查发现内部唯一模态说明和顶点发散箭头接近标签；根线程仅移动说明节点与箭头落点后重建。最终三视图中的标签净空清楚，密度明暗与解析边界行为一致。
- 灰度下仍由共同明度、固定边界线型、三组参数标题和直接极限文字提供冗余编码。
- 三面板构成“大于 1 → 等于 1 → 小于 1”的单一比较链，当前页面密度适中，无需拆图。

## 构建、身份与原始证据

- 最终 standalone：`p668_root_r3_standalone.pdf`，77,746 bytes，A4、1 页。
- 最终 page：`p668_root_r3_page.pdf`，97,928 bytes，A4、1 页；AUX 将标签解析为图 34.8、页 665、`figure.caption.2`。
- 两份最终 LOG 对 LaTeX Error、Emergency/Fatal、Undefined control sequence、Overfull/Underfull、Missing character、重复标签和未定义引用的硬诊断命中均为 0。
- 两份 FLS 分别输入当前 `v260_FIG-P668-01_standalone.tex` / `v260_FIG-P668-01_page.tex`，并均命中当前 `fig_v5_c05_dirichlet_shape_atlas.tex`。
- 两份 PDF 的全部列出字体均为嵌入、子集化和 Unicode 编码。

## 根线程局部裁决

`FIG-P668-01` 当前候选通过根线程 R3 数学、身份、日志、彩色、灰度、字号、阅读顺序与页面融合局部门。

ROOT_RESULT: **PASS_LOCAL**  
SPLIT_REQUIRED: **NO**  
BLOCKERS: **NONE**  
NEXT_ACTION: **由全新独立 SA1 与隔离 SA3 只读复核当前源和 R3 原始证据；双 PASS 前不作最终接受。**
