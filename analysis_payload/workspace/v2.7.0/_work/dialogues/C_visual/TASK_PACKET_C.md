# v2.7.0 支线3任务包

## 权威目标与恢复顺序

1. 固定工作目录为 `D:\Users\ASUS\Desktop\机器学习`。
2. 完整读取 `C:\Users\ASUS\.agents\skills\codex-lean-execution\SKILL.md`。
3. 完整读取 Goal：`D:\Users\ASUS\.codex\attachments\99aa1e8a-0c07-4cb3-a04c-e66d4f1f29f3\goal-objective.md`。
4. 再完整读取本文件与 `FIGURE_SCOPE.csv`；不得从零重建既有主线状态。

## 身份与写域

- 对话：`v2.7.0支线3`；职责：`FIGURE_VISUAL_C`。
- 独立工作树：`D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\worktrees\dialogue_C_visual`。
- 分支：`v2.7.0/dialogue-c-visual`；基线：`eea4060c5229168e2b973bbaea81cf391e7a9dfd`。
- 本地状态：`D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\C_visual\state`。
- 本地证据：`D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\C_visual\evidence`。
- 交接：`D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\handoff\C`。
- 只允许修改 `FIGURE_SCOPE.csv` 所列46个图源；不得修改章节正文、共享宏、字体、编号、索引、构建入口、A/B证据或中央状态。
- A继续独占B01--B50以及 `FIG-P608-01`、`FIG-P654-01`、`FIG-P715-01`；C绝对不得触碰这三图。`FIG-P547-01`既有A_LOCAL_PASS仍归A。

## 候选与验收

- 当前官方候选仍为R101：`D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\build\strict_current_r101_fullbook\main_full.pdf`，814页A4、4,947,496 bytes、SHA-256 `0870FF226DC383875C4A1B6EABB06AAB942317DA294D90D2864B3030D46DF1A1`。
- 旧清单的“已完成”、旧PDF、旧证据和聊天结论不能直接转为当前PASS。每图必须走独立 fresh SA1；失败才进入单图SA2；修复后必须由主线冻结新官方候选，再走另一fresh SA1与隔离fresh SA3。
- 每图严格执行Goal的全对象分母、全部无序pair、native 1x/8x、灰度、裁切/重叠/字号/语义/正文一致性和逐ID人工账；禁止bulk/default/global布尔或模板化人工PASS。
- 一次只允许一个业务图源写者。只读SA1可并行，但不得跨图复用结论。
- 任何LuaLaTeX/latexmk/全书构建前必须向主线申请唯一全局TeX槽并收到显式grant；进程为空不等于自动获权。
- 本地仅可声明 `C_LOCAL_PASS`；中央inventory、官方候选、最终0/99与14项交付始终由主线单写。

## 启动动作

- 先只读核验工作树身份与46行scope；状态分母应为46，不得写成99。
- 从未闭环且高严重度对象中选择第一张，启动一个完全fresh SA1；首个SA1不得启TeX或修改图源。
- 每次向主线回报必须包含UID、角色、候选身份、证据根、真实分母、结论、是否需要源码写者/TeX槽。
- 不得停在计划阶段。
