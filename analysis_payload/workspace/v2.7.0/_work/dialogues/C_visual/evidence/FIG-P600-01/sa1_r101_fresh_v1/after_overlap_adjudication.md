# FIG-P600-01 overlap adjudication — SA1 R101 fresh

- 原图：`figure_only_native_300dpi.png`（最终 PDF 直接 300 dpi，无 resize）。
- 高倍：`figure_only_direct_2400dpi.png`（最终 PDF 直接 2400 dpi；相对 300 dpi 为 8x）。
- 矢量坐标：`page649_bbox.html`、`machine_object_inventory.csv` 与 `machine_critical_intersections.csv`。
- 卡片：`critical_contact_8x_direct2400_01.png`、`critical_contact_8x_direct2400_02.png`，均已逐卡打开审阅。

机器共有 24 个候选。P011/P015/P016/P051/P054/P055/P085/P087/P117/P119/P145/P146 是箭线与其应连接节点边界的合法拓扑端点；P001/P042/P079/P112/P141/P229/P230 是文字被节点框容纳而不是文字与边线共享前景；P181/P190/P222/P231 是近邻但原生墨迹分离。

唯一非零独立对象候选为 P211（O16/O17），机器表给出 10 px。机器掩膜在 `draw_path_mask` 中用 path bounding rectangle 近似填充箭头头部，扩大了候选前景。直接 2400 dpi 卡显示两条蓝弧的有效墨迹在全程分离；矢量端点也不同：O16 的曲线始于 (157.678,549.515)，O17 的箭头/曲线终点位于约 (159.093–162.089,546.268–548.489)，不存在共享坐标。故这 10 px 全部分类为 `MASK_CONTAMINATION`，不是 `TRUE_COLLISION`。

- OVERLAP_CANDIDATE_PIXEL_COUNT = 10（只计需要污染/真实碰撞二选一裁决的独立对象候选 P211；合法拓扑接点不计非法候选分母）
- MASK_CONTAMINATION_PIXEL_COUNT = 10
- OVERLAP_PIXEL_COUNT = 0
- UNRESOLVED_CLUSTER_COUNT = 0
- PIXEL_ADJUDICATION_STATUS = MASK_CONTAMINATION_CONFIRMED

本裁决不消除 S07 的正文一致性硬失败；总结果仍为 FAIL。
