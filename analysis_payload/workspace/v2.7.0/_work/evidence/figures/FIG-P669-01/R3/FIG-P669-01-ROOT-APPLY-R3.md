# FIG-P669-01｜根线程应用与局部门（R3）

- FIGURE_ID: `FIG-P669-01`
- ROUND: `R3`
- ROOT_RESULT: `PASS_LOCAL`
- SPLIT_REQUIRED: `NO`
- BLOCKERS: `NONE`
- FINAL_ACCEPTANCE: `PENDING_INDEPENDENT_SA1_AND_SA3`

## 根线程应用范围

根线程完整核验联合设计、专属 SA2 报告和当前工作树，只同步当前 P669 图源、正文邻域、page/standalone wrapper、V5-C05 `figure_sources.json`、数值清单与中央 `figure_manifest.csv`。中央 canonical UID 总数仍为 99 且唯一；未改公共宏、构建入口、全局编号或任何已关闭图。

正文与 page wrapper 均保持“段题 → 首次引用 → 图 → `\FloatBarrier` → 专属读图句”。page wrapper 使用当前整书身份：图 34.9、印刷页 666、v2.7.0。

## 数学与教学语义

- 固定 $\boldsymbol m=(0.5,0.3,0.2)$，左侧严格线性 $\alpha_0$ 轴只取 `3 / 10 / 30`，对应 $\boldsymbol\alpha=(1.5,.9,.6)/(5,3,2)/(15,9,6)$；均值不动。
- 图内同时给出 $\operatorname{Var}(\Theta_i)=m_i(1-m_i)/(\alpha_0+1)$ 与 $\operatorname{Cov}(\Theta_i,\Theta_j)=-m_im_j/(\alpha_0+1)$，并明确后式只适用于 $i\ne j$。
- 在 $x=4\theta_2+2\theta_3$、$y=2\sqrt3\theta_3$ 投影下，协方差为 `[[3.04,.277128129211],[.277128129211,1.92]]/(alpha0+1)`；三条曲线直连同线型 0.8σ 椭圆边界。
- 根线程独立复算三组 Cholesky 因子，最大重构残差 `4.49e-13`；椭圆共心残差为 0，面积比为 `1 : 4/11 : 4/31`，最外层椭圆最小概率坐标为 `.04`，支持域越界数为 0。
- 图内与题注明确椭圆是协方差尺度，不是密度等高线或置信域；教学任务只承担“固定均值下浓度控制不确定性”，与 P668 的密度边界任务正交。

## 字号、布局与视觉门

- 默认可见字号 9.6pt，面板标题 10.1pt；无 `resizebox`、`scalebox`、`adjustbox`、`transform shape` 或整体 `scale=`。
- 根线程亲自查看最终彩色整页、灰度整页和 standalone 三份 300 dpi PNG。线性轴、三组参数、三条连接曲线、同心椭圆、公式框、题注和读图句均可读，无裁切或越界。
- 首轮视觉检查发现参数行被顶部说明框遮挡，连接曲线与公式区过近；根线程下移参数行、收窄右侧说明框并抬高连接曲线。第二轮又发现左面板标题与说明框净空不足，仅将标题从 `y=3.28` 上移到 `y=3.50` 后重建。最终三视图无标题遮挡、文字碰撞或曲线穿字。
- 灰度下点形、线型、轴位置和直接图例仍能区分三组 $\alpha_0$；色彩不是唯一编码。
- 左轴参数与右侧协方差椭圆是一条连续因果链，当前密度适中，无需拆图。

## 构建、身份与原始证据

- 最终 standalone：`p669_root_r3_standalone.pdf`，53,736 bytes，A4、1 页。
- 最终 page：`p669_root_r3_page.pdf`，71,485 bytes，A4、1 页；AUX 将标签解析为图 34.9、页 666、`figure.caption.2`。
- 两份最终 LOG 对 LaTeX Error、Emergency/Fatal、Undefined control sequence、Overfull/Underfull、Missing character、重复标签和未定义引用的硬诊断命中均为 0。
- 两份 FLS 分别输入当前 `v260_FIG-P669-01_standalone.tex` / `v260_FIG-P669-01_page.tex`，并均命中当前 `fig_v5_c05_concentration_mean.tex`。
- 两份 PDF 的全部列出字体均为嵌入、子集化和 Unicode 编码。

## 根线程局部裁决

`FIG-P669-01` 当前候选通过根线程 R3 数学、身份、日志、彩色、灰度、字号、阅读顺序与页面融合局部门。

ROOT_RESULT: **PASS_LOCAL**  
SPLIT_REQUIRED: **NO**  
BLOCKERS: **NONE**  
NEXT_ACTION: **由全新独立 SA1 与隔离 SA3 只读复核当前源和 R3 原始证据；双 PASS 前不作最终接受。**
