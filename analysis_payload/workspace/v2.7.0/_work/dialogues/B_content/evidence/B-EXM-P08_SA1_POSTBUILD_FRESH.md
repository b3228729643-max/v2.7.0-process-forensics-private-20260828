# B-EXM-P08｜SA1 post-build fresh 独立盲审报告

## 1. 身份、隔离与结论

- `HANDOFF_ID`: `B-EXM-P08`
- `OWNER_DIALOGUE`: `DIALOGUE_B_CONTENT`
- `ROLE`: fresh post-build SA1，只读业务/PDF reviewer
- `WORKTREE`: `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\worktrees\dialogue_B_content`
- `R1_OUTPUT`: `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\worktrees\dialogue_B_content\build\dialogue_B_content\B-EXM-P08-R1-RESUME`
- `R1_CONTROL`: `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\worktrees\dialogue_B_content\build\dialogue_B_content\B-EXM-P08-R1-CONTROL`
- `FINAL_DECISION`: **PASS**
- `files_changed`（业务源码）: `[]`
- `TeX_run_by_reviewer`: **NO**。本轮没有执行 `lualatex`、`latexmk` 或任何 TeX 构建命令。

本轮严格按 fresh isolation 执行：没有读取任何既有 P08 SA1/preaudit/root/build-visual 证据、`CURRENT_STATE`、handoff、聊天结论、主线 precheck 结论，也没有读取 P01--P07 证据。只使用任务授权的两份当前业务源码、goal objective、`TASK_PACKET_B.md`、PDF skill 和 R1 的 PDF/AUX/log/index/CONTROL 产物独立得出本报告。

## 2. 逐对象独立数学复算（5/5）

### 2.1 例题 36.3 `exm:V5-C07-damped-four`

给定 (d=4/5)、(v=\boldsymbol1/4)，传送项确为 (\boldsymbol1/20)。固定点方程逐分量为

\[
\begin{aligned}
r_A&=\tfrac25r_B+\tfrac1{20},&
r_B&=\tfrac4{15}r_A+\tfrac25r_D+\tfrac1{20},\\
r_C&=\tfrac4{15}r_A+\tfrac45r_C+\tfrac25r_D+\tfrac1{20},&
r_D&=\tfrac4{15}r_A+\tfrac25r_B+\tfrac1{20}.
\end{aligned}
\]

由第二、四式相减，
(r_B-r_D=\frac25(r_D-r_B))，故 (r_B=r_D)。代回得

\[
\frac{37}{75}r_B=\frac{19}{300},\qquad
r_B=r_D=\frac{19}{148},\qquad
r_A=\frac{15}{148},\qquad
r_C=\frac{95}{148}.
\]

四分量严格为正且和为 (148/148=1)；逐分量代回残差为零。由于 (S) 列随机，
(\lVert 0.8S\rVert_1=0.8<1)，Neumann 级数给出 (I-0.8S) 可逆，故固定点唯一。排序
(C\succ B=D\succ A) 正确。**通过。**

### 2.2 例题 36.4 `exm:V5-C07-power-three`

从 (r^{(0)}=\boldsymbol1/3) 出发，独立计算

\[
Sr^{(0)}=(1/3,1/6,1/2)^{\mathsf T},
\]

从而

\[
r^{(1)}=(1/3,23/120,19/40)^{\mathsf T}.
\]

再由
(Sr^{(1)}=(19/40,1/6,43/120)^{\mathsf T})，得

\[
r^{(2)}=(363/800,23/120,851/2400)^{\mathsf T}.
\]

两轮分量和均为 1。固定点三式独立求解为

\[
r=(686,380,703)^{\mathsf T}/1769,
\]

代回 ((I-0.85S)r=0.05\boldsymbol1) 残差为零，且 (686+380+703=1769)。按最大分量归一化得到

\[
z=(686/703,380/703,1)^{\mathsf T},\qquad
\boldsymbol1^{\mathsf T}z=1769/703,
\]

因此 (z/(\boldsymbol1^{\mathsf T}z)=(686,380,703)^{\mathsf T}/1769)。源码正确区分“固定尺度”的 max-normalization 与“分量和为 1”的概率 (L^1)-normalization。排序 (3\succ1\succ2) 正确。**通过。**

### 2.3 例题 37.1 `exm:V5-C08-two-candidate-selection`

预先规则要求两折全部成功。成功向量为
(a_A=(1,1))、(a_B=(1,0))，故可选集合严格为 ({A})；B 的聚合损失未定义，不能用唯一成功折与 A 的完整两折比较。A 的平均量为

\[
\bar L_A=(0.42+0.46)/2=0.44,\qquad
\bar C_A=(8+9)/2=8.5\text{ 分钟}.
\]

复核和量为 (0.88) 与 (17)。选择 A 后只可在完整开发集重拟合，再一次性解封测试集并报告 (L_{\rm test}=0.47)；测试结果不得反馈到候选、超参数、停止规则或预处理。**通过。**

### 2.4 例题 37.3 `exm:V5-C08-lsa-shape`

对 (X\in\mathbb R^{6\times4})、(K=2)，薄截断 SVD 维数为

\[
U_2\in\mathbb R^{6\times2},\quad
\Sigma_2\in\mathbb R^{2\times2},\quad
V_2\in\mathbb R^{4\times2},\quad
H=\Sigma_2V_2^{\mathsf T}\in\mathbb R^{2\times4}.
\]

重构维数链 ((6\times2)(2\times2)(2\times4)=6\times4) 正确。虽然
(V_2^{\mathsf T}V_2=I_2)，但一般 (V_2V_2^{\mathsf T}\ne I_4)。任意两个文档列满足

\[
h_j^{\mathsf T}h_\ell=e_j^{\mathsf T}V_2\Sigma_2^2V_2^{\mathsf T}e_\ell,
\]

一般不为零。另一方面

\[
HH^{\mathsf T}=\Sigma_2V_2^{\mathsf T}V_2\Sigma_2=\Sigma_2^2,
\]

所以成立的是 H 的两行正交（行范数由奇异值给出），而非四个文档列两两正交。**通过。**

### 2.5 例题 37.4 `exm:V5-C08-holdout` 与命题边界

相邻命题 `prop:V5-C08-test-unbiased` 的条件完整：
(\widehat f) 是 (\mathcal D_{\rm dev})-可测函数；给定开发数据后测试基本单元条件 iid 于目标分布；损失可积。给定开发数据后 (\widehat f) 固定，有限求和与条件期望可交换，因此测试均值条件无偏。证明正确。

当

\[
\widehat K\in\arg\min_{1\le K\le20}\widehat R_K
\]

读取测试误差时，通常 (f_{\widehat K}) 依赖测试集，不再是给定开发数据后固定的可测候选。源码明确给出两类保留可测性的退化例外：给定开发数据后 (\widehat K) 几乎处处固定；或所有可能选中索引对应同一预测器。

条件不等式链独立核验为

\[
\mathbb E[\min_K\widehat R_K\mid\mathcal D_{\rm dev}]
\le \min_KR(f_K)
\le \mathbb E[R(f_{\widehat K})\mid\mathcal D_{\rm dev}].
\]

左端来自“最小值不大于任一固定候选”再取条件期望；右端来自逐点
(R(f_{\widehat K})\ge\min_KR(f_K))。两个精确取等条件均正确：

1. 左侧取等，当且仅当存在固定的总体风险最小索引 (K_\star)，使
   (\widehat R_{K_\star}=\min_K\widehat R_K) 条件几乎处处成立；
2. 右侧取等，当且仅当
   (\mathbb P(\widehat K\in\arg\min_KR(f_K)\mid\mathcal D_{\rm dev})=1)。

因此只能说最小测试报告“一般/典型地”偏乐观，不能声称无例外的严格不等式。正确流程是开发集内选秩、锁定并重拟合、未打开测试集只评估一次。命题、证明、退化边界和问题答案均 **通过**。

## 3. 源码结构与写域

### 3.1 目标解答阶段

五个目标各自恰有且仅有一组、顺序一致的七阶段：

`SLReadTranslation → SolGiven → SLMethodTrigger → SolPlan → SolDerive → SolCheck → SolAnswer`

逐对象均为 `7/7`，合计 **35/35**；每个阶段在对应 `solution` 内恰出现一次且严格按上述顺序排列。

### 3.2 标签、标题与环境平衡

- 五个 `\label{...}`：各 1 次；五个 `\SLExampleSolutionHeading{...}`：各 1 次。
- `V5-C07.tex`：`solution 4/4`、`SLRunningExample 1/1`、独立显示数学 `\[ / \] = 49/49`、`example 4/4`。
- `V5-C08.tex`：`solution 4/4`、`SLRunningExample 0/0`、独立显示数学 `\[ / \] = 50/50`、`example 4/4`。
- 五个目标题干、解答标题、解答环境边界闭合；37.4 引用的命题、proof 与后续问题边界闭合。

### 3.3 Git 只读写域检查

`git status --short`、`git diff --name-only`、`git diff --numstat` 与 `git diff --stat` 独立复核只显示两份授权业务文件：

| 文件 | numstat |
|---|---:|
| `src/讲义源码/第05册_采样方法主题模型与图排序/chapters/V5-C07.tex` | `37  32` |
| `src/讲义源码/第05册_采样方法主题模型与图排序/chapters/V5-C08.tex` | `41  43` |

汇总为 `2 files changed, 78 insertions(+), 75 deletions(-)`；`git diff --check` 退出码 0。未发现第三个业务文件、公共/全局/绘图文件或其他越权源码变更。

## 4. R1 构建身份与机械硬门（没有重跑 TeX）

- CONTROL：`exit_code.txt = 0`；开始时间 `2026-08-25T12:48:00.5146338+08:00`；完成时间 `2026-08-25T12:58:07.7048225+08:00`。
- CONTROL 最终结构化结果：`result=PASS`、`release_version=v2.7.0`、`engine=lualatex`、`automatic_install=false`。
- PDF：`main_full.pdf`，817 页，4,962,906 bytes，A4，PDF 1.7；构建 stdout 与 `main_full.log` 都报告 `817 pages, 4962906 bytes`，与文件实际长度一致。
- 构建产物尺寸：AUX 992,762 bytes；log 249,757 bytes；主索引 23,734 bytes；符号索引 25,820 bytes。
- log 硬错误模式：无 `!` 错误、Undefined control sequence、Emergency stop、Fatal error、Runaway argument 或 TeX capacity exceeded。
- 引用/字形硬门：无 undefined reference/citation、multiply-defined label、Missing character。
- 版面日志硬门：无 overfull/underfull hbox/vbox。
- 主索引：731 entries accepted、0 rejected、719 lines、0 warnings，`theindex` 环境 1/1。
- 符号索引：355 entries accepted、0 rejected、572 lines、0 warnings，`theindex` 环境 1/1。
- CONTROL stderr 的 Perl locale fallback 以及 log 中既有 package/hyperref/unicode-math/microtype/imakeidx 提示不触发上述硬门；latexmk 最终明确报告 PDF up-to-date，索引两路为 0 warnings。

## 5. AUX 定位与 12/12 视觉复核

新 AUX 独立定位：

| 对象 | AUX 印刷页 | 对应物理页 |
|---|---:|---:|
| 36.3 `exm:V5-C07-damped-four` | 766 | 779 |
| 36.4 `exm:V5-C07-power-three` | 767 | 780 |
| 37.1 `exm:V5-C08-two-candidate-selection` | 781 | 794 |
| 命题 `prop:V5-C08-test-unbiased` | 784（cref 锚点起于 783） | 797（前导边界见 796） |
| 37.3 `exm:V5-C08-lsa-shape` | 790 | 803 |
| 37.4 `exm:V5-C08-holdout` | 790 | 803 |

R1 PDF 的物理页与印刷页在这些窗口固定相差 13 页。按任务指定，以 200 dpi 渲染并逐张在可读分辨率检查以下 **12/12** 物理页：

| 物理页 | 印刷页 | 覆盖与结论 |
|---:|---:|---|
| 778 | 765 | 36.1 续解、36.2 题干/解答起始；框体、公式、续页标题和页脚正常。 |
| 779 | 766 | 36.2 续解与 36.3 完整题干、解答前五阶段；矩阵/分式清楚，底部跨页自然。 |
| 780 | 767 | 36.3 核验/结论完整，36.4 题干及主要推导；公式表格完整，无拥挤或裁切。 |
| 781 | 768 | 36.4 max-to-L1 归一化、核验/结论完整，平滑进入章末练习。 |
| 793 | 780 | 第 37 章目标/准备、三条目标推导及命题 37.1 证明；无公式、边框或页脚缺陷。 |
| 794 | 781 | 推导第 3 步、命题 37.2 及证明、37.1 题干和解答起始；分页自然。 |
| 795 | 782 | 37.1 后续阶段、核验/结论完整，并平滑回到正文解释与数值例子。 |
| 796 | 783 | 37.3 节首、验证协议图与命题前导自检边界；图文锐利，未见孤立标题或截断。 |
| 802 | 789 | 37.5 节首及例题 37.2 主体；公式与长解答框完整。 |
| 803 | 790 | 37.2 结论、37.3 全题全解、37.4 完整题干；题干位于页底但完整，不是孤立标题。 |
| 804 | 791 | 37.4 七阶段解答完整，条件不等式链与两个取等条件清楚；下接图 37.8 引文自然。 |
| 805 | 792 | 图 37.8、读图检查、章节练习过渡与相邻练习；图、框、文字和页脚均正常。 |

逐页统一检查项：目标题干与全部解答阶段、公式与表格、页面过渡、页眉/页脚/印刷页码、裁切、重叠、破框、孤立标题、异常 flushbottom 空白、缺字及相邻页回归。结论为 **12/12 PASS**：未见裁切、重叠、破框、缺字、页码错误、异常大空隙或内容缺失。

视觉证据目录：

`D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\B_content\evidence\B-EXM-P08-SA1-R1-VISUAL`

目录内恰有 `physical-778.png`、`779`、`780`、`781`、`793`、`794`、`795`、`796`、`802`、`803`、`804`、`805` 共 12 张 PNG。

## 6. Findings

| severity | file/page | finding | remedy |
|---|---|---|---|
| NONE | 两份目标源码；R1 物理页 778--781、793--796、802--805 | 未发现数学、结构、写域、构建身份、日志/索引硬门或视觉缺陷。 | 无需修复。 |

## 7. 交接字段

- `assigned_scope`: 五个例题及 37.4 关联命题/证明；两份业务源码结构与写域；R1 CONTROL/PDF/AUX/log/index；指定 12 页视觉复核。
- `completed`: 全部完成，数学 5/5、阶段 35/35、标签/标题 5/5、指定物理页 12/12。
- `files_changed`: 业务源码 `[]`；仅新增本报告与指定视觉 PNG 证据。
- `decisions`: `FINAL_DECISION=PASS`。
- `unresolved`: `NONE`。
- `validation`: 独立数学复算、源码机械计数、Git 只读 name/numstat/stat/diff-check、CONTROL/PDF/AUX/log/index 硬门、200 dpi 逐页视觉检查。
- `next_action`: 主协调器可据此继续 P08 的独立后续复核/交接；本 SA1 不执行 SA3、P09、提交、合并或构建。

