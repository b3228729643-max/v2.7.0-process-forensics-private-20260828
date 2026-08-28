# FIG-P737-01 / ROOT-APPLY-R3

**RESULT: PASS_LOCAL_PENDING_INDEPENDENT**  
**SPLIT_REQUIRED: NO**  
**BLOCKERS: NONE_LOCAL**

## 身份与限域

- canonical UID：`FIG-P737-01`
- legacy/source object：`FIG-V5-C08-03`
- label：`fig:V5-C08-three-axis`
- 当前正式图保持单一 `figure`、单一 `tikzpicture`，没有拆图；五个方法行、两处分叉卡与图例共同构成一个不可分割的定位投影说明。
- 专属 SA2 只改本图源、V5-C08 首次引用邻域及 R2 报告；根线程统一正式七项规格记号，并同步两个 wrapper、V5-C08 source JSON、中央 CSV 与本 R3 证据。本图无 numeric manifest 记录。

## 语义与结构检查

- 图首明确 `(T,R,I)` 只是粗粒度定位投影，既不能唯一确定方法，也不能替代正式七项规格 `\mathfrak U=(\mathcal X,\mathcal T,\mathcal R,J,\mathcal A,\mathcal E,\mathcal B)`；图前正文、图内边界、caption、对象级 alt 与图后读图检查一致。
- 五行分别给出 k 均值、PCA、NMF、LDA 与 PageRank 的限定条件示例。每行含任务、表示和推断三列，以两段路径连接，合计十段主路径；线型、端点形状、方法标签及条件文字共同编码，不依赖颜色表达数学强弱。
- k 均值写明硬分配与质心、分配—质心交替及平方距离目标；PCA 写明中心化数据的正交低秩与特征分解/SVD；NMF 写明非负加性低秩、交替优化且损失 `J` 另定；LDA 写明潜变量表示及 VI/Gibbs 等后验推断；PageRank 写明阻尼且悬挂已修复的随机核与满足收敛条件的幂迭代。
- 底部两张真实分叉卡分别展示同一低秩表示可接平方损失或计数似然、同一潜变量表示可接 VI 或 Gibbs；四条分叉路径保留不同线型与端点，直接证明表示并非与准则或推断唯一绑定。
- 章节与 page wrapper 均为“首次引用及三轴边界 -> input -> FloatBarrier -> P737 专属读图检查 -> 后续表格”，没有把相邻图或表并入本图。

## 构建与机器门

- 使用项目已有、不会自动安装宏包的 TeX Live 2026 LuaLaTeX 工具链定向构建。
- `p737_root_r3_page.pdf`：87,599 bytes，A4 单页；AUX 为图 37.3、页 734。
- `p737_root_r3_standalone.pdf`：73,713 bytes，A4 单页。
- 两份最终日志的 LaTeX/Package error、undefined control/reference/citation、fatal/no-page、duplicate label、overfull/underfull 与 missing-character 硬命中均为 0。
- page 的 6 个字体与 standalone 的 5 个字体全部 `emb/sub/uni=yes`。
- 两份 FLS 均回指各自 v2.7.0 wrapper 与当前 canonical source；PDF metadata 均为 v2.7.0。
- 图源普通可见字号为 9.6pt、列/分区标题为 10.2pt、关键公式为 12pt；未使用整体缩放、`resizebox`、`scalebox`、`transform shape` 或 `scale=`。

## 根级视觉门

- 已实看最终 300 dpi 彩色 page、灰度 page 与 standalone；三图均无裁切、遮挡、文字碰线、箭头丢失、标签溢出或节点越界。
- 五行网格、十段主路径及五类端点均清楚；两处分叉卡和四条分叉路径有足够净空，分叉结果不会被误读为方法身份。
- 正式七项规格公式在顶部边界卡、caption 与读图检查中清楚可读；caption 与读图检查同页且换行自然。
- 灰度下仍可凭线型、端点、方法标签、条件文字和框层级区分所有路径；颜色不是唯一语义通道。

## 根级结论

当前 P737 源码、正文、wrapper、source JSON、双 PDF、机器证据与三视图均通过根级局部门。中央 CSV 总体验收更新为 `待独立复核`；须等待独立 SA1 与隔离盲审 SA3 双 PASS 后，根线程才能写最终接受报告并关闭本图。tagged PDF/ActualText 不属于本轮权威硬门；对象级语义替代说明以图源和 source JSON 为证。

