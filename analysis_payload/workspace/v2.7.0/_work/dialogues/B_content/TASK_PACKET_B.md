# TASK_PACKET_B｜v2.7.0支线2（内容与数学域）

## 1. 身份与固定路径

- `OWNER_DIALOGUE`: `v2.7.0支线2` / Dialogue B / Content
- `MODEL`: `gpt-5.6-sol`
- `REASONING_EFFORT`: `xhigh`
- `WORKTREE`: `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\worktrees\dialogue_B_content`
- `BRANCH`: `v2.7.0/dialogue-b-content`
- `BASELINE_COMMIT`: `7f65bd75ce94aee876aa25735e92214bb5ebe004`（Revision 130 共同基线；强制字节保持）
- `DIALOGUE_ROOT`: `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\B_content`
- `HANDOFF_ROOT`: `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\handoff\B`
- `INTEGRATION_WORKTREE`（只读）: `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0`
- 自包含执行提示词：`D:\Users\ASUS\Desktop\机器学习\v2.7.0\GPT_Pro_统计学习方法讲义_v2.7.0_对话B_内容数学重构执行提示词.md`

## 2. 权威恢复身份

- 旧现场入口：`D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\state\v2.7.0续_交接文档.md` 第 14 节 Revision 130；其视觉三线由 Dialogue A 接管，B 不得参与。
- 官方候选：R98，813 页，4,934,249 bytes。
- R98 PDF（只读）：`D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\build\strict_current_r98_fullbook\main_full.pdf`
- R98 SHA-256：`52FA2EF0769553C8B6FD4B8D3CBA5BE671FA0F3190591A596FB8B6512C108A41`
- 新版 Goal SHA-256：`4FB8A2B615AC7EDA635D0F8DACACE9CF88692153A049D4A04BE06B56BCB53F1A`
- 所有旧“已完成”字段只作定位线索；必须以当前源码、当前候选 PDF 和逐对象证据重新确认。

## 3. 唯一授权写域

允许直接修改：

- 本工作树 `src/讲义源码/**/chapters/*.tex` 及任务明确指定的非图局部文本 `.tex`；
- `DIALOGUE_ROOT` 下 B 自有状态、证据、模型路由与请求文件；
- `HANDOFF_ROOT` 下 B 独占交接目录。

禁止直接修改：

- `src/绘图源码/**`、逐图证据和视觉库存；
- 公共宏、公共样式、字体、颜色、全局编号、索引、导航、构建入口、封面、版本与 PDF 元数据；
- 主线 `STATE_ROOT`、最终发布根、Dialogue A 的任何文件；
- `INTEGRATION_WORKTREE` 中的任何文件。

需要共享/全局改动时写 `SHARED_CHANGE_REQUESTS_B.md`；跨域图文问题写 `CROSS_DOMAIN_REQUESTS_B.md`，由主线裁定单写者。

## 4. 完整对象域与首批顺序

B 负责：935 条阅读阻塞残留、66 道正文例题、596 个知识点、192 条定理/定义、59 条核心推导、553 道章末练习、7 个算法契约，以及 M02/M04/M05/M06/M07 和 M08/M09 的非图局部部分。

首批执行顺序：

1. 读取 `全量索引库.xlsx` 的“全局问题台账”与“阅读阻塞残留”935 行，建立 B 本地对象表，不把旧状态当结论。
2. 读取 66 例题索引和逐题路线；优先修复 Goal 明确标为中/高风险或错套模板的例题：C15、C16、C18、C36、C42、C50，以及夹带工程状态码/结论重复的相关题。
3. 同步处理 596 知识点、192 定理定义、59 推导中的公式、假设、维数、边界、符号与重复模板问题；正式公式必须回原 LaTeX 恢复并重新计算。
4. 按 37 章核对 553 练习覆盖、题解顺序、唯一结论与核验；不得批量粘贴同一“核验”模板。
5. 完成 7 个算法契约的输入、输出、前置条件、失败状态、停止条件、复杂度与可复现实例。

每个对象必须有唯一 `TASK_ID`、源码锚点、受影响页、当前问题、专属改法、独立复算/核验、前后证据与状态。相邻对象可以按文件批次执行，但不得用一条宽泛结论替代逐对象验收。

## 5. 数学与内容硬门

- 公式、符号、标签、宏与源码结构以原始 LaTeX 为准；抽取 Markdown 只是路线，不得机械粘贴。
- 每个例题恢复完整“题意翻译 → 专属路线 → 分步计算 → 独立核验 → 唯一结论”；不得保留实现状态码干扰初学者主线。
- 定理/定义必须有准确条件、量词、对象域与反例边界；推导必须逐步合法且维数/归一化/极限/KKT/概率支持等可复算。
- 练习题与解答一一对应，题号、标签、目录与 PDF 顺序一致；答案不能重复输出。
- 任何需要改图源的发现只形成请求，不得越权；任何需要改公共宏/样式/编号/索引/构建入口的发现只形成共享请求。
- 本地测试通过仅可标记 `B_LOCAL_PASS`；合入主线并重建后才可能最终通过。

模型路由：协调/数学判定/盲审使用 `gpt-5.6-sol/xhigh`；定向 LaTeX 修复默认 `gpt-5.6-terra/high`；机械索引、格式整理用 `gpt-5.6-luna/medium`，不可用时 `terra/medium`。每次代理任务必须写明 `OWNER_DIALOGUE`、`WORKTREE`、`HANDOFF_ID`、对象 ID、文件/页、问题、方案、证据、验收、允许/禁止范围和实际模型路由。

## 6. 交接契约

每个交接写入 `HANDOFF_ROOT/<HANDOFF_ID>/`，至少含：修改文件、关键数学结论、逐对象测试结果、未解决问题、分支/提交、共享/跨域请求、受影响页、证据相对路径、模型路由与当前状态。完成批次后提交到 `v2.7.0/dialogue-b-content`，并生成可由主线实际读取的 `B_HANDOFF.md`；聊天消息不能替代文件交接。

主线合并顺序固定为 B 内容先、A 图源后。立即从当前索引与源码续跑，不得停在计划阶段。
