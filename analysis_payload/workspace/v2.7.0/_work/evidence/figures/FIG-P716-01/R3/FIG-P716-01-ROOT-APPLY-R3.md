# FIG-P716-01 / ROOT-APPLY-R3

**RESULT: PASS_LOCAL_PENDING_INDEPENDENT**  
**SPLIT_REQUIRED: NO**  
**BLOCKERS: NONE_LOCAL**

## 身份与限域

- canonical UID：`FIG-P716-01`
- source object：`FIG-V5-C07-03`
- label：`fig:V5-C07-periodic-dangling`
- 当前正式图仍为单一 `figure`、单一 `tikzpicture` 和左右两个反例面板，
  无需拆图。
- 专属 SA2 只改本图源与 V5-C07 首次引用邻域；根线程只同步两个 wrapper、
  V5-C07 source JSON、中央 CSV 与本 R3 证据。numeric manifest 的历史失败字段
  暂不提前消除，等待最终双独立复核后由中央单写者收束。

## 数学与语义检查

- 左栏保持
  `M_p=[[0,1],[1,0]]` 与 `r^(0)=e_1`；精确复算给出
  `M_p e_1=e_2`、`M_p e_2=e_1`，故周期为 2。候选
  `r_*=(1/2,1/2)^T` 的固定点残差为 0，图中明确区分“唯一平稳分布”与
  “从该初值逐步收敛”。
- 右栏保持 `M_d=[[0,0],[1,0]]`。两列和为 `(1,0)`，第二列和为 0；
  `M_d e_2=0` 且下一步总质量为 0，所以未修复的 `M_d` 不是列随机概率核。
- 修复顺序写为先用 `v` 回填悬挂列
  `S=M_d+v e_2^T`，再构造
  `G=dS+(1-d)v1^T`，`0<=d<1`；没有在含零列的 `M_d` 上直接宣称阻尼核
  列随机。
- 章节与 page wrapper 均为“首次引用 -> input -> FloatBarrier -> 专属读图检查”。
  P715/P717/P721 等已关闭邻域未改。

## 构建与机器门

- `p716_root_r3_standalone.pdf`：52,888 bytes，A4 单页。
- `p716_root_r3_page.pdf`：82,333 bytes，A4 单页；AUX 为图 36.3、页 714。
- 两份最终日志的 LaTeX/Package error、undefined control/reference/citation、
  fatal/no-page、duplicate label、overfull/underfull 与 missing-character
  硬命中均为 0。
- standalone 的 7 个字体与 page 的 10 个字体全部
  `emb/sub/uni=yes`。
- 两份 FLS 均回指各自 v2.7.0 wrapper 与当前 canonical source；PDF metadata
  均为 v2.7.0。
- 图源普通可见字号为 9.6pt，标题为 10.2pt；未使用整体缩放、
  `resizebox`、`scalebox`、`transform shape` 或 `scale=`。

## 根级视觉门

- 已实看最终 300 dpi 彩色 page、灰度 page 与 standalone；三图均无裁切、
  遮挡、文字碰线、公式溢出或面板越界。
- 左右面板、题注和图后读图检查均在同一 page 上，层次与留白清楚。
- 灰度下圆形/矩形节点、实线/虚线/点划线卡片以及状态文字仍可区分；颜色不是
  唯一语义通道。

## 根级结论

当前 P716 源码、正文、wrapper、source JSON、双 PDF、机器证据与三视图均通过
根级局部门。中央 CSV 总体验收仅更新为 `待独立复核`；须等待全新独立 SA1 与
隔离盲审 SA3 双 PASS 后，根线程才能收束 numeric manifest、写最终接受报告并关闭本图。
