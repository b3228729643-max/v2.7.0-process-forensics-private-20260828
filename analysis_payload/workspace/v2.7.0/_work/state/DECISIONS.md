# 持久决策

## D-001

- status: accepted
- date: 2026-08-17
- decision: 用户本轮指定的 v2.7.0 执行包与主提示词成为当前最高任务目标；v2.6.0 冻结交付仅作为只读输入，旧 complete 状态不得用于证明 v2.7.0 完成。
- reason: 用户明确要求读取并执行 v2.7.0 主提示词，且提示词规定新版本的独立工作树、对象级闭环和十二项交付。
- affected_scope: 固定 D 盘工作根、状态、v2.7.0 工作副本与全部交付
- affected_files: `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\state\*`; 后续 `SOURCE_WORKTREE/**`; `FINAL_ROOT` 正式文件
- supersedes: 根目录旧 v2.6.0 当前目标（保留其历史事实）

## D-002

- status: accepted
- date: 2026-08-17
- decision: 执行包内同名输入优先，固定 D 盘路径不可替换为当前 C 盘工作区镜像；所有修改、构建证据与状态只进入提示词规定的 D 盘目录。
- reason: 主提示词和执行说明均把 D 盘定义为唯一工作根与完成条件。
- affected_scope: 输入解析、工作树、证据、打包与最终验收
- affected_files: `INPUT_RESOLUTION.md`; `CURRENT_STATUS.md`; 后续全部 v2.7.0 工作文件
- supersedes: none

## D-003

- status: accepted
- date: 2026-08-17
- decision: 长任务执行采用“执行包全量读取一次、对象卡按当前工作集增量读取、关键集成 Gate 1、最终 Gate 2”；不因上下文压缩重复扫描、哈希或验收。
- reason: 用户显式指定 `codex-lean-execution`，且项目 `AGENTS.md` 限定哈希和 L0/L1/L2 范围。
- affected_scope: 输入读取、验证、上下文恢复与报告
- affected_files: `CURRENT_STATUS.md`; `NEXT_ACTIONS.md`; 后续验证记录
- supersedes: none

## D-004

- status: accepted
- date: 2026-08-17
- decision: v2.7.0 的正式逐图对象数为 99；旧“101 幅图”由 99 幅带编号正式图加封面 `UFIG-P001-01`、阅读路线 `UFIG-P158-01` 两幅未编号辅助插图组成，辅助插图仍进入逐页视觉审查但不伪增正式图任务。
- reason: 源映射与 99 行权威绘图索引集合差异恰为上述两项；`BND-P015-01` 明确是表格/文本框边界对象，未计入 101。
- affected_scope: M01 文档、M03 逐图闭环、M09 逐页视觉与最终台账
- affected_files: `README_v2.7.0.md`; 后续 99 图台账与视觉报告
- supersedes: 旧 README 的未解释“101 幅正式绘图”表述

## D-005

- status: accepted
- date: 2026-08-17
- decision: 保持源码中的 66 个真实编号算法，不复制所谓兼容拆分以凑旧阈值；中心状态只保留 `completed`、`converged`、`budget_stop`、`invalid_input`、`numerical_failure`、`line_search_failed`、`random_source_failure`。数值平台、验证耐心、无可行路径和无正弱边改由中心状态加诊断表达。
- reason: 权威源码实际包含 66 个独立算法；旧 70 阈值没有对应独立环境。主提示词要求更新过时检查而不是伪造算法，并要求原因词不得充当状态枚举。
- affected_scope: M07、算法契约附录、静态审计与最终 CHANGELOG
- affected_files: 7 个补契约章文件、6 个状态迁移章文件、`statlearnbook.sty`、`static_source_audit.py` 及其测试
- supersedes: 旧算法数阈值与 4 类原因式状态码

## D-006

- status: accepted
- date: 2026-08-17
- decision: 当前任务的最终文字权威采用 Codex Goal 附件 `goal-objective.md`（已逐行读至 EOF），执行包内同名主提示词作为固定磁盘副本与交付来源；若逐图卡片的题注/结论字段与 99 行索引或真实源码错位，按“真实源码数学关系 → 当前 PDF 图文关系 → 99 行索引 → 卡片文字”的顺序定向核对，不机械粘贴错位字段。
- reason: 附件完整展开了 99 幅图和 66 例题任务卡；抽查发现少量卡片字段存在相邻对象错配风险，主提示词同时明确源码与 PDF 的权威层级。
- affected_scope: M03、M04、最终 Goal 提示词副本与台账
- affected_files: 99 图源码/章节上下文、两份三角色台账、最终提示词副本
- supersedes: none

## D-007

- status: accepted
- date: 2026-08-22
- decision: 用户已将本项目范围内后续必要的源码、证据、状态与构建写入设为持续授权，不再逐项重复请求会话确认；系统/平台权限提升、破坏性操作和范围扩张仍按高优先级安全规则处理。
- reason: 用户先明确回复“批准更新这10项”，随后说明“后续需要批准的内容全部默认我已批准”。
- affected_scope: 当前 v2.7.0 工作树内的正常实施、验证、状态持久化和最终交付
- affected_files: `SOURCE_WORKTREE/**`; `_work/evidence/**`; `_work/state/**`; `FINAL_ROOT` 正式交付文件
- supersedes: M02 十项一次性会话授权门及后续同范围重复确认

## D-008

- status: accepted
- date: 2026-08-22
- decision: `V3-C06.tex` 的合法支持 Hammersley--Clifford 正向 Möbius 证明存在“所用混合配置未证明仍在合法支持内”的数学缺口；M02 ordinal 523 改问同一证明内严谨的反向“团因子分解推出全局 G-Markov”步骤，以关闭自检直接可答性，但正文证明缺口单独路由到 M05 的定理/证明逐项修订，最终验收前必须修复并独立复核。
- reason: 全新 M02-SA1-R2 指出，仅补 `G`-Markov 与局部硬约束前提不能保证 Möbius 混合配置或条件优势比四项合法；M02-SA2-R3/SA1-R3 证明反向任务可严谨绕开该缺口。Goal 的 M05 明确要求定理条件、量词、对象域完整，且每个等号与交换均有合法依据。
- affected_scope: M02 自检迁移边界；M05 的 V3-C06 定理、证明和相关知识点/推导；最终数学验收
- affected_files: `src/讲义源码/第03册_优化模型与序列模型/chapters/V3-C06.tex`; `R03_M02_SA1_R2_20260822.md`; `R03_M02_SA2_R3_20260822.md`; 后续 M05 对象证据
- supersedes: none

## D-009

- status: accepted
- date: 2026-08-22
- decision: `FIG-P049-01` 的首个重开实例因广域 `rg` 排除规则在绝对路径调用下失效，意外看到恢复摘要的一行结论；该实例立即暂停并被根线程中断，未写报告、未改文件，其全部中间结果不进入正式证据。P049 改由全新实例在显式命名的源码/PDF/目标证据目录范围内从头审查，禁止搜索整个 `_work/evidence` 根。
- reason: 初始 SA1 的独立性要求严禁读取旧恢复摘要；即使代理声明未据该行下结论，暴露本身也使该实例不再满足盲审来源隔离门。
- affected_scope: FIG-P049-01 初始 SA1；后续所有恢复摘要缺口的搜索范围
- affected_files: 后续 `evidence/figures/FIG-P049-01/R1/FIG-P049-01-SA1-R1.md`; `SUBAGENT_HANDOFF.md`
- supersedes: 被中断的首个 FIG-P049-01 重开实例全部未落盘中间结果

## D-010

- status: accepted
- date: 2026-08-23
- decision: FIG-P577-01 的数学与读图权威采用真实图源及 V5-C02 正文：p(y)=6y(1-y)、q(y)=1、c=8/5，接受门为 Ucq(Y)<=p(Y)（含边界）。Goal 附录 B42 与中央 figure manifest 中误写的“广义逆”读图结论属于相邻对象串项，只作只读冲突证据，不再驱动本图修改。
- reason: 图源、标签、章节首次引用、数值清单和图 31.4 题注均唯一指向接受--拒绝包络；独立复算得到最小间隙 1/10、接受率 5/8、平均提议数 8/5、拒绝区面积 3/5，两固定点的阈值均为 45/64。该证据链高于错位卡片文字，并符合 D-006 的材料权威顺序。
- affected_scope: FIG-P577-01 的图源、wrapper、V5-C02 图文关系、source/numeric metadata、中央 figure manifest 与逐图证据
- affected_files: src/绘图源码/第05册_采样方法主题模型与图排序/V5-C02/fig_v5_c02_rejection_envelope.tex; src/讲义源码/第05册_采样方法主题模型与图排序/chapters/V5-C02.tex; src/绘图源码/figure_numeric_manifest_v16.json; figures/figure_manifest.csv; evidence/figures/FIG-P577-01/**
- supersedes: Goal 附录 B42 与旧中央清单中误路由到 FIG-P577-01 的“广义逆”读图结论；Goal 原文件保持只读

## D-011

- status: accepted
- date: 2026-08-23
- decision: FIG-P578-01 的权威对象是 V5-C02 正文正式接受--拒绝算法契约及其带预算工程状态机。Goal 附录 B43 与旧中央清单中沿用的包络几何/曲线判点结论属于相邻 FIG-P577-01 串项，只作只读冲突证据，不再驱动 P578 修改。
- reason: P578 唯一图源、标签、章节首次引用与图31.5题注均指向带预算流程；其必要信息是随机调用前预检、`m/a`原子更新、完成优先于预算、五个适用规范状态、合法前缀与失败诊断。包络曲线、接受点和拒绝面积已由图31.4承担。该对象分工符合 D-006 的材料权威顺序并避免两图重复。
- affected_scope: FIG-P578-01 的图源、wrapper、V5-C02 图文关系、source metadata、中央 figure manifest 与逐图证据
- affected_files: src/绘图源码/第05册_采样方法主题模型与图排序/V5-C02/fig_v5_c02_rejection_flow.tex; src/讲义源码/第05册_采样方法主题模型与图排序/chapters/V5-C02.tex; figures/figure_manifest.csv; evidence/figures/FIG-P578-01/**
- supersedes: Goal 附录 B43 与旧中央清单中误路由到 FIG-P578-01 的包络几何读图结论；Goal 原文件保持只读

## D-012

- status: accepted
- date: 2026-08-23
- decision: FIG-P580-01 的权威对象是 V5-C02 的重要性抽样支持覆盖对照：在共同有限域上使用解析归一化的目标与提议密度，左图展示 `q_L=0<p` 的支持缺口，右图展示 `p\ll q_R` 及真实密度比。Goal 附录 B44 与旧中央清单中沿用的带预算接受--拒绝状态机结论属于相邻 FIG-P578-01 串项，只作只读冲突证据，不再驱动 P580 修改。
- reason: P580 唯一图源、标签、章节首次引用与图31.6题注均指向重要性抽样支持关系；三密度可解析归一化，三个代表点比率可精确复算。状态、预算和包络失败已由图31.5承担。该对象分工符合 D-006 的材料权威顺序并避免相邻图语义重复。
- affected_scope: FIG-P580-01 的图源、wrapper、V5-C02 图文关系、source/numeric metadata、中央 figure manifest 与逐图证据
- affected_files: src/绘图源码/第05册_采样方法主题模型与图排序/V5-C02/fig_v5_c02_is_support.tex; src/讲义源码/第05册_采样方法主题模型与图排序/chapters/V5-C02.tex; src/绘图源码/figure_numeric_manifest_v16.json; figures/figure_manifest.csv; evidence/figures/FIG-P580-01/**
- supersedes: Goal 附录 B44 与旧中央清单中误路由到 FIG-P580-01 的带预算接受--拒绝流程结论；Goal 原文件保持只读

## D-013

- status: accepted
- date: 2026-08-23
- decision: 用户附件 `e9427863-0663-4847-93b3-d9c784a212b5/pasted-text.txt` 及其发布根逐字副本成为 v2.7.0 当前最高 Goal；其第 9.2.1 节覆盖旧视觉协议和旧“通过图保持关闭”口径。旧源码、数学复算与设计成果继续复用，但缺少新五类 `after_*` 产物的历史 PASS 不得迁移为最终 PASS。
- reason: 用户明确要求“把目标更新为这个”；新 Goal 把有效字号、300 dpi 逐元素量测、同类/角色比例、零重叠、零裁切和最小净空设为不可缺失的硬门。迁移盘点显示五类强制最终产物均为 0/99。
- affected_scope: M01--M10、99 图重新资格认定、全书最终视觉扫描、两份三角色台账与 12 项交付
- affected_files: 根 `GOAL.md`、`PROMPT_RUNTIME_CORE.md`、`CONTEXT_CAPSULE.md`、`CURRENT_TASK.json`、全部 `_work/state/**`、`evidence/figures/**` 与最终发布文件
- supersedes: D-006 中旧 `goal-objective.md` 的“当前最终文字权威”身份；Revision 86 临时 9.6pt/4px 协议；旧 28 图根接受作为最终放行的效力。D-006 的材料冲突处理顺序继续有效。

## D-014

- status: accepted
- date: 2026-08-23
- decision: 新 Goal 的规范 `WORK_ROOT=v2.7.0_work` 通过目录联接指向现有物理树 `v2.7.0\_work`，不复制或重建工作树。所有恢复文档使用规范路径，并明确兼容事实。
- reason: 新 Goal 固定同级 `v2.7.0_work`，而长期任务已在 `v2.7.0\_work` 产生大量有效源码与证据；目录联接同时满足固定路径和“继续现有工作树、不得从零重建”。
- affected_scope: 工作路径、状态恢复、subagent 交接、构建与证据输出
- affected_files: `v2.7.0_work` Junction；根恢复入口；`PROJECT_CHARTER.md`
- supersedes: PROJECT_CHARTER revision 1 中把 `v2.7.0\_work` 写作规范 WORK_ROOT 的路径定义

## D-015

- status: accepted
- date: 2026-08-23
- decision: 最新附件 `cf14964e-b5d2-474a-a753-eb49e993ff9d/goal-objective.md` 成为最高 Goal 身份，并逐字同步到发布根同名主提示词；其大小为 287,029 bytes，SHA-256 为 `B60E2436C422BDEF817F8D3316C7AD0AB5E1B340256ED3DFBE86DFFDEBEB3BF9`。
- reason: 用户明确要求更新目标。完整规范化比较显示它与 D-013 所指 Goal 仅有 Markdown 转义差异，去除 `\_`、`\*`、`\.` 后逐字符一致，故不改变任务实质、不重置已有源码/证据/计数，也不重新打开 P632/P756。
- affected_scope: Goal 身份、根恢复文件、状态检查点、十二项交付中的主提示词副本
- affected_files: `GOAL.md`; `PROMPT_RUNTIME_CORE.md`; `CONTEXT_CAPSULE.md`; `CURRENT_TASK.json`; `PROJECT_CHARTER.md`; `INPUT_RESOLUTION.md`; 发布根 Goal 主提示词
- supersedes: D-013 中旧附件路径、字节数与哈希身份；D-013 的实质目标与验收规则继续有效

## D-016

- status: accepted
- date: 2026-08-23
- decision: 用户再次指定 `e9427863-0663-4847-93b3-d9c784a212b5/pasted-text.txt` 为最高 Goal 身份，并逐字同步到发布根同名主提示词；其大小为 285,753 bytes，SHA-256 为 `51BA862B1EEBCD6765565FEE6243BD2BC8BF2611D586115B52623668711928C2`。
- reason: 新附件是 D-015 所指文本去除 Markdown 转义后的同文版本；规范化后仅剩 `\*`、`\.` 两处转义差异，故不改变任务实质、不重置已有源码/证据/计数，也不重开新协议已通过的 P020/P632/P756。
- affected_scope: Goal 身份、根恢复文件、状态检查点、十二项交付中的主提示词副本
- affected_files: `GOAL.md`; `PROMPT_RUNTIME_CORE.md`; `CONTEXT_CAPSULE.md`; `CURRENT_TASK.json`; `PROJECT_CHARTER.md`; `INPUT_RESOLUTION.md`; 发布根 Goal 主提示词
- supersedes: D-015 中附件路径、字节数与哈希身份；D-013/D-015 的实质目标与验收规则继续有效

## D-017

- status: accepted
- date: 2026-08-24
- decision: 用户指定附件 `e9427863-0663-4847-93b3-d9c784a212b5/pasted-text.txt` 及发布根逐字副本继续作为交付中的 Goal 权威；平台当前执行镜像 `3cad37cf-9e33-47b2-aea3-7ff46f3a6153/goal-objective.md` 作为运行上下文镜像共同记录。
- reason: 根线程完整读取平台镜像2,275行，并确认它与用户附件在去除 Markdown 转义 `\_`、`\*`、`\.` 及统一换行后逐字符一致。两种身份没有实质目标或验收门差异，因此既满足平台当前上下文，也保持用户明确指定的发布文件，不触发源码、证据、计数或阶段重置。
- affected_scope: Goal恢复身份、revision 101状态、代理恢复指令；不影响图源、官方R93或严格通过计数
- affected_files: `GOAL.md`; `PROMPT_RUNTIME_CORE.md`; `CONTEXT_CAPSULE.md`; `CURRENT_TASK.json`; `PROJECT_CHARTER.md`; `NEXT_ACTIONS.md`; `SUBAGENT_HANDOFF.md`; `CURRENT_STATUS.md`
- supersedes: 不取代D-016的用户指定发布身份；补充平台执行镜像身份与二者同一性证据

## D-018

- status: accepted
- date: 2026-08-24
- decision: 最新 Goal 的 99 图逐图任务表与用户后续“以前通过的绘图全部重新检查”明确要求，覆盖早期交接中的七图旧协议豁免。P547/P602/P608/P609/P630/P654/P715 保留历史源码和证据，但旧 PASS 不得迁移，必须按第 9.2.1 节重新资格认定。
- reason: 最新附件逐项列出全部 99 图且没有排除这七图；用户在发现 P632/P580 肉眼可见重叠后又明确要求复查当前任务与原 v2.7.0 对话中的全部已通过绘图。继续跳过七图会与最新 Goal 和后续明确请求冲突。
- affected_scope: 99 图严格复核库存、后续独立 SA1/SA3 排队、最终绘图台账
- affected_files: `PROMPT_RUNTIME_CORE.md`; `CONTEXT_CAPSULE.md`; `CURRENT_TASK.json`; `PROJECT_CHARTER.md`; `NEXT_ACTIONS.md`; `CURRENT_STATUS.md`; `SUBAGENT_HANDOFF.md`
- supersedes: Revision 103--106 及较早恢复文本中的“禁止重开/跳过 P547/P602/P608/P609/P630/P654/P715”执行口径；P020/P157/P632/P756 的后续处置由 D-019 更新

## D-019

- status: accepted
- date: 2026-08-24
- decision: 撤销 P020/P157/P632/P756 的当前最终计数，把四图重新排入独立 SA1；其旧源码、旧证据和根签发仅作历史，不删除。
- reason: 当前严格 schema 强制 100% 可见字形 contact sheet、逐格人工 ledger、final raw-mask 完整性/污染闭合和 1×+8×失败/临界包；schema 更新时间晚于四图旧签发，而四个终局目录中上述 contact/ledger/integrity 文件均为 0。用户又明确要求把所有已经完成的绘图全部重新检查，因此证据不足不能继续记作 PASS。
- affected_scope: 99图严格最终计数、中央资格库存、历史通过图双 subagent 队列、最终视觉证据包
- affected_files: `STRICT_REQUALIFICATION_INVENTORY.csv`; `CURRENT_STATUS.md`; `SUBAGENT_HANDOFF.md`; `NEXT_ACTIONS.md`; 根恢复文件
- supersedes: D-018、PROJECT_CHARTER revision 4 及 Revision 109 中保留 P020/P157/P632/P756 为 CLOSED/4-of-99 的口径

## D-020

- status: accepted
- date: 2026-08-24
- decision: 对 Goal 未列绝对下限的低轮廓标点采用同字形/同字体/同有效字号的原生300dpi校准门，不再机械套用22px/30px；数学运算符与分数主体的既有22px门保持不变。
- reason: Goal 9.2.1-C 的五档绝对门不包含低轮廓标点；把正常句点、逗号或CJK句号按全高/数学运算符强制放大，会制造突兀字形并与用户明确要求的字体协调性冲突。独立raw mask加同字形H_INK/面积双比例校准既保留逐像素严格性，也避免借父对象高度或错误分类伪造结论。
- affected_scope: 99图逐字形像素门、P580/P577/P582/P634失败计数复算、所有后续SA1/SA2/SA3证据
- affected_files: `STRICT_FIGURE_EVIDENCE_SCHEMA.md`; `CURRENT_STATUS.md`; `SUBAGENT_HANDOFF.md`; 根恢复文件
- supersedes: 任何把句点/逗号/分号等低轮廓标点机械归入22px数学运算符或30px全高字符的临时解释；不改变运算符、分数主体及合法上下标/上下限阈值

## D-021

- status: accepted
- date: 2026-08-24
- decision: P577 R3 图本身以六项 root 独立确认的关系/遮挡失败保守转入 SA2；代理宣称的 evidence integrity PASS 因两份 CSV 重复列名被降为 FAIL。
- reason: 345字形、345人工行、59,340 pair、3条精化关系、6条遮挡关系、2021 PNG及ADS均已由root复算，但 `text_graphic_relations.csv` 及其 superseded 版本不能无歧义解析。严格流程不能把不可解析底表写成证据PASS；同时真实2px净空和3825px白底遮曲线证据足以要求返修，无需把坏图留在SA1重复取证。
- affected_scope: FIG-P577-01 R3 根验收、中央资格库存、唯一SA2队列、历史通过图复审槽
- affected_files: `FIG-P577-01/STRICT_R1/SA1_20260824_R3/STRICT_R1_FINAL/ROOT_ROUTING_ACCEPTANCE.md`; `STRICT_REQUALIFICATION_INVENTORY.csv`; 状态与恢复文件
- supersedes: P577 R3 `TERMINAL_MANIFEST.json` 中的 `evidence_integrity_result=PASS`；不改变其 figure FAIL 与六项真实返修事实

## D-022

- status: accepted
- date: 2026-08-24
- decision: 接受 P582 R95 独立 SA1 证据完整性，但否决图形通过并转入 SA2；释放的独立审查实例立即用于 P157 的旧通过图盲审。
- reason: 根线程复算并打开 139 个 final glyph、12 张 contact sheet、1,891 pair、1,686 关系和 1,329 PNG，确认 E014 箭头与 E016 `.380` 末位 `0` 有 3px 真实碰撞；另有源字号、逐字像素、D/E 和字体视觉协调硬门失败。证据 terminal 与底表一致，因此无需重复 SA1 取证，可保守进入串行修图队列。
- affected_scope: FIG-P582-01 路由、99 图中央库存、P157 历史通过图重新资格认定、字号协调审查门
- affected_files: `FIG-P582-01/STRICT_R1/SA1_20260824_R1/ROOT_ROUTING_ACCEPTANCE.md`; `STRICT_REQUALIFICATION_INVENTORY.csv`; 状态与恢复文件
- supersedes: P582 的历史“已完成”状态及任何未按当前 schema 产生的旧通过印象；不改变 P580 唯一业务源码写者约束

## D-023

- status: accepted
- date: 2026-08-24
- decision: P020 旧 PASS 的当前 schema 重审以图形 `FAIL→SA2` 路由；代理 evidence-integrity PASS 因 stop 后继续写 terminal 被 root 降为 FAIL。
- reason: 根线程逐张打开18张contact和全图视图，并从G091 raw mask独立复算CJK `一` 的 `H_INK=5<30px`。同时磁盘明确显示 `WRITE_STOPPED.md` 后8秒仍写入两份terminal JSON，与“最后写入”声明冲突。真实图硬门失败可保守用于修图，但证据终态不能记PASS。
- affected_scope: FIG-P020-01 重新资格认定、中央库存、第一条历史旧图审查线、terminal封存流程
- affected_files: `FIG-P020-01/STRICT_R6_REQUAL_R111_SA1_20260824/ROOT_ROUTING_ACCEPTANCE.md`; `STRICT_REQUALIFICATION_INVENTORY.csv`; 状态与恢复文件
- supersedes: P020 的所有旧最终PASS及本轮 `MACHINE_INTEGRITY.json` 的 evidence PASS；不否定本轮直接可复算的G091失败

## D-024

- status: accepted
- date: 2026-08-24
- decision: P157与P632的当前schema重新资格认定均判图形硬门FAIL并转SA2；P157 evidence integrity为PASS，P632 evidence integrity为FAIL。
- reason: P157有五个低轮廓校准失败、E门8 glyph及两条独立曲线139px真实共享；P632有30个原生像素字号失败、D13/E12、36个真实净空失败，并存在R0046旧结果不一致、G204–G209语义父级错误、413行raw role-ratio未闭合和stop最后写入不可证明。root已打开P157全部10张、P632全部42张glyph contact及关键1×/8×关系包。
- affected_scope: FIG-P157-01与FIG-P632-01路由、中央资格库存、两条历史旧图审查线、字号协调与净空硬门
- affected_files: 两图各自 `ROOT_ROUTING_ACCEPTANCE.md`; `STRICT_REQUALIFICATION_INVENTORY.csv`; 状态与恢复文件
- supersedes: 两图全部旧PASS与当前SA1字段；不把R0046一致性失败误计为第37个物理净空失败

## D-025

- status: accepted
- date: 2026-08-24
- decision: 按用户最新明确边界，不为P547/P602/P608/P609/P630/P654/P715创建新的重开审查任务；保留现有源码、历史证据和库存行，不迁移旧PASS，也不虚增严格最终完成数。
- reason: 当前恢复指令明确列出七个UID“不要重开”。这限制后续调度，但不把缺少当前schema闭环的历史状态自动升级为新PASS。
- affected_scope: 历史通过图盲审排队、中央库存解释、恢复文件
- affected_files: `CURRENT_STATUS.md`; `NEXT_ACTIONS.md`; `SUBAGENT_HANDOFF.md`; 根恢复文件
- supersedes: D-018及Revision107以后要求重新打开这七个UID的调度口径；不改写已经保留的历史证据

## D-026

- status: accepted
- date: 2026-08-24
- decision: 用户再次明确要求“把目标更新为”附件 `e9427863-0663-4847-93b3-d9c784a212b5/pasted-text.txt`；该附件逐项要求 99 图全量闭环，故 P547/P602/P608/P609/P630/P654/P715 恢复到当前 schema 的重新资格认定队列。
- reason: 附件与发布目录主提示词逐字一致，明确规定不得因旧“已完成”跳过任何图，并把七图列入 99 图任务表。较早恢复摘要的七图豁免与本次完整 Goal 冲突，必须以后者为准。
- affected_scope: Goal 权威、历史通过图调度、中央库存解释、恢复文件
- affected_files: `GOAL.md`; `CURRENT_TASK.json`; `PROMPT_RUNTIME_CORE.md`; `CONTEXT_CAPSULE.md`; `CURRENT_STATUS.md`; `NEXT_ACTIONS.md`; `SUBAGENT_HANDOFF.md`
- supersedes: D-025 的七图“不创建新重开任务”调度限制；不改写七图历史证据、不迁移旧 PASS、不立即抢占当前 P580 单一源码写者或 P756/P582-02 两条审查槽

## D-027

- status: accepted
- date: 2026-08-24
- decision: 接受P580 SA2本地修复为官方R96构建输入并冻结R96，但只把P580路由到新的独立SA1；同时接受P756和P582-02的当前schema失败并转SA2，启动P547/P602两条旧PASS重新资格认定线。
- reason: P580局部证据和root原生1×/8×复核足以支持正式构建，R96的813页/A4/字体/最终日志及候选哈希全部闭合；这些构建与root预检仍不能代替独立SA1/SA3。P756的独立路线792px共享及三个29px CJK、P582-02的67个低字号/三个raw高度/21项校准缺口均是不可被其他PASS门抵消的当前硬失败。完整Goal又要求旧通过图全部重审，因此P547/P602立即占用两条只读槽。
- affected_scope: R96官方候选、FIG-P580-01新SA1、FIG-P756-01与FIG-P582-02路由、P547/P602旧PASS重审、中央严格库存
- affected_files: `FIG-P580-01/STRICT_R3_ROOT_R96_FREEZE/`; `FIG-P756-01/STRICT_R10_ROOT_FAIL_ACCEPTANCE_R115_20260824/`; `FIG-P582-02/STRICT_R11_ROOT_FAIL_ACCEPTANCE_R115_20260824/`; `STRICT_REQUALIFICATION_INVENTORY.csv`; 状态与恢复文件
- supersedes: Revision116中R95仍为官方候选、P580仍为唯一源码写者、P756/P582-02仍在SA1的现场描述；不改变严格最终0/99或任何图需SA1→必要SA2→新SA1→隔离SA3→root闭环的门

## D-028

- status: accepted
- date: 2026-08-24
- decision: 接受P756 R97全新独立SA1的证据完整性与图形硬门PASS，但只把它路由到全新隔离SA3，不计最终关闭。
- reason: root独立重哈希1408项JSON/1409项SHA manifest为0错，确认stop最后写，并实际打开16张glyph contact、11张graphic contact、32个当前critical五联卡、G030/G031 z-order与官方整页/图体/灰度。251 glyph、69对象、2,346 pair、39条drawing path、0数学规则的0↔0对账、overlap0、clip0、普通9.60--10.20pt与字体协调均闭合；当前schema仍要求独立隔离SA3从官方候选自行重建证据。
- affected_scope: FIG-P756-01 R97路由、中央严格库存、独立SA3隔离边界、revision124恢复状态
- affected_files: `FIG-P756-01/STRICT_R16_ROOT_SA1_ACCEPTANCE_R97_20260824/ROOT_ROUTING_ACCEPTANCE.md`; `STRICT_REQUALIFICATION_INVENTORY.csv`; 状态与恢复文件
- supersedes: Revision123中P756仍在SA1与35项临界关系未完成的现场描述；不改变严格最终0/99或P547唯一业务源码写者约束
