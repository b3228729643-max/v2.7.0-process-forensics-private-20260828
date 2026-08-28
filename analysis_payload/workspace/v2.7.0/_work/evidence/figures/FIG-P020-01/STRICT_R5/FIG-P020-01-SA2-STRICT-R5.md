# FIG-P020-01｜专属 SA2 严格返修（R5）

- RESULT: **FIXED_PENDING_INDEPENDENT_SA1_R5**
- FINAL_PASS_CLAIMED: `NO`
- FILE_CHANGED: `src/绘图源码/第01册_数学基础与统计学习基本理论/V1-C01/fig_v1_c01_language_flow.tex`
- OTHER_FILES_CHANGED_BY_SA2: `NONE`

## 修复

关系节点中 14.5pt 文本 `\to` 已删除，替换为内联 TikZ Stealth 图形箭头：使用 7mm 固定图形盒、4.90mm 路径、1.55×1.05mm 箭头头部和 0.72pt 线宽。普通正文仍为 10.0pt、节点标题 10.5pt；箭头不再参加文字角色字号比，且无整体缩放。

## 局部构建与原生 300 dpi

- page/standalone 均 LuaLaTeX 成功、A4 单页，日志中错误、未定义引用、重跑提示及 over/underfull 合计 0。
- 两张 PNG 均为 `2481×3508 @ 300dpi`，未 resize。
- 箭头实际墨迹 bbox `(1055,1337)–(1114,1350)`，60×14px；深色核心约 58×10px。
- 左文字—箭头净空 12px，箭头—右文字 13px；左右文字水平净空 85px；节点文字—边框至少 15px。
- 局部 `TEXT–LINE_ARROW` overlap=0，clip=0；page/standalone 到画布边缘最小 162/291px。

## 剩余门

SA2 只证明定向修复候选。根线程须从包含 R5 的官方连续页生成全量新五类证据，重新核全部组合的 overlap/clip/clearance、同类/角色比例与四视图；之后才能交全新独立 SA1，SA1 PASS 后才允许 SA3。

## 临时候选

- `page.pdf`, `page.log`, `page_300dpi.png`
- `standalone.pdf`, `standalone.log`, `standalone_300dpi.png`
- `relation_roi_300dpi_1to1.png`
