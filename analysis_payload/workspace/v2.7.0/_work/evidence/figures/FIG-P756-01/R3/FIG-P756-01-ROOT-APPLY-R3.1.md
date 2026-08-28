# FIG-P756-01｜ROOT-APPLY-R3.1

## 结论

- `PASS_LOCAL_PENDING_INDEPENDENT`
- `SPLIT_REQUIRED=NO`
- R3 初版因“仅此单向出口”内联标签压入相邻节点而视觉失败；同一 SA2 的 R2.1 只移动该注记。R3.1 源码、机器门和三视图均通过，旧 R3 仅保留为失败历史。

## 对象与身份

- canonical UID：`FIG-P756-01`
- legacy ID：`FIG-V5-C08-08`
- label：`fig:V5-C08-course-map`
- 唯一图源：`src/绘图源码/第05册_采样方法主题模型与图排序/V5-C08/full_course_synthesis_map.tex`
- 单图约束：`figure=1`、`tikzpicture=1`、caption/label/combined alt 各1，无拆图。
- 页级定位：图 `37.8`，物理页 `753`。

## 教学与流程语义

- 上层保留五站前向链：问题定义 → 建模 → 计算 → 证据 → 边界，共4条主前向边；边界暴露或证据失败时，唯一橙色虚线反馈从边界返回问题定义。
- 下层监督任务与无监督任务分别以实线/虚线进入同一个共享可复用计算引擎池；池内明确列出线性代数、优化、概率、推断四类引擎，并写明“两类任务均按问题调用”，不存在旧排他所有权语义。
- 共享引擎池只前向进入隔离验证；隔离验证只前向进入双线框可复现报告。报告没有任何出边，文字明确“无回流”。
- R2.1 将完整短语“仅此单向出口”移到报告节点上方，箭头恢复为干净主边；拓扑、节点位置、caption、alt 与章节均未改变。
- 章节和 page wrapper 均满足“首次引用及共享/单向边界 → input → FloatBarrier → 专属读图检查”。

## 字号、布局与数值边界

- 普通图中文字、站号、失败反馈、出口注记与图例均为 `9.6pt`；面板标题和共享引擎池标题为 `10.2pt`。
- 无 `scale/xscale/yscale/resizebox/scalebox/transform shape`；无 `lrbox/makebox/captionof` 旧封装。
- 单一标准 figure 同时包含 TikZ、caption 与 label；page 中图体、122字 caption 和专属读图检查在同一物理页。
- 本图没有可复算数值或关键公式，不存在 numeric manifest 记录，也无需拆图。
- tagged PDF/ActualText 不属于本轮硬门；源级 alt 与 source JSON combined alt 已同步。

## R3.1 构建与机器门

- 页包装 PDF：`p756_root_r3p1_page.pdf`，`78,448 bytes`，A4 单页。
- 独立包装 PDF：`p756_root_r3p1_standalone.pdf`，`62,986 bytes`，A4 单页。
- AUX：`fig:V5-C08-course-map = 37.8 / page 753`。
- 两份日志的 TeX/引用/盒警告/缺字硬模式命中均为 `0`。
- 字体检查：page `4` 个字体、standalone `3` 个字体，全部嵌入、子集化并具 Unicode 映射。
- 两份 FLS 均各自命中当前 v2.7.0 wrapper 与当前唯一图源一次。

## R3.1 三视图

- `p756_root_r3p1_page_300dpi.png`
- `p756_root_r3p1_gray_page_300dpi.png`
- `p756_root_r3p1_standalone_300dpi.png`

三图均为 `2481×3508`、`300 dpi`。根线程逐图实看：五站与编号、失败返回、两任务入口、共享池四芯片、池到验证、验证到报告箭头、上置出口注记、双线终点、caption 与读图检查均清楚；无碰撞、裁切、半词断行或灰度失辨。

## 根级裁决

根级验收通过，中央清单暂记 `待独立复核`。只有新的独立 SA1 与隔离 SA3 均判 `PASS / SPLIT_REQUIRED=NO / NEW_ISSUE=NONE` 后，才可写最终接受报告并永久关闭本图。
