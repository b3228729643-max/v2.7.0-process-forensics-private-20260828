# R547｜P126 R116 SA2 静态修复范围与 P690 并行路线

- 时间：`2026-08-28T19:27:52+08:00`
- 主线候选：R116，817页，4,967,281 bytes，SHA-256=`19F3D0413AD8C72B4D855B2C23246F10DD7ACECF2FD1E984AEE9F25E1051D3DC`。
- inventory：`30 SA1 / 30 SA2 / 0 SA3 / 40 local pass`；严格最终`0/99`；B累计`66/66`。

## P126

Main已在R546接受P126 fresh SA1 sealed FAIL并确认两处真实穿墨：PAIR-0085 outer contour与`x^(0)` superscript，PAIR-0189 inner contour与digit5。P126保持SA2、NO_SA3。

现授权唯一STATIC_ONLY源码范围：

- HANDOFF=`A-R116-P126-SA2-STATIC-TEXT-CURVE-COLLISION-PATCH-20260828`
- worktree=`D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\worktrees\dialogue_A_visual`
- source=`src/绘图源码/第01册_数学基础与统计学习基本理论/V1-C08/fig_v1_c08_coordinate.tex`
- before identity=4,686 bytes/SHA-256 `2887758F5CC94987BE750E1EC53B555FB88CE8F71B7260CABBE0A17DDF237405`
- 仅允许修改当前line44的`x^{(0)}` node与line49的digit5 node option list；允许项限anchor、x/y shift及局部`fill=white,fill opacity=1,text opacity=1,inner sep=...`保护。
- 必须静态证明两处文字避开全部contour、marker、arrow、axis与其他label；opaque background只可局部遮蔽灰色contour，不得遮蔽任何深色文字、轴、箭头或marker。
- 禁字体缩小、曲线/轨迹/marker/axis/legend/math/caption/其他node修改；禁TeX/build/commit/fresh role/second UID/central write。
- 只回一个sealed `STATIC_ONLY_NOT_RENDERED_NOT_PASS`证据根与精确diff/reverse reconstruction；Main接受前不得申请或启动build。

## P690

HANDOFF=`C-FIG-P690-01-R116-SA2-R168-READONLY-ADJUDICATION-V1`、actual=`/root/sa2_fig_p690_r116_r168_readonly_v1`的parent/child/Main双absence门已接受。同一sole instance继续从exact R116 PDF、current P690 source与current V5-C06 chapter独立完成一次R168 sealed SA2结果；禁止旧P690/P689/其他UID材料、目录fallback/search、restart/duplicate、第二角色及TeX/source/Git/central/process。

## 中央边界

当前无TeX/build槽。P126与P690并行但写域互斥；Main保持公共宏、字体、编号、索引、构建入口、inventory/state与最终交付单写。
