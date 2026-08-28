# FIG-P750-01｜ROOT-APPLY-R3

## 结论

- `PASS_LOCAL_PENDING_INDEPENDENT`
- `SPLIT_REQUIRED=NO`
- 根级源码、包装器、机器门与三视图均通过；本报告不代替独立 SA1/SA3 终审。

## 对象与身份

- canonical UID：`FIG-P750-01`
- legacy ID：`FIG-V5-C08-07`
- label：`fig:V5-C08-selection-map`
- 唯一图源：`src/绘图源码/第05册_采样方法主题模型与图排序/V5-C08/method_selection_decision_map.tex`
- 单图约束：图源内 `figure=1`、`tikzpicture=1`，无拆图。
- 页级定位：图 `37.7`，物理页 `747`。

## 教学与流程语义

- 主路径共有 10 条显式前向边：首要任务到语义/约束 1 条，语义/约束到四个候选族 4 条，四个候选族到验证节点 4 条，验证到最终锁定 1 条。
- 反馈边恰有 1 条，仅从验证节点返回候选族框，标注“仅验证回修候选族”。
- 最终节点不是任何绘图边的起点；双线 `terminal` 徽标明确“最终测试与报告不回流”。
- 图后专属读图检查按“任务与约束 → 候选族 → 验证筛选 → 锁定出口”闭环，caption、alt 与正文边界一致。

## 字号、布局与数值边界

- 普通图中文字为 `9.6pt`，两个首层根节点为 `10.2pt`。
- 未使用整体缩放；未发现裁切、文字碰撞、箭头穿字或不可辨的交叉。
- 本图没有关键公式或可复算数值，因此不存在数值清单对象，也无需拆图。
- tagged PDF 结构化 alt 不作为本轮硬门；源级 alt、caption 与读图检查已经落地并保持一致。

## 构建与机器门

- 页包装 PDF：`p750_root_r3_page.pdf`，`62,693 bytes`，A4 单页。
- 独立包装 PDF：`p750_root_r3_standalone.pdf`，`43,896 bytes`，A4 单页。
- AUX：`fig:V5-C08-selection-map = 37.7 / page 747`。
- 页包装与独立包装硬错误命中均为 `0`。
- 字体检查：页包装 `4` 个字体、独立包装 `2` 个字体，全部嵌入、子集化并具 Unicode 映射。
- FLS 输入链指向当前 v2.7.0 包装器、章节与唯一图源。

## 三视图

- `p750_root_r3_page_300dpi.png`
- `p750_root_r3_gray_page_300dpi.png`
- `p750_root_r3_standalone_300dpi.png`

三图均为 `2481×3508`、`300 dpi`。彩色整页、灰度整页与独立包装均可辨；10 条前向边、唯一反馈、候选族框、终点徽标、caption 和读图检查完整，无裁切或遮挡。

## 根级裁决

根级验收通过，中央清单暂记 `待独立复核`。只有在两路独立终审均判 `PASS / SPLIT_REQUIRED=NO / NEW_ISSUE=NONE` 后，才可写最终接受报告并永久关闭本图。
