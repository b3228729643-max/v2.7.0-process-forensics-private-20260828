# FIG-P716-01 / ROOT-ACCEPTANCE-R3

**FINAL_RESULT: PASS**  
**SPLIT_REQUIRED: NO**  
**BLOCKERS: NONE**  
**CLOSED: YES**

## 接受依据

- 保持 UID `FIG-P716-01`、对象 `FIG-V5-C07-03`、label
  `fig:V5-C07-periodic-dangling`、单一 figure、单一 TikZ 与左右双反例面板。
- 根级 standalone/page 均 exit 0、A4 单页，分别为 52,888/82,333 bytes；
  AUX 为图 36.3、页 714，两日志硬诊断 0。standalone 的 7 个字体与 page
  的 10 个字体均嵌入、子集化且具 Unicode 映射。
- 根级 300 dpi 彩色 page、灰度 page 与 standalone 均通过；矩阵、状态框、
  事实/失败/修复卡、题注和图后读图检查无碰撞、裁切或灰度失辨。
- 周期反例精确给出 `M_p e_1=e_2`、`M_p e_2=e_1`，并把唯一平稳分布
  `(1/2,1/2)^T` 与从 `e_1` 的逐步不收敛严格分开。
- 悬挂反例的列和为 `(1,0)`，`M_d e_2=0`，质量从 1 降为 0；图没有把
  含零列的 `M_d` 称为列随机概率核。
- 修复顺序固定为先 `S=M_d+v e_2^T`、再
  `G=dS+(1-d)v1^T`，`0<=d<1`；正文与 wrapper 均满足
  “首次引用→input→FloatBarrier→专属读图检查”。
- 最终独立 SA1 与隔离盲审 SA3 均为
  `PASS / SPLIT_REQUIRED=NO / BLOCKERS=NONE`。

## 中央单写者收束

- V5-C07 source JSON 中 P716 对象唯一，caption、教学目标与对象—关系—结论
  alt 均对应当前双反例与先修复后阻尼顺序。
- numeric manifest 的当前矩阵、周期、零列和与质量结果均已由根级和双独立复算；
  历史 `r07_failure` 据当前证据收束为 `resolved/passed`，verification 标记为
  精确反例与双独立复核通过，记录数和 UID 唯一性不变。
- 中央 CSV 保持 99 行、19 列、99 个唯一 UID，正式通过数更新为 17；P716
  行为 `通过 / RESOLVED_EVIDENCE_CLEAR`。

根线程据此正式接受并关闭 FIG-P716-01。后续不得重开或重复构建；只有最终
候选全书级受影响范围验证可以读取该对象。
