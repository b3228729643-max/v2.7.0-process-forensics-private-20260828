# B-EXM-P06 选批、数学复算与静态冻结证据

## 恢复与选批

- 主线已无冲突集成 P05：B commit `73049af2eac24af285a29b627ad98c085bc7d699`，main commit `d32aa49`；累计主线集成 41/66。
- P01--P05 提交、证据与 handoff 保持冻结，不写回主线提交。
- P06 按权威对象表中尚未审查例题的自然顺序，选择连续前 10 题；其余 15 题留待后续批次。
- 本阶段仅执行选批、章节源码局部改写与静态门；未运行 LuaLaTeX/latexmk。

## 对象、源码与 R3 只读锚点

| TASK_ID | 例题 | 文件 | 标签 | R3印刷页 | R3物理页 |
|---|---:|---|---|---:|---:|
| M04-EXM-25.1 | 25.1 | V4-C02.tex | `exm:V4-C02-five-points` | 479 | 492 |
| M04-EXM-26.2 | 26.2 | V4-C03.tex | `exm:V4-C03-tall` | 498 | 511 |
| M04-EXM-27.1 | 27.1 | V4-C04.tex | `exm:V4-C04-pca-projection` | 520 | 533 |
| M04-EXM-28.1 | 28.1 | V4-C05.tex | `exm:V4-C05-one-nmf-step` | 544 | 557 |
| M04-EXM-30.1 | 30.1 | V5-C01.tex | `exm:V5-C01-stationary-reversible` | 590 | 603 |
| M04-EXM-30.2 | 30.2 | V5-C01.tex | `exm:V5-C01-two-state-audit` | 595 | 608 |
| M04-EXM-31.1 | 31.1 | V5-C02.tex | `exm:V5-C02-four-uniforms` | 619 | 632 |
| M04-EXM-31.2 | 31.2 | V5-C02.tex | `exm:V5-C02-mc-audit` | 626 | 639 |
| M04-EXM-32.1 | 32.1 | V5-C03.tex | `exm:V5-C03-asymmetric-proposal` | 648 | 661 |
| M04-EXM-32.2 | 32.2 | V5-C03.tex | `exm:V5-C03-three-state-kernel` | 653 | 666 |

R3 页仅用于改写前定位；P06 构建后必须以新 AUX/PDF 重新确定覆盖页，不把这些页号当最终视觉证据。

## 逐题重新复算

| 例题 | 关键复算与边界 | 判定 |
|---:|---|---|
| 25.1 | 第一轮距离给出 $G_1=\{x_1,x_5\}$、$G_2=\{x_2,x_3,x_4\}$，新中心为 $(2.5,2)^T,(2,0)^T$；第二轮分配不变，目标由 51 降至 26.5。 | PASS |
| 26.2 | $A^TA=\operatorname{diag}(9,1)$，奇异值 $3,1$；完整/紧SVD尺寸正确，最佳秩1近似舍弃唯一奇异值1，因此谱误差和Frobenius误差均为1。 | PASS |
| 27.1 | $S$ 的特征值为 $6,1$，第一单位主轴 $(2,1)^T/\sqrt5$，贡献率 $6/7$；中心化点 $(3,0)^T$ 投影重构为 $(17/5,11/5)^T$，残差与主轴正交。 | PASS |
| 28.1 | 顺序乘法更新得到 $W^{(1)}=\operatorname{diag}(3/2,3/2)$、$H^{(1)}=\begin{psmallmatrix}4/3&2/3\\2/3&4/3\end{psmallmatrix}$；乘积等于 $X$，损失由1降至0；零锁定边界明确。 | PASS |
| 30.1 | $\rho_1=(0,1),\rho_2=(1,0)$ 展示周期2；唯一平稳分布 $(1/2,1/2)$ 满足细致平衡。$C_L$ 每项为1/2，任意初值一步到平稳分布且正自环消除周期。 | PASS |
| 30.2 | 行随机矩阵两步分布为 $(0.7,0.3),(0.55,0.45)$；平稳分布 $(0.4,0.6)$，双向流均为0.12；双向正边与正自环给出不可约、非周期，有限链逐步收敛。 | PASS |
| 31.1 | 普通重要性贡献 $Z$ 取 $0,10000$，$E_qZ=1$、$\operatorname{Var}_qZ=10^4-1=9999$；四次全取状态0的概率约0.99960006，此时估计为0而观察权重相等使经验ESS为4。 | PASS |
| 31.2 | 函数值为 $0.16,0.64,0.01,0.49$，均值0.325、误差 $-1/120$；离差平方和0.2529，$s^2=0.0843$，标准误 $\sqrt{0.0843/4}\approx0.14517$。 | PASS |
| 32.1 | 定向三环每条正向边的反向提议均为0，三项接受率全为0，故 $K=I_3$；$\pi$虽平稳但链完全可约，一般初值不收敛到 $\pi$。 | PASS |
| 32.2 | 接受率 $\alpha_{12}=1/3,\alpha_{21}=\alpha_{23}=\alpha_{32}=1$；补对角得 $K=\begin{psmallmatrix}5/6&1/6&0\\1/4&1/2&1/4\\0&1/2&1/2\end{psmallmatrix}$。两条双向流均为1/12，图连通且有自环；固定输入得到 $x_1=2,x_2=3$。 | PASS |

数学结论：10/10 PASS；未发现需要改变现有 `SolDerive` 数值、题干、标签或引用的错误。本轮将泛化开头改为题目专属路线，补齐正式 `SolPlan/SolCheck/SolAnswer`，并保留原有正确推导。

## 精确写域

累计差异严格为 7 个章节文件：

1. `src/讲义源码/第04册_无监督学习与矩阵分解/chapters/V4-C02.tex`
2. `src/讲义源码/第04册_无监督学习与矩阵分解/chapters/V4-C03.tex`
3. `src/讲义源码/第04册_无监督学习与矩阵分解/chapters/V4-C04.tex`
4. `src/讲义源码/第04册_无监督学习与矩阵分解/chapters/V4-C05.tex`
5. `src/讲义源码/第05册_采样方法主题模型与图排序/chapters/V5-C01.tex`
6. `src/讲义源码/第05册_采样方法主题模型与图排序/chapters/V5-C02.tex`
7. `src/讲义源码/第05册_采样方法主题模型与图排序/chapters/V5-C03.tex`

差异统计：`7 files changed, 60 insertions(+), 54 deletions(-)`。

未修改 P01--P05、图源、共享宏/样式、测试、索引、构建入口、主线权威状态或 A 域。

## 静态冻结门

```powershell
git diff --check
```

结果：PASS，exit 0。

```powershell
python -m unittest src.tests.test_style_term_solution_contracts src.tests.test_layout_source_contracts
```

结果：`Ran 9 tests in 0.413s`，`OK`，exit 0。

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\B_content\tools\check_p06_static.ps1 `
  -Worktree D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\worktrees\dialogue_B_content
```

结果：

```text
P06_STATIC=PASS
TARGET_SOLUTIONS=10
STAGE_MACROS=70/70
TARGET_LABELS_AND_HEADINGS=10/10
TARGET_NESTED_RUNNING_EXAMPLE=0
ENVIRONMENT_STACKS=BALANCED
HANDWRITTEN_CHECK_ANSWER_HEADINGS=0
```

## 全新只读 SA1

- 全新 SA1 在源码冻结后启动，未读取本文件、root 复算、状态或旧 SA1/SA3 结论。
- 十题逐题独立复算 10/10 PASS；七阶段、题解专属性、标签/引用、环境边界和七文件写域全部 PASS。
- `FINAL_DECISION=PASS`；FAIL findings 0，未解决数学风险 0。
- 报告：`B-EXM-P06_SA1_FRESH.md`。

静态与 SA1 总判定：`PASS`。源码与证据现已冻结；未提交、未进入 P07、未启动 TeX。下一步必须由主线显式授予 P06 唯一构建槽。
