# TASK_PACKET_A｜v2.7.0支线1（视觉域）

## 1. 身份与固定路径

- `OWNER_DIALOGUE`: `v2.7.0支线1` / Dialogue A / Visual
- `MODEL`: `gpt-5.6-sol`
- `REASONING_EFFORT`: `xhigh`
- `WORKTREE`: `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\worktrees\dialogue_A_visual`
- `BRANCH`: `v2.7.0/dialogue-a-visual`
- `BASELINE_COMMIT`: `7f65bd75ce94aee876aa25735e92214bb5ebe004`（Revision 130 共同基线；强制字节保持）
- `DIALOGUE_ROOT`: `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual`
- `HANDOFF_ROOT`: `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\handoff\A`
- `INTEGRATION_WORKTREE`（只读）: `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0`
- 自包含执行提示词：`D:\Users\ASUS\Desktop\机器学习\v2.7.0\GPT_Pro_统计学习方法讲义_v2.7.0_对话A_逐图视觉重构执行提示词.md`

## 2. 权威恢复身份

- 唯一旧现场入口：`D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\state\v2.7.0续_交接文档.md` 第 14 节 Revision 130。
- 官方候选：R98，813 页，4,934,249 bytes。
- R98 PDF（只读）：`D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\build\strict_current_r98_fullbook\main_full.pdf`
- R98 SHA-256：`52FA2EF0769553C8B6FD4B8D3CBA5BE671FA0F3190591A596FB8B6512C108A41`
- 新版 Goal SHA-256：`4FB8A2B615AC7EDA635D0F8DACACE9CF88692153A049D4A04BE06B56BCB53F1A`
- 中央库存：99 行，45 SA1 / 53 SA2 / 1 SA3；严格最终 `0/99`。旧 PASS、旧“已完成”和局部角色 PASS 均不得直接继承为最终结论。

## 3. 唯一授权写域

允许直接修改：

- 本工作树 `src/绘图源码/**` 中当前任务明确授权的单幅图源；
- `DIALOGUE_ROOT` 下 A 自有状态、证据、模型路由、像素裁决与请求文件；
- `HANDOFF_ROOT` 下 A 独占交接目录。

禁止直接修改：

- `src/讲义源码/**` 的正文、题注、相邻段落；
- 公共宏、公共样式、字体、颜色、全局编号、索引、导航、构建入口、封面、版本与 PDF 元数据；
- 主线 `STATE_ROOT`、最终发布根、Dialogue B 的任何文件；
- `INTEGRATION_WORKTREE` 中的任何文件。

需要正文/题注改动时写 `A_CHAPTER_CHANGE_REQUESTS.md`；需要共享/全局改动时写 `SHARED_CHANGE_REQUESTS_A.md`，由主线单写处理。

## 4. Revision 130 首批精确断点

同一时刻最多一个业务图源写者；首批只有 P608 可以改图源。

### A-R130-P608-SA2（当前唯一写者）

- `FIGURE_ID`: `FIG-P608-01`
- 图源：`src/绘图源码/第05册_采样方法主题模型与图排序/V5-C03/fig_v5_c03_trace_running_mean.tex`
- 基线源 SHA-256：`7E24A58CD39F44B34FB85FFD65F83A2950913D37A009B978B75E961DB5D45297`
- 续写证据：`FIG-P608-01/STRICT_R4_SA2_REPAIR_R98_LOCAL_20260824` 的 `after_final_r2`。
- 必须补齐：旋转标签的 inverse-rotation local H/W；hatch 与全部 glyph/MATH_RULE 关系；低轮廓；91 对象与 4095 全 pair；raw mask purity/completeness；原生 1×/8×实际开图账；terminal→manifest→`WRITE_STOPPED`。
- 不得沿用已被主线拒绝的 `after_final`；本地全门与 A 根验收前不得请求 R99。

### A-R130-P654-SA1（只读）

- `FIGURE_ID`: `FIG-P654-01`
- 图源基线 SHA-256：`01EA85F46A9567D7ED6CF88C92346F9BE317FAFDDCF1F7791C07B2A3ED3858EB`
- 续写证据：`STRICT_R1_SA1_REQUAL_R98_20260824`。
- 旧 21 graphic masks、7626 pair、16 critical 与 `PAIR_106_118` 全部 `SUPERSEDED`。
- 按 seqno 逐 path 重放，先证明 `foreign=0`、`missing=0`，再重建 103 glyph + 21 graphics = 124 对象与 7626 全 pair；重开 G0017/G0059/G0066 与字号比例失败。

### A-R130-P547-SA3（严格隔离只读）

- `FIGURE_ID`: `FIG-P547-01`
- 续写证据：`STRICT_R12_SA3_BLIND_R98_20260824`。
- 禁止读取 P547 R10/R11、root/旧 PASS/旧证据与库存结论。
- 独立闭合 57 对象 / 1596 pair、193 glyph、71 paths；G139 的 1px missing stroke 必须以 multi-owner ledger 与 20:1 归属规则消除污染和漏笔。

## 5. 每图闭环与硬门

每幅图必须独立执行：A 协调器/SA2 → mechanical worker 重建证据 → 新 SA1 → 新隔离 SA3 → A 协调器本地验收。SA1/SA3 用 `gpt-5.6-sol/xhigh`；SA2 默认 `gpt-5.6-terra/high`，同图连续两轮完整修复失败后才升级 `gpt-5.6-sol/xhigh`；机械任务用 `gpt-5.6-luna/medium`，不可用时 `terra/medium`。

每次代理任务必须写明 `OWNER_DIALOGUE`、`WORKTREE`、`HANDOFF_ID`、对象 ID、文件/页、问题、修改方案、证据、验收标准、允许/禁止范围、实际模型与 reasoning。

重叠候选逐项裁决为 `TRUE_COLLISION`、`MASK_CONTAMINATION` 或 `UNRESOLVED`。`OVERLAP_PIXEL_COUNT` 只统计确认的真实非法重叠；任何 1 个真实非法重叠像素都必须返修。争议才调用 `gpt-5.6-sol/max` 的 `PIXEL_DISPUTE_ARBITRATION`，裁决后仍须新盲审。

每图至少保存 before/after 全页、局部、300 dpi、灰度、色觉、glyph/graphic/path/critical contact sheets、源级字号、像素高度、坐标框、全 pair、mask 纯度与完整性、`after_visual_acceptance.md`、`after_overlap_adjudication.md`、`after_model_route.md`。本地只能标记 `A_LOCAL_PASS`，不得声明最终 PASS。

## 6. 交接契约

每个交接写入 `HANDOFF_ROOT/<HANDOFF_ID>/`，至少含：修改文件、关键结论、测试结果、未解决问题、分支/提交、共享请求、对象与页码、证据相对路径、模型路由、像素裁决、当前状态。完成批次后提交到 `v2.7.0/dialogue-a-visual`，并生成可由主线实际读取的 `A_HANDOFF.md`；聊天消息不能替代文件交接。

立即从三条 R130 断点续跑，不得重建既有未封存证据，不得停在计划阶段。
