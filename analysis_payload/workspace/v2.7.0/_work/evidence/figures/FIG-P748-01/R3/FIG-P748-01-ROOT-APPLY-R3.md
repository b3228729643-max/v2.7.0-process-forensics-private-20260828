# FIG-P748-01 / ROOT-APPLY-R3

**RESULT: PASS_LOCAL_PENDING_INDEPENDENT**  
**SPLIT_REQUIRED: NO**  
**BLOCKERS: NONE_LOCAL**

## 身份与限域

- canonical UID：`FIG-P748-01`
- legacy/source object：`FIG-V5-C08-06`
- label：`fig:V5-C08-evaluation`
- 当前正式图保持单一 `figure`、单一 `tikzpicture`、五张等宽评价卡和一条联合报告结论条；五类证据属于同一阅读任务，拆图会破坏“互补而不合成总分”的关系，故无需拆图。
- 专属 SA2 只改本图源、V5-C08 首次引用邻域及 R2 报告；根线程同步两个 wrapper、V5-C08 source JSON、中央 CSV 的 C077 记录与本 R3 证据。本图无 numeric manifest 记录。

## 语义、统计口径与关系检查

- 五卡完整且并列：拟合为 `holdout loss` 向下、单位 nats、均值加减 SE；任务效用为预登记任务效用向上、单位百分比、估计加减 95%CI；稳定性为 ARI 向上、范围 `[0,1]`、中位数加 IQR；可解释性为盲评一致率向上、单位百分比、比例加减 CI；计算代价为时间秒与内存 GB 均向下、以多次运行 IQR 表示波动。
- `SE/95%CI/IQR/CI` 分别承担均值不确定性、区间估计或分布离散口径，没有互换统计角色。
- 五个微图只以点、区间、点云、纹理条和双资源条提示报告形态，不给坐标值、刻度、样本量或数据来源；图、caption、alt、JSON、正文与读图检查均明确它们不是可复算数值结果。
- 结论条要求联合报告主指标、不确定性/分布、稳定性、解释性与资源，并明确不制造无依据的单一总分。
- 卡片位置、边框、实/虚/点线、空心/实心点、斜线/点纹理与文字共同编码，颜色不是唯一语义通道。
- 章节与 page wrapper 均满足“首次引用及概念微图边界→input→FloatBarrier→P748 专属读图检查→后续知识段”。

## 字号与源级结构

- 普通可见文字为 9.6pt，卡标题为 10.2pt，关键指标、方向、单位/范围和统计口径为 12pt。
- 源码实计一个 figure、一个 tikzpicture、五个 card 节点、一个 conclusion 节点、一个 caption 与一个 label；无 `scale=`、`resizebox`、`scalebox` 或 `transform shape`。
- source JSON 中 canonical/legacy/label 身份桥唯一，`numeric_recomputation.required=false`，对象级 alt 与当前图源一致。
- 首次 page 构建捕获到 alt 文本中未转义的 `95%CI`；根线程只将其修为 `95\%CI`，随后在同一 R3 目录以 `latexmk -g` 强制重建。最终证据均来自修正后的成功构建，不使用失败产物。

## 构建与机器门

- 使用项目已有、不会自动安装宏包的 TeX Live 2026 LuaLaTeX 工具链定向构建。
- `p748_root_r3_page.pdf`：66,245 bytes，A4 单页；AUX 为图 37.6、页 745。
- `p748_root_r3_standalone.pdf`：52,409 bytes，A4 单页。
- 两份最终日志的 LaTeX/Package error、undefined control/reference/citation、fatal/no-page、duplicate label、overfull/underfull 与 missing-character 硬命中均为 0。
- page 的 5 个字体与 standalone 的 4 个字体全部 `emb/sub/uni=yes`。
- 两份 FLS 均回指各自 v2.7.0 wrapper 与当前 canonical source；PDF metadata 均为 v2.7.0。

## 根级视觉门

- 已实看最终 300 dpi 彩色 page、灰度 page 与 standalone；三图均为 2481×3508、300 dpi，无裁切、遮挡、文字碰框、换行溢出或节点越界。
- 顶排三卡、底排两卡和结论条间距稳定；五类标题、关键指标、方向、单位、统计口径与微图均清晰，caption 与图后读图检查同页且换行自然。
- 灰度下空心点/区间、斜线纹理/虚线框、点云、点纹理/点线框和实心/纹理资源条仍可区分；联合报告条与文字可读。

## 根级结论

当前 P748 源码、正文、wrapper、source JSON、中央 C077 记录、双 PDF、机器证据与三视图均通过根级局部门。中央 CSV 总体验收更新为 `待独立复核`；须等待独立 SA1 与隔离盲审 SA3 双 PASS 后，根线程才能写最终接受报告并关闭本图。tagged PDF/ActualText 不属于本轮权威硬门；对象级语义替代说明以图源和 source JSON 为证。
