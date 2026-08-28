---
task_id: STATLEARN-V2.7.0-STRICT-FULL-REVISION
charter_revision: 5
created_at: 2026-08-17T21:19:47+08:00
updated_at: 2026-08-24T08:25:27+08:00
---

# 最终目标

以用户 2026-08-23 提供的完整 Goal 为最高权威，在保留现有 v2.7.0 工作成果的前提下完成 M01--M10、99 图严格逐图三角色闭环、全书对象修订、完整构建、全页视觉扫描、独立复建与十二项发布交付。不得从零重建，不得以旧 PASS 或初审覆盖替代新证据。

# Goal 身份

- 权威副本：`D:\Users\ASUS\Desktop\机器学习\v2.7.0\GPT_Pro_统计学习方法讲义_v2.7.0_Codex_Goal主提示词.md`
- 原始附件：`D:\Users\ASUS\.codex\attachments\e9427863-0663-4847-93b3-d9c784a212b5\pasted-text.txt`
- 字节数：`285753`
- SHA-256：`51BA862B1EEBCD6765565FEE6243BD2BC8BF2611D586115B52623668711928C2`
- 平台执行镜像：`D:\Users\ASUS\.codex\attachments\3cad37cf-9e33-47b2-aea3-7ff46f3a6153\goal-objective.md`，`287029` bytes，SHA-256 `B60E2436C422BDEF817F8D3316C7AD0AB5E1B340256ED3DFBE86DFFDEBEB3BF9`
- 镜像同一性：去除 Markdown 转义 `\_`、`\*`、`\.` 并统一换行后，平台执行镜像、用户附件与发布副本逐字符一致。
- 语义连续性：它是上一附件去除 Markdown 转义后的同文版本；规范化后仅剩 `\*`、`\.` 两处转义差异，不重置阶段、证据或完成计数。
- 冲突规则：本 Goal 覆盖旧 Goal、旧交接文档与旧视觉协议的冲突口径；系统/安全规则与用户后续明确要求仍优先。

# 固定路径

- `PROJECT_ROOT=D:\Users\ASUS\Desktop\机器学习`
- `RELEASE_ROOT=FINAL_ROOT=D:\Users\ASUS\Desktop\机器学习\v2.7.0`
- `WORK_ROOT=D:\Users\ASUS\Desktop\机器学习\v2.7.0_work`
- `SOURCE_WORKTREE=D:\Users\ASUS\Desktop\机器学习\v2.7.0_work\source\v2.7.0`
- `STATE_ROOT=D:\Users\ASUS\Desktop\机器学习\v2.7.0_work\state`
- `EVIDENCE_ROOT=D:\Users\ASUS\Desktop\机器学习\v2.7.0_work\evidence`
- 兼容事实：规范 `WORK_ROOT` 是目录联接，指向已有物理树 `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work`；两者是同一数据，不复制、不迁移、不重建。

# 对象基线与硬性视觉门

- 37 章、99 图、66 例题、596 知识点、192 定义/定理、59 推导、553 练习、935 条内部工作文案、139 项页级视觉问题。
- 一般可见文字源级有效字号 `>=9.5pt`；数学上下标仅允许由不低于 9.5pt 的基字号自然缩小。
- 原始 300 dpi 图逐 ELEMENT_ID 测量；执行第 9.2.1 节的字高、同类比例、角色比例、跨面板一致性、灰度和页面融合阈值。
- `OVERLAP_PIXEL_COUNT=0`、`CLIP_PIXEL_COUNT=0`；文字间、文字到线/箭头/标记、节点内边距、图边和跨面板净空全部达标。任何未知、缺证据或失败项均为 FAIL。
- 每图最终必须有五类指定 `after_*` 产物。历史 28 图接受和 99/99 初审只作源码/问题史，不计新协议最终完成；实时完成数以 `CURRENT_STATUS.md` 为准。
- 99 图无旧协议或旧证据豁免。P547/P602/P608/P609/P630/P654/P715 以及早于当前证据 schema 签发的 P020/P157/P632/P756 都必须重新资格认定；只有在当前 schema 下完成独立 SA1、隔离 SA3 与 root 签发的同一候选才能计入最终完成。

# 三角色与单写者

- SA1：`gpt-5.6-terra`、`max`、只读首审；每图独立实例。
- SA2：`gpt-5.6-sol`、`max`、仅可修改任务白名单文件；任何时刻最多一个源码写者。
- SA3：`gpt-5.6-terra`、`max`、与 SA1 判断隔离的独立二审；每图独立实例。
- 公共宏、全局编号、索引、构建入口、中央 CSV/JSON、状态与发布文件由根线程单写。

# 输入与保留边界

原书、v2.6.0 PDF/ZIP、索引与执行材料只读。已有 v2.7.0 源码修复、局部构建、数学复算与历史报告全部保留；仅按影响范围补做新 Goal 缺失的源码修复、证据和复核。不得重复无变化的全量输入扫描、转储、哈希或构建。

# 最终完成条件

主提示词第 3 节规定的十二项正式文件须在 `FINAL_ROOT` 顶层名称完全匹配、真实存在且可读取；最终证据 ZIP 只含 99 图最终通过候选与全书最终证据；源码 ZIP 在独立目录按 README 单条 PowerShell 命令离线重建同名 PDF；总交付 ZIP 通过独立解压检查且不含自身、工作树、旧输入、缓存或失败候选。
