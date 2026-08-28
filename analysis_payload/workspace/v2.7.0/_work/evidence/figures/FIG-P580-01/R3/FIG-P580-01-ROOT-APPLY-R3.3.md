# FIG-P580-01｜ROOT-APPLY-R3.3

## 裁决

- `RESULT=FAIL_PIXEL_COLLISION_AND_SAFETY_MARGIN`
- `SPLIT_REQUIRED=NO`
- 不更新中央 CSV / numeric manifest，不启动修复后 SA1/SA3。

## 本轮对象与机器门

- SA2 源级轮次：`R2.4`。
- 图源：`src/绘图源码/第05册_采样方法主题模型与图排序/V5-C02/fig_v5_c02_is_support.tex`。
- 新 jobname：`p580_root_r3p3_page`、`p580_root_r3p3_standalone`。
- page PDF：69,427 bytes；standalone PDF：42,491 bytes；均为 A4 单页。
- AUX：图 31.6，逻辑页 579；FLS 命中 TeX Live 2026 LuaLaTeX 与当前唯一图源。
- 两份日志按项目硬模式扫描均为 0；page 7 个字体、standalone 5 个字体，全部嵌入、子集化并带 Unicode 映射。
- 彩色 page、灰度 page、standalone 均按原生 2481×3508、300dpi 检查，所有 ROI 均为 1:1、无重采样。

## 已修复项

- R3.2 的卡片下边框与蓝色“实线 $p(x)$”标签 0px 接触已经解除。
- R3.3 三种渲染中，该对象最近中心 Chebyshev 距离均为 20px，即连续原生空白净距 **19px**，达到返修候选至少 12px 门槛。
- standalone 中纵轴与卡片最近空白净距为 **16px**；数值行与卡片下边框为 **18px**，均通过。
- 数学、三个点形、`0.96/1.50/0.96`、caption、label、alt、UID 与 9.6pt/10.2pt 字号合同未回归。

## 阻断像素证据

严格协议把任意非纯白抗锯齿像素计入实墨，并对返修候选采用至少 12px 安全门。R3.3 仍有两个明确失败：

1. **标题与中列表头发生像素连通。** 卡内标题“$w=p/q_R$（同一公式）”与下方中列 `$w(\frac52)$` 的分数分子在三种渲染中形成同一个 8 邻域实墨连通分量：standalone 的连通分量 bbox 为 `(1672,416)-(1725,477)`；彩色/灰度 page 对应 bbox 均为 `(1678,726)-(1730,787)`。这不是缩略图观感推断，而是原生像素连通，净距为 **0px**，直接 FAIL。
2. **卡片上边框到标题仅 8px。** standalone 与彩色/灰度 page 的最近中心 Chebyshev 距离均为 9px，即连续空白净距仅 **8px**，低于返修候选至少 12px 门槛。

直接证据：

- `p580_root_r3p3_roi_title_fraction_collision_1to1.png`
- `p580_root_r3p3_roi_card_all_1to1.png`
- `p580_root_r3p3_roi_card_top_axis_1to1.png`
- `p580_root_r3p3_roi_card_label_tight_1to1.png`

## 字体与层级

- 源级可见普通节点为 9.6pt、面板标题为 10.2pt，未见低于 9.6pt 的别名或整体缩放。
- 但“同一公式”粗体标题与中列高分数因行距不足发生实际连通；在连通解除且上下净距达标前，不能以“字号合同正确”替代视觉通过。
- 下一轮优先通过排布解除碰撞；如确有必要，可按用户最新许可对局部文字受控缩小到约 9.0pt，但须保留整页可读性、同类角色差异不超过 10%，并维持字重有明确语义且不显突兀。禁止 `tiny/scriptsize` 与整体缩放。

## 下一步

退回同一专属 SA2 做 `R2.5`，只调整右侧比率卡纵向排布，并可在上述受控范围内调整卡内局部字号。新候选必须同时满足：标题与中列高分数之间、卡片上边框与标题之间、卡片下边框与蓝色标签/曲线/中心方点之间均有至少 12 个原生空白像素；卡片与纵轴/面板边界也至少 12px。不得修改数学、三种点形、caption、label、alt、UID 或其他文件；不得用整体缩放规避问题。
