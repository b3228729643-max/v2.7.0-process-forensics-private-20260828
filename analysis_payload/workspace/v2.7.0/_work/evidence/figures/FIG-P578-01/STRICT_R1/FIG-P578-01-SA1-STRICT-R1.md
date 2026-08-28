# FIG-P578-01｜独立 SA1 严格复审（R1）

- ROLE: `SA1`
- MODEL: `gpt-5.6-terra / max`
- RESULT: **FAIL**
- FAILURE_CLASS: `EVIDENCE_PACKAGE_MISSING`
- VISUAL_DEFECT_FOUND: `NO`
- SOURCE_WRITE: `NONE`

本轮直接视觉、字号、算法语义和灰度复审未发现可见缺陷；严格 FAIL 的硬原因是当前没有该图的 `STRICT_FINAL` 证据包及全部 `after_*` 记录。按统一 schema，缺文件、缺行或不可复核不得给 PASS。

## 候选与实际检查

- 当前图源：`src/绘图源码/第05册_采样方法主题模型与图排序/V5-C02/fig_v5_c02_rejection_flow.tex`。
- 页包装：`src/讲义源码/合并总册/v260_FIG-P578-01_page.tex`；同时核对当前章节 `V5-C02.tex:356--362`。
- 审查员从当前源在系统临时目录新建 LuaLaTeX 候选，并由 Poppler 直接生成未 resize 的 2481x3508 原始 300 dpi 页图。
- 实际查看 full-page 200 dpi、page/figure-crop 300 dpi、standalone 300 dpi、grayscale 300 dpi，以及 R01--R08 原始像素 ROI；未读取旧 SA1／SA3／ROOT 结论。

## 直接视觉与量测结论

| 审项 | 结果 | 关键量测 |
|---|---|---|
| 当前源--候选身份 | PASS | A4、1 页、LuaLaTeX 当前源新建 |
| 文字--文字 | PASS | 最紧两行净空 18px |
| 文字--曲线/箭头 | PASS | `m=B?` 后“否”到路径中心距 5px，即 4 个空白像素，门槛 3px |
| 文字/公式--节点边框 | PASS | 菱形内文字到边线约 10.2px；节点最小内距设计值约 5px |
| 箭头头部 | PASS | 原始像素 ROI 无断头或文字碰撞 |
| 裁切与页面融合 | PASS | 四页边暗像素 0；图形--题注 25px；题注--正文 80px；文字到页边最小 473px |
| 有效字号与像素高度 | PASS | 节点/边标签统一 9.6pt；CJK 37px、x-height 18px、数字 26--27px、基线数学 29--30px、自然下标 21px |
| 字号比例 | PASS | 同角色源字号比 1.000；抽样像素比例在门内；单面板无跨面板对象 |
| 数学/算法语义 | PASS | 预检先于随机调用；完成优先于预算；计数与接受/拒绝分支、失败前缀和包络诊断一致 |
| 灰度 | PASS | 实线、虚线、双线异常框、形状和状态码均可辨，不依赖颜色作为唯一语义 |

## 严格失败原因

- 直接 ROI 未见重叠或裁切，但正式 `OVERLAP_PIXEL_COUNT=0`、`CLIP_PIXEL_COUNT=0` 逐元素记录尚不存在，不能用临时人工检查替代。
- 缺少 `STRICT_FINAL/` 及 `after_font_audit.csv`、`after_pixel_measurements.csv`、`after_overlap_report.csv`、`after_text_measurement_overlay_300dpi.png`、`after_visual_acceptance.md`。
- 临时目录新建渲染只用于本轮独立核查，不是冻结最终候选证据。

## 下一步

图面暂无定向源码修复依据。根线程应从当前候选生成正式完整证据包；证据齐全后必须启动新的独立 SA1，PASS 后再启动隔离 SA3。本轮不得迁移为最终 PASS。
