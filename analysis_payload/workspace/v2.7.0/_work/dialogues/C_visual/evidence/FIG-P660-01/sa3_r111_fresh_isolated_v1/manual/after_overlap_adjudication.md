# FIG-P660-01 SA3 像素候选裁决

候选输入：`all_unordered_pair_metrics_machine.csv`、`all_pair_matrix_machine.png`、`candidate_P001_O01_O02_native1x.png`、`candidate_P001_O01_O02_nearest8x.png`、O01/O02 独立对象掩膜、当前源码坐标。

## P001 / O01 simplex geometry × O02 component construction

- 自动 3 px 膨胀候选像素：922。
- 其中对象层坐标交集：88 px；其余 834 px 是 3 px 膨胀后产生的近接区域。
- 源坐标关系：O02 的三条虚线就是从 θ 点到三个三角形边的投影，必须画在 O01 的单纯形参考网格上；中心点也必须位于网格内部。它们不是互相独立、不得相交的语义前景。
- 原生 300 dpi 观察：虚线在穿越浅灰参考网格时保持完整且层级更强；中心点有意覆盖其下网格交点；边界端点清楚。没有任何文字、公式、数字、节点边框或图例被遮挡，也没有造成投影方向、坐标值或中心位置误读。
- Required-taxonomy classification：`MASK_CONTAMINATION`。原因不是抗锯齿污染，而是通用 all-pair 掩膜把“允许的构造层叠”当作非法独立对象候选；在 R168 下这是检测分类的非硬性差异。922 px 全部由 native1x、NN8x、分离掩膜与源码坐标闭合解释。
- TRUE_COLLISION：0 px。
- UNRESOLVED：0 px。

汇总：

`OVERLAP_CANDIDATE_PIXEL_COUNT = 922`  
`MASK_CONTAMINATION_PIXEL_COUNT = 922`  
`OVERLAP_PIXEL_COUNT = 0`  
`PIXEL_ADJUDICATION_STATUS = MASK_CONTAMINATION_CONFIRMED`  
`PIXEL_ARBITER_MODEL = NOT_USED`  
`PIXEL_ARBITER_REASONING = NOT_USED`

P002–P120 均已在八张 montage 中逐项打开；它们的 exact shared foreground 和 3 px dilation candidate 都为 0。没有第二候选、没有文本碰撞、没有未决簇。
