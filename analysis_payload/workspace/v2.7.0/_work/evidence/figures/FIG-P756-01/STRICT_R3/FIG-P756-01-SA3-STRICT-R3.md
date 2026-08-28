# FIG-P756-01｜SA3 隔离严格终审（R3）

- Role: isolated SA3 (`gpt-5.6-terra`, maximum reasoning)
- Date: 2026-08-23
- RESULT: **PASS**

SA3 未读取既有角色结论，按原生 300 dpi、1:1 像素独立检查了六张主视图以及 `after_overlap_report.csv` 引用的全部 67 个 ROI。

## 硬门复核

- 唯一文字元素 39 个；font/pixel 各 39 行，全部 PASS。
- 有效字号范围 9.5641--10.1619pt，全部不低于 9.5pt；无天然上下标例外。字号层级协调，无突兀缩小或放大。
- overlap manifest/report 各 67 个唯一检查，ID 与 ROI 一一对应；重叠 0px、裁切 0px、全部净空达标。
- 独立重测全 67 项得到 `fail=0`、`overlap_sum=0`、`clip_sum=0`、全局最小净空 12px。
- 最小净空例证 C41：标题墨迹 `(1861,1564)-(2070,1599)`，正文墨迹 `(1880,1612)-(2051,1743)`，净空 12px（要求 4px）。

## 视觉与页面集成

- 未见文字—文字、文字—线/箭头/边框、图例—图注、图注—正文、跨面板碰撞或裁切。
- 图义、反馈方向、共享引擎、隔离验证和单向报告关系与正文一致；灰度下实/虚线、反馈线与双线终点仍可辨。
- 当前官方 `main_full.pdf` 共 813 页；AUX 将该图记录为图 37.8、印刷页 788，物理页 801。
- 候选连续页与当前官方 PDF 第 801 页分别以 300 dpi 渲染，尺寸同为 2481x3508，逐像素差异为 0。
- 当前全书日志中 `Float(s) lost`、fatal、`Emergency stop`、`Undefined control sequence`、`LaTeX Error` 均为 0。

## 结论

`SA3_STRICT_PASS`

本结论仅覆盖 FIG-P756-01 当前候选；后续图源或页面集成发生变化时必须重新取证。
