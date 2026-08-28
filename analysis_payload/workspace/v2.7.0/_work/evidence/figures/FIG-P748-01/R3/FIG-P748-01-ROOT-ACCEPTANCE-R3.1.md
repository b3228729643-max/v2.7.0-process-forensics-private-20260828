# FIG-P748-01 / ROOT-ACCEPTANCE-R3.1

**FINAL_RESULT: PASS**  
**SPLIT_REQUIRED: NO**  
**BLOCKERS: NONE**  
**CLOSED: YES**

## 接受依据

- 保持 canonical UID `FIG-P748-01`、legacy/source object `FIG-V5-C08-06`、label `fig:V5-C08-evaluation`、单一 figure 与单一 TikZ；五张等宽评价卡及联合报告条共同表达“互补证据而非单一总分”，无需拆图。
- 五卡口径一致：holdout loss 向下/nats/均值±SE，预登记任务效用向上/百分比/估计±95%CI，标准 ARI 向上/无量纲且可为负/中位数＋IQR，盲评一致率向上/百分比/比例±CI，时间秒与内存GB向下/多次运行IQR。
- 初始隔离 SA3 以 `ARI=-1/2` 的四对象反例发现 `[0,1]` 误限；专属 SA2 R2.1 将其纠正为“无量纲；可为负”，根线程同步 source JSON。R3.1 中旧范围、固定下界及未定义的截断/归一化变体均不存在。
- 五类微图只提示点、区间、分布或资源报告形态，不给数值刻度、样本量或数据来源；图、caption、alt、JSON、正文与专属读图检查均明确其不是可复算结果，也不得合成无依据总分。
- 普通文字9.6pt、卡标题10.2pt、关键指标/方向/单位/统计口径12pt；无整体缩放。卡片位置、边框、点线、实/虚框与纹理形成灰度冗余。
- R3.1 page/standalone 均为 A4 单页，分别 66,679/52,994 bytes；AUX 为图37.6、页745，两日志硬诊断0。page 5个字体与 standalone 4个字体均嵌入、子集化且具 Unicode 映射。
- R3.1 的300dpi彩色page、灰度page与standalone均通过；五卡、新ARI文字、微图、联合报告条、题注和图后读图检查无碰撞、裁切或灰度失辨。
- source JSON 的 legacy/canonical 身份桥唯一；正文与wrapper均满足“首次引用及概念边界→input→FloatBarrier→P748专属读图检查→后续内容”。本图无numeric manifest记录。
- 新的 post-fix 独立SA1与隔离盲审SA3报告已由根线程完整回读，二者均为 `PASS / SPLIT_REQUIRED=NO / BLOCKERS=NONE`；初始R3的SA1 PASS与SA3 FAIL只保留为历史，不参与本次放行。

## 中央单写者收束

- 中央CSV保持99行、19列、99个唯一UID；P748更新为 `通过 / RESOLVED_EVIDENCE_CLEAR`，正式通过数更新为22。
- tagged PDF/ActualText不属于本轮权威硬门；对象级语义替代说明由图源和source JSON提供，不阻塞本次闭环。

根线程据此正式接受并关闭 FIG-P748-01。后续不得重开或重复构建；只有最终候选全书级受影响范围验证可以读取该对象。
