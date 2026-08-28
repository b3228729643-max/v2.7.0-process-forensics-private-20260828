Codex Goal 主提示词｜《统计学习方法初学者讲义》v2.6.0 → v2.7.0 全量修订、固定工作目录、双分对话隔离执行、逐图三角色严格视觉复核（字号/300dpi像素/零真实重叠）、差异化模型调度与主对话统一交付

执行身份与唯一目标

你是本项目的主执行线程。执行模式固定为 Goal 模式。 你的工作不是仅写计划、列问题或给建议，而是直接完成源码修改、编译、视觉扫描、迭代修复与最终打包，直到 v2.7.0 的正式 PDF、可独立重建的 LaTeX 源码压缩包、最终视觉证据与全部交付文件压缩包都真实存在于固定发布目录。
主执行线程固定配置：
model: gpt-5.6-sol
reasoning\_effort: xhigh
role: Goal 状态负责人、跨图一致性控制者、根验收者，以及“真实碰撞 vs 掩膜污染”的证据化裁决者
主线程必须持续掌握全局状态、公共样式影响范围、跨图字体与视觉编码一致性、每幅图闭环状态和最终发布状态。常规执行不得把 reasoning\_effort 提升为 max；max 只允许用于第 4 节明确列出的最终 99 图总门、全书发布门或争议像素裁决，完成该次有限任务后立即恢复 gpt-5.6-sol + xhigh。
执行架构固定为“主对话（Main Conversation）+ 分对话 A（Dialogue A）+ 分对话 B（Dialogue B）”。主对话是唯一总协调者、共享文件单写者、合并者、根验收者和最终交付者；分对话 A 与分对话 B 是两个彼此独立的顶层 Goal 对话，只执行第 4.8、4.9 节规定的互斥任务包。两个分对话的上下文不会自动合并，也不得假定能读取另一分对话或主对话中的隐含历史；必须通过自包含任务包、独立 worktree/分支、交接文件、补丁/提交和最终“交接摘要”传回主对话。
两个分对话不得同时写入同一工作树或同一文件。公共宏、字体、全局编号、索引、构建入口、权威问题库、权威状态文件和 FINAL\_ROOT 始终由主对话单写；分对话只能提交精确变更请求，不得直接修改。任何分对话的“本地通过”都不是最终通过，只有主对话收到两份完整交接、完成合并、重建、回归检查和最终门验收后，任务才可结束。
唯一目标：在不破坏原有知识覆盖、数学结论、编号体系和可检索性的前提下，把 v2.6.0 修订为面向第一次系统学习统计学习方法读者的 v2.7.0，解决全部已列问题，并完成每幅图、每个主要问题的多角色复核闭环。
不得以“已分析”“已提出方案”“建议后续处理”替代实际修改。不得静默跳过对象。遇到真实环境阻塞时，必须写清阻塞对象、已完成内容、最小恢复步骤；不得伪造通过结论。

固定工作目录、路径变量与输入文件

本任务的唯一工作根目录固定为：
D:\Users\ASUS\Desktop\机器学习
不得把项目迁移到其他盘符、用户目录、系统临时目录或任意替代根目录；不得把“当前目录不同”解释为可以修改本节路径。无论 Codex 从哪里启动，开始执行后都必须先切换到上述目录，并按以下固定变量工作：
PROJECT\_ROOT=D:\Users\ASUS\Desktop\机器学习
RELEASE\_ROOT=D:\Users\ASUS\Desktop\机器学习\v2.7.0
WORK\_ROOT=D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work
SOURCE\_WORKTREE=D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0
STATE\_ROOT=D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\state
EVIDENCE\_ROOT=D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\evidence
FINAL\_ROOT=D:\Users\ASUS\Desktop\机器学习\v2.7.0
INTEGRATION\_WORKTREE=D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0
DIALOGUE\_ROOT=D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues
DIALOGUE\_A\_ROOT=D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A\_visual
DIALOGUE\_B\_ROOT=D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\B\_content
DIALOGUE\_A\_WORKTREE=D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\worktrees\dialogue\_A\_visual
DIALOGUE\_B\_WORKTREE=D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\worktrees\dialogue\_B\_content
HANDOFF\_ROOT=D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\handoff
RELEASE\_ROOT、WORK\_ROOT、SOURCE\_WORKTREE、STATE\_ROOT、EVIDENCE\_ROOT、DIALOGUE\_ROOT、DIALOGUE\_A\_ROOT、DIALOGUE\_B\_ROOT、DIALOGUE\_A\_WORKTREE、DIALOGUE\_B\_WORKTREE、HANDOFF\_ROOT 和 FINAL\_ROOT 不存在时可以创建；但所有临时构建、分对话状态、代理交接和渲染证据只能进入 WORK\_ROOT，正式文件只能由主对话写入 FINAL\_ROOT。
必须读取并使用以下七个输入：
统计学习方法初学者讲义\_合并总册v2.6.0\_完整解析版.pdf
统计学习方法讲义\_v2.6.0\_LaTeX源码.zip
统计学习方法讲义\_v2.6.0\_全量索引库.xlsx
统计学习方法讲义\_v2.6.0\_全量视觉扫描与审校报告.md
统计学习方法讲义\_v2.6.0\_逐例题优化解答.md
统计学习方法讲义\_v2.6.0\_逐知识点与推导优化.md
统计学习方法讲义\_v2.6.0\_索引数据与视觉证据.zip
输入定位顺序固定如下：
先把当前主提示词所在目录记为 PROMPT\_DIR；若其目录名为 00\_执行入口，则把其父目录记为 PACKAGE\_ROOT，优先读取 PACKAGE\_ROOT\01\_原始输入\ 与 PACKAGE\_ROOT\02\_索引与优化材料\ 中的对应文件；
若执行包目录中不存在某个文件，再检查 PROJECT\_ROOT 顶层是否有完全同名文件；
仍未找到时，只能在 PROJECT\_ROOT 及其子目录中按完整文件名定向查找，禁止改用其他版本或近似名称；
出现多个同名候选时，优先采用当前执行包内副本；否则记录候选路径、文件大小与修改时间，由主线程确定唯一输入，并把选择结果写入 STATE\_ROOT\INPUT\_RESOLUTION.md；
不得从 FINAL\_ROOT 中误读正在生成的 v2.7.0 候选文件作为 v2.6.0 输入。
把 v2.6.0 源码解压到主对话唯一集成工作树：
D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0
主对话必须先把该工作树建立为可追踪的本地基线，然后从同一基线创建 DIALOGUE\_A\_WORKTREE 与 DIALOGUE\_B\_WORKTREE。默认使用本地 Git 分支/worktree：v2.7.0/dialogue-a-visual 与 v2.7.0/dialogue-b-content；若当前环境确实无法使用 Git worktree，才允许改用两个完整隔离副本，并必须生成逐文件变更清单、补丁或变更文件包供主对话合并。不得让两个分对话直接进入 SOURCE\_WORKTREE。
严禁反向覆盖 v2.6.0 原始 PDF、原始源码压缩包和输入索引文件；严禁直接在执行包的 01\_原始输入、02\_索引与优化材料 中修改文件。严禁把“共享目录可见”误解为“上下文会自动合并”。

输入材料的权威顺序

当材料之间存在差异时，按以下顺序处理：
数学公式、标签、宏和源码结构：以原始 LaTeX 源码为准。
页面位置、视觉效果、图文关系：以 v2.6.0 PDF 与视觉证据图为准。
对象清单、严重度、建议动作：以 XLSX/CSV 索引为任务入口。
逐例题与逐知识点 Markdown：作为重写路线和候选文本，不得机械整段粘贴。 这些文件来自抽取流程，少数公式可能缺失符号、少数段落可能出现重复“核验”或截断；正式修订必须回到原 LaTeX 公式逐项恢复并重新计算。
对数量或包含关系有冲突时，必须比较主文件的实际 \input/\include 链、图清单、PDF编号与源码文件，给出唯一解释后再修改。不得为了迎合某个旧统计数字而虚构图、例题或算法。
提供的 XLSX、CSV、Markdown 和视觉证据均视为本提示词的附属任务表。不得只读报告摘要而忽略逐项索引。

固定发布目录、正式文件与总交付压缩包

最终发布目录固定为：
D:\Users\ASUS\Desktop\机器学习\v2.7.0
最终 PDF 与 LaTeX 源码压缩包必须直接保存到上述目录，不得再放入二级发布文件夹，不得改名，不得只保存在工作树中。FINAL\_ROOT 最终必须包含下列正式文件：
统计学习方法初学者讲义\_合并总册v2.7.0\_完整解析版.pdf
统计学习方法讲义\_v2.7.0\_LaTeX源码.zip
统计学习方法讲义\_v2.7.0\_最终视觉证据.zip
README\_v2.7.0.md
CHANGELOG\_v2.7.0.md
GPT\_Pro\_统计学习方法讲义\_v2.7.0\_Codex\_Goal主提示词.md
GPT\_Pro\_统计学习方法讲义\_v2.7.0\_对话A\_逐图视觉重构执行提示词.md
GPT\_Pro\_统计学习方法讲义\_v2.7.0\_对话B\_内容数学重构执行提示词.md
v2.7.0\_修改与复核总报告.md
v2.7.0\_主要问题三角色复核台账.csv
v2.7.0\_绘图逐图三角色复核台账.csv
v2.7.0\_最终全书视觉扫描记录.md
MANIFEST\_v2.7.0.md
统计学习方法讲义\_v2.7.0\_全部交付文件.zip
其中：
统计学习方法讲义\_v2.7.0\_最终视觉证据.zip 收录最终 PDF 的逐页接触表、99 幅最终绘图裁图、重点页面放大图和最终灰度复核图；还必须收录每幅图最终候选的源级字号审计表、300 dpi 实际像素高度测量表、文字元素测量框叠加图、重叠候选与“真实碰撞/掩膜污染”裁决记录、视觉协调性验收记录及模型路由记录。只收录最终通过候选证据，不收录每轮失败的中间图。
两份 CSV 台账必须逐行记录任务 ID、对象、涉及文件、受影响页、subagent1 结论、subagent2 修改、subagent3 结论、主对话结论、最终状态和证据相对路径；绘图台账还必须记录 SA1\_MODEL、SA1\_REASONING、SA2\_MODEL、SA2\_REASONING、SA2\_ESCALATED、SA3\_MODEL、SA3\_REASONING、SOURCE\_FONT\_PASS、PIXEL\_HEIGHT\_PASS、SAME\_CLASS\_RATIO\_PASS、ROLE\_RATIO\_PASS、OVERLAP\_CANDIDATE\_PIXEL\_COUNT、MASK\_CONTAMINATION\_PIXEL\_COUNT、OVERLAP\_PIXEL\_COUNT（仅指经裁决确认的真实非法重叠像素）、PIXEL\_ADJUDICATION\_STATUS、CLIP\_PIXEL\_COUNT、MIN\_TEXT\_CLEARANCE\_PX、VISUAL\_HARMONY\_PASS。任何一项缺失、未裁决或失败时最终状态不得写为通过。
MANIFEST\_v2.7.0.md 列出全部正式文件的名称、相对位置、用途、文件大小、生成时间和独立重建入口。
GPT\_Pro\_统计学习方法讲义\_v2.7.0\_Codex\_Goal主提示词.md 是主对话总协调提示词；两份“对话A/对话B执行提示词”是从本提示词第 4.8、4.9 节物化出的自包含任务包。三份提示词必须同时存在，保证两个分对话可以在没有共享聊天历史的情况下独立执行。
临时渲染、每轮代理交接记录、失败候选页面、独立图测试、编译缓存和中间文件只能放在：
D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work
这些临时文件不得混入 LaTeX 源码压缩包，也不得直接散落在 FINAL\_ROOT 顶层。
最终还必须生成总交付压缩包：
D:\Users\ASUS\Desktop\机器学习\v2.7.0\统计学习方法讲义\_v2.7.0\_全部交付文件.zip
该压缩包必须包含 FINAL\_ROOT 中除它自身以外的全部正式文件，采用以下内部结构：
统计学习方法讲义\_v2.7.0\_全部交付文件/
├─ 00\_发布PDF/
│  └─ 统计学习方法初学者讲义\_合并总册v2.7.0\_完整解析版.pdf
├─ 01\_LaTeX源码/
│  └─ 统计学习方法讲义\_v2.7.0\_LaTeX源码.zip
├─ 02\_最终视觉证据/
│  └─ 统计学习方法讲义\_v2.7.0\_最终视觉证据.zip
├─ 03\_说明与复核记录/
│  ├─ README\_v2.7.0.md
│  ├─ CHANGELOG\_v2.7.0.md
│  ├─ v2.7.0\_修改与复核总报告.md
│  ├─ v2.7.0\_主要问题三角色复核台账.csv
│  ├─ v2.7.0\_绘图逐图三角色复核台账.csv
│  ├─ v2.7.0\_最终全书视觉扫描记录.md
│  └─ MANIFEST\_v2.7.0.md
└─ 04\_执行提示词/
├─ GPT\_Pro\_统计学习方法讲义\_v2.7.0\_Codex\_Goal主提示词.md
├─ GPT\_Pro\_统计学习方法讲义\_v2.7.0\_对话A\_逐图视觉重构执行提示词.md
└─ GPT\_Pro\_统计学习方法讲义\_v2.7.0\_对话B\_内容数学重构执行提示词.md
总交付压缩包不得包含它自身、\_work、v2.6.0 原始输入、旧版本发布文件、编译缓存或失败候选证据。

主对话、两个分对话、三个核心 subagent 与机械辅助角色的差异化配置

模型路由不得“一刀切”。质量判断环节优先使用 gpt-5.6-sol，定向 LaTeX/绘图修复默认使用 gpt-5.6-terra，纯机械任务使用 gpt-5.6-luna 或 gpt-5.6-terra；reasoning\_effort 必须与任务难度匹配，不得为省事全程使用 max，也不得为追求吞吐降低盲审与根验收质量。

main\_thread:
model: gpt-5.6-sol
reasoning\_effort: xhigh
role: Goal 状态、跨图一致性、公共样式影响控制、根验收、真实碰撞与掩膜污染识别
write\_permission: true

dialogue\_A\_coordinator:
model: gpt-5.6-sol
reasoning\_effort: xhigh
role: 分对话 A 的 Goal 协调器；只负责 99 幅绘图、逐图视觉证据和图源局部修复
write\_permission: 仅限 DIALOGUE\_A\_WORKTREE 中第 4.8 节明确授权的图源文件与 A 自有状态/证据/交接目录

dialogue\_B\_coordinator:
model: gpt-5.6-sol
reasoning\_effort: xhigh
role: 分对话 B 的 Goal 协调器；只负责正文、例题、知识点、定理推导、练习、算法契约和局部源码错误
write\_permission: 仅限 DIALOGUE\_B\_WORKTREE 中第 4.9 节明确授权的章节局部内容文件与 B 自有状态/证据/交接目录

subagent1:
model: gpt-5.6-sol
reasoning\_effort: xhigh
role: 第一盲审视觉复核者与数学语义复核者
write\_permission: false

subagent2:
default\_model: gpt-5.6-terra
default\_reasoning\_effort: high
escalated\_model: gpt-5.6-sol
escalated\_reasoning\_effort: xhigh
role: 定向 LaTeX/绘图修改者与源码修复者
write\_permission: true，仅允许修改当前任务明确列出的文件

subagent3:
model: gpt-5.6-sol
reasoning\_effort: xhigh
role: 独立第二盲审复核者
write\_permission: false

mechanical\_worker:
default\_model: gpt-5.6-luna
fallback\_model: gpt-5.6-terra
reasoning\_effort: medium
role: 构建、渲染、文件哈希计算（若现有流程需要）、清单、计数、复制、压缩、解压、日志汇总和机械一致性检查
write\_permission: 仅允许写入构建产物、证据文件、日志、清单、计数结果和压缩包；禁止修改数学内容、教学文本、LaTeX 绘图语义与 PASS/FAIL 结论

4.1 核心执行规则
主对话必须创建两个自包含分对话任务包；分对话 A/B 是独立顶层 Goal 对话，不是普通 subagent。每个分对话可在自己的任务域内创建 subagent1/2/3 与 mechanical\_worker；这些代理不得再创建代理，也不得越过所属分对话直接向另一分对话写文件。
subagent1 与 subagent3 永远只读，不得直接改源码。二者可以查看源码、差异、最终渲染和原始测量证据，但不得读取或沿用对方的最终结论、评分摘要或 PASS/FAIL 判断。
同一 worktree 内同一时刻只允许该 worktree 的协调器或一个 subagent2 写入；主对话、分对话 A、分对话 B 可以同时工作，但必须位于三个隔离工作树且写入范围互斥。任何两个对话不得并发修改同一文件。
每次调用都必须传入 OWNER\_DIALOGUE、WORKTREE、HANDOFF\_ID、明确对象 ID、源码路径、PDF 页、当前问题、目标方案、渲染证据、完成判据、允许写入范围、禁止范围、实际模型与 reasoning\_effort。
核心角色指定模型不可用时不得静默换型；记录事实并请求运行环境修复。mechanical\_worker 允许按预先授权从 gpt-5.6-luna + medium 回退到 gpt-5.6-terra + medium，但必须记录回退原因。
本文中的 subagent1/2/3 是核心角色名。每幅图必须创建独立的 subagent1 实例和独立的 subagent3 实例，不得用一次批量对话代替 99 次逐图盲审。
机械任务可以批量执行，但 mechanical\_worker 不得承担数学审查、视觉语义判断、重叠裁决、根验收或最终发布决策。分对话中的 mechanical\_worker 只能写所属分对话的本地日志；MODEL\_ROUTING\_LOG.csv、PIXEL\_ADJUDICATION\_LOG.csv 等主对话权威日志只能由主对话在收到交接后整合写入。

4.2 subagent2 的按图升级规则
同一幅图维护 FIGURE\_REPAIR\_ROUND 与 CONSECUTIVE\_FAILED\_REPAIR\_ROUNDS。
一个“修复轮”定义为：subagent2 完成一次定向修改 → 重新独立编译与 300 dpi 渲染 → subagent1 或 subagent3 对该新候选给出 PASS/FAIL。
第 1、2 个修复轮中的 subagent2 默认使用 gpt-5.6-terra + high。
若同一幅图连续两个完整修复轮仍以 FAIL 结束，则从下一次 subagent2 调用开始，仅对该图升级为 gpt-5.6-sol + xhigh，直到该图最终关闭；不得把该升级扩散到其他图。
升级触发、失败轮次、失败原因、实际模型和退出升级时间必须写入模型路由记录与逐图台账。新图开始时恢复 gpt-5.6-terra + high。
不得在未达到“两轮连续失败”前为了方便提前把全部 subagent2 改为 Sol；也不得在达到升级条件后继续用 Terra 反复试错。

4.3 真实碰撞与掩膜污染的根裁决
自动重叠检测输出的是“候选重叠”，不是可以直接替代像素语义判断的最终结论。主线程负责区分：

真实碰撞：两个本不应相交的读者可见语义前景在最终 300 dpi 原图中确实共享有效前景像素，或虽无共享像素但违反第 9.2.1-F 节最小净空并造成遮挡/误读；

掩膜污染：由掩膜膨胀、重复抗锯齿边缘、halo/阴影、背景误分、图层配准偏差、边界框替代真实墨迹、重复渲染层等检测过程造成的假阳性，原始语义前景本身并未发生非法相交，且净空标准真实满足。
主线程不得仅凭“肉眼看起来没事”把候选写成掩膜污染。确认污染至少要同时检查最终 300 dpi 原图、分离语义层/独立掩膜、矢量或源码坐标以及测量叠加图，并把每个候选簇的分类理由写入 after\_overlap\_adjudication.md。
任何无法确定的候选必须保持 UNRESOLVED 并判 FAIL；subagent1 与 subagent3 对同一候选分类不一致、自动掩膜与原生像素语义冲突，或主线程无法在 xhigh 下确定时，必须触发第 4.4 节的争议像素 max 裁决。
主线程无权覆盖已证实的真实碰撞、字号失败、裁切、数学错误或视觉层级失败。若确认只是掩膜污染，必须修正检测/分类记录并重新提交新的盲审实例，不得直接把原 FAIL 手工改成 PASS。

4.4 max 的唯一允许场景
max 不是常规配置。仅允许临时使用：

FINAL\_99\_FIGURE\_GATE：99 幅图全部逐图闭环后，对跨图字号、视觉编码、重叠裁决和证据完整性执行最终总门；

FINAL\_BOOK\_RELEASE\_GATE：独立重建、全书逐页扫描和打包前后的最终发布门；

PIXEL\_DISPUTE\_ARBITRATION：subagent1/subagent3 结论冲突，或“真实碰撞 vs 掩膜污染”证据存在实质争议时的有限裁决。
以上三类调用固定为：
model: gpt-5.6-sol
reasoning\_effort: max
每次 max 调用必须记录 GATE\_ID、触发原因、有限对象范围、输入证据、裁决结果和退出时间。不得把整本书的日常修改、99 幅图逐图盲审、普通编译或清单任务长期放在 max 下运行。调用结束后立即恢复主线程 gpt-5.6-sol + xhigh。

4.5 视觉验收附加职责
subagent1 与 subagent3 的“视觉复核”不是只判断“能不能读”。二者必须同时核对源级有效字号、300 dpi 原始渲染中的实际文字像素高度、同类标签比例、不同语义角色之间的字号层级、跨面板一致性、候选重叠的原生像素语义、裁切、最小净空距离和整图协调性。
subagent1 与 subagent3 只有在第 9.2.1 节全部硬性指标都有证据且全部通过时才允许返回 PASS。不得使用“基本可读”“影响不大”“轻微重叠”“肉眼可接受”“大体协调”等措辞把失败项判成通过。
任一读者可见文字、公式、轴标签、刻度、图例、注释、面板标号、节点标签或题注关联元素出现 1 个及以上经证据裁决确认的真实非法重叠像素，必须返回 FAIL；未经裁决的候选重叠也不得 PASS。
subagent2 必须针对真实失败项修改结构、坐标、间距、字号、换行、面板划分或标注位置；不得单纯整体缩小图或文字来躲避重叠与拥挤。修改后必须生成全新的 300 dpi 证据和测量结果，再交由 subagent1/subagent3 重新独立验收。
主线程不得用主观判断覆盖 subagent1/subagent3 的硬性 FAIL；只有完成证据化像素裁决、必要修复、重新测量、重新渲染并重新取得独立 PASS 才能闭合任务。

4.6 双分对话总架构与非自动合并原则

执行时必须真实建立三个相互区分的顶层会话角色：

主对话 MAIN：唯一协调、共享文件单写、合并、冲突解决、全局回归、根验收和发布；

分对话 A DIALOGUE\_A\_VISUAL：执行任务 A，不读取或依赖分对话 B 的聊天历史；

分对话 B DIALOGUE\_B\_CONTENT：执行任务 B，不读取或依赖分对话 A 的聊天历史。

主对话必须分别生成并发送 TASK\_PACKET\_A.md 与 TASK\_PACKET\_B.md。每个任务包必须自包含：项目目标、固定路径、七个输入、材料权威顺序、对象清单、允许/禁止写入范围、模型路由、验收标准、局部测试、交接格式和失败处理；不得写“沿用主对话上文”“参考另一对话结论”等依赖隐含上下文的语句。

两个分对话的上下文、工具结果和 PASS/FAIL 不会自动合并。信息传递仅允许通过：

各自隔离 worktree/分支中的真实文件变更；

HANDOFF\_ROOT 下各自独占目录中的交接文件；

可复核的补丁、提交、变更文件包和证据路径；

分对话最终消息中的结构化“交接摘要”。

主对话没有收到真实文件变更或明确 NO\_CHANGE 证据时，不得只凭聊天摘要宣布任务已完成；分对话也不得把“已写交接文件”表述为“主对话已自动合并”。

4.7 隔离 worktree、互斥写域与单写者边界

默认本地分支/worktree：

主对话集成分支：v2.7.0/integration；工作树 INTEGRATION\_WORKTREE；

分对话 A：v2.7.0/dialogue-a-visual；工作树 DIALOGUE\_A\_WORKTREE；

分对话 B：v2.7.0/dialogue-b-content；工作树 DIALOGUE\_B\_WORKTREE。

三个工作树必须从同一已确认基线创建。主对话记录基线文件清单和创建时间；不把 Git 提交哈希当作质量判据。分对话只能在自己的工作树中写入，不得切换到 integration 分支，不得把文件直接复制覆盖到 SOURCE\_WORKTREE，不得向 FINAL\_ROOT 发布文件。

永久由主对话单写的共享/全局对象包括但不限于：

公共宏、公共 TikZ/PGFPlots 样式、字体配置、颜色主题和全书版式参数；

封面、版本中心宏、PDF 元数据、根 main\_full.tex、全局 \input/\include 链；

全局编号、标签命名策略、目录、符号索引、主题索引、书签和页脚导航；

顶层构建入口、发布脚本、README、CHANGELOG、MANIFEST 和最终打包脚本；

权威问题库、CURRENT\_STATUS.md、DECISIONS.md、NEXT\_ACTIONS.md、MODEL\_ROUTING\_LOG.csv、PIXEL\_ADJUDICATION\_LOG.csv、DIALOGUE\_STATUS.csv、HANDOFF\_INTEGRATION\_LOG.csv；

FINAL\_ROOT 中的全部正式文件。

分对话发现必须修改上述对象时，只能写入 SHARED\_CHANGE\_REQUESTS\_A.md 或 SHARED\_CHANGE\_REQUESTS\_B.md，逐项给出请求 ID、原因、建议最小补丁、受影响对象、回归范围和风险；主对话决定是否合并并承担全量回归。

4.8 分对话 A：任务 A——99 幅绘图、严格视觉证据与图源局部修复

TASK\_ID：DIALOGUE\_A\_VISUAL
OWNER：分对话 A 协调器，gpt-5.6-sol + xhigh。

任务范围：

完整执行 M03；

执行 M09 中全部“图内字号、300 dpi 实际像素、同类比例、视觉层级、跨面板一致性、真实重叠/掩膜污染、裁切、净空、灰度和图页融合”事项；

执行 M08 中位于图源内部的局部标签、变量、引用和字面命令问题；

完整执行第 9、10 节、附录 A 的 21 幅高优先级图和附录 B 的 99 幅逐图任务卡；

为每幅图完成独立 subagent1 → subagent2 → mechanical\_worker → subagent1 → subagent3 的闭环，形成 A\_LOCAL\_PASS 或 A\_BLOCKED，不得伪造最终 PASS。

允许直接修改：

DIALOGUE\_A\_WORKTREE 中 src/绘图源码/\*\* 下与当前图直接相关的局部图源；

A 自有目录 DIALOGUE\_A\_ROOT/state、evidence、reports、handoff；

为独立图测试创建的临时包装文件，但不得进入正式源码包。

禁止直接修改：

src/讲义源码/\*\* 的章节正文、题注、读图说明、例题、知识点、练习和解析；

任何公共宏、公共样式、字体、全局编号、索引、构建入口、权威状态文件和 FINAL\_ROOT；

分对话 B 的 worktree 与交接目录。

若图修复需要改题注、相邻正文、分页、共享样式或公共字体，分对话 A 必须把精确修改请求写入 A\_CHAPTER\_CHANGE\_REQUESTS.md 或 SHARED\_CHANGE\_REQUESTS\_A.md，不得越权修改。每条请求必须包含 FIGURE\_ID、目标文件/位置、原文、建议新文、理由、受影响页和验证方法。

A 的本地完成产物至少包括：

DIALOGUE\_A\_HANDOFF.md；

DIALOGUE\_A\_CHANGED\_FILES.csv；

DIALOGUE\_A\_TEST\_RESULTS.md；

DIALOGUE\_A\_UNRESOLVED.md；

A\_CHAPTER\_CHANGE\_REQUESTS.md；

SHARED\_CHANGE\_REQUESTS\_A.md；

DIALOGUE\_A\_MODEL\_ROUTING\_LOG.csv；

DIALOGUE\_A\_PIXEL\_ADJUDICATION\_LOG.csv；

99 幅图逐图本地复核台账、证据目录、补丁/分支或变更文件包；

HANDOFF\_ROOT\A\READY\_FOR\_MAIN.md。

分对话 A 只能声明“对话 A 本地任务完成并等待主对话合并”。主对话合并 B 的正文改动后必须重新渲染图页；若集成版产生回归，A 必须接受主对话发回的 REWORK\_PACKET\_A.md 并在 A worktree 中继续修复。

4.9 分对话 B：任务 B——正文数学内容、例题知识点、练习算法与局部源码修复

TASK\_ID：DIALOGUE\_B\_CONTENT
OWNER：分对话 B 协调器，gpt-5.6-sol + xhigh。

任务范围：

完整执行 M02、M04、M05、M06、M07；

执行 M08 中所有非图源的局部字面命令、章节标签、算法/例题/练习/定理引用问题；

执行 M09 中非绘图正文、例题、算法、表格、公式框、章首卡片、留白和局部分页问题；

完整执行第 11 节、附录 C 的 66 道正文例题和附录 D 中除“绘图索引 99 行”之外的内容任务；

逐项处理 935 处阅读阻塞残留、66 道例题、596 个知识点、192 个定义/定理类对象、59 组核心推导、553 道章末练习及 7 个算法契约。

允许直接修改：

DIALOGUE\_B\_WORKTREE 中章节级正文、例题、知识点、定理/证明、推导、练习、解析、局部算法说明及局部表格对应的 .tex 文件；

B 自有目录 DIALOGUE\_B\_ROOT/state、evidence、reports、handoff。

禁止直接修改：

src/绘图源码/\*\*；

公共宏、公共样式、字体、颜色主题、全局编号、目录/索引、根 main\_full.tex、顶层构建脚本、权威问题库、权威状态文件和 FINAL\_ROOT；

分对话 A 的 worktree 与交接目录。

若内容修复需要修改图源、共享样式、公共字体、全局标签策略、根构建入口或发布文件，分对话 B 必须写入 FIGURE\_CHANGE\_REQUESTS\_B.md 或 SHARED\_CHANGE\_REQUESTS\_B.md。不得为避免交接而越权写入。

B 的本地完成产物至少包括：

DIALOGUE\_B\_HANDOFF.md；

DIALOGUE\_B\_CHANGED\_FILES.csv；

DIALOGUE\_B\_TEST\_RESULTS.md；

DIALOGUE\_B\_UNRESOLVED.md；

FIGURE\_CHANGE\_REQUESTS\_B.md；

SHARED\_CHANGE\_REQUESTS\_B.md；

DIALOGUE\_B\_MODEL\_ROUTING\_LOG.csv；

内容对象逐项处理台账、受影响页渲染、补丁/分支或变更文件包；

HANDOFF\_ROOT\B\READY\_FOR\_MAIN.md。

分对话 B 只能声明“对话 B 本地任务完成并等待主对话合并”。主对话合并 A 的图源改动和共享修改后必须重新编译受影响章节；若集成版产生回归，B 必须接受 REWORK\_PACKET\_B.md 并继续修复。

4.10 主对话唯一负责的任务

主对话独占执行：

M01、M10；

M08 中跨域标签冲突、根 \input/\include、全局引用和命名策略；

M09 中公共字体、全局字号族、版心、全书间距、公共环境、跨章节分页和集成后页面回归；

所有共享修改请求的评估、最小合并和受影响范围重建；

两个分支/worktree 的创建、接收、合并、冲突解决、回归测试和状态更新；

FINAL\_99\_FIGURE\_GATE、FINAL\_BOOK\_RELEASE\_GATE、独立重建、全书逐页视觉扫描、最终证据、发布目录和全部压缩包；

两份分对话执行提示词的物化、保存和最终打包。

主对话可在 A/B 运行期间处理上述单写任务，但不得进入 A/B 的授权写域重复修改，也不得在收到交接前根据猜测代替 A/B 完成其任务。主对话对共享文件的修改必须记录影响范围，以便合并后重建所有受影响对象。

4.11 分对话交接摘要与文件回传协议

每个分对话完成一个可合并批次或全部本地任务后，必须同时生成文件交接和消息交接。最终“交接摘要”固定为：

HANDOFF\_ID: {A\_OR\_B}-{BATCH\_OR\_FINAL}
OWNER\_DIALOGUE: DIALOGUE\_A\_VISUAL / DIALOGUE\_B\_CONTENT
BASELINE: {基线说明，不把哈希作为质量判据}
STATUS: READY\_FOR\_MAIN / PARTIAL / BLOCKED
SCOPE\_COMPLETED:
OBJECTS\_COMPLETED:
FILES\_CHANGED: 逐文件列出相对路径与修改目的
KEY\_DECISIONS: 关键数学/视觉/排版结论及依据
TESTS\_RUN: 命令、退出状态、页/图/对象覆盖、证据路径
ACCEPTANCE\_RESULTS: 本地 PASS/FAIL 及硬指标
UNRESOLVED\_ISSUES: 未解决对象、原因、阻塞与最小恢复动作
OUT\_OF\_SCOPE\_REQUESTS: 需要主对话或另一对话处理的请求 ID
SHARED\_CHANGE\_REQUESTS:
REGRESSION\_RISKS:
PATCH\_OR\_BRANCH: 分支、补丁或变更文件包位置
HANDOFF\_FILES:
NEXT\_ACTION\_FOR\_MAIN:

FILES\_CHANGED 不得只写“若干文件”；TESTS\_RUN 不得只写“已测试”；UNRESOLVED\_ISSUES 为空时明确写 NONE。STATUS=READY\_FOR\_MAIN 仅表示可以交给主对话审阅，不等于已合并、已集成验证或已最终通过。

交接文件必须写入各自独占目录：HANDOFF\_ROOT\A... 或 HANDOFF\_ROOT\B...。分对话最终消息必须重复精简版交接摘要和交接文件路径，便于在聊天上下文不互通时由用户复制/转发给主对话。主对话必须实际读取交接文件与真实变更，不得只依赖转述。

4.12 主对话接收、合并、检查与返工闭环

主对话维护 HANDOFF\_INTEGRATION\_LOG.csv，状态至少包括：NOT\_STARTED、RUNNING、READY\_FOR\_MAIN、RECEIVED\_NOT\_MERGED、MERGED\_LOCAL\_TEST\_PENDING、MERGED\_VALIDATED、REWORK\_REQUIRED、BLOCKED。

接收顺序固定为：

验证 A、B 的 READY\_FOR\_MAIN、交接摘要、变更清单、测试结果、未解决项和补丁/分支均真实存在；

先把分对话 B 的章节局部内容变更合入 INTEGRATION\_WORKTREE，并运行 B 指定的局部测试；

再把分对话 A 的图源变更合入，并运行 A 指定的独立图和图页测试；

主对话逐项处理 A\_CHAPTER\_CHANGE\_REQUESTS.md、FIGURE\_CHANGE\_REQUESTS\_B.md 与两份 SHARED\_CHANGE\_REQUESTS；

对全部合并结果运行引用检查、章节构建、所有受影响页渲染和必要的 300 dpi 复测；

完成整书干净构建、全书视觉扫描和最终门。

若分对话越权修改共享文件或两个分支出现本不应存在的重叠写入，主对话不得盲目自动选择任一版本；应标记 REWORK\_REQUIRED，恢复到互斥写域，由责任对话重做并重新交接。若合并后发现问题，主对话按归属创建 REWORK\_PACKET\_A.md 或 REWORK\_PACKET\_B.md，写清文件、页码、证据、失败指标、允许写入范围和完成判据；责任分对话完成新交接后再合并。

只有 A、B 均为 MERGED\_VALIDATED，所有共享请求已闭合或有明确无须修改结论，集成版局部/全书测试均通过，主对话才可进入最终发布。主对话必须在 v2.7.0\_修改与复核总报告.md 中分别总结 A、B 的任务、修改文件、测试、未决项处置和主对话最终合并结论。

4.13 两份分对话执行提示词的物化要求

主对话在启动两个分对话前必须生成并保存：

GPT\_Pro\_统计学习方法讲义\_v2.7.0\_对话A\_逐图视觉重构执行提示词.md；

GPT\_Pro\_统计学习方法讲义\_v2.7.0\_对话B\_内容数学重构执行提示词.md。

两份文件必须分别包含第 4.8/4.9 节的完整任务包、固定路径、输入权威顺序、模型路由、允许/禁止写域、验收协议、局部测试、交接模板和立即开始指令；不能只写“参见主提示词某节”。两份文件必须由主对话发送到两个独立对话执行，并在最终发布时与主提示词一起进入 04\_执行提示词。

长任务状态保存与上下文恢复

在固定目录：
D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\state
持续维护：
PROJECT\_CHARTER.md：目标、不可变约束、固定路径、输入层级和输出命名；
INPUT\_RESOLUTION.md：七个输入的最终采用路径与选择理由；
CURRENT\_STATUS.md：已完成对象、当前对象、失败对象和下一动作；
DECISIONS.md：数学、排版和源码结构的重要决定；
NEXT\_ACTIONS.md：按优先级列出下一批操作；
SUBAGENT\_HANDOFF.md：最近一次代理输入、结论和待修项。
MODEL\_ROUTING\_LOG.csv：逐次记录 TASK\_ID、角色、实际模型、reasoning\_effort、默认/升级/回退原因、开始与结束时间；
PIXEL\_ADJUDICATION\_LOG.csv：逐候选簇记录候选像素数、真实碰撞像素数、掩膜污染像素数、证据路径、SA1/SA3意见、主对话或 max 裁决；
DIALOGUE\_STATUS.csv：记录主对话、分对话 A、分对话 B 的任务包版本、worktree、当前批次、完成比例和状态；
HANDOFF\_INTEGRATION\_LOG.csv：记录每份交接从 READY\_FOR\_MAIN 到 RECEIVED\_NOT\_MERGED、MERGED\_LOCAL\_TEST\_PENDING、MERGED\_VALIDATED 或 REWORK\_REQUIRED 的全过程。
上述 STATE\_ROOT 文件全部由主对话单写。分对话 A/B 分别在 DIALOGUE\_A\_ROOT/state 与 DIALOGUE\_B\_ROOT/state 维护同名或带 A/B 后缀的本地状态文件，不得直接写主对话权威状态；主对话收到交接后再整合。
上下文压缩前先更新以上文件；压缩后按 PROJECT\_CHARTER.md → INPUT\_RESOLUTION.md → CURRENT\_STATUS.md → DECISIONS.md → NEXT\_ACTIONS.md → SUBAGENT\_HANDOFF.md → DIALOGUE\_STATUS.csv → HANDOFF\_INTEGRATION\_LOG.csv → MODEL\_ROUTING\_LOG.csv → PIXEL\_ADJUDICATION\_LOG.csv 的顺序重读，再继续执行。不得把关键背景只留在对话中。不要从零重建已经提供的全量索引；仅在索引与源码冲突时做定向回查。

必须解决的主要问题

固定归属：M01、M10 归主对话；M02、M04、M05、M06、M07 归分对话 B；M03 归分对话 A；M08、M09 按第 4.8—4.10 节的文件/对象边界拆分。任何对象只允许一个直接写者。

M01｜[主对话] 发布版本与构建入口统一
把封面、页眉、PDF元数据、包版本、版本宏、内部 PDF 链接、发布文件名、README、构建脚本和源码包根目录统一为 v2.7.0。
版本必须由一个中心宏/变量派生，禁止多处手写造成再次漂移。
读者可见页面不得继续显示 v2.5.0 或 v2.6.0；历史版本只可出现在 CHANGELOG 的来源说明中。
更新 AGENTS.md、构建说明和发布脚本，使其与本提示词的 99 幅正式图、66 道正文例题、596 个知识点、192 个定义/定理类对象和 59 组核心推导一致；先解释旧文档“101 幅图”等统计差异，再写入最终数字。
M02｜[分对话 B] 清除 935 处内部工作文案泄漏
逐项读取 阅读阻塞残留 工作表/CSV，定位源码行。删除或改写以下非读者文案：
“需要解决的阅读阻塞”
“核验路线”
“首次调用处”
以编辑者口吻出现的“原文”“下方严格细节保留”等说明
机械重复的“第一步”块
不得粗暴删除所有“第一步”。真正属于数学推导、算法执行或解题过程的自然步骤应保留。替换后的读者自检必须是可直接回答的问题，包含对象、条件或一个最小代入任务；不能只是把内部描述换个标题。
M03｜[分对话 A] 99 幅正式绘图逐图重构与复核
以 绘图索引 99 行为唯一逐图任务表。
21 幅高优先级、37 幅中优先级先处理；其余图仍必须逐幅复核。
不得因旧图清单写着“已完成”而跳过当前视觉检查。
每幅图执行第 9 节定义的独立 subagent 闭环。
最终统一图内字号、线宽、节点内边距、箭头、灰度辨识、题注和“先看—再看—得到”读图顺序。
M04｜[分对话 B] 66 道正文例题逐题重写与复算
全部例题保持题后即解，编号、题干、引用和原有有效公式不丢失。
每题按本题对象写“题意整理—解题关键—逐步推导—核验—结论”，避免批量套话。
明确修复例题 11.1、12.2、24.1、29.1、33.2；例题 24.1 的结论只保留一次。
逐例题 Markdown 中出现的重复核验、抽取截断或公式缺失必须修复，不能直接复制进源码。
概率题检查归一化和正分母；矩阵题检查维数、正交或重构；优化题检查可行性、KKT或曲率；算法题手算一轮并检查更新顺序；分类题复算全部样本或混淆矩阵总数。
M05｜[分对话 B] 596 个知识点、192 个定义/定理类对象、59 组推导重构
逐行处理对应索引，不得只挑高优先级：
知识点采用五层入口：解决什么问题；对象/取值域/成立条件；核心定义或公式；最小例或非例；误区、边界和后续用途。
定义与定理必须把条件和结论视觉分开；证明中标明每个假设实际用于哪一步。
核心推导采用七步：目标—对象—条件—第一数学动作—主变形—结果核验—条件失效边界。
对初学者不熟悉的先修概念，先补最短定义和最小例，再使用符号。
不得用空泛“先理解概念”取代具体讲解；不得把实现状态码放在第一次阅读主线。
保留严格性，不得为了通俗而删去量词、支持集、维数、正分母、可行域、独立性、可逆性、正定性等关键条件。
M06｜[分对话 B] 553 道章末练习与解析结构核对
比较源文件、PDF和练习覆盖表，解决“报告认为题后有解析、覆盖表解析计数为 0”的派生数据冲突。
保证每道题干后紧邻同号解析，长解析跨页时题号清楚。
修复唯一明显过短的解析 V4-C04-S05-02，补齐已知条件、方法选择、必要计算和结论。
不得为了增加字数重复同一句核验。
M07｜[分对话 B] 算法契约、状态语义与数量一致性
补齐 7 个缺少统一契约的算法：感知机原始形式、感知机对偶形式、kd 树搜索、CART 剪枝、逻辑斯谛 Newton、BFGS、SMO。
把 13 处非统一状态名映射到项目已有的中心状态集合；具体失败原因放到诊断字段，不要把原因词当状态枚举。
每个算法第一次阅读只保留输入、初始化、核心更新、数学停止与输出；异常处理放到实现补充。
对“算法数量低于旧脚本预期”先核对实际包含关系；不要为了满足旧数字复制或伪造算法。若旧预期已经过时，更新相应检查逻辑并写入 CHANGELOG。
M08｜[按对象分流：A/B/主对话] 明确源码错误与标签冲突
修复 V1-C01 中字面 qquad，恢复正确 LaTeX 命令并搜索同类未转义字符串。
解决重复算法标签，删除不再包含的旧批次残留或改成唯一标签；不得通过关闭交叉引用检查掩盖冲突。
检查所有图、表、定理、算法、例题和练习引用，保证无未定义引用、重复标签和错误跳转。
M09｜[按对象分流：A/B/主对话] 字号、密度与版面
针对 139 个页级视觉问题逐页回查；19 页含低于 6pt 文字，132 页含低于 8.5pt 文字。
读者正文、例题、算法、图例和表格必须在正常阅读比例下清晰。图内所有承担读者信息的正文、轴标签、刻度、图例、节点标签、注释和公式块，必须按第 9.2.1 节核对“声明字号→累计缩放→最终有效字号”，一般文本有效字号不得低于 9.5pt；数学上下标可因语义进入 script/script-script 样式，但其基准公式有效字号仍不得低于 9.5pt，且最终 300 dpi 像素高度必须满足脚本级下限。任何读者信息不得通过整体缩放落到标准以下。
最终是否通过不能只依赖 pt 数值：必须在无二次缩放的 300 dpi 原始图中逐元素或逐文字行测量实际墨迹像素高度，比较同类标签比例和语义层级；轴标签、刻度、图例、注释、公式块若无明确语义理由却明显放大或缩小、抢占主体、跨面板不一致，均直接判为失败。
禁止用 \resizebox、\scalebox 或整体缩小环境掩盖溢出；优先拆图、缩短文字、扩大宽度、改分面或调整分页。
处理 PDF 物理页 371、388、399 的过多留白，以及 737、788、823、849 的章首卡片过高问题。
版面紧凑不等于拥挤；数学式、题解块和图必须有稳定层级与合理留白。
M10｜[主对话] 导航、索引、元数据与可重建发布
保留五册、37 章与全书连续编号；目录、符号索引、主题索引、书签和页脚导航一致。
PDF 元数据与文件名为 v2.7.0；书签和内部链接可点击且目标正确。
构建不联网、不自动安装软件、宏包或字体。
最终源码压缩包解压后，应能按 README 中的一条 PowerShell 命令独立生成同名完整解析版 PDF。
正式源码包只保留构建所需源码、脚本、说明和必要数据；中间渲染、代理记录和旧版本临时发布文件不进入正式包。

主要问题的分对话归属、三角色处理与主对话根验收

对 M01—M10 每个主要问题建立独立任务 ID，并先按第 4.8—4.10 节确定唯一 OWNER\_DIALOGUE 与唯一直接写者：

主对话任务由主对话在 INTEGRATION\_WORKTREE 中执行；

任务 A 由分对话 A 在 DIALOGUE\_A\_WORKTREE 中执行；

任务 B 由分对话 B 在 DIALOGUE\_B\_WORKTREE 中执行。

每个所有者协调器使用 gpt-5.6-sol + xhigh 完成本任务域内的第一次修改与本地 Goal 状态管理，然后调用所属对话内部的核心角色：
subagent1：gpt-5.6-sol + xhigh，第一轮盲审视觉/数学复核；
subagent2：默认 gpt-5.6-terra + high，按第 4.2 节在同一图连续两轮失败后升级；
subagent3：gpt-5.6-sol + xhigh，独立第二盲审；
mechanical\_worker：gpt-5.6-luna + medium，或预授权回退 gpt-5.6-terra + medium，负责所属 worktree 的构建、渲染、计数、清单与本地交接产物。

本地循环固定为：
所有者协调器/所属 subagent2 定向修改
→ 所属 mechanical\_worker 重新构建、渲染和生成证据
→ 所属 subagent1 盲审
→ 所属 subagent3 独立盲审
→ 所有者协调器本地验收
→ 仍有问题则回到所属 subagent2。

分对话 A/B 不得修改共享样式或公共宏；发现此类需求必须形成共享变更请求。分对话的 PASS 只能记为 A\_LOCAL\_PASS 或 B\_LOCAL\_PASS。完成后按第 4.11 节输出交接摘要、变更文件、测试结果和未解决问题，并把结果传到主对话。

主对话收到两个交接后按第 4.12 节统一合并。合并后主对话必须重新渲染全部受影响页、检查跨任务相互作用，并执行根验收；若失败，必须向原责任分对话发 REWORK\_PACKET，不得由主对话在其专属写域偷偷代改以绕过交接闭环。

若失败仅来自未决候选像素，先执行证据化碰撞/污染裁决；确认真实碰撞后返给分对话 A 的图修复闭环，确认掩膜污染后修正检测记录并重新创建盲审实例。共享样式、公共宏、字体、全局编号、索引和构建入口始终由主对话修改，并重新渲染所有受影响对象。

主要问题代理提示模板

主对话或所属分对话协调器必须把以下模板按任务变量完整填写后发给对应代理。每份模板必须额外填写 OWNER\_DIALOGUE、WORKTREE、HANDOFF\_ID、ALLOWED\_WRITE\_SCOPE 和 FORBIDDEN\_SCOPE；不得让代理自行猜测所属对话或写域。
8.1 发给 subagent1 的模板
你是 subagent1，固定使用模型 gpt-5.6-sol，推理强度 xhigh。你是第一盲审者，只读，不得改文件，也不得读取 subagent3 的任何结论。
OWNER\_DIALOGUE：{OWNER\_DIALOGUE}
WORKTREE：{WORKTREE}
HANDOFF\_ID：{HANDOFF\_ID}
任务ID：{MAJOR\_ID}
问题名称：{MAJOR\_TITLE}
原问题与数量：{ISSUE\_SUMMARY}
主线程修改文件：{CHANGED\_FILES}
受影响PDF页：{AFFECTED\_PAGES}
完成标准：{ACCEPTANCE\_CRITERIA}
证据目录：{EVIDENCE\_DIR}
必须执行：

阅读修改前后源码差异和相邻上下文；

对受影响页逐页查看完整页渲染，不得只读文本或编译日志；

对数学公式核对对象、条件、维数、支持集、分母、索引和结论；

对教学表达判断初学者是否知道第一步、为何这样做及如何核验；

检查是否引入编号、标签、分页、字体、重叠、裁切或导航问题；

不因修改量大而抽样，必须覆盖本任务列出的全部受影响对象；

对涉及绘图/表格/算法框/公式框的任务，逐项执行第 9.2.1 节的源级有效字号审计和 300 dpi 像素验收；

对同一语义角色在同图、同面板和跨面板的实际像素高度计算比例，未满足同类一致性阈值时必须 FAIL；

对读者可见文字与文字、文字与线/箭头/标记、文字与边框/裁切边界做像素级交叠检查。非法重叠像素数必须严格等于 0；任意一项 >=1 均必须 FAIL；

不仅判断可读性，还必须判断视觉协调：普通标签不得无语义理由突然放大/缩小，不得压过数据、几何结构或流程主线，不得跨面板字号漂移；

若测量证据缺失、元素无法定位、有效字号无法还原、像素高度无法复核或重叠报告不完整，结论只能是 FAIL/证据不足，不得 PASS。

返回格式：
RESULT: PASS 或 FAIL
TASK\_ID:
COVERAGE:
BLOCKERS:
MATHEMATICAL\_FINDINGS:
TEACHING\_FINDINGS:
VISUAL\_FINDINGS:
SOURCE\_FONT\_AUDIT:
PIXEL\_HEIGHT\_AUDIT:
SAME\_CLASS\_RATIO\_AUDIT:
ROLE\_RATIO\_AUDIT:
OVERLAP\_PIXEL\_AUDIT:
VISUAL\_HARMONY\_AUDIT:
REFERENCE\_FINDINGS:
REQUIRED\_ACTIONS:
EVIDENCE\_USED:
不得给模糊建议；每个 FAIL 必须包含文件、行或PDF页与可执行修复动作。
8.2 发给 subagent2 的模板
你是 subagent2。当前调用模型与推理强度由主线程严格按第 4.2 节填写：
MODEL：{SA2\_MODEL}
REASONING\_EFFORT：{SA2\_REASONING\_EFFORT}
默认必须为 gpt-5.6-terra + high；仅当同一图连续两个完整修复轮仍失败且 SA2\_ESCALATED=true 时，才允许为 gpt-5.6-sol + xhigh。
SA2\_ESCALATED：{SA2\_ESCALATED}
REPAIR\_ROUND：{REPAIR\_ROUND}
CONSECUTIVE\_FAILED\_REPAIR\_ROUNDS：{CONSECUTIVE\_FAILED\_REPAIR\_ROUNDS}
你是定向修改者。
OWNER\_DIALOGUE：{OWNER\_DIALOGUE}
WORKTREE：{WORKTREE}
HANDOFF\_ID：{HANDOFF\_ID}
任务ID：{MAJOR\_ID}
允许修改文件：{ALLOWED\_FILES}
禁止修改范围：{FORBIDDEN\_SCOPE}
subagent1问题清单：{SA1\_FINDINGS}
主线程目标：{TARGET\_STATE}
规则：

先复现每个问题，再修改；

只改允许范围，不做无关重构；

数学公式以原LaTeX和相邻定义为准，不复制抽取文件中的残缺公式；

修改后完成局部编译和受影响页渲染；

若共享宏必须修改，先提交最小补丁说明，由主线程决定是否合并；

若不存在真实问题，明确返回 NO\_CHANGE\_REQUIRED，不得为了显示工作量而改写；

若失败涉及字号、比例、拥挤或重叠，不得用整体缩放规避。必须先恢复足够的有效字号，再通过改坐标、改布局、换行、增大图宽、拆面板、移动图例/注释或减少非必要文字消除问题；

修改后重新生成 300 dpi 原始渲染，并重新输出源级字号、实际像素高度、同类比例、语义角色比例、重叠像素和最小净空证据。任何非法重叠像素仍 >=1 时不得返回 FIXED。

返回格式：
RESULT: FIXED / PARTIAL / NO\_CHANGE\_REQUIRED / BLOCKED
TASK\_ID:
FILES\_CHANGED:
ROOT\_CAUSE:
PATCH\_SUMMARY:
LOCAL\_BUILD:
RENDERED\_PAGES:
FONT\_CHANGES:
PIXEL\_RECHECK:
OVERLAP\_RECHECK:
REMAINING\_RISKS:
HANDOFF\_TO\_REVIEWERS:
8.3 发给 subagent3 的模板
你是 subagent3，固定使用模型 gpt-5.6-sol，推理强度 xhigh。你是独立第二盲审者，只读，不得改文件，也不得读取 subagent1 的最终判断、评分摘要或 PASS/FAIL。
OWNER\_DIALOGUE：{OWNER\_DIALOGUE}
WORKTREE：{WORKTREE}
HANDOFF\_ID：{HANDOFF\_ID}
任务ID：{MAJOR\_ID}
问题名称：{MAJOR\_TITLE}
当前候选文件：{CANDIDATE\_FILES}
受影响PDF页：{AFFECTED\_PAGES}
完成标准：{ACCEPTANCE\_CRITERIA}
证据目录：{EVIDENCE\_DIR}
你必须独立复核，不读取或沿用subagent1的最终判断。重新检查：

原问题是否真正消失；

修改是否引入新的数学、教学、排版或引用问题；

全部受影响页是否清晰、连续、无异常留白与断裂；

任务是否完整覆盖而不是只修代表性样本；

涉及绘图/表格/算法框/公式框时，独立执行第 9.2.1 节的源级字号、300 dpi 实际像素高度、同类比例、角色比例、零重叠和视觉协调性复核，不得沿用 subagent1 的数字结论；

任何非法重叠像素 >=1、任一字号/比例硬阈值失败、或测量证据不完整时必须 FAIL。

返回格式：
RESULT: PASS 或 FAIL
TASK\_ID:
INDEPENDENT\_COVERAGE:
BLOCKERS:
NEW\_REGRESSIONS:
MATHEMATICAL\_FINDINGS:
VISUAL\_FINDINGS:
SOURCE\_FONT\_AUDIT:
PIXEL\_HEIGHT\_AUDIT:
SAME\_CLASS\_RATIO\_AUDIT:
OVERLAP\_PIXEL\_AUDIT:
VISUAL\_HARMONY\_AUDIT:
REQUIRED\_ACTIONS:
EVIDENCE\_USED:

8.4 发给 mechanical\_worker 的模板
你是 mechanical\_worker。
MODEL：{MECHANICAL\_MODEL}
REASONING\_EFFORT：medium
默认模型为 gpt-5.6-luna；仅在不可用时按预授权回退 gpt-5.6-terra，并记录原因。
TASK\_ID：{TASK\_ID}
机械任务类型：{BUILD\_RENDER\_HASH\_LIST\_COUNT\_PACKAGE}
允许写入目录：{ALLOWED\_OUTPUT\_DIRS}
禁止修改：任何数学内容、教学正文、LaTeX 绘图语义、代理结论与验收状态
输入：{INPUTS}
输出：{EXPECTED\_OUTPUTS}
必须执行：

严格按命令构建、渲染、计数、复制、压缩或解压；

不对视觉语义、数学正确性或 PASS/FAIL 作判断；

失败时返回真实日志、退出码、缺失文件和最小复现步骤；

所有输出路径、文件大小、页数/图数/行数和实际模型写入所属对话本地 MODEL\_ROUTING\_LOG；仅主对话可把已核验记录整合进 STATE\_ROOT\MODEL\_ROUTING\_LOG.csv。
返回：
RESULT: COMPLETED/PARTIAL/BLOCKED
TASK\_ID:
MODEL\_USED:
COMMANDS:
OUTPUTS:
COUNTS:
ERRORS:
LOGS:

8.5 发给 max 根验收/争议像素裁决的模板
你是有限范围的根验收或争议像素裁决者。
model: gpt-5.6-sol
reasoning\_effort: max
GATE\_ID：{GATE\_ID}
GATE\_TYPE：FINAL\_99\_FIGURE\_GATE / FINAL\_BOOK\_RELEASE\_GATE / PIXEL\_DISPUTE\_ARBITRATION
有限对象范围：{BOUNDED\_SCOPE}
触发原因：{TRIGGER\_REASON}
输入证据：{EVIDENCE}
规则：

不扩散到范围外对象；

像素争议必须逐候选簇比较 300 dpi 原图、分离语义掩膜、矢量/源码坐标与测量叠加图；

将每个候选分类为 TRUE\_COLLISION、MASK\_CONTAMINATION 或 UNRESOLVED；

任何 UNRESOLVED 不得通过，任何 TRUE\_COLLISION 必须回修；

最终 99 图总门检查跨图字体、同类比例、线宽、箭头、图例、灰度编码与证据完整性；

全书发布门检查独立重建、逐页视觉扫描、引用、打包和所有子门闭合；

返回后立即退出 max，不得继续承担常规任务。
返回：
RESULT: PASS/FAIL/UNRESOLVED
GATE\_ID:
SCOPE\_COVERED:
PIXEL\_CLASSIFICATIONS:
CROSS\_FIGURE\_FINDINGS:
RELEASE\_FINDINGS:
BLOCKERS:
REQUIRED\_ACTIONS:
EVIDENCE\_USED:

8.6 分对话最终交接摘要模板

你是 {OWNER\_DIALOGUE} 的顶层协调器。你不能假定主对话自动获得本对话上下文。完成本地任务后，必须把真实文件变更、测试结果、未解决问题和精简摘要同时写入 HANDOFF\_ROOT 的本对话独占目录，并在最终消息中返回第 4.11 节的完整字段。

额外硬规则：

没有变更时写 NO\_CHANGE 并给出覆盖证据；

有变更时必须附逐文件清单和分支/补丁/变更包；

STATUS=READY\_FOR\_MAIN 前必须完成本对话规定的全部本地测试；

BLOCKED/PARTIAL 不得伪装成 READY\_FOR\_MAIN；

不得宣称“已合并”“已发布”或“主对话已收到”，除非主对话在 HANDOFF\_INTEGRATION\_LOG.csv 中确认。

8.7 主对话交接接收与返工模板

HANDOFF\_ID：{HANDOFF\_ID}
OWNER\_DIALOGUE：{OWNER\_DIALOGUE}
RECEIPT\_STATUS：RECEIVED\_NOT\_MERGED / MERGED\_LOCAL\_TEST\_PENDING / MERGED\_VALIDATED / REWORK\_REQUIRED / BLOCKED
FILES\_RECEIVED：
PATCH\_OR\_BRANCH\_RECEIVED：
LOCAL\_TESTS\_REPEATED：
MERGE\_RESULT：
CONFLICTS：
INTEGRATED\_REGRESSIONS：
SHARED\_REQUEST\_DECISIONS：
REWORK\_PACKET：
FINAL\_MAIN\_CONCLUSION：

主对话不得在未读取真实变更和证据时填写 MERGED\_VALIDATED；若返工，必须把可定位的文件、页码、失败指标、允许写域和验收标准发回原分对话。

每幅绘图的独立处理闭环

本节由分对话 A 在 DIALOGUE\_A\_WORKTREE 中执行。对附录 A/B 的 99 幅图逐幅执行，不得合并多个图给同一个代理任务。A 的本地关闭状态只能是 A\_LOCAL\_PASS；集成后的最终关闭由主对话完成。
9.1 每幅图的顺序
分对话 A 协调器读取该图的索引行、相邻正文、题注、图源和视觉证据。相邻章节文件只读；需要改题注或正文时写入 A\_CHAPTER\_CHANGE\_REQUESTS.md。
分对话 A 协调器仅在授权图源内形成第一次候选修改；高优先级图必须先判断是否拆图。
编译该图的独立预览，并编译包含该图的完整页面。
分对话 A 创建该图专属 subagent1，使用 gpt-5.6-sol + xhigh 执行 9.3 模板的第一盲审视觉复核。
若 subagent1 为 FAIL，先判断是否为真实修复项或未决像素候选。真实修复项进入 subagent2；未决候选先按第 4.3 节裁决。subagent2 第 1、2 个修复轮使用 gpt-5.6-terra + high；若两个完整修复轮连续 FAIL，从下一轮起仅对该图升级为 gpt-5.6-sol + xhigh。
每次修改后由 mechanical\_worker 重新独立编译、渲染并生成全套证据，再交回新的 subagent1 盲审。不得复用旧渲染、旧测量或旧代理实例的结论。
subagent1 PASS 后，创建该图专属 subagent3，使用 gpt-5.6-sol + xhigh 进行第二次独立盲审。
若 subagent3 为 FAIL，失败轮次同样计入该图连续修复失败计数；回到 subagent2 修改，再由新的 subagent1 复核；subagent1 通过后再次创建新的 subagent3。不得跳过任何环节。
若 subagent1/subagent3 对“真实碰撞 vs 掩膜污染”分类不一致，触发 PIXEL\_DISPUTE\_ARBITRATION（gpt-5.6-sol + max）；裁决后仍必须重新提交新的盲审实例。
subagent3 通过后，分对话 A 协调器使用 gpt-5.6-sol + xhigh 查看完整页、局部裁图、灰度图、分离掩膜与源码坐标，并核对 after\_visual\_acceptance.md、after\_overlap\_adjudication.md 与原始测量 CSV；只有 SOURCE\_FONT\_PASS、PIXEL\_HEIGHT\_PASS、SAME\_CLASS\_RATIO\_PASS、ROLE\_RATIO\_PASS、VISUAL\_HARMONY\_PASS 等全部为 true，PIXEL\_ADJUDICATION\_STATUS 为 CLEAR 或 MASK\_CONTAMINATION\_CONFIRMED，OVERLAP\_PIXEL\_COUNT=0、CLIP\_PIXEL\_COUNT=0 且净空达标，才可标记 A\_LOCAL\_PASS。主对话合并 B 与共享修改后必须重新生成集成版图页证据，A\_LOCAL\_PASS 不自动继承为最终 PASS。
9.2 每幅图的强制渲染证据
每次候选至少生成：
before\_full\_page\_200dpi.png
before\_figure\_crop\_300dpi.png
after\_full\_page\_200dpi.png
after\_figure\_crop\_300dpi.png
after\_standalone\_300dpi.png
after\_grayscale\_300dpi.png
after\_text\_measurement\_overlay\_300dpi.png
after\_font\_audit.csv
after\_pixel\_measurements.csv
after\_overlap\_report.csv
after\_overlap\_adjudication.md
after\_model\_route.md
after\_visual\_acceptance.md
高优先级图若拆成两个面板，两个面板都要有独立裁图。代理必须实际查看像素图，不得仅根据源代码或日志判断。

9.2.1 严格视觉验收协议：源级字号、300 dpi 像素、比例、零重叠与协调性

本节是 99 幅图、所有受影响图表页面以及 subagent1/subagent3 的统一硬性 PASS 标准。任务卡中的“复核重点”只能增加标准，不能降低本节阈值。任何一项失败、缺数据或无法复核，结论都必须为 FAIL。

A. 源级有效字号审计

对每个读者可见文字元素建立唯一 ELEMENT\_ID，至少包括：图内标题（若有）、面板标号、轴标题/单位、刻度、图例、节点标签、边标签、普通注释、公式块、数值标签、状态文字以及其他承担语义的信息。纯装饰性图形不列入文字元素。

对每个 ELEMENT\_ID 同时记录 declared\_pt、累计 graphics\_scale、effective\_pt。effective\_pt 必须反映 \small/\footnotesize、自定义 \fontsize、TikZ every node 字号、PGFPlots tick/legend style 以及任何 scale/transform shape/resizebox/scalebox 的最终综合效果。若无法还原有效字号，直接 FAIL。

一般读者文字 effective\_pt >= 9.5pt。轴标签、刻度、图例、节点文字、普通注释、公式块基准字号均受此下限约束。不得以“图很密”为理由降到 9.5pt 以下。

数学上下标/上下限因 TeX 语义自动进入 scriptstyle/scriptscriptstyle 时允许小于 9.5pt，但必须由 >=9.5pt 的基准公式自然派生，禁止人为把整条公式设为 scriptstyle 来缩小；脚本级实际像素高度还必须满足 C 节下限。

同一语义角色、同一面板内若无明确语义理由，effective\_pt 的最大值/最小值 <=1.03，且绝对差 <=0.25pt；跨面板同角色最大值/最小值 <=1.05。任一超限直接 FAIL。

任何整体图形缩放都会计入 graphics\_scale。若 \resizebox、\scalebox、scale 或 transform shape 使文字 effective\_pt 低于标准，不能按“源码写了 \small”判通过。

B. 300 dpi 原图与坐标统一

像素测量只能使用直接由最终候选 PDF/独立图按 300 dpi 渲染得到的原始 PNG；禁止使用浏览器截图、聊天窗口截图、图片查看器二次缩放图、压缩预览或 200 dpi 图替代。

300 dpi 渲染后不得再 resize。TeX pt 到 300 dpi 的理论 em 高度基准为：H\_em = effective\_pt \* 300 / 72.27，约等于 effective\_pt \* 4.151。9.5pt 对应约 39.43 px 的 em 基准。该数值用于检查渲染倍率是否异常，但实际墨迹高度仍按 C 节直接测量。

文字元素的 PDF/vector 边界框必须映射到 300 dpi 像素坐标，测量框叠加图中显示 ELEMENT\_ID、边界框与角色类别，保证每个测量值可追溯。

C. 实际文字像素高度

对每个读者可见 ELEMENT\_ID 测量实际墨迹高度 H\_ink\_px，而不是只读取字体 pt。以元素局部背景为基准，只有与局部背景亮度/颜色差达到至少 20/255 的像素计入有效前景；抗锯齿极浅边缘不计入，以避免 1px 噪声虚增高度。

纯中文/全角符号/接近全字面高度的字符：H\_ink\_px >=30 px；拉丁大写字母与数字：>=24 px；以 x-height 为主的拉丁小写/希腊小写：>=17 px；基准数学符号、运算符与分数字号主体：>=22 px；由合法基准公式自然产生的上标/下标/上下限：>=15 px。任一承担关键信息的元素低于对应下限直接 FAIL。

对混排元素同时记录主要脚本类别和整行 bbox 高度，不得用一个高大的中文字符掩盖同一行中极小的数学/拉丁标签；疑似过小的子串必须单独建 ELEMENT\_ID 再测。

after\_pixel\_measurements.csv 至少包含：ELEMENT\_ID、PANEL\_ID、ROLE、SOURCE\_FILE、SOURCE\_LINE、DECLARED\_PT、GRAPHICS\_SCALE、EFFECTIVE\_PT、TEXT\_SAMPLE、SCRIPT\_CLASS、BBOX\_X0、BBOX\_Y0、BBOX\_X1、BBOX\_Y1、H\_INK\_PX、CLASS\_MEDIAN\_PX、RATIO\_TO\_CLASS\_MEDIAN、ROLE\_RATIO、TEXT\_TEXT\_OVERLAP\_PX、TEXT\_GRAPHIC\_OVERLAP\_PX、MIN\_CLEARANCE\_PX、PASS\_FAIL、REASON。

D. 同类标签比例与跨面板一致性

只在相同脚本类别、相同语义角色之间比较实际像素高度，避免中文全高字符与拉丁 x-height 直接混比。

同一面板同一角色：每个元素的 H\_ink\_px / 该角色中位数必须位于 [0.92,1.08]；同一角色的最大中位高度/最小中位高度 <=1.08。

跨面板同一角色：各面板角色中位数的最大值/最小值 <=1.10。若面板间采用同一源级字号却像素比例超过 10%，必须检查是否存在隐式缩放、不同 transform、不同字体或导出倍率，不能直接 PASS。

同类刻度、同类图例项、同类节点标签、同类注释不得在同一图中出现“这一块明显大、另一块明显小”的视觉漂移。任何超阈值对象必须定位到 ELEMENT\_ID。

E. 不同语义角色的字号层级

以刻度/普通节点正文的角色中位数为局部 BASE。若无刻度，则选择图中最主要的普通正文角色作为 BASE，并记录选择理由。

轴标题/轴单位相对 BASE 的实际像素高度比例必须位于 [1.00,1.18]；图例 [0.95,1.10]；普通注释 [0.95,1.10]；公式块基准文字 [1.00,1.18]；面板标号 [1.05,1.20]。

若确有语义需要强调，必须在 FIGURE\_PLAN 中预先说明“哪个元素为什么更大/更小”，且强调角色对 BASE 的比例仍不得超过 1.25 或低于 0.90；同一强调规则必须跨面板一致。未预先说明的异常放大/缩小一律 FAIL。

普通轴标签、刻度、图例、注释、公式块不能靠大字号抢占主体。任一普通元素高度 > 同类中位数 1.20 倍，或单行未换行文本宽度 > 所在面板宽度 40% 且造成数据/结构区明显被挤压，直接 FAIL，应改为换行、缩短文字、移入正文或拆图。

“能读清”不是通过条件。即使 H\_ink\_px 高于下限，只要角色比例失衡、跨面板不一致、普通标签压过主体、公式块视觉权重异常，仍必须 FAIL。

F. 像素级零真实重叠、掩膜污染裁决与最小净空

对 300 dpi 原图建立候选前景掩膜。将独立语义对象分为 TEXT、FORMULA、LINE\_ARROW、MARKER、NODE\_BORDER、PANEL\_BORDER、DATA\_CURVE 等类别。节点填充色/注释底色属于背景，不视为与内部文字的非法重叠；但节点边框与文字属于独立前景。

自动检测先输出 OVERLAP\_CANDIDATE\_PIXEL\_COUNT 与候选连通簇。候选像素不能直接等同于真实碰撞，也不能直接被忽略。subagent1、subagent3 与主线程必须查看原始像素语义，而不是只看膨胀掩膜或 bbox 相交。

每个候选簇必须分类：

TRUE\_COLLISION：最终原图中的独立语义前景确实共享有效像素，或净空不足导致视觉遮挡/误读；

MASK\_CONTAMINATION：检测掩膜、抗锯齿复制、halo/阴影、背景误分、图层偏移、边界框替代墨迹等造成的假阳性，真实语义前景未相交且净空满足；

UNRESOLVED：证据不足、审阅者意见冲突或无法排除真实碰撞。

canonical OVERLAP\_PIXEL\_COUNT 只记录经证据裁决确认的 TRUE\_COLLISION 有效像素总数；MASK\_CONTAMINATION\_PIXEL\_COUNT 单独记录。OVERLAP\_CANDIDATE\_PIXEL\_COUNT 应等于已分类候选总量或给出差异解释。

PASS 的硬条件仍是 OVERLAP\_PIXEL\_COUNT=0。MASK\_CONTAMINATION\_PIXEL\_COUNT 可以大于 0，但只有在 after\_overlap\_adjudication.md 对每个候选簇提供 300 dpi 原图、分离掩膜、矢量/源码坐标和分类理由，且 PIXEL\_ADJUDICATION\_STATUS=MASK\_CONTAMINATION\_CONFIRMED 时才允许通过。任何 UNRESOLVED 必须 FAIL。

subagent1/subagent3 分类冲突、自动掩膜与原生像素语义冲突或主线程无法确定时，必须调用 gpt-5.6-sol + max 执行 PIXEL\_DISPUTE\_ARBITRATION。不得用“只有 1--2 像素”“看起来没事”跳过裁决。

必查组合：TEXT-TEXT、TEXT/FORMULA-LINE\_ARROW、TEXT/FORMULA-MARKER、TEXT/FORMULA-NODE\_BORDER、TEXT/FORMULA-PANEL\_BORDER、LEGEND-DATA\_CURVE、ANNOTATION-DATA\_CURVE、ARROWHEAD-TEXT。

在 OVERLAP\_PIXEL\_COUNT=0 之外，还必须满足最小净空：文字-文字 bbox >=4 px；文字/公式墨迹到线、箭头、标记 >=3 px；节点内文字/公式到节点边框 >=5 px；文字到面板裁切边/图像边 >=6 px；相邻面板中最接近的读者元素之间 >=8 px。

CLIP\_PIXEL\_COUNT 必须为 0。任何文字、公式、箭头头部、标记或图例被裁切 1 个及以上有效前景像素，直接 FAIL。

若曲线必须从文字附近通过，应移动文字、增加引线或给文字建立明确不透明背景/halo，使最终真实语义前景仍满足 OVERLAP\_PIXEL\_COUNT=0 和净空阈值；不得让曲线直接穿字。

G. 视觉协调与主体权重

subagent1/subagent3 必须在 full\_page\_200dpi、figure\_crop\_300dpi、standalone\_300dpi、grayscale\_300dpi 四种视图同时判断。局部合格但整页比例失衡，或彩色合格但灰度下层级崩塌，均 FAIL。

轴标签、刻度、图例、注释、公式块若无语义理由明显放大或缩小、抢占主体、跨面板不一致，直接 FAIL；不得以“可读”替代“协调”。

数据曲线/几何关系/流程主线应拥有最高视觉优先级；普通说明文字不得成为第一视觉焦点。若文字密度导致必须缩小才放得下，应优先删减重复说明、移入正文、重排或拆图。

图例不得遮挡数据；注释不得盖住关键拐点、样本、决策边界、概率质量、箭头方向或节点关系。即使像素没有实际交叠，但净空不足、遮挡视觉路径或造成误读，也判 FAIL。

灰度图中同一语义层级仍应稳定。不能依赖颜色大小差来弥补字号/线型层级混乱。

H. PASS/FAIL 判定矩阵
每幅图的 after\_visual\_acceptance.md 必须逐项写出：
SA1\_MODEL = gpt-5.6-sol
SA1\_REASONING = xhigh
SA2\_MODEL = gpt-5.6-terra 或 gpt-5.6-sol
SA2\_REASONING = high 或 xhigh
SA2\_ESCALATED = true/false
SA3\_MODEL = gpt-5.6-sol
SA3\_REASONING = xhigh
SOURCE\_FONT\_PASS = true/false
PIXEL\_HEIGHT\_PASS = true/false
SAME\_CLASS\_RATIO\_PASS = true/false
ROLE\_RATIO\_PASS = true/false
OVERLAP\_CANDIDATE\_PIXEL\_COUNT = 非负整数
MASK\_CONTAMINATION\_PIXEL\_COUNT = 非负整数
OVERLAP\_PIXEL\_COUNT = 经裁决确认的真实非法重叠像素非负整数
PIXEL\_ADJUDICATION\_STATUS = CLEAR / MASK\_CONTAMINATION\_CONFIRMED / DISPUTED / UNRESOLVED
PIXEL\_ARBITER\_MODEL = gpt-5.6-sol 或 NOT\_USED
PIXEL\_ARBITER\_REASONING = max 或 NOT\_USED
CLIP\_PIXEL\_COUNT = 非负整数
MIN\_TEXT\_CLEARANCE\_PX = 实测最小值
VISUAL\_HARMONY\_PASS = true/false
MATH\_SEMANTICS\_PASS = true/false
TEXT\_CONSISTENCY\_PASS = true/false
GRAYSCALE\_PASS = true/false
PAGE\_INTEGRATION\_PASS = true/false

只有全部布尔项为 true、PIXEL\_ADJUDICATION\_STATUS 为 CLEAR 或 MASK\_CONTAMINATION\_CONFIRMED、OVERLAP\_PIXEL\_COUNT=0、CLIP\_PIXEL\_COUNT=0，且各类最小净空满足 F8 时，subagent1/subagent3 才能返回 PASS。任何一项未知、未测、缺文件、模型路由不符、超阈值、存在真实非法重叠像素或存在 UNRESOLVED 候选，均必须返回 FAIL。

I. 失败后的唯一处理方式
任何视觉硬指标失败后，必须执行：subagent2 按默认或升级路由定向修复 → mechanical\_worker 重新独立编译 → 重新生成 300 dpi 原图 → 全量重做字号/像素/比例/候选重叠测量与碰撞/污染分类 → subagent1 重新盲审。subagent1 PASS 后才可进入 subagent3；subagent3 也必须独立按本节重测/复核，不能继承 subagent1 的 PASS。若只剩像素分类争议，则执行 PIXEL\_DISPUTE\_ARBITRATION，更新证据后再重新盲审。循环次数不设上限，直到全部硬指标通过。

9.3 发给逐图 subagent1 的模板
你是本图专属 subagent1，固定使用模型 gpt-5.6-sol，推理强度 xhigh。你是第一盲审者，只读，不得修改源码，也不得读取 subagent3 的任何结论。
OWNER\_DIALOGUE：DIALOGUE\_A\_VISUAL
WORKTREE：{DIALOGUE\_A\_WORKTREE}
HANDOFF\_ID：{HANDOFF\_ID}
FIGURE\_ID：{FIG\_NO}
CANONICAL\_UID：{UID}
章节：{CHAPTER\_TITLE}
PDF物理页：{PDF\_PAGE}
图类型：{FIG\_TYPE}
图源：{SOURCE\_FILE}
相邻正文：{CONTEXT\_FILE\_AND\_LINES}
当前问题：{CURRENT\_ISSUE}
本图专属方案：{FIGURE\_PLAN}
复核重点：{REVIEW\_FOCUS}
证据目录：{EVIDENCE\_DIR}
必须查看完整页200dpi、局部300dpi、独立图300dpi、灰度图，并逐项判断：
A. 数学与统计语义：对象、方向、索引、概率、归一化、曲线数据、几何关系是否正确；
B. 图文一致：图内变量、题注和相邻正文是否一一对应；
C. 阅读路径：读者是否能按单一方向完成“先看—再看—得到”；
D. 字号与密度：严格执行第 9.2.1 节。逐元素核对 declared\_pt、graphics\_scale、effective\_pt，并在 300 dpi 原图中核对 H\_ink\_px；不能只写“可读”；
E. 同类比例与视觉层级：核对同角色像素比例、跨面板一致性和 axis/tick/legend/annotation/formula 等角色比例。无语义理由的明显放大、缩小或抢占主体均为 FAIL；
F. 零重叠与净空：非法 OVERLAP\_PIXEL\_COUNT 必须严格为0，CLIP\_PIXEL\_COUNT 必须为0，并满足第9.2.1-F节最小净空；任意1个非法重叠像素即FAIL；
G. 布局：无文字/线条/箭头重叠，无裁切、溢出、挤压、异常留白；
H. 编码：颜色之外还有线型、点型、形状或结构编码，灰度下仍能区分；
I. 题注：只保留一条读图结论，方法细节移入正文；
J. 页面融合：图宽、上下留白、分页与相邻题解不会造成孤行或大块空白；
K. 技术：编译无致命错误，图号、标签和引用稳定。
任何一项不满足、任何测量缺失、任何非法重叠像素>=1即FAIL。返回：
RESULT: PASS/FAIL
FIGURE\_ID:
BLOCKERS:
MATH\_SEMANTICS:
TEXT\_CONSISTENCY:
READING\_ORDER:
SOURCE\_FONT\_AUDIT:
PIXEL\_HEIGHT\_AUDIT:
SAME\_CLASS\_RATIO\_AUDIT:
ROLE\_RATIO\_AUDIT:
OVERLAP\_CANDIDATE\_PIXEL\_COUNT:
MASK\_CONTAMINATION\_PIXEL\_COUNT:
OVERLAP\_PIXEL\_COUNT:
PIXEL\_ADJUDICATION\_STATUS:
CLIP\_PIXEL\_COUNT:
MIN\_TEXT\_CLEARANCE\_PX:
VISUAL\_HARMONY:
FONT\_AND\_DENSITY:
LAYOUT:
GRAYSCALE:
CAPTION:
PAGE\_INTEGRATION:
REQUIRED\_FIXES:
EVIDENCE\_USED:
9.4 发给逐图 subagent2 的模板
你是本图专属 subagent2。当前模型路由由分对话 A 协调器填写：
MODEL：{SA2\_MODEL}
REASONING\_EFFORT：{SA2\_REASONING\_EFFORT}
SA2\_ESCALATED：{SA2\_ESCALATED}
REPAIR\_ROUND：{REPAIR\_ROUND}
CONSECUTIVE\_FAILED\_REPAIR\_ROUNDS：{CONSECUTIVE\_FAILED\_REPAIR\_ROUNDS}
默认使用 gpt-5.6-terra + high；只有同一图连续两个完整修复轮仍失败后，下一轮才升级 gpt-5.6-sol + xhigh。你负责定向修复。
OWNER\_DIALOGUE：DIALOGUE\_A\_VISUAL
WORKTREE：{DIALOGUE\_A\_WORKTREE}
HANDOFF\_ID：{HANDOFF\_ID}
FIGURE\_ID：{FIG\_NO}
图源：{SOURCE\_FILE}
允许修改：仅该图源及 A 自有测试包装文件。直接包含它的章节题注/读图说明只能写入 A\_CHAPTER\_CHANGE\_REQUESTS.md；共享样式只能写入 SHARED\_CHANGE\_REQUESTS\_A.md，由主对话决定。
subagent1失败项：{FAIL\_ITEMS}
目标方案：{FIGURE\_PLAN}
要求：

逐项复现失败项；

优先重构结构、拆图、调整节点/坐标/图例/题注，不得靠整体缩小解决；

保持数学数据和正文符号准确；

修改后独立编译图源并编译整页；

生成新一轮完整页、局部、独立、灰度渲染；

生成新的 after\_font\_audit.csv、after\_pixel\_measurements.csv、after\_overlap\_report.csv、after\_overlap\_adjudication.md、after\_model\_route.md、after\_text\_measurement\_overlay\_300dpi.png 与 after\_visual\_acceptance.md；

任何经裁决确认的真实非法重叠像素 >=1、任何候选仍为 UNRESOLVED、CLIP\_PIXEL\_COUNT>=1、有效字号低于下限、同类比例/角色比例超阈值时，不得返回 FIXED；必须继续修改或触发像素裁决；

返回精确文件差异和剩余风险。

返回：
RESULT: FIXED/PARTIAL/BLOCKED
FIGURE\_ID:
FILES\_CHANGED:
ROOT\_CAUSE:
PATCH\_SUMMARY:
STANDALONE\_BUILD:
PAGE\_BUILD:
NEW\_EVIDENCE:
FONT\_AUDIT\_RESULT:
PIXEL\_MEASUREMENT\_RESULT:
OVERLAP\_CANDIDATE\_PIXEL\_COUNT:
MASK\_CONTAMINATION\_PIXEL\_COUNT:
OVERLAP\_PIXEL\_COUNT:
PIXEL\_ADJUDICATION\_STATUS:
CLIP\_PIXEL\_COUNT:
MIN\_TEXT\_CLEARANCE\_PX:
REMAINING\_RISKS:
9.5 发给逐图 subagent3 的模板
你是本图专属 subagent3，固定使用模型 gpt-5.6-sol，推理强度 xhigh。你是独立第二盲审者，只读，不得读取 subagent1 的最终判断、评分摘要或 PASS/FAIL。
OWNER\_DIALOGUE：DIALOGUE\_A\_VISUAL
WORKTREE：{DIALOGUE\_A\_WORKTREE}
HANDOFF\_ID：{HANDOFF\_ID}
FIGURE\_ID：{FIG\_NO}
CANONICAL\_UID：{UID}
图源：{SOURCE\_FILE}
当前完整页与局部证据：{EVIDENCE\_DIR}
本图完成标准：{REVIEW\_FOCUS}
不要读取subagent1的最终结论。重新从数学、图文一致、阅读顺序、字号、布局、灰度、题注、页面融合和编译引用九方面检查，并独立执行第 9.2.1 节的严格视觉验收：核对所有源级有效字号；在 300 dpi 原始图中复核实际像素高度；重新检查同类标签和跨面板比例；重新检查 axis/tick/legend/annotation/formula 等视觉层级；独立检查每个候选重叠簇的原生像素语义并分类；确认 PIXEL\_ADJUDICATION\_STATUS 为 CLEAR 或 MASK\_CONTAMINATION\_CONFIRMED、OVERLAP\_PIXEL\_COUNT=0、CLIP\_PIXEL\_COUNT=0 和最小净空达标。任何一项有问题、任何真实非法重叠像素>=1、任何候选 UNRESOLVED、或任一证据缺失即FAIL；与 subagent1 分类冲突时明确标记 PIXEL\_DISPUTE\_REQUIRED。
返回：
RESULT: PASS/FAIL
FIGURE\_ID:
INDEPENDENT\_FINDINGS:
SOURCE\_FONT\_AUDIT:
PIXEL\_HEIGHT\_AUDIT:
SAME\_CLASS\_RATIO\_AUDIT:
ROLE\_RATIO\_AUDIT:
OVERLAP\_CANDIDATE\_PIXEL\_COUNT:
MASK\_CONTAMINATION\_PIXEL\_COUNT:
OVERLAP\_PIXEL\_COUNT:
PIXEL\_ADJUDICATION\_STATUS:
CLIP\_PIXEL\_COUNT:
MIN\_TEXT\_CLEARANCE\_PX:
VISUAL\_HARMONY:
NEW\_REGRESSIONS:
BLOCKERS:
REQUIRED\_FIXES:
EVIDENCE\_USED:

绘图统一修改标准

图必须服务于一个明确教学任务。无法用一句话说清图的唯一读图结论时，应拆图。
复杂图使用固定网格、明确面板编号和单向阅读路线；避免交叉箭头、回折箭头和大段说明塞进节点。
坐标图减少无用刻度；轴、单位、图例和参数必须与正文一致；数值曲线必须由公式/数据生成，不凭手画。
概率图、马尔可夫链、PageRank、HMM/CRF 等必须明确有向边、无向边、条件关系和矩阵约定，不能用相同线型混淆。
图内中文、英文、数学字体风格统一；不得因单图自行缩放破坏全书一致性。所有读者可见文字均须满足第 9.2.1 节的源级有效字号与 300 dpi 像素高度下限，并通过同类比例、角色比例、跨面板一致性和视觉协调性检查。
任何独立语义对象之间的非法像素重叠必须为 0；文字、公式、图例、轴标签、刻度、注释和节点标签只要出现 1 个经阈值确认的重叠像素，立即重做，不得判为“轻微问题”或“可接受”。
主线、次线、辅助线层级明确；箭头头部大小与线宽匹配。
关键节点间距与内边距足够；文字基线、公式框和对齐稳定。
同一含义在全书使用相同视觉编码；颜色不作为唯一信号。
题注只给结论，不重复完整流程；图后正文补一条“先看什么、再看什么、最终得到什么”。
若图被拆分，保持原图号的子图 (a)(b) 或按章节语义重新编号，并同步更新正文引用、目录/图清单与标签。

例题、知识点、定理和推导的完成判据

11.1 例题
每道例题都必须回答全部问项，并让读者看出：
题目给了什么对象和条件；
第一数学动作是什么；
为什么采用该方法；
中间式如何得到；
最后怎样核验；
结论是什么且只写一次。
禁止把题型无关的模板句保留下来。对于简单题，允许精炼，不得为凑结构重复核验。
11.2 知识点
每个知识点至少包含一个真正落地的对象或例子。抽象定义出现后立即说明作用域和一个最小辨识问题。可复用公共结构，但具体措辞必须与该知识点匹配。
11.3 定义、定理与证明
条件、量词、对象域和结论完整；
证明路线先说关键变形，再展开技术细节；
每个条件的使用位置可定位；
等号、极限、求导、积分、交换次序、矩阵求逆和除法都有合法依据；
给出一个只破坏单一条件的边界例或反例，确有教学价值时才加入。
11.4 核心推导
推导不得跳过决定性变形；每一步都能由上一行和已声明条件推出。末尾必须有维数、归一化、代回、残差、目标单调性或边界检查中的至少一种恰当核验。

源码修改、局部编译、分对话测试与整书构建

分对话 A/B 只在各自 worktree 中执行局部编译和规定测试，结果随交接传回主对话；只有主对话能在 INTEGRATION\_WORKTREE 修改公共构建入口、执行最终整书构建并向 FINAL\_ROOT 复制正式文件。分对话本地构建通过不等于集成构建通过。
默认沿用 LuaLaTeX；XeLaTeX 仅作为明确记录的兼容回退。
不联网，不自动安装软件、宏包或字体。
修改单图时先独立编译图，再编译受影响章节/页面；修改公共样式后编译全部受影响对象。
长篇构建可使用现有 Resume 机制，但最终必须做一次全新完整构建。
由主对话更新顶层构建脚本为 build\_v2.7.0.ps1，更新发布名和临时缓存名；分对话不得直接修改该脚本。
最终完整解析版以合并总册 main\_full.tex 为唯一入口。
编译日志不得含致命错误、未定义控制序列、重复标签、未定义引用、字体替代异常、对象越界或严重 overfull/underfull 版面问题。

主对话合并后的最终全书视觉扫描

仅当 DIALOGUE\_A\_VISUAL 与 DIALOGUE\_B\_CONTENT 的交接均已进入 MERGED\_VALIDATED，主对话完成共享变更后，才可执行本节。分对话生成的本地页面证据只能作为输入，最终证据必须从 INTEGRATION\_WORKTREE 的集成 PDF 重新生成。
完成全部对象后：
对最终 PDF 每一页生成 200dpi 渲染并建立接触表；
主对话逐页扫描全部页面；
对所有图页、章首页、算法页、跨页例题、索引页和曾有小字号的页面单独放大复核；
对 99 幅图逐幅保存最终局部图，并逐幅保存第 9.2.1 节要求的最终字号/像素/比例/零重叠证据；
检查封面版本、目录、书签、页眉页脚、图表编号、题后即解、跨页续题、字体、重叠、裁切、空白、链接与索引；对于所有图页再次确认有效字号达标、300 dpi 实际像素高度达标、同类标签比例与跨面板比例达标、所有候选重叠均已分类、PIXEL\_ADJUDICATION\_STATUS 为 CLEAR 或 MASK\_CONTAMINATION\_CONFIRMED、OVERLAP\_PIXEL\_COUNT=0、CLIP\_PIXEL\_COUNT=0。不得仅凭“肉眼可读”关闭最终扫描；
最终主对话发现任何问题，尤其是任意 1 个经裁决确认的真实非法重叠像素、任何未决像素候选、任何像素高度/比例硬阈值失败或视觉层级失衡，必须按对象归属生成 REWORK\_PACKET\_A 或 REWORK\_PACKET\_B；共享问题由主对话修复。责任分对话完成 subagent2 → subagent1 → subagent3 → 协调器本地闭环并重新交接后，主对话重新合并和复测。
最终全书扫描不能用抽样替代，但无需再次从零重建内容索引。
99 幅图逐图关闭且全书扫描完成后，必须单独调用 FINAL\_99\_FIGURE\_GATE：gpt-5.6-sol + max。该总门只做跨图一致性与最终证据裁决，不替代前面的 99 次 subagent1/subagent3 盲审。总门必须检查全书图内字号族、同类标签比例、面板编号、线宽、箭头、图例、灰度编码、真实碰撞/掩膜污染分类和模型路由记录；FAIL 时回到对应图闭环。

主对话最终构建、独立重建与全部文件打包

只有两份交接均 MERGED\_VALIDATED、所有返工已闭合、集成版局部测试通过后，主对话才按以下顺序执行，不得省略：
从 SOURCE\_WORKTREE 做一次干净完整构建，生成并复制：
D:\Users\ASUS\Desktop\机器学习\v2.7.0\统计学习方法初学者讲义\_合并总册v2.7.0\_完整解析版.pdf
清理正式源码副本中的中间文件、临时图、代理记录、旧版本临时发布内容和本机绝对路径；把源码根目录命名为 v2.7.0，生成：
D:\Users\ASUS\Desktop\机器学习\v2.7.0\统计学习方法讲义\_v2.7.0\_LaTeX源码.zip
在 WORK\_ROOT\package\_validation\source\_rebuild\ 解压上述源码压缩包，严格按 README\_v2.7.0.md 中的一条 PowerShell 命令离线重建同名完整 PDF；不得调用工作树外的源码或隐藏依赖。
对独立重建版核对页数、封面版本、目录、书签、交叉引用、99 幅图、66 道正文例题、553 道练习和关键页面视觉；发现差异即返回对应修复闭环。
从最终 PDF 生成全书逐页接触表、99 幅最终绘图裁图、重点页面放大图和灰度复核图；同时收集 99 幅图最终 after\_font\_audit.csv、after\_pixel\_measurements.csv、after\_overlap\_report.csv、after\_overlap\_adjudication.md、after\_model\_route.md、after\_text\_measurement\_overlay\_300dpi.png 和 after\_visual\_acceptance.md，整理为：
D:\Users\ASUS\Desktop\机器学习\v2.7.0\统计学习方法讲义\_v2.7.0\_最终视觉证据.zip
生成并更新 README\_v2.7.0.md、CHANGELOG\_v2.7.0.md、v2.7.0\_修改与复核总报告.md、两份 CSV 台账、v2.7.0\_最终全书视觉扫描记录.md 和 MANIFEST\_v2.7.0.md。
把当前主提示词及两份分对话执行提示词复制到 FINAL\_ROOT：
D:\Users\ASUS\Desktop\机器学习\v2.7.0\GPT\_Pro\_统计学习方法讲义\_v2.7.0\_Codex\_Goal主提示词.md
D:\Users\ASUS\Desktop\机器学习\v2.7.0\GPT\_Pro\_统计学习方法讲义\_v2.7.0\_对话A\_逐图视觉重构执行提示词.md
D:\Users\ASUS\Desktop\机器学习\v2.7.0\GPT\_Pro\_统计学习方法讲义\_v2.7.0\_对话B\_内容数学重构执行提示词.md
按第 3 节规定的内部结构创建：
D:\Users\ASUS\Desktop\机器学习\v2.7.0\统计学习方法讲义\_v2.7.0\_全部交付文件.zip
在 WORK\_ROOT\package\_validation\full\_delivery\ 解压总交付压缩包并执行以下复核：
压缩包能够完整打开和解压；
内部成员名称与第 3 节清单逐项一致；
发布 PDF、源码 ZIP、最终视觉证据 ZIP、说明文件、复核台账与主提示词均存在；
不含总交付压缩包自身，不含 \_work、v2.6.0 输入、旧版本产物、绝对路径条目和临时文件；
从包内的 LaTeX 源码 ZIP 再做一次独立解压，并按包内 README 的命令完成构建入口检查。
在完成独立重建、最终视觉证据整理、说明文件更新和总交付包独立解压检查后，必须调用 FINAL\_BOOK\_RELEASE\_GATE：gpt-5.6-sol + max。该发布门检查所有逐图门、FINAL\_99\_FIGURE\_GATE、全书逐页扫描、交叉引用、离线重建、文件清单和压缩包完整性是否真实闭合；FAIL 时回到对应环节，不得带病发布。
最后由主对话恢复 gpt-5.6-sol + xhigh，逐一确认 FINAL\_ROOT 顶层的十四个规定文件真实存在、名称完全匹配、可正常读取；不得只报告“已生成”而不检查实际路径。

最终完成条件

仅当以下全部成立才可结束：
主对话、分对话 A、分对话 B 已按第 4.6—4.13 节真实建立；A/B 使用隔离 worktree 和互斥写域，不存在并发覆盖同一文件；
DIALOGUE\_A\_HANDOFF.md、DIALOGUE\_B\_HANDOFF.md、两份变更清单、测试结果、未解决项、共享请求和补丁/分支均已传回主对话；HANDOFF\_INTEGRATION\_LOG.csv 中两者最终均为 MERGED\_VALIDATED，所有 REWORK\_REQUIRED 已闭合；
主对话实际工作根目录为 D:\Users\ASUS\Desktop\机器学习，集成工作树、分对话工作树、状态、交接和证据均位于 D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work；
最终 PDF 与 LaTeX 源码压缩包直接位于 D:\Users\ASUS\Desktop\机器学习\v2.7.0，名称完全符合第 3 节；
封面、元数据、构建脚本和发布名均为 v2.7.0；
935 处内部工作文案已逐项处理，没有读者版泄漏；
99 幅图均有使用 gpt-5.6-sol + xhigh 的独立 subagent1 与 subagent3 盲审记录；subagent2 默认使用 gpt-5.6-terra + high，连续两个修复轮失败的图已按规则升级 gpt-5.6-sol + xhigh；每幅图最终均有完整的源级字号审计、300 dpi 实际像素高度、同类比例/角色比例、候选重叠与真实碰撞/掩膜污染裁决、最小净空和模型路由证据，PIXEL\_ADJUDICATION\_STATUS 为 CLEAR 或 MASK\_CONTAMINATION\_CONFIRMED，OVERLAP\_PIXEL\_COUNT=0、CLIP\_PIXEL\_COUNT=0，且不存在“证据缺失但判 PASS”的记录；
66 道正文例题均完成本题专属解答与数学复算；
596 个知识点、192 个定义/定理类对象和 59 组核心推导逐项处理；
553 道练习与解析配对清楚，短解析已补全；
算法契约、状态语义、标签和字面命令错误已修复；
139 个问题页得到回查，最终没有不可读小字、重叠、裁切和异常大留白；所有涉及图表的受影响页均满足第 9.2.1 节，任意读者元素不存在 1 个及以上非法重叠像素；
全书逐页视觉扫描完成，统计学习方法讲义\_v2.7.0\_最终视觉证据.zip 可正常解压；
最终源码 ZIP 可在独立目录离线重建同名 PDF；
两份三角色复核台账逐项闭合，MODEL\_ROUTING\_LOG.csv 与 PIXEL\_ADJUDICATION\_LOG.csv 无缺项，FINAL\_99\_FIGURE\_GATE 与 FINAL\_BOOK\_RELEASE\_GATE 均由 gpt-5.6-sol + max 返回 PASS，所有最终状态均为通过；
MANIFEST\_v2.7.0.md 与 FINAL\_ROOT 实际文件逐项一致；
统计学习方法讲义\_v2.7.0\_全部交付文件.zip 已创建并通过独立解压检查，包含第 3 节列出的全部正式文件且不含自身或临时文件；
FINAL\_ROOT 顶层十四个规定文件全部真实存在并可正常读取，其中包括主对话提示词和两份分对话执行提示词。
附录 A｜21 幅高优先级图的额外要求
图 30.2｜PDF物理页 645｜FIG-P547-01
图源：src/绘图源码/第05册\_采样方法主题模型与图排序/V5-C01/fig\_v5\_c01\_transition\_graph.tex
当前问题：所在页存在低于7.5pt文字（最小约6.14pt）；所在页小于8.5pt字符较多（37个）；题注偏长，图结论与使用说明混在同一题注中；逐图视觉复核显示可读性仍可提升
额外修改：把状态图、转移方向与矩阵行列约定分层呈现；显式说明箭头方向对应哪一个矩阵下标，避免读者把行随机与列随机混用。
复核重点：阅读方向唯一、节点层级清楚、箭头端点停在边界、无回折交叉与语义歧义；图内文字、公式、符号、变量、题注和相邻正文完全一致；整页与局部渲染均无重叠、裁切、溢出、过密、过大留白或异常断行；必须评估拆图或重构，不得仅靠放大画布和整体缩放掩盖结构问题
图 32.5｜PDF物理页 710｜FIG-P602-01
图源：src/绘图源码/第05册\_采样方法主题模型与图排序/V5-C03/fig\_v5\_c03\_mh\_accept\_reject.tex
当前问题：所在页存在低于6pt文字（最小约6.00pt）；所在页有11个字符低于8.5pt；题注偏长，图结论与使用说明混在同一题注中；逐图视觉复核显示可读性仍可提升
额外修改：把“提出候选—计算比值—接受/拒绝—保留旧状态”拆成单向流程，公式只保留决定接受率的核心一式。
复核重点：关系类型、条件方向与层级不能只靠颜色表达；概念边界与正文定义一致；图内文字、公式、符号、变量、题注和相邻正文完全一致；整页与局部渲染均无重叠、裁切、溢出、过密、过大留白或异常断行；必须评估拆图或重构，不得仅靠放大画布和整体缩放掩盖结构问题
图 32.8｜PDF物理页 718｜FIG-P608-01
图源：src/绘图源码/第05册\_采样方法主题模型与图排序/V5-C03/fig\_v5\_c03\_trace\_running\_mean.tex
当前问题：所在页存在低于7.5pt文字（最小约6.42pt）；所在页小于8.5pt字符较多（51个）；题注偏长，图结论与使用说明混在同一题注中；逐图视觉复核显示可读性仍可提升
额外修改：将轨迹图与运行均值分成上下两个面板，明确燃烧期、保留区间和目标均值，不让多条注释压在曲线上。
复核重点：坐标轴、刻度、单位、图例、曲线数据与正文公式一致；线型和点型可在灰度下区分；图内文字、公式、符号、变量、题注和相邻正文完全一致；整页与局部渲染均无重叠、裁切、溢出、过密、过大留白或异常断行；必须评估拆图或重构，不得仅靠放大画布和整体缩放掩盖结构问题
图 32.9｜PDF物理页 718｜FIG-P609-01
图源：src/绘图源码/第05册\_采样方法主题模型与图排序/V5-C03/fig\_v5\_c03\_autocorrelation\_ess.tex
当前问题：所在页存在低于7.5pt文字（最小约6.42pt）；所在页小于8.5pt字符较多（51个）；题注偏长，图结论与使用说明混在同一题注中；逐图视觉复核显示可读性仍可提升
额外修改：将自相关曲线与ESS解释分离；保留少量关键滞后和一条从相关性到有效样本量的读图结论。
复核重点：坐标轴、刻度、单位、图例、曲线数据与正文公式一致；线型和点型可在灰度下区分；图内文字、公式、符号、变量、题注和相邻正文完全一致；整页与局部渲染均无重叠、裁切、溢出、过密、过大留白或异常断行；必须评估拆图或重构，不得仅靠放大画布和整体缩放掩盖结构问题
图 33.1｜PDF物理页 738｜FIG-P630-01
图源：src/绘图源码/第05册\_采样方法主题模型与图排序/V5-C04/fig\_v5\_c04\_dependency\_graph.tex
当前问题：所在页存在低于7.5pt文字（最小约6.42pt）；所在页小于8.5pt字符较多（33个）；题注偏长，图结论与使用说明混在同一题注中；逐图视觉复核显示可读性仍可提升
额外修改：突出“给定其余坐标”后只更新一个坐标的条件依赖；图边只表示依赖，不暗示生成时间方向。
复核重点：关系类型、条件方向与层级不能只靠颜色表达；概念边界与正文定义一致；图内文字、公式、符号、变量、题注和相邻正文完全一致；整页与局部渲染均无重叠、裁切、溢出、过密、过大留白或异常断行；必须评估拆图或重构，不得仅靠放大画布和整体缩放掩盖结构问题
图 33.3｜PDF物理页 742｜FIG-P634-01
图源：src/绘图源码/第05册\_采样方法主题模型与图排序/V5-C04/fig\_v5\_c04\_coordinate\_sweep.tex
当前问题：所在页存在低于7.5pt文字（最小约6.14pt）；所在页小于8.5pt字符较多（60个）；题注偏长，图结论与使用说明混在同一题注中；逐图视觉复核判定为优先重绘/拆图对象
额外修改：明确系统扫描的先后次序与“同轮新值”使用位置；用编号和箭头双编码，避免读者误作并行更新。
复核重点：关系类型、条件方向与层级不能只靠颜色表达；概念边界与正文定义一致；图内文字、公式、符号、变量、题注和相邻正文完全一致；整页与局部渲染均无重叠、裁切、溢出、过密、过大留白或异常断行；必须评估拆图或重构，不得仅靠放大画布和整体缩放掩盖结构问题
图 33.7｜PDF物理页 747｜FIG-P640-01
图源：src/绘图源码/第05册\_采样方法主题模型与图排序/V5-C04/fig\_v5\_c04\_mixing\_rho\_comparison.tex
当前问题：题注偏长，图结论与使用说明混在同一题注中；逐图视觉复核判定为优先重绘/拆图对象
额外修改：把不同|rho|的自相关衰减曲线与ESS比率面板分开，统一坐标尺度并减少图例文字。
复核重点：坐标轴、刻度、单位、图例、曲线数据与正文公式一致；线型和点型可在灰度下区分；图内文字、公式、符号、变量、题注和相邻正文完全一致；整页与局部渲染均无重叠、裁切、溢出、过密、过大留白或异常断行；必须评估拆图或重构，不得仅靠放大画布和整体缩放掩盖结构问题
图 34.8｜PDF物理页 775｜FIG-P668-01
图源：src/绘图源码/第05册\_采样方法主题模型与图排序/V5-C05/fig\_v5\_c05\_dirichlet\_shape\_atlas.tex
当前问题：所在页存在低于6pt文字（最小约4.68pt）；所在页小于8.5pt字符较多（41个）；题注偏长，图结论与使用说明混在同一题注中；逐图视觉复核判定为优先重绘/拆图对象
额外修改：将Dirichlet形状图谱拆为多个同尺度单纯形小面板，统一顶点标签、参数顺序和密度高低表达。
复核重点：关系类型、条件方向与层级不能只靠颜色表达；概念边界与正文定义一致；图内文字、公式、符号、变量、题注和相邻正文完全一致；整页与局部渲染均无重叠、裁切、溢出、过密、过大留白或异常断行；必须评估拆图或重构，不得仅靠放大画布和整体缩放掩盖结构问题
图 34.9｜PDF物理页 775｜FIG-P669-01
图源：src/绘图源码/第05册\_采样方法主题模型与图排序/V5-C05/fig\_v5\_c05\_concentration\_mean.tex
当前问题：所在页存在低于6pt文字（最小约4.68pt）；所在页小于8.5pt字符较多（41个）；题注偏长，图结论与使用说明混在同一题注中；逐图视觉复核判定为优先重绘/拆图对象
额外修改：将“均值方向”和“总浓度”分为两个独立视觉变量，避免在同一面板中同时改变二者。
复核重点：阅读方向唯一、节点层级清楚、箭头端点停在边界、无回折交叉与语义歧义；图内文字、公式、符号、变量、题注和相邻正文完全一致；整页与局部渲染均无重叠、裁切、溢出、过密、过大留白或异常断行；必须评估拆图或重构，不得仅靠放大画布和整体缩放掩盖结构问题
图 35.3｜PDF物理页 794｜FIG-P684-01
图源：src/绘图源码/第05册\_采样方法主题模型与图排序/V5-C06/fig\_v5\_c06\_generative\_process.tex
当前问题：所在页存在低于6pt文字（最小约4.58pt）；所在页有19个字符低于8.5pt；题注偏长，图结论与使用说明混在同一题注中；逐图视觉复核判定为优先重绘/拆图对象
额外修改：把LDA生成过程按文档级、主题级、词元级分层；板式框、随机变量、超参数和重复次数各司其职，减少长公式框。
复核重点：阅读方向唯一、节点层级清楚、箭头端点停在边界、无回折交叉与语义歧义；图内文字、公式、符号、变量、题注和相邻正文完全一致；整页与局部渲染均无重叠、裁切、溢出、过密、过大留白或异常断行；必须评估拆图或重构，不得仅靠放大画布和整体缩放掩盖结构问题
图 35.7｜PDF物理页 805｜FIG-P694-01
图源：src/绘图源码/第05册\_采样方法主题模型与图排序/V5-C06/fig\_v5\_c06\_variational\_updates.tex
当前问题：题注偏长，图结论与使用说明混在同一题注中；逐图视觉复核判定为优先重绘/拆图对象
额外修改：将外层变分EM与内层局部坐标更新拆为两个面板；标明输入、更新顺序、停止量与输出，不在一条回路中塞入全部公式。
复核重点：阅读方向唯一、节点层级清楚、箭头端点停在边界、无回折交叉与语义歧义；图内文字、公式、符号、变量、题注和相邻正文完全一致；整页与局部渲染均无重叠、裁切、溢出、过密、过大留白或异常断行；必须评估拆图或重构，不得仅靠放大画布和整体缩放掩盖结构问题
图 35.8｜PDF物理页 805｜FIG-P695-01
图源：src/绘图源码/第05册\_采样方法主题模型与图排序/V5-C06/fig\_v5\_c06\_method\_comparison.tex
当前问题：题注偏长，图结论与使用说明混在同一题注中；逐图视觉复核判定为优先重绘/拆图对象
额外修改：把推断方法比较改为对照表或两栏结构，列出目标、局部变量、更新方式、优缺点和适用条件，避免密集关系网。
复核重点：关系类型、条件方向与层级不能只靠颜色表达；概念边界与正文定义一致；图内文字、公式、符号、变量、题注和相邻正文完全一致；整页与局部渲染均无重叠、裁切、溢出、过密、过大留白或异常断行；必须评估拆图或重构，不得仅靠放大画布和整体缩放掩盖结构问题
图 36.4｜PDF物理页 830｜FIG-P717-01
图源：src/绘图源码/第05册\_采样方法主题模型与图排序/V5-C07/inbound\_contribution.tex
当前问题：所在页存在低于6pt文字（最小约4.58pt）；所在页小于8.5pt字符较多（45个）；逐图视觉复核判定为优先重绘/拆图对象
额外修改：将入链节点、出度归一化和目标节点贡献分步呈现；公式中的求和索引与图中边方向逐项对应。
复核重点：关系类型、条件方向与层级不能只靠颜色表达；概念边界与正文定义一致；图内文字、公式、符号、变量、题注和相邻正文完全一致；整页与局部渲染均无重叠、裁切、溢出、过密、过大留白或异常断行；必须评估拆图或重构，不得仅靠放大画布和整体缩放掩盖结构问题
图 36.7｜PDF物理页 834｜FIG-P721-01
图源：src/绘图源码/第05册\_采样方法主题模型与图排序/V5-C07/numerical\_rank\_trajectory.tex
当前问题：所在页存在低于7.5pt文字（最小约6.42pt）；所在页有15个字符低于8.5pt；逐图视觉复核判定为优先重绘/拆图对象
额外修改：将PageRank迭代轨迹与最终排名条形图分离；轨迹图只显示收敛，排名图只显示终值与次序。
复核重点：坐标轴、刻度、单位、图例、曲线数据与正文公式一致；线型和点型可在灰度下区分；图内文字、公式、符号、变量、题注和相邻正文完全一致；整页与局部渲染均无重叠、裁切、溢出、过密、过大留白或异常断行；必须评估拆图或重构，不得仅靠放大画布和整体缩放掩盖结构问题
图 37.2｜PDF物理页 852｜FIG-P736-01
图源：src/绘图源码/第05册\_采样方法主题模型与图排序/V5-C08/method\_family\_relationships.tex
当前问题：题注偏长，图结论与使用说明混在同一题注中；逐图视觉复核判定为优先重绘/拆图对象
额外修改：每个方法族只保留核心输出和关键假设，方法之间的联系用少量有类型的边表示。
复核重点：阅读方向唯一、节点层级清楚、箭头端点停在边界、无回折交叉与语义歧义；图内文字、公式、符号、变量、题注和相邻正文完全一致；整页与局部渲染均无重叠、裁切、溢出、过密、过大留白或异常断行；必须评估拆图或重构，不得仅靠放大画布和整体缩放掩盖结构问题
图 37.3｜PDF物理页 852｜FIG-P737-01
图源：src/绘图源码/第05册\_采样方法主题模型与图排序/V5-C08/task\_representation\_inference\_cube.tex
当前问题：题注偏长，图结论与使用说明混在同一题注中；逐图视觉复核判定为优先重绘/拆图对象
额外修改：把任务、表示、推断三个维度改成可顺序阅读的二维分面，避免三维立方体造成层级混淆。
复核重点：阅读方向唯一、节点层级清楚、箭头端点停在边界、无回折交叉与语义歧义；图内文字、公式、符号、变量、题注和相邻正文完全一致；整页与局部渲染均无重叠、裁切、溢出、过密、过大留白或异常断行；必须评估拆图或重构，不得仅靠放大画布和整体缩放掩盖结构问题
图 37.4｜PDF物理页 854｜FIG-P740-01
图源：src/绘图源码/第05册\_采样方法主题模型与图排序/V5-C08/matrix\_probability\_bridge.tex
当前问题：所在页存在低于7.5pt文字（最小约6.42pt）；所在页有6个字符低于8.5pt；题注偏长，图结论与使用说明混在同一题注中；逐图视觉复核判定为优先重绘/拆图对象
额外修改：突出矩阵分解与概率模型之间的桥接变量、目标和归一化条件，删除重复说明。
复核重点：阅读方向唯一、节点层级清楚、箭头端点停在边界、无回折交叉与语义歧义；图内文字、公式、符号、变量、题注和相邻正文完全一致；整页与局部渲染均无重叠、裁切、溢出、过密、过大留白或异常断行；必须评估拆图或重构，不得仅靠放大画布和整体缩放掩盖结构问题
图 37.5｜PDF物理页 857｜FIG-P745-01
图源：src/绘图源码/第05册\_采样方法主题模型与图排序/V5-C08/fig\_v5\_c08\_validation\_protocols.tex
当前问题：逐图视觉复核判定为优先重绘/拆图对象
额外修改：左右两条验证协议保持同构；明确数据隔离、超参数选择、锁定测试的先后次序。
复核重点：阅读方向唯一、节点层级清楚、箭头端点停在边界、无回折交叉与语义歧义；图内文字、公式、符号、变量、题注和相邻正文完全一致；整页与局部渲染均无重叠、裁切、溢出、过密、过大留白或异常断行；必须评估拆图或重构，不得仅靠放大画布和整体缩放掩盖结构问题
图 37.6｜PDF物理页 860｜FIG-P748-01
图源：src/绘图源码/第05册\_采样方法主题模型与图排序/V5-C08/evaluation\_dashboard.tex
当前问题：逐图视觉复核判定为优先重绘/拆图对象
额外修改：将多证据评价面板改成分组卡片或简洁表格，统一指标方向，标明不能由单一总分替代原始指标。
复核重点：关系类型、条件方向与层级不能只靠颜色表达；概念边界与正文定义一致；图内文字、公式、符号、变量、题注和相邻正文完全一致；整页与局部渲染均无重叠、裁切、溢出、过密、过大留白或异常断行；必须评估拆图或重构，不得仅靠放大画布和整体缩放掩盖结构问题
图 37.7｜PDF物理页 861｜FIG-P750-01
图源：src/绘图源码/第05册\_采样方法主题模型与图排序/V5-C08/method\_selection\_decision\_map.tex
当前问题：题注偏长，图结论与使用说明混在同一题注中；逐图视觉复核判定为优先重绘/拆图对象
额外修改：决策图从“输出语义”开始，随后经过约束、候选方法、验证与资源预算；每个分支只回答一个问题。
复核重点：阅读方向唯一、节点层级清楚、箭头端点停在边界、无回折交叉与语义歧义；图内文字、公式、符号、变量、题注和相邻正文完全一致；整页与局部渲染均无重叠、裁切、溢出、过密、过大留白或异常断行；必须评估拆图或重构，不得仅靠放大画布和整体缩放掩盖结构问题
图 37.8｜PDF物理页 866｜FIG-P756-01
图源：src/绘图源码/第05册\_采样方法主题模型与图排序/V5-C08/full\_course\_synthesis\_map.tex
当前问题：题注偏长，图结论与使用说明混在同一题注中；逐图视觉复核判定为优先重绘/拆图对象
额外修改：保留五站主闭环和监督/无监督两条支线，但拆成两个独立面板；共同出口、返回路径和边界条件必须一眼可读。
复核重点：阅读方向唯一、节点层级清楚、箭头端点停在边界、无回折交叉与语义歧义；图内文字、公式、符号、变量、题注和相邻正文完全一致；整页与局部渲染均无重叠、裁切、溢出、过密、过大留白或异常断行；必须评估拆图或重构，不得仅靠放大画布和整体缩放掩盖结构问题
附录 B｜99 幅绘图逐图任务卡
下面每一项都是独立任务。主线程必须把本项内容连同第 9 节模板发给本图专属 subagent1；失败时发给 subagent2；subagent1 通过后再发给本图专属 subagent3。附录 B 每一项自动继承第 9.2.1 节全部硬性视觉标准；任务卡中未重复写出的源级字号、300 dpi 像素高度、同类比例、角色比例、零重叠、裁切与最小净空要求仍必须逐图执行，不能以“本图严重度低/无”为理由跳过。
B01｜图 1.1｜FIG-P020-01
章节：第 1 章《数学语言、符号约定与学习路线》；PDF物理页：17
类型：概念关系图；严重度：无
图源：src/绘图源码/第01册\_数学基础与统计学习基本理论/V1-C01/fig\_v1\_c01\_language\_flow\.tex
当前题注：图 1.1: 数学语言从对象声明到任务陈述的依赖关系。每一条箭头都表示右侧内容使用左侧定义。
唯一读图结论：数学语言从对象声明到任务陈述的依赖关系。每一条箭头都表示右侧内容使用左侧定义。
当前问题：未发现明显缺图、裁切、重叠或变量不一致；仍建议保留常规灰度与字号复核
本图专属修改方案：统一节点最小宽度、内边距与层级间距；箭头端点停在节点边界，避免穿过文字和交叉；保留原变量命名，并在图后加入一句“先看什么、再看什么、最终得到什么”的阅读顺序
建议图宽：>=0.72\textwidth（核心图）；按版心自适应
subagent1/subagent3复核重点：关系类型、条件方向与层级不能只靠颜色表达；概念边界与正文定义一致；图内文字、公式、符号、变量、题注和相邻正文完全一致；整页与局部渲染均无重叠、裁切、溢出、过密、过大留白或异常断行
B02｜图 2.1｜FIG-P033-01
章节：第 2 章《线性代数基础》；PDF物理页：29
类型：几何/结构示意图；严重度：中
图源：src/绘图源码/第01册\_数学基础与统计学习基本理论/V1-C02/fig\_v1\_c02\_projection.tex
当前题注：图 2.1: 向量的正交分解。投影向量属于子空间，残差属于其正交补，虚线残差给出到子空间的最 短距离。
唯一读图结论：向量的正交分解。投影向量属于子空间，残差属于其正交补，虚线残差给出到子空间的最短距离。
当前问题：所在页存在低于7.5pt文字（最小约6.42pt）；所在页有4个字符低于8.5pt；题注偏长，图结论与使用说明混在同一题注中
本图专属修改方案：将图内正文、刻度、图例统一提升到源级至少9.5pt；PGFPlots设置tick label style={font=\small}, legend style={font=\small}，TikZ设置every node/.style={font=\small}；图宽优先提高到0.88--0.95\textwidth；不要通过\resizebox整体缩小文字；题注压缩为一条“读图结论”：向量的正交分解。投影向量属于子空间，残差属于其正交补，虚线残差给出到子空间的最短距离。；其余教学提示另起正文段落；保留原变量命名，并在图后加入一句“先看什么、再看什么、最终得到什么”的阅读顺序
建议图宽：>=0.72\textwidth（核心图）；按版心自适应
subagent1/subagent3复核重点：几何关系、角度、投影、邻接或空间归属必须准确，示意不能误导比例关系；图内文字、公式、符号、变量、题注和相邻正文完全一致；整页与局部渲染均无重叠、裁切、溢出、过密、过大留白或异常断行
B03｜图 3.1｜FIG-P049-01
章节：第 3 章《多元微积分与矩阵微分》；PDF物理页：50
类型：坐标/曲线图；严重度：中
图源：src/绘图源码/第01册\_数学基础与统计学习基本理论/V1-C03/fig\_v1\_c03\_gradient\_contour.tex
当前题注：图 3.1: 梯度与等值线。箭头在该点垂直于局部切线，并指向函数值增加的方向。
唯一读图结论：梯度与等值线。箭头在该点垂直于局部切线，并指向函数值增加的方向。
当前问题：所在页存在低于7.5pt文字（最小约6.42pt）；所在页有19个字符低于8.5pt
本图专属修改方案：将图内正文、刻度、图例统一提升到源级至少9.5pt；PGFPlots设置tick label style={font=\small}, legend style={font=\small}，TikZ设置every node/.style={font=\small}；图宽优先提高到0.88--0.95\textwidth；不要通过\resizebox整体缩小文字；固定axis宽高比例，减少刻度数量；用线型+点型双编码，标注只保留极值、阈值、最终点等关键对象；保留原变量命名，并在图后加入一句“先看什么、再看什么、最终得到什么”的阅读顺序
建议图宽：>=0.72\textwidth（核心图）；按版心自适应
subagent1/subagent3复核重点：坐标轴、刻度、单位、图例、曲线数据与正文公式一致；线型和点型可在灰度下区分；图内文字、公式、符号、变量、题注和相邻正文完全一致；整页与局部渲染均无重叠、裁切、溢出、过密、过大留白或异常断行
B04｜图 4.1｜FIG-P067-01
章节：第 4 章《概率论基础》；PDF物理页：72
类型：坐标/曲线图；严重度：中
图源：src/绘图源码/第01册\_数学基础与统计学习基本理论/V1-C04/fig\_v1\_c04\_cdf.tex
当前题注：图 4.1: 离散随机变量的分布函数：跳跃高度等于对应点的概率质量
唯一读图结论：离散随机变量的分布函数：跳跃高度等于对应点的概率质量
当前问题：所在页存在低于7.5pt文字（最小约6.42pt）；所在页有8个字符低于8.5pt
本图专属修改方案：将图内正文、刻度、图例统一提升到源级至少9.5pt；PGFPlots设置tick label style={font=\small}, legend style={font=\small}，TikZ设置every node/.style={font=\small}；图宽优先提高到0.88--0.95\textwidth；不要通过\resizebox整体缩小文字；固定axis宽高比例，减少刻度数量；用线型+点型双编码，标注只保留极值、阈值、最终点等关键对象；保留原变量命名，并在图后加入一句“先看什么、再看什么、最终得到什么”的阅读顺序
建议图宽：>=0.72\textwidth（核心图）；按版心自适应
subagent1/subagent3复核重点：坐标轴、刻度、单位、图例、曲线数据与正文公式一致；线型和点型可在灰度下区分；图内文字、公式、符号、变量、题注和相邻正文完全一致；整页与局部渲染均无重叠、裁切、溢出、过密、过大留白或异常断行
B05｜图 5.1｜FIG-P077-01
章节：第 5 章《常用分布与统计推断》；PDF物理页：84
类型：坐标/曲线图；严重度：中
图源：src/绘图源码/第01册\_数学基础与统计学习基本理论/V1-C05/fig\_v1\_c05\_gaussian.tex
当前题注：图 5.1: 方差增大使高斯密度变宽、峰值降低，但曲线下面积保持为 1
唯一读图结论：方差增大使高斯密度变宽、峰值降低，但曲线下面积保持为1
当前问题：所在页存在低于7.5pt文字（最小约6.42pt）；所在页有1个字符低于8.5pt；题注偏长，图结论与使用说明混在同一题注中
本图专属修改方案：将图内正文、刻度、图例统一提升到源级至少9.5pt；PGFPlots设置tick label style={font=\small}, legend style={font=\small}，TikZ设置every node/.style={font=\small}；图宽优先提高到0.88--0.95\textwidth；不要通过\resizebox整体缩小文字；固定axis宽高比例，减少刻度数量；用线型+点型双编码，标注只保留极值、阈值、最终点等关键对象；题注压缩为一条“读图结论”：方差增大使高斯密度变宽、峰值降低，但曲线下面积保持为1；其余教学提示另起正文段落；保留原变量命名，并在图后加入一句“先看什么、再看什么、最终得到什么”的阅读顺序
建议图宽：>=0.72\textwidth（核心图）；按版心自适应
subagent1/subagent3复核重点：坐标轴、刻度、单位、图例、曲线数据与正文公式一致；线型和点型可在灰度下区分；图内文字、公式、符号、变量、题注和相邻正文完全一致；整页与局部渲染均无重叠、裁切、溢出、过密、过大留白或异常断行
B06｜图 6.1｜FIG-P092-01
章节：第 6 章《信息论基础》；PDF物理页：101
类型：坐标/曲线图；严重度：中
图源：src/绘图源码/第01册\_数学基础与统计学习基本理论/V1-C06/fig\_v1\_c06\_binary\_entropy.tex
当前题注：图 6.1: 二元熵在 𝑝= 1/2 处达到 1 比特，在确定分布两端趋于 0
唯一读图结论：二元熵在$p=1/2$处达到1比特，在确定分布两端趋于0
当前问题：所在页存在低于7.5pt文字（最小约6.42pt）；所在页有2个字符低于8.5pt
本图专属修改方案：将图内正文、刻度、图例统一提升到源级至少9.5pt；PGFPlots设置tick label style={font=\small}, legend style={font=\small}，TikZ设置every node/.style={font=\small}；图宽优先提高到0.88--0.95\textwidth；不要通过\resizebox整体缩小文字；固定axis宽高比例，减少刻度数量；用线型+点型双编码，标注只保留极值、阈值、最终点等关键对象；保留原变量命名，并在图后加入一句“先看什么、再看什么、最终得到什么”的阅读顺序
建议图宽：>=0.72\textwidth（核心图）；按版心自适应
subagent1/subagent3复核重点：坐标轴、刻度、单位、图例、曲线数据与正文公式一致；线型和点型可在灰度下区分；图内文字、公式、符号、变量、题注和相邻正文完全一致；整页与局部渲染均无重叠、裁切、溢出、过密、过大留白或异常断行
B07｜图 7.1｜FIG-P109-01
章节：第 7 章《凸优化与拉格朗日对偶》；PDF物理页：123
类型：几何/结构示意图；严重度：无
图源：src/绘图源码/第01册\_数学基础与统计学习基本理论/V1-C07/fig\_v1\_c07\_convex\_set.tex
当前题注：图 7.1: 凸集中任意两点的线段仍位于可行域内
唯一读图结论：凸集中任意两点的线段仍位于可行域内
当前问题：未发现明显缺图、裁切、重叠或变量不一致；仍建议保留常规灰度与字号复核
本图专属修改方案：保留原变量命名，并在图后加入一句“先看什么、再看什么、最终得到什么”的阅读顺序
建议图宽：>=0.72\textwidth（核心图）；按版心自适应
subagent1/subagent3复核重点：几何关系、角度、投影、邻接或空间归属必须准确，示意不能误导比例关系；图内文字、公式、符号、变量、题注和相邻正文完全一致；整页与局部渲染均无重叠、裁切、溢出、过密、过大留白或异常断行
B08｜图 8.1｜FIG-P126-01
章节：第 8 章《数值优化方法》；PDF物理页：146
类型：坐标/曲线图；严重度：中
图源：src/绘图源码/第01册\_数学基础与统计学习基本理论/V1-C08/fig\_v1\_c08\_coordinate.tex
当前题注：图 8.1: 坐标下降的每个子步只改变一个坐标，因此轨迹沿轴向折线逼近最优点。
唯一读图结论：坐标下降的每个子步只改变一个坐标，因此轨迹沿轴向折线逼近最优点。
当前问题：所在页存在低于7.5pt文字（最小约6.42pt）；所在页有4个字符低于8.5pt；题注偏长，图结论与使用说明混在同一题注中
本图专属修改方案：将图内正文、刻度、图例统一提升到源级至少9.5pt；PGFPlots设置tick label style={font=\small}, legend style={font=\small}，TikZ设置every node/.style={font=\small}；图宽优先提高到0.88--0.95\textwidth；不要通过\resizebox整体缩小文字；固定axis宽高比例，减少刻度数量；用线型+点型双编码，标注只保留极值、阈值、最终点等关键对象；题注压缩为一条“读图结论”：坐标下降的每个子步只改变一个坐标，因此轨迹沿轴向折线逼近最优点。；其余教学提示另起正文段落；保留原变量命名，并在图后加入一句“先看什么、再看什么、最终得到什么”的阅读顺序
建议图宽：>=0.72\textwidth（核心图）；按版心自适应
subagent1/subagent3复核重点：坐标轴、刻度、单位、图例、曲线数据与正文公式一致；线型和点型可在灰度下区分；图内文字、公式、符号、变量、题注和相邻正文完全一致；整页与局部渲染均无重叠、裁切、溢出、过密、过大留白或异常断行
B09｜图 9.1｜FIG-P142-01
章节：第 9 章《统计学习的基本框架》；PDF物理页：162
类型：流程/网络图；严重度：中
图源：src/绘图源码/第01册\_数学基础与统计学习基本理论/V1-C09/fig\_v1\_c09\_learning\_loop.tex
当前题注：图 9.1: 统计学习从数据到模型再到新数据处理的基本闭环。反馈的形式由学习类型决定。
唯一读图结论：统计学习从数据到模型再到新数据处理的基本闭环。反馈的形式由学习类型决定。
当前问题：所在页存在低于7.5pt文字（最小约6.42pt）；所在页有3个字符低于8.5pt
本图专属修改方案：将图内正文、刻度、图例统一提升到源级至少9.5pt；PGFPlots设置tick label style={font=\small}, legend style={font=\small}，TikZ设置every node/.style={font=\small}；图宽优先提高到0.88--0.95\textwidth；不要通过\resizebox整体缩小文字；统一节点最小宽度、内边距与层级间距；箭头端点停在节点边界，避免穿过文字和交叉；保留原变量命名，并在图后加入一句“先看什么、再看什么、最终得到什么”的阅读顺序
建议图宽：>=0.72\textwidth（核心图）；按版心自适应
subagent1/subagent3复核重点：阅读方向唯一、节点层级清楚、箭头端点停在边界、无回折交叉与语义歧义；图内文字、公式、符号、变量、题注和相邻正文完全一致；整页与局部渲染均无重叠、裁切、溢出、过密、过大留白或异常断行
B10｜图 10.1｜FIG-P157-01
章节：第 10 章《模型评估、选择与泛化》；PDF物理页：181
类型：坐标/曲线图；严重度：无
图源：src/绘图源码/第01册\_数学基础与统计学习基本理论/V1-C10/fig\_v1\_c10\_complexity.tex
当前题注：图 10.1: 模型复杂度增加时训练误差通常下降，而验证误差可能先降后升。
唯一读图结论：模型复杂度增加时训练误差通常下降，而验证误差可能先降后升。
当前问题：未发现明显缺图、裁切、重叠或变量不一致；仍建议保留常规灰度与字号复核
本图专属修改方案：固定axis宽高比例，减少刻度数量；用线型+点型双编码，标注只保留极值、阈值、最终点等关键对象；保留原变量命名，并在图后加入一句“先看什么、再看什么、最终得到什么”的阅读顺序
建议图宽：>=0.72\textwidth（核心图）；按版心自适应
subagent1/subagent3复核重点：坐标轴、刻度、单位、图例、曲线数据与正文公式一致；线型和点型可在灰度下区分；图内文字、公式、符号、变量、题注和相邻正文完全一致；整页与局部渲染均无重叠、裁切、溢出、过密、过大留白或异常断行
B11｜图 11.1｜FIG-P172-01
章节：第 11 章《监督学习任务与应用》；PDF物理页：199
类型：流程/网络图；严重度：低
图源：src/绘图源码/第01册\_数学基础与统计学习基本理论/V1-C11/fig\_v1\_c11\_tagging.tex
当前题注：图 11.1: HMM 与线性链 CRF 都利用相邻标记关系，但箭头只用于 HMM 的生成方向； CRF 中的 无向线段表示给定观测后的局部因子。
唯一读图结论：HMM与线性链CRF都利用相邻标记关系，但箭头只用于HMM的生成方向；CRF中的无向线段表示给定观测后的局部因子。
当前问题：图内信息密度偏高；题注偏长，图结论与使用说明混在同一题注中
本图专属修改方案：把“定义/输入”和“计算/结论”拆为两幅子图，或按(a)(b)分面；每个面板只保留一个阅读任务；减少跨面板回折箭头，采用从左到右或从上到下的单向网格；长说明移到图后正文；统一节点最小宽度、内边距与层级间距；箭头端点停在节点边界，避免穿过文字和交叉；题注压缩为一条“读图结论”：HMM与线性链CRF都利用相邻标记关系，但箭头只用于HMM的生成方向；CRF中的无向线段表示给定观测后的局部因子。；其余教学提示另起正文段落；保留原变量命名，并在图后加入一句“先看什么、再看什么、最终得到什么”的阅读顺序
建议图宽：>=0.72\textwidth（核心图）；按版心自适应
subagent1/subagent3复核重点：阅读方向唯一、节点层级清楚、箭头端点停在边界、无回折交叉与语义歧义；图内文字、公式、符号、变量、题注和相邻正文完全一致；整页与局部渲染均无重叠、裁切、溢出、过密、过大留白或异常断行
B12｜图 12.1｜FIG-P186-01
章节：第 12 章《感知机》；PDF物理页：212
类型：坐标/曲线图；严重度：无
图源：src/绘图源码/第02册\_基础监督学习方法/V2-C01/fig\_v2\_c01\_separator.tex
当前题注：图 12.1: 超平面、法向量与两类样本的几何关系。法向量指向分数增大的半空间。
唯一读图结论：超平面、法向量与两类样本的几何关系。法向量指向分数增大的半空间。
当前问题：未发现明显缺图、裁切、重叠或变量不一致；仍建议保留常规灰度与字号复核
本图专属修改方案：固定axis宽高比例，减少刻度数量；用线型+点型双编码，标注只保留极值、阈值、最终点等关键对象；保留原变量命名，并在图后加入一句“先看什么、再看什么、最终得到什么”的阅读顺序
建议图宽：>=0.72\textwidth（核心图）；按版心自适应
subagent1/subagent3复核重点：坐标轴、刻度、单位、图例、曲线数据与正文公式一致；线型和点型可在灰度下区分；图内文字、公式、符号、变量、题注和相邻正文完全一致；整页与局部渲染均无重叠、裁切、溢出、过密、过大留白或异常断行
B13｜图 13.1｜FIG-P206-01
章节：第 13 章《法》；PDF物理页：236
类型：坐标/曲线图；严重度：中
图源：src/绘图源码/第02册\_基础监督学习方法/V2-C02/fig\_v2\_c02\_lp\_balls.tex
当前题注：图 13.1: 二维 𝐿𝑝单位球。不同边界形状会改变哪些训练点先进入查询邻域。
唯一读图结论：二维$L\_p$单位球。不同边界形状会改变哪些训练点先进入查询邻域。
当前问题：所在页存在低于7.5pt文字（最小约6.42pt）；所在页有2个字符低于8.5pt
本图专属修改方案：将图内正文、刻度、图例统一提升到源级至少9.5pt；PGFPlots设置tick label style={font=\small}, legend style={font=\small}，TikZ设置every node/.style={font=\small}；图宽优先提高到0.88--0.95\textwidth；不要通过\resizebox整体缩小文字；固定axis宽高比例，减少刻度数量；用线型+点型双编码，标注只保留极值、阈值、最终点等关键对象；保留原变量命名，并在图后加入一句“先看什么、再看什么、最终得到什么”的阅读顺序
建议图宽：>=0.72\textwidth（核心图）；按版心自适应
subagent1/subagent3复核重点：坐标轴、刻度、单位、图例、曲线数据与正文公式一致；线型和点型可在灰度下区分；图内文字、公式、符号、变量、题注和相邻正文完全一致；整页与局部渲染均无重叠、裁切、溢出、过密、过大留白或异常断行
B14｜图 13.2｜FIG-P210-01
章节：第 13 章《法》；PDF物理页：242
类型：几何/结构示意图；严重度：低
图源：src/绘图源码/第02册\_基础监督学习方法/V2-C02/fig\_v2\_c02\_kd\_tree.tex
当前题注：图 13.2: 六点示例的一棵平衡 kd 树。节点同时保存样本与本层切分轴。
唯一读图结论：六点示例的一棵平衡kd树。节点同时保存样本与本层切分轴。
当前问题：题注偏长，图结论与使用说明混在同一题注中
本图专属修改方案：题注压缩为一条“读图结论”：六点示例的一棵平衡kd树。节点同时保存样本与本层切分轴。；其余教学提示另起正文段落；保留原变量命名，并在图后加入一句“先看什么、再看什么、最终得到什么”的阅读顺序
建议图宽：>=0.72\textwidth（核心图）；按版心自适应
subagent1/subagent3复核重点：几何关系、角度、投影、邻接或空间归属必须准确，示意不能误导比例关系；图内文字、公式、符号、变量、题注和相邻正文完全一致；整页与局部渲染均无重叠、裁切、溢出、过密、过大留白或异常断行
B15｜图 14.1｜FIG-P222-01
章节：第 14 章《朴素贝叶斯法》；PDF物理页：255
类型：流程/网络图；严重度：中
图源：src/绘图源码/第02册\_基础监督学习方法/V2-C03/fig\_v2\_c03\_star.tex
当前题注：图 14.1: 朴素贝叶斯的条件依赖结构：给定 𝑌后，各特征节点相互独立
唯一读图结论：朴素贝叶斯的条件依赖结构：给定$Y$后，各特征节点相互独立
当前问题：所在页存在低于7.5pt文字（最小约6.42pt）；所在页有2个字符低于8.5pt
本图专属修改方案：将图内正文、刻度、图例统一提升到源级至少9.5pt；PGFPlots设置tick label style={font=\small}, legend style={font=\small}，TikZ设置every node/.style={font=\small}；图宽优先提高到0.88--0.95\textwidth；不要通过\resizebox整体缩小文字；统一节点最小宽度、内边距与层级间距；箭头端点停在节点边界，避免穿过文字和交叉；保留原变量命名，并在图后加入一句“先看什么、再看什么、最终得到什么”的阅读顺序
建议图宽：>=0.72\textwidth（核心图）；按版心自适应
subagent1/subagent3复核重点：阅读方向唯一、节点层级清楚、箭头端点停在边界、无回折交叉与语义歧义；图内文字、公式、符号、变量、题注和相邻正文完全一致；整页与局部渲染均无重叠、裁切、溢出、过密、过大留白或异常断行
B16｜图 15.1｜FIG-P242-01
章节：第 15 章《决策树》；PDF物理页：277
类型：坐标/曲线图；严重度：中
图源：src/绘图源码/第02册\_基础监督学习方法/V2-C04/fig\_v2\_c04\_tree\_partition.tex
当前题注：图 15.1: 决策树中的每条根到叶路径对应特征空间中的一个轴对齐区域。
唯一读图结论：决策树中的每条根到叶路径对应特征空间中的一个轴对齐区域。
当前问题：所在页存在低于7.5pt文字（最小约6.42pt）；所在页有5个字符低于8.5pt
本图专属修改方案：将图内正文、刻度、图例统一提升到源级至少9.5pt；PGFPlots设置tick label style={font=\small}, legend style={font=\small}，TikZ设置every node/.style={font=\small}；图宽优先提高到0.88--0.95\textwidth；不要通过\resizebox整体缩小文字；固定axis宽高比例，减少刻度数量；用线型+点型双编码，标注只保留极值、阈值、最终点等关键对象；保留原变量命名，并在图后加入一句“先看什么、再看什么、最终得到什么”的阅读顺序
建议图宽：>=0.72\textwidth（核心图）；按版心自适应
subagent1/subagent3复核重点：坐标轴、刻度、单位、图例、曲线数据与正文公式一致；线型和点型可在灰度下区分；图内文字、公式、符号、变量、题注和相邻正文完全一致；整页与局部渲染均无重叠、裁切、溢出、过密、过大留白或异常断行
B17｜图 16.1｜FIG-P262-01
章节：第 16 章《逻辑斯谛回归》；PDF物理页：303
类型：坐标/曲线图；严重度：中
图源：src/绘图源码/第02册\_基础监督学习方法/V2-C05/fig\_v2\_c05\_sigmoid.tex
当前题注：图 16.1: 逻辑斯谛函数把线性预测量映射为概率，并满足关于 (0, 1/2) 的中心对称性
唯一读图结论：逻辑斯谛函数把线性预测量映射为概率，并满足关于$(0,1/2)$的中心对称性
当前问题：所在页存在低于7.5pt文字（最小约6.07pt）；所在页有5个字符低于8.5pt
本图专属修改方案：将图内正文、刻度、图例统一提升到源级至少9.5pt；PGFPlots设置tick label style={font=\small}, legend style={font=\small}，TikZ设置every node/.style={font=\small}；图宽优先提高到0.88--0.95\textwidth；不要通过\resizebox整体缩小文字；固定axis宽高比例，减少刻度数量；用线型+点型双编码，标注只保留极值、阈值、最终点等关键对象；保留原变量命名，并在图后加入一句“先看什么、再看什么、最终得到什么”的阅读顺序
建议图宽：>=0.72\textwidth（核心图）；按版心自适应
subagent1/subagent3复核重点：坐标轴、刻度、单位、图例、曲线数据与正文公式一致；线型和点型可在灰度下区分；图内文字、公式、符号、变量、题注和相邻正文完全一致；整页与局部渲染均无重叠、裁切、溢出、过密、过大留白或异常断行
B18｜图 17.1｜FIG-P282-01
章节：第 17 章《最大熵模型》；PDF物理页：323
类型：坐标/曲线图；严重度：中
图源：src/绘图源码/第03册\_优化模型与序列模型/V3-C01/fig\_v3\_c01\_simplex.tex
当前题注：图 17.1: 概率单纯形上的熵等高线与线性约束；本例约束交点是唯一可行的最大熵点
唯一读图结论：概率单纯形、线性约束与最大熵可行点的示意
当前问题：所在页存在低于7.5pt文字（最小约6.69pt）；所在页有3个字符低于8.5pt
本图专属修改方案：将图内正文、刻度、图例统一提升到源级至少9.5pt；PGFPlots设置tick label style={font=\small}, legend style={font=\small}，TikZ设置every node/.style={font=\small}；图宽优先提高到0.88--0.95\textwidth；不要通过\resizebox整体缩小文字；固定axis宽高比例，减少刻度数量；用线型+点型双编码，标注只保留极值、阈值、最终点等关键对象；保留原变量命名，并在图后加入一句“先看什么、再看什么、最终得到什么”的阅读顺序
建议图宽：>=0.72\textwidth（核心图）；按版心自适应
subagent1/subagent3复核重点：坐标轴、刻度、单位、图例、曲线数据与正文公式一致；线型和点型可在灰度下区分；图内文字、公式、符号、变量、题注和相邻正文完全一致；整页与局部渲染均无重叠、裁切、溢出、过密、过大留白或异常断行
B19｜图 18.1｜FIG-P309-01
章节：第 18 章《支持向量机》；PDF物理页：358
类型：坐标/曲线图；严重度：中
图源：src/绘图源码/第03册\_优化模型与序列模型/V3-C02/fig\_v3\_c02\_margin.tex
当前题注：图 18.1: 分类超平面、两条间隔边界与几何间隔
唯一读图结论：分类超平面、两条间隔边界与几何间隔
当前问题：所在页存在低于7.5pt文字（最小约6.63pt）；所在页有2个字符低于8.5pt
本图专属修改方案：将图内正文、刻度、图例统一提升到源级至少9.5pt；PGFPlots设置tick label style={font=\small}, legend style={font=\small}，TikZ设置every node/.style={font=\small}；图宽优先提高到0.88--0.95\textwidth；不要通过\resizebox整体缩小文字；固定axis宽高比例，减少刻度数量；用线型+点型双编码，标注只保留极值、阈值、最终点等关键对象；保留原变量命名，并在图后加入一句“先看什么、再看什么、最终得到什么”的阅读顺序
建议图宽：>=0.72\textwidth（核心图）；按版心自适应
subagent1/subagent3复核重点：坐标轴、刻度、单位、图例、曲线数据与正文公式一致；线型和点型可在灰度下区分；图内文字、公式、符号、变量、题注和相邻正文完全一致；整页与局部渲染均无重叠、裁切、溢出、过密、过大留白或异常断行
B20｜图 19.1｜FIG-P324-01
章节：第 19 章《提升方法》；PDF物理页：374
类型：流程/网络图；严重度：中
图源：src/绘图源码/第03册\_优化模型与序列模型/V3-C03/fig\_v3\_c03\_adaboost\_loop.tex
当前题注：图 19.1: AdaBoost 中样本权重 𝐷𝑚决定下一轮训练重点，分类器权重 𝛼𝑚与弱分类器 𝐺𝑚直接进 入加法模型；两类权重位于不同计算支路。
唯一读图结论：AdaBoost中样本权重$D\_m$决定下一轮训练重点，分类器权重$\alpha\_m$与弱分类器$G\_m$直接进入加法模型；两类权重位于不同计算支路。
当前问题：所在页存在低于7.5pt文字（最小约6.14pt）；所在页有28个字符低于8.5pt；题注偏长，图结论与使用说明混在同一题注中
本图专属修改方案：将图内正文、刻度、图例统一提升到源级至少9.5pt；PGFPlots设置tick label style={font=\small}, legend style={font=\small}，TikZ设置every node/.style={font=\small}；图宽优先提高到0.88--0.95\textwidth；不要通过\resizebox整体缩小文字；统一节点最小宽度、内边距与层级间距；箭头端点停在节点边界，避免穿过文字和交叉；题注压缩为一条“读图结论”：AdaBoost中样本权重$D\_m$决定下一轮训练重点，分类器权重$\alpha\_m$与弱分类器$G\_m$直接进入加法模型；两类权重位于不同计算支路。；其余教学提示另起正文段落；保留原变量命名，并在图后加入一句“先看什么、再看什么、最终得到什么”的阅读顺序
建议图宽：>=0.72\textwidth（核心图）；按版心自适应
subagent1/subagent3复核重点：阅读方向唯一、节点层级清楚、箭头端点停在边界、无回折交叉与语义歧义；图内文字、公式、符号、变量、题注和相邻正文完全一致；整页与局部渲染均无重叠、裁切、溢出、过密、过大留白或异常断行
B21｜图 20.1｜FIG-P346-01
章节：第 20 章《EM算法及其推广》；PDF物理页：406
类型：坐标/曲线图；严重度：低
图源：src/绘图源码/第03册\_优化模型与序列模型/V3-C04/fig\_v3\_c04\_bound.tex
当前题注：图 20.1: 可复算的相切下界：𝐵(𝜃, 2) = ℓ(𝜃) −0.16(𝜃−2)2 ≤ℓ(𝜃)，并在 𝜃= 2 处函数值与导数同 时相等。两条曲线按图中给定的显式函数精确绘制，而非未标比例的定性示意。
唯一读图结论：可复算的相切下界：$B(\theta,2)=\ell(\theta)-0.16(\theta-2)^2\le\ell(\theta)$，并在$\theta=2$处函数值与导数同时相等。两条曲线按图中给定的显式函数精确绘制，而非未标比例的定性示意。
当前问题：题注偏长，图结论与使用说明混在同一题注中
本图专属修改方案：固定axis宽高比例，减少刻度数量；用线型+点型双编码，标注只保留极值、阈值、最终点等关键对象；题注压缩为一条“读图结论”：可复算的相切下界：$B(\theta,2)=\ell(\theta)-0.16(\theta-2)^2\le\ell(\theta)$，并在$\theta=2$处函数值与导数同时相等。两条曲线按图中给定的显式函数精确绘制，而非未标比例的定性示意。；其余教学提示另起正文段落；保留原变量命名，并在图后加入一句“先看什么、再看什么、最终得到什么”的阅读顺序
建议图宽：>=0.72\textwidth（核心图）；按版心自适应
subagent1/subagent3复核重点：坐标轴、刻度、单位、图例、曲线数据与正文公式一致；线型和点型可在灰度下区分；图内文字、公式、符号、变量、题注和相邻正文完全一致；整页与局部渲染均无重叠、裁切、溢出、过密、过大留白或异常断行
B22｜图 21.1｜FIG-P372-01
章节：第 21 章《隐马尔可夫模型》；PDF物理页：443
类型：概念关系图；严重度：中
图源：src/绘图源码/第03册\_优化模型与序列模型/V3-C05/fig\_v3\_c05\_lattice.tex
当前题注：图 21.1: HMM 状态格的三种读法：前向与后向对共享路径求和， Viterbi 只保存获胜前驱
唯一读图结论：HMM状态格：前向/后向对路径求和，Viterbi保留最大概率前驱
当前问题：所在页存在低于7.5pt文字（最小约6.42pt）；所在页有27个字符低于8.5pt；逐图视觉复核显示可读性仍可提升
本图专属修改方案：将图内正文、刻度、图例统一提升到源级至少9.5pt；PGFPlots设置tick label style={font=\small}, legend style={font=\small}，TikZ设置every node/.style={font=\small}；图宽优先提高到0.88--0.95\textwidth；不要通过\resizebox整体缩小文字；统一节点最小宽度、内边距与层级间距；箭头端点停在节点边界，避免穿过文字和交叉；保留原变量命名，并在图后加入一句“先看什么、再看什么、最终得到什么”的阅读顺序
建议图宽：>=0.72\textwidth（核心图）；按版心自适应
subagent1/subagent3复核重点：关系类型、条件方向与层级不能只靠颜色表达；概念边界与正文定义一致；图内文字、公式、符号、变量、题注和相邻正文完全一致；整页与局部渲染均无重叠、裁切、溢出、过密、过大留白或异常断行
B23｜图 22.1｜FIG-P392-01
章节：第 22 章《条件随机场》；PDF物理页：468
类型：流程/网络图；严重度：中
图源：src/绘图源码/第03册\_优化模型与序列模型/V3-C06/fig\_v3\_c06\_chain.tex
当前题注：图 22.1: 线性链 CRF 的边界状态、相邻标签因子与已知观测依赖
唯一读图结论：线性链条件随机场的局部结构。灰色观测在条件分布中视为已知，白色标签构成链。
当前问题：所在页存在低于7.5pt文字（最小约6.42pt）；所在页有12个字符低于8.5pt；逐图视觉复核显示可读性仍可提升
本图专属修改方案：将图内正文、刻度、图例统一提升到源级至少9.5pt；PGFPlots设置tick label style={font=\small}, legend style={font=\small}，TikZ设置every node/.style={font=\small}；图宽优先提高到0.88--0.95\textwidth；不要通过\resizebox整体缩小文字；统一节点最小宽度、内边距与层级间距；箭头端点停在节点边界，避免穿过文字和交叉；保留原变量命名，并在图后加入一句“先看什么、再看什么、最终得到什么”的阅读顺序
建议图宽：>=0.72\textwidth（核心图）；按版心自适应
subagent1/subagent3复核重点：阅读方向唯一、节点层级清楚、箭头端点停在边界、无回折交叉与语义歧义；图内文字、公式、符号、变量、题注和相邻正文完全一致；整页与局部渲染均无重叠、裁切、溢出、过密、过大留白或异常断行
B24｜图 23.1｜FIG-P412-01
章节：第 23 章《监督学习方法总结》；PDF物理页：492
类型：流程/网络图；严重度：无
图源：src/绘图源码/第03册\_优化模型与序列模型/V3-C07/fig\_v3\_c07\_selection\_loop.tex
当前题注：图 23.1: 监督学习方法选择闭环。测试集不进入返回候选模型族的反馈回路。
唯一读图结论：监督学习方法选择闭环。测试集不进入返回候选模型族的反馈回路。
当前问题：未发现明显缺图、裁切、重叠或变量不一致；仍建议保留常规灰度与字号复核
本图专属修改方案：统一节点最小宽度、内边距与层级间距；箭头端点停在节点边界，避免穿过文字和交叉；保留原变量命名，并在图后加入一句“先看什么、再看什么、最终得到什么”的阅读顺序
建议图宽：>=0.72\textwidth（核心图）；按版心自适应
subagent1/subagent3复核重点：阅读方向唯一、节点层级清楚、箭头端点停在边界、无回折交叉与语义歧义；图内文字、公式、符号、变量、题注和相邻正文完全一致；整页与局部渲染均无重叠、裁切、溢出、过密、过大留白或异常断行
B25｜图 24.1｜FIG-P429-01
章节：第 24 章《无监督学习概论》；PDF物理页：509
类型：流程/网络图；严重度：低
图源：src/绘图源码/第04册\_无监督学习与矩阵分解/V4-C01/fig\_v4\_c01\_three\_structures.tex
当前题注：图 24.1: 聚类、降维和概率建模分别从样本分组、属性压缩和联合生成三个方向把观测映射为可检 验的潜在结构。
唯一读图结论：聚类、降维和概率建模分别从样本分组、属性压缩和联合生成三个方向把观测映射为可检验的潜在结构。
当前问题：题注偏长，图结论与使用说明混在同一题注中
本图专属修改方案：统一节点最小宽度、内边距与层级间距；箭头端点停在节点边界，避免穿过文字和交叉；题注压缩为一条“读图结论”：聚类、降维和概率建模分别从样本分组、属性压缩和联合生成三个方向把观测映射为可检验的潜在结构。；其余教学提示另起正文段落；保留原变量命名，并在图后加入一句“先看什么、再看什么、最终得到什么”的阅读顺序
建议图宽：>=0.72\textwidth（核心图）；按版心自适应
subagent1/subagent3复核重点：阅读方向唯一、节点层级清楚、箭头端点停在边界、无回折交叉与语义歧义；图内文字、公式、符号、变量、题注和相邻正文完全一致；整页与局部渲染均无重叠、裁切、溢出、过密、过大留白或异常断行
B26｜图 25.1｜FIG-P445-01
章节：第 25 章《聚类方法》；PDF物理页：529
类型：概念关系图；严重度：中
图源：src/绘图源码/第04册\_无监督学习与矩阵分解/V4-C02/fig\_v4\_c02\_dendrogram.tex
当前题注：图 25.1: 树的纵坐标表示合并高度；在虚线高度切割时，虚线以下的连通分支分别成为一个类。
唯一读图结论：树的纵坐标表示合并高度；在虚线高度切割时，虚线以下的连通分支分别成为一个类。
当前问题：所在页存在低于7.5pt文字（最小约6.42pt）；所在页有9个字符低于8.5pt
本图专属修改方案：将图内正文、刻度、图例统一提升到源级至少9.5pt；PGFPlots设置tick label style={font=\small}, legend style={font=\small}，TikZ设置every node/.style={font=\small}；图宽优先提高到0.88--0.95\textwidth；不要通过\resizebox整体缩小文字；统一节点最小宽度、内边距与层级间距；箭头端点停在节点边界，避免穿过文字和交叉；保留原变量命名，并在图后加入一句“先看什么、再看什么、最终得到什么”的阅读顺序
建议图宽：>=0.72\textwidth（核心图）；按版心自适应
subagent1/subagent3复核重点：关系类型、条件方向与层级不能只靠颜色表达；概念边界与正文定义一致；图内文字、公式、符号、变量、题注和相邻正文完全一致；整页与局部渲染均无重叠、裁切、溢出、过密、过大留白或异常断行
B27｜图 26.1｜FIG-P467-01
章节：第 26 章《奇异值分解》；PDF物理页：557
类型：坐标/曲线图；严重度：低
图源：src/绘图源码/第04册\_无监督学习与矩阵分解/V4-C03/fig\_v4\_c03\_svd\_geometry.tex
当前题注：图 26.1: SVD 把线性变换分成正交变换、轴向缩放和正交变换
唯一读图结论：SVD把线性变换分成正交变换、轴向缩放和正交变换
当前问题：图内信息密度偏高
本图专属修改方案：把“定义/输入”和“计算/结论”拆为两幅子图，或按(a)(b)分面；每个面板只保留一个阅读任务；减少跨面板回折箭头，采用从左到右或从上到下的单向网格；长说明移到图后正文；固定axis宽高比例，减少刻度数量；用线型+点型双编码，标注只保留极值、阈值、最终点等关键对象；保留原变量命名，并在图后加入一句“先看什么、再看什么、最终得到什么”的阅读顺序
建议图宽：>=0.72\textwidth（核心图）；按版心自适应
subagent1/subagent3复核重点：坐标轴、刻度、单位、图例、曲线数据与正文公式一致；线型和点型可在灰度下区分；图内文字、公式、符号、变量、题注和相邻正文完全一致；整页与局部渲染均无重叠、裁切、溢出、过密、过大留白或异常断行
B28｜图 27.1｜FIG-P482-01
章节：第 27 章《主成分分析》；PDF物理页：575
类型：坐标/曲线图；严重度：无
图源：src/绘图源码/第04册\_无监督学习与矩阵分解/V4-C04/fig\_v4\_c04\_ellipse.tex
当前题注：图 27.1: 二维协方差椭圆与主轴示意
唯一读图结论：二维协方差椭圆与主轴示意
当前问题：未发现明显缺图、裁切、重叠或变量不一致；仍建议保留常规灰度与字号复核
本图专属修改方案：固定axis宽高比例，减少刻度数量；用线型+点型双编码，标注只保留极值、阈值、最终点等关键对象；保留原变量命名，并在图后加入一句“先看什么、再看什么、最终得到什么”的阅读顺序
建议图宽：>=0.72\textwidth（核心图）；按版心自适应
subagent1/subagent3复核重点：坐标轴、刻度、单位、图例、曲线数据与正文公式一致；线型和点型可在灰度下区分；图内文字、公式、符号、变量、题注和相邻正文完全一致；整页与局部渲染均无重叠、裁切、溢出、过密、过大留白或异常断行
B29｜图 28.1｜FIG-P504-01
章节：第 28 章《潜在语义分析与非负矩阵分解》；PDF物理页：601
类型：概念关系图；严重度：中
图源：src/绘图源码/第04册\_无监督学习与矩阵分解/V4-C05/fig\_v4\_c05\_two\_geometries.tex
当前题注：图 28.1: LSA 的正交子空间表示与 NMF 的非负锥表示：二者维数相同，坐标约束和最优性不同
唯一读图结论：LSA的正交子空间表示与NMF的非负锥表示：二者维数相同，坐标约束和最优性不同
当前问题：所在页存在低于7.5pt文字（最小约6.42pt）；所在页有11个字符低于8.5pt；题注偏长，图结论与使用说明混在同一题注中
本图专属修改方案：将图内正文、刻度、图例统一提升到源级至少9.5pt；PGFPlots设置tick label style={font=\small}, legend style={font=\small}，TikZ设置every node/.style={font=\small}；图宽优先提高到0.88--0.95\textwidth；不要通过\resizebox整体缩小文字；统一节点最小宽度、内边距与层级间距；箭头端点停在节点边界，避免穿过文字和交叉；题注压缩为一条“读图结论”：LSA的正交子空间表示与NMF的非负锥表示：二者维数相同，坐标约束和最优性不同；其余教学提示另起正文段落；保留原变量命名，并在图后加入一句“先看什么、再看什么、最终得到什么”的阅读顺序
建议图宽：>=0.72\textwidth（核心图）；按版心自适应
subagent1/subagent3复核重点：关系类型、条件方向与层级不能只靠颜色表达；概念边界与正文定义一致；图内文字、公式、符号、变量、题注和相邻正文完全一致；整页与局部渲染均无重叠、裁切、溢出、过密、过大留白或异常断行
B30｜图 29.1｜FIG-P521-01
章节：第 29 章《概率潜在语义分析》；PDF物理页：620
类型：流程/网络图；严重度：中
图源：src/绘图源码/第04册\_无监督学习与矩阵分解/V4-C06/fig\_v4\_c06\_plsa\_dag.tex
当前题注：图 29.1: PLSA 生成图：文档决定主题混合，主题决定单词分布；给定主题后单词与文档条件独立
唯一读图结论：PLSA生成图：文档决定主题混合，主题决定单词分布；给定主题后单词与文档条件独立
当前问题：所在页存在低于7.5pt文字（最小约6.14pt）；所在页有3个字符低于8.5pt；题注偏长，图结论与使用说明混在同一题注中
本图专属修改方案：将图内正文、刻度、图例统一提升到源级至少9.5pt；PGFPlots设置tick label style={font=\small}, legend style={font=\small}，TikZ设置every node/.style={font=\small}；图宽优先提高到0.88--0.95\textwidth；不要通过\resizebox整体缩小文字；统一节点最小宽度、内边距与层级间距；箭头端点停在节点边界，避免穿过文字和交叉；题注压缩为一条“读图结论”：PLSA生成图：文档决定主题混合，主题决定单词分布；给定主题后单词与文档条件独立；其余教学提示另起正文段落；保留原变量命名，并在图后加入一句“先看什么、再看什么、最终得到什么”的阅读顺序
建议图宽：>=0.72\textwidth（核心图）；按版心自适应
subagent1/subagent3复核重点：阅读方向唯一、节点层级清楚、箭头端点停在边界、无回折交叉与语义歧义；图内文字、公式、符号、变量、题注和相邻正文完全一致；整页与局部渲染均无重叠、裁切、溢出、过密、过大留白或异常断行
B31｜图 29.2｜FIG-P525-01
章节：第 29 章《概率潜在语义分析》；PDF物理页：625
类型：流程/网络图；严重度：中
图源：src/绘图源码/第04册\_无监督学习与矩阵分解/V4-C06/fig\_v4\_c06\_simplex.tex
当前题注：图 29.2: 三个单词维度中的主题单纯形：文档分布是主题点按 𝜃∶𝑗形成的凸组合
唯一读图结论：三个单词维度中的主题单纯形：文档分布是主题点按$\theta\_{}$形成的凸组合
当前问题：所在页存在低于7.5pt文字（最小约6.14pt）；所在页有1个字符低于8.5pt
本图专属修改方案：将图内正文、刻度、图例统一提升到源级至少9.5pt；PGFPlots设置tick label style={font=\small}, legend style={font=\small}，TikZ设置every node/.style={font=\small}；图宽优先提高到0.88--0.95\textwidth；不要通过\resizebox整体缩小文字；统一节点最小宽度、内边距与层级间距；箭头端点停在节点边界，避免穿过文字和交叉；保留原变量命名，并在图后加入一句“先看什么、再看什么、最终得到什么”的阅读顺序
建议图宽：>=0.72\textwidth（核心图）；按版心自适应
subagent1/subagent3复核重点：阅读方向唯一、节点层级清楚、箭头端点停在边界、无回折交叉与语义歧义；图内文字、公式、符号、变量、题注和相邻正文完全一致；整页与局部渲染均无重叠、裁切、溢出、过密、过大留白或异常断行
B32｜图 30.1｜FIG-P544-01
章节：第 30 章《马尔可夫链基础》；PDF物理页：642
类型：概念关系图；严重度：低
图源：src/绘图源码/第05册\_采样方法主题模型与图排序/V5-C01/fig\_v5\_c01\_dependency\_graph.tex
当前题注：图 30.1: 本章概念依赖：从马尔可夫性质和转移规则出发，分别经平稳固定点与结构条件到达长期 结论；可逆性只提供通向平稳性的充分条件
唯一读图结论：本章概念依赖：从马尔可夫性质和转移规则出发，分别经平稳固定点与结构条件到达长期结论；可逆性只提供通向平稳性的充分条件
当前问题：题注偏长，图结论与使用说明混在同一题注中
本图专属修改方案：统一节点最小宽度、内边距与层级间距；箭头端点停在节点边界，避免穿过文字和交叉；题注压缩为一条“读图结论”：本章概念依赖：从马尔可夫性质和转移规则出发，分别经平稳固定点与结构条件到达长期结论；可逆性只提供通向平稳性的充分条件；其余教学提示另起正文段落；保留原变量命名，并在图后加入一句“先看什么、再看什么、最终得到什么”的阅读顺序
建议图宽：>=0.72\textwidth（核心图）；按版心自适应
subagent1/subagent3复核重点：关系类型、条件方向与层级不能只靠颜色表达；概念边界与正文定义一致；图内文字、公式、符号、变量、题注和相邻正文完全一致；整页与局部渲染均无重叠、裁切、溢出、过密、过大留白或异常断行
B33｜图 30.2｜FIG-P547-01
章节：第 30 章《马尔可夫链基础》；PDF物理页：645
类型：流程/网络图；严重度：高
图源：src/绘图源码/第05册\_采样方法主题模型与图排序/V5-C01/fig\_v5\_c01\_transition\_graph.tex
当前题注：图 30.2: 行随机约定下的两状态转移图，并给出到列随机 PageRank 约定的显式转置桥。
唯一读图结论：行随机约定下的两状态转移图，并给出到列随机PageRank约定的显式转置桥。
当前问题：所在页存在低于7.5pt文字（最小约6.14pt）；所在页小于8.5pt字符较多（37个）；题注偏长，图结论与使用说明混在同一题注中；逐图视觉复核显示可读性仍可提升
本图专属修改方案：将图内正文、刻度、图例统一提升到源级至少9.5pt；PGFPlots设置tick label style={font=\small}, legend style={font=\small}，TikZ设置every node/.style={font=\small}；图宽优先提高到0.88--0.95\textwidth；不要通过\resizebox整体缩小文字；统一节点最小宽度、内边距与层级间距；箭头端点停在节点边界，避免穿过文字和交叉；题注压缩为一条“读图结论”：行随机约定下的两状态转移图，并给出到列随机PageRank约定的显式转置桥。；其余教学提示另起正文段落；保留原变量命名，并在图后加入一句“先看什么、再看什么、最终得到什么”的阅读顺序
建议图宽：>=0.72\textwidth（核心图）；按版心自适应
subagent1/subagent3复核重点：阅读方向唯一、节点层级清楚、箭头端点停在边界、无回折交叉与语义歧义；图内文字、公式、符号、变量、题注和相邻正文完全一致；整页与局部渲染均无重叠、裁切、溢出、过密、过大留白或异常断行；必须评估拆图或重构，不得仅靠放大画布和整体缩放掩盖结构问题
B34｜图 30.3｜FIG-P552-01
章节：第 30 章《马尔可夫链基础》；PDF物理页：651
类型：流程/网络图；严重度：低
图源：src/绘图源码/第05册\_采样方法主题模型与图排序/V5-C01/fig\_v5\_c01\_return\_time.tex
当前题注：图 30.3: 首次到达与首次正回返的区分：正常返考察从 𝑖出发的 𝔼𝑖[𝜏+ 𝑖]，而不是某个固定时刻首次 到达的概率
唯一读图结论：两状态概率单纯形上的平稳固定点：映射$r\mapsto0.2+0.5r$把任意初值逐步拉向$r\_\star=0.4$
当前问题：题注偏长，图结论与使用说明混在同一题注中
本图专属修改方案：统一节点最小宽度、内边距与层级间距；箭头端点停在节点边界，避免穿过文字和交叉；题注压缩为一条“读图结论”：两状态概率单纯形上的平稳固定点：映射$r\mapsto0.2+0.5r$把任意初值逐步拉向$r\_\star=0.4$；其余教学提示另起正文段落；保留原变量命名，并在图后加入一句“先看什么、再看什么、最终得到什么”的阅读顺序
建议图宽：>=0.72\textwidth（核心图）；按版心自适应
subagent1/subagent3复核重点：阅读方向唯一、节点层级清楚、箭头端点停在边界、无回折交叉与语义歧义；图内文字、公式、符号、变量、题注和相邻正文完全一致；整页与局部渲染均无重叠、裁切、溢出、过密、过大留白或异常断行
B35｜图 30.4｜FIG-P556-01
章节：第 30 章《马尔可夫链基础》；PDF物理页：656
类型：坐标/曲线图；严重度：低
图源：src/绘图源码/第05册\_采样方法主题模型与图排序/V5-C01/fig\_v5\_c01\_stationary\_fixed\_point.tex
当前题注：图 30.4: 两状态概率单纯形上的平稳固定点：映射 𝑟↦0.2 + 0.5𝑟把任意初值逐步拉向 𝑟⋆= 0.4
唯一读图结论：三类结构必须分别判断：支撑图连通性决定不可约性，正回返时长的最大公约数决定周期性
当前问题：题注偏长，图结论与使用说明混在同一题注中
本图专属修改方案：固定axis宽高比例，减少刻度数量；用线型+点型双编码，标注只保留极值、阈值、最终点等关键对象；题注压缩为一条“读图结论”：三类结构必须分别判断：支撑图连通性决定不可约性，正回返时长的最大公约数决定周期性；其余教学提示另起正文段落；保留原变量命名，并在图后加入一句“先看什么、再看什么、最终得到什么”的阅读顺序
建议图宽：>=0.72\textwidth（核心图）；按版心自适应
subagent1/subagent3复核重点：坐标轴、刻度、单位、图例、曲线数据与正文公式一致；线型和点型可在灰度下区分；图内文字、公式、符号、变量、题注和相邻正文完全一致；整页与局部渲染均无重叠、裁切、溢出、过密、过大留白或异常断行
B36｜图 30.5｜FIG-P556-02
章节：第 30 章《马尔可夫链基础》；PDF物理页：657
类型：流程/网络图；严重度：中
图源：src/绘图源码/第05册\_采样方法主题模型与图排序/V5-C01/fig\_v5\_c01\_chain\_properties.tex
当前题注：图 30.5: 三类结构必须分别判断：支撑图连通性决定不可约性，正回返时长的最大公约数决定周 期性
唯一读图结论：首次到达与首次正回返的区分：正常返考察从$i$出发的$\mathbb E\_i[\tau\_i^+]$，而不是某个固定时刻首次到达的概率
当前问题：所在页存在低于7.5pt文字（最小约6.42pt）；所在页有15个字符低于8.5pt；逐图视觉复核显示可读性仍可提升
本图专属修改方案：将图内正文、刻度、图例统一提升到源级至少9.5pt；PGFPlots设置tick label style={font=\small}, legend style={font=\small}，TikZ设置every node/.style={font=\small}；图宽优先提高到0.88--0.95\textwidth；不要通过\resizebox整体缩小文字；统一节点最小宽度、内边距与层级间距；箭头端点停在节点边界，避免穿过文字和交叉；保留原变量命名，并在图后加入一句“先看什么、再看什么、最终得到什么”的阅读顺序
建议图宽：>=0.72\textwidth（核心图）；按版心自适应
subagent1/subagent3复核重点：阅读方向唯一、节点层级清楚、箭头端点停在边界、无回折交叉与语义歧义；图内文字、公式、符号、变量、题注和相邻正文完全一致；整页与局部渲染均无重叠、裁切、溢出、过密、过大留白或异常断行
B37｜图 30.6｜FIG-P556-03
章节：第 30 章《马尔可夫链基础》；PDF物理页：658
类型：流程/网络图；严重度：中
图源：src/绘图源码/第05册\_采样方法主题模型与图排序/V5-C01/fig\_v5\_c01\_detailed\_balance\_counterexample.tex
当前题注：图 30.6: 流量对称可证平稳，却不能证连通或唯一
唯一读图结论：流量对称可证平稳，却不能证连通或唯一
当前问题：所在页存在低于7.5pt文字（最小约6.14pt）；所在页有1个字符低于8.5pt
本图专属修改方案：将图内正文、刻度、图例统一提升到源级至少9.5pt；PGFPlots设置tick label style={font=\small}, legend style={font=\small}，TikZ设置every node/.style={font=\small}；图宽优先提高到0.88--0.95\textwidth；不要通过\resizebox整体缩小文字；统一节点最小宽度、内边距与层级间距；箭头端点停在节点边界，避免穿过文字和交叉；保留原变量命名，并在图后加入一句“先看什么、再看什么、最终得到什么”的阅读顺序
建议图宽：>=0.72\textwidth（核心图）；按版心自适应
subagent1/subagent3复核重点：阅读方向唯一、节点层级清楚、箭头端点停在边界、无回折交叉与语义歧义；图内文字、公式、符号、变量、题注和相邻正文完全一致；整页与局部渲染均无重叠、裁切、溢出、过密、过大留白或异常断行
B38｜图 30.7｜FIG-P558-01
章节：第 30 章《马尔可夫链基础》；PDF物理页：660
类型：坐标/曲线图；严重度：中
图源：src/绘图源码/第05册\_采样方法主题模型与图排序/V5-C01/fig\_v5\_c01\_random\_walk.tex
当前题注：图 30.7: 三节点路径的简单游走与惰性游走：加入自环保持平稳分布并消除周期振荡
唯一读图结论：三节点路径的简单游走与惰性游走：加入自环保持平稳分布并消除周期振荡
当前问题：所在页存在低于7.5pt文字（最小约6.42pt）；所在页有2个字符低于8.5pt；图内信息密度偏高；题注偏长，图结论与使用说明混在同一题注中
本图专属修改方案：将图内正文、刻度、图例统一提升到源级至少9.5pt；PGFPlots设置tick label style={font=\small}, legend style={font=\small}，TikZ设置every node/.style={font=\small}；图宽优先提高到0.88--0.95\textwidth；不要通过\resizebox整体缩小文字；把“定义/输入”和“计算/结论”拆为两幅子图，或按(a)(b)分面；每个面板只保留一个阅读任务；减少跨面板回折箭头，采用从左到右或从上到下的单向网格；长说明移到图后正文；固定axis宽高比例，减少刻度数量；用线型+点型双编码，标注只保留极值、阈值、最终点等关键对象；题注压缩为一条“读图结论”：三节点路径的简单游走与惰性游走：加入自环保持平稳分布并消除周期振荡；其余教学提示另起正文段落；保留原变量命名，并在图后加入一句“先看什么、再看什么、最终得到什么”的阅读顺序
建议图宽：>=0.72\textwidth（核心图）；按版心自适应
subagent1/subagent3复核重点：坐标轴、刻度、单位、图例、曲线数据与正文公式一致；线型和点型可在灰度下区分；图内文字、公式、符号、变量、题注和相邻正文完全一致；整页与局部渲染均无重叠、裁切、溢出、过密、过大留白或异常断行
B39｜图 31.1｜FIG-P570-01
章节：第 31 章《蒙特卡罗方法与直接采样》；PDF物理页：673
类型：流程/网络图；严重度：低
图源：src/绘图源码/第05册\_采样方法主题模型与图排序/V5-C02/fig\_v5\_c02\_dependency\_graph.tex
当前题注：图 31.1: 本章知识依赖：由期望、积分与独立抽样进入蒙特卡罗估计，再分别学习三种直接采样或 重加权方法，最后统一进行误差和支持诊断
唯一读图结论：本章知识依赖：由期望、积分与独立抽样进入蒙特卡罗估计，再分别学习三种直接采样或重加权方法，最后统一进行误差和支持诊断
当前问题：题注偏长，图结论与使用说明混在同一题注中
本图专属修改方案：统一节点最小宽度、内边距与层级间距；箭头端点停在节点边界，避免穿过文字和交叉；题注压缩为一条“读图结论”：本章知识依赖：由期望、积分与独立抽样进入蒙特卡罗估计，再分别学习三种直接采样或重加权方法，最后统一进行误差和支持诊断；其余教学提示另起正文段落；保留原变量命名，并在图后加入一句“先看什么、再看什么、最终得到什么”的阅读顺序
建议图宽：>=0.72\textwidth（核心图）；按版心自适应
subagent1/subagent3复核重点：阅读方向唯一、节点层级清楚、箭头端点停在边界、无回折交叉与语义歧义；图内文字、公式、符号、变量、题注和相邻正文完全一致；整页与局部渲染均无重叠、裁切、溢出、过密、过大留白或异常断行
B40｜图 31.2｜FIG-P573-01
章节：第 31 章《蒙特卡罗方法与直接采样》；PDF物理页：676
类型：坐标/曲线图；严重度：低
图源：src/绘图源码/第05册\_采样方法主题模型与图排序/V5-C02/fig\_v5\_c02\_mc\_integral.tex
当前题注：图 31.2: 蒙特卡罗积分把曲线下的面积改写为分布下的期望；竖线表示固定的四个均匀样本，虚线 表示该积分的参考值
唯一读图结论：蒙特卡罗积分把曲线下的面积改写为分布下的期望；竖线表示固定的四个均匀样本，虚线表示该积分的参考值
当前问题：题注偏长，图结论与使用说明混在同一题注中
本图专属修改方案：固定axis宽高比例，减少刻度数量；用线型+点型双编码，标注只保留极值、阈值、最终点等关键对象；题注压缩为一条“读图结论”：蒙特卡罗积分把曲线下的面积改写为分布下的期望；竖线表示固定的四个均匀样本，虚线表示该积分的参考值；其余教学提示另起正文段落；保留原变量命名，并在图后加入一句“先看什么、再看什么、最终得到什么”的阅读顺序
建议图宽：>=0.72\textwidth（核心图）；按版心自适应
subagent1/subagent3复核重点：坐标轴、刻度、单位、图例、曲线数据与正文公式一致；线型和点型可在灰度下区分；图内文字、公式、符号、变量、题注和相邻正文完全一致；整页与局部渲染均无重叠、裁切、溢出、过密、过大留白或异常断行
B41｜图 31.3｜FIG-P575-01
章节：第 31 章《蒙特卡罗方法与直接采样》；PDF物理页：680
类型：坐标/曲线图；严重度：低
图源：src/绘图源码/第05册\_采样方法主题模型与图排序/V5-C02/fig\_v5\_c02\_generalized\_inverse.tex
当前题注：图 31.3: 广义逆采用首次达到规则：连续情形沿水平线找到交点；离散情形中 𝑢= 0.7 落在第二个 跳点，而 𝑢= 0.72 落在第三个跳点
唯一读图结论：固定样本序列 $0.8,0.1,0.7,0.4$ 下 $U\_i^2$ 的运行均值；曲线先降后升再下降，说明收敛结论不等于逐步单调逼近
当前问题：题注偏长，图结论与使用说明混在同一题注中
本图专属修改方案：固定axis宽高比例，减少刻度数量；用线型+点型双编码，标注只保留极值、阈值、最终点等关键对象；题注压缩为一条“读图结论”：固定样本序列 $0.8,0.1,0.7,0.4$ 下 $U\_i^2$ 的运行均值；曲线先降后升再下降，说明收敛结论不等于逐步单调逼近；其余教学提示另起正文段落；保留原变量命名，并在图后加入一句“先看什么、再看什么、最终得到什么”的阅读顺序
建议图宽：>=0.72\textwidth（核心图）；按版心自适应
subagent1/subagent3复核重点：坐标轴、刻度、单位、图例、曲线数据与正文公式一致；线型和点型可在灰度下区分；图内文字、公式、符号、变量、题注和相邻正文完全一致；整页与局部渲染均无重叠、裁切、溢出、过密、过大留白或异常断行
B42｜图 31.4｜FIG-P577-01
章节：第 31 章《蒙特卡罗方法与直接采样》；PDF物理页：682
类型：坐标/曲线图；严重度：中
图源：src/绘图源码/第05册\_采样方法主题模型与图排序/V5-C02/fig\_v5\_c02\_rejection\_envelope.tex
当前题注：图 31.4: 接受 – 拒绝抽样的包络条件：目标密度处处不高于 𝑐𝑞，候选点下方均匀高度若落在目标 曲线之下便被接受
唯一读图结论：广义逆采用首次达到规则：连续情形沿水平线找到交点；离散情形中 $u=0.7$ 落在第二个跳点，而 $u=0.72$ 落在第三个跳点
当前问题：所在页存在低于8.5pt文字（最小约8.47pt）；所在页有18个字符低于8.5pt；题注偏长，图结论与使用说明混在同一题注中
本图专属修改方案：将图内正文、刻度、图例统一提升到源级至少9.5pt；PGFPlots设置tick label style={font=\small}, legend style={font=\small}，TikZ设置every node/.style={font=\small}；图宽优先提高到0.88--0.95\textwidth；不要通过\resizebox整体缩小文字；固定axis宽高比例，减少刻度数量；用线型+点型双编码，标注只保留极值、阈值、最终点等关键对象；题注压缩为一条“读图结论”：广义逆采用首次达到规则：连续情形沿水平线找到交点；离散情形中 $u=0.7$ 落在第二个跳点，而 $u=0.72$ 落在第三个跳点；其余教学提示另起正文段落；保留原变量命名，并在图后加入一句“先看什么、再看什么、最终得到什么”的阅读顺序
建议图宽：>=0.72\textwidth（核心图）；按版心自适应
subagent1/subagent3复核重点：坐标轴、刻度、单位、图例、曲线数据与正文公式一致；线型和点型可在灰度下区分；图内文字、公式、符号、变量、题注和相邻正文完全一致；整页与局部渲染均无重叠、裁切、溢出、过密、过大留白或异常断行
B43｜图 31.5｜FIG-P578-01
章节：第 31 章《蒙特卡罗方法与直接采样》；PDF物理页：682
类型：流程/网络图；严重度：中
图源：src/绘图源码/第05册\_采样方法主题模型与图排序/V5-C02/fig\_v5\_c02\_rejection\_flow\.tex
当前题注：图 31.5: 带预算的接受 – 拒绝流程：比率越界表示包络条件失效而非一次普通拒绝；预算耗尽则停 止并返回当前已接受但未达到目标数量的样本。
唯一读图结论：接受--拒绝抽样的包络条件：目标密度处处不高于 $c q$，候选点下方均匀高度若落在目标曲线之下便被接受
当前问题：所在页存在低于8.5pt文字（最小约8.47pt）；所在页有18个字符低于8.5pt；题注偏长，图结论与使用说明混在同一题注中；逐图视觉复核显示可读性仍可提升
本图专属修改方案：将图内正文、刻度、图例统一提升到源级至少9.5pt；PGFPlots设置tick label style={font=\small}, legend style={font=\small}，TikZ设置every node/.style={font=\small}；图宽优先提高到0.88--0.95\textwidth；不要通过\resizebox整体缩小文字；统一节点最小宽度、内边距与层级间距；箭头端点停在节点边界，避免穿过文字和交叉；题注压缩为一条“读图结论”：接受--拒绝抽样的包络条件：目标密度处处不高于 $c q$，候选点下方均匀高度若落在目标曲线之下便被接受；其余教学提示另起正文段落；保留原变量命名，并在图后加入一句“先看什么、再看什么、最终得到什么”的阅读顺序
建议图宽：>=0.72\textwidth（核心图）；按版心自适应
subagent1/subagent3复核重点：阅读方向唯一、节点层级清楚、箭头端点停在边界、无回折交叉与语义歧义；图内文字、公式、符号、变量、题注和相邻正文完全一致；整页与局部渲染均无重叠、裁切、溢出、过密、过大留白或异常断行
B44｜图 31.6｜FIG-P580-01
章节：第 31 章《蒙特卡罗方法与直接采样》；PDF物理页：684
类型：坐标/曲线图；严重度：低
图源：src/绘图源码/第05册\_采样方法主题模型与图排序/V5-C02/fig\_v5\_c02\_is\_support.tex
当前题注：图 31.6: 重要性抽样首先是支持问题：左图的提议分布漏掉目标分布的一部分支持集，任何有限样 本都无法通过加权恢复这部分积分；右图满足支持覆盖
唯一读图结论：带预算的接受--拒绝流程：比率越界表示包络条件失效而非一次普通拒绝；预算耗尽则停止并返回当前已接受但未达到目标数量的样本。
当前问题：题注偏长，图结论与使用说明混在同一题注中
本图专属修改方案：固定axis宽高比例，减少刻度数量；用线型+点型双编码，标注只保留极值、阈值、最终点等关键对象；题注压缩为一条“读图结论”：带预算的接受--拒绝流程：比率越界表示包络条件失效而非一次普通拒绝；预算耗尽则停止并返回当前已接受但未达到目标数量的样本。；其余教学提示另起正文段落；保留原变量命名，并在图后加入一句“先看什么、再看什么、最终得到什么”的阅读顺序
建议图宽：>=0.72\textwidth（核心图）；按版心自适应
subagent1/subagent3复核重点：坐标轴、刻度、单位、图例、曲线数据与正文公式一致；线型和点型可在灰度下区分；图内文字、公式、符号、变量、题注和相邻正文完全一致；整页与局部渲染均无重叠、裁切、溢出、过密、过大留白或异常断行
B45｜图 31.7｜FIG-P582-01
章节：第 31 章《蒙特卡罗方法与直接采样》；PDF物理页：686
类型：坐标/曲线图；严重度：无
图源：src/绘图源码/第05册\_采样方法主题模型与图排序/V5-C02/fig\_v5\_c02\_running\_mean.tex
当前题注：图 31.7: 固定样本序列 0.8, 0.1, 0.7, 0.4 下 𝑈2 𝑖的运行均值；曲线先降后升再下降，说明收敛结论不 等于逐步单调逼近
唯一读图结论：重要性抽样首先是支持问题：左图的提议分布漏掉目标分布的一部分支持集，任何有限样本都无法通过加权恢复这部分积分；右图满足支持覆盖
当前问题：未发现明显缺图、裁切、重叠或变量不一致；仍建议保留常规灰度与字号复核
本图专属修改方案：固定axis宽高比例，减少刻度数量；用线型+点型双编码，标注只保留极值、阈值、最终点等关键对象；保留原变量命名，并在图后加入一句“先看什么、再看什么、最终得到什么”的阅读顺序
建议图宽：>=0.72\textwidth（核心图）；按版心自适应
subagent1/subagent3复核重点：坐标轴、刻度、单位、图例、曲线数据与正文公式一致；线型和点型可在灰度下区分；图内文字、公式、符号、变量、题注和相邻正文完全一致；整页与局部渲染均无重叠、裁切、溢出、过密、过大留白或异常断行
B46｜图 31.8｜FIG-P582-02
章节：第 31 章《蒙特卡罗方法与直接采样》；PDF物理页：686
类型：坐标/曲线图；严重度：低
图源：src/绘图源码/第05册\_采样方法主题模型与图排序/V5-C02/fig\_v5\_c02\_weight\_ess.tex
当前题注：图 31.8: 退化归一化权重 0.90, 0.05, 0.03, 0.02；其启发式有效样本量约为 1.23，提示少数样本主导 估计，但不能单独证明估计可靠
唯一读图结论：退化归一化权重 $0.90,0.05,0.03,0.02$；其启发式有效样本量约为 $1.23$，提示少数样本主导估计，但不能单独证明估计可靠
当前问题：题注偏长，图结论与使用说明混在同一题注中；逐图视觉复核显示可读性仍可提升
本图专属修改方案：固定axis宽高比例，减少刻度数量；用线型+点型双编码，标注只保留极值、阈值、最终点等关键对象；题注压缩为一条“读图结论”：退化归一化权重 $0.90,0.05,0.03,0.02$；其启发式有效样本量约为 $1.23$，提示少数样本主导估计，但不能单独证明估计可靠；其余教学提示另起正文段落；保留原变量命名，并在图后加入一句“先看什么、再看什么、最终得到什么”的阅读顺序
建议图宽：>=0.72\textwidth（核心图）；按版心自适应
subagent1/subagent3复核重点：坐标轴、刻度、单位、图例、曲线数据与正文公式一致；线型和点型可在灰度下区分；图内文字、公式、符号、变量、题注和相邻正文完全一致；整页与局部渲染均无重叠、裁切、溢出、过密、过大留白或异常断行
B47｜图 31.9｜FIG-P583-01
章节：第 31 章《蒙特卡罗方法与直接采样》；PDF物理页：686
类型：坐标/曲线图；严重度：低
图源：src/绘图源码/第05册\_采样方法主题模型与图排序/V5-C02/fig\_v5\_c02\_rmse\_rate.tex
当前题注：图 31.9: 独立同分布且方差有限时的理论均方根误差速率；相关样本或无限方差情形不能直接沿 用这条直线
唯一读图结论：独立同分布且方差有限时的理论均方根误差速率；相关样本或无限方差情形不能直接沿用这条直线
当前问题：题注偏长，图结论与使用说明混在同一题注中
本图专属修改方案：固定axis宽高比例，减少刻度数量；用线型+点型双编码，标注只保留极值、阈值、最终点等关键对象；题注压缩为一条“读图结论”：独立同分布且方差有限时的理论均方根误差速率；相关样本或无限方差情形不能直接沿用这条直线；其余教学提示另起正文段落；保留原变量命名，并在图后加入一句“先看什么、再看什么、最终得到什么”的阅读顺序
建议图宽：>=0.72\textwidth（核心图）；按版心自适应
subagent1/subagent3复核重点：坐标轴、刻度、单位、图例、曲线数据与正文公式一致；线型和点型可在灰度下区分；图内文字、公式、符号、变量、题注和相邻正文完全一致；整页与局部渲染均无重叠、裁切、溢出、过密、过大留白或异常断行
B48｜图 32.1｜FIG-P596-01
章节：第 32 章《马尔可夫链蒙特卡罗法》；PDF物理页：704
类型：流程/网络图；严重度：低
图源：src/绘图源码/第05册\_采样方法主题模型与图排序/V5-C03/fig\_v5\_c03\_dependency\_graph.tex
当前题注：图 32.1: 本章局部知识依赖：平稳分布与遍历平均支撑 MCMC 基本思想，细致平衡支撑 Metropolis– Hastings 构造，样本相关性进一步引出诊断；箭头仅表示教学前置关系
唯一读图结论：本章局部知识依赖：平稳分布与遍历平均支撑MCMC基本思想，细致平衡支撑Metropolis--Hastings构造，样本相关性进一步引出诊断；箭头仅表示教学前置关系
当前问题：题注偏长，图结论与使用说明混在同一题注中
本图专属修改方案：统一节点最小宽度、内边距与层级间距；箭头端点停在节点边界，避免穿过文字和交叉；题注压缩为一条“读图结论”：本章局部知识依赖：平稳分布与遍历平均支撑MCMC基本思想，细致平衡支撑Metropolis--Hastings构造，样本相关性进一步引出诊断；箭头仅表示教学前置关系；其余教学提示另起正文段落；保留原变量命名，并在图后加入一句“先看什么、再看什么、最终得到什么”的阅读顺序
建议图宽：>=0.72\textwidth（核心图）；按版心自适应
subagent1/subagent3复核重点：阅读方向唯一、节点层级清楚、箭头端点停在边界、无回折交叉与语义歧义；图内文字、公式、符号、变量、题注和相邻正文完全一致；整页与局部渲染均无重叠、裁切、溢出、过密、过大留白或异常断行
B49｜图 32.2｜FIG-P598-01
章节：第 32 章《马尔可夫链蒙特卡罗法》；PDF物理页：705
类型：流程/网络图；严重度：低
图源：src/绘图源码/第05册\_采样方法主题模型与图排序/V5-C03/fig\_v5\_c03\_markov\_chain\_path.tex
当前题注：图 32.2: 马尔可夫链在转移核 𝐾下产生相关样本路径；箭头 𝑥→𝑦表示 𝐾(𝑥, d𝑦) 在 𝑦附近有正质 量，自环表示链可能保持在当前状态
唯一读图结论：马尔可夫链在转移核 $K$ 下产生相关样本路径；箭头 $x\to y$ 表示 $K(x,\mathrm{d}y)$ 在 $y$ 附近有正质量，自环表示链可能保持在当前状态
当前问题：题注偏长，图结论与使用说明混在同一题注中
本图专属修改方案：统一节点最小宽度、内边距与层级间距；箭头端点停在节点边界，避免穿过文字和交叉；题注压缩为一条“读图结论”：马尔可夫链在转移核 $K$ 下产生相关样本路径；箭头 $x\to y$ 表示 $K(x,\mathrm{d}y)$ 在 $y$ 附近有正质量，自环表示链可能保持在当前状态；其余教学提示另起正文段落；保留原变量命名，并在图后加入一句“先看什么、再看什么、最终得到什么”的阅读顺序
建议图宽：>=0.72\textwidth（核心图）；按版心自适应
subagent1/subagent3复核重点：阅读方向唯一、节点层级清楚、箭头端点停在边界、无回折交叉与语义歧义；图内文字、公式、符号、变量、题注和相邻正文完全一致；整页与局部渲染均无重叠、裁切、溢出、过密、过大留白或异常断行
B50｜图 32.3｜FIG-P598-02
章节：第 32 章《马尔可夫链蒙特卡罗法》；PDF物理页：705
类型：流程/网络图；严重度：低
图源：src/绘图源码/第05册\_采样方法主题模型与图排序/V5-C03/fig\_v5\_c03\_mcmc\_pipeline.tex
当前题注：图 32.3: MCMC 工作流按箭头依次完成三步：由目标分布 𝜋构造以 𝜋为平稳分布的转移核，运行 链并舍弃预热段，再以保留样本的遍历平均估计 𝔼𝜋[ℎ(𝑋)]。
唯一读图结论：MCMC工作流按箭头依次完成三步：由目标分布$\pi$构造以$\pi$为平稳分布的转移核，运行链并舍弃预热段，再以保留样本的遍历平均估计$\mathbb E\_\pi[h(X)]$。
当前问题：题注偏长，图结论与使用说明混在同一题注中；逐图视觉复核显示可读性仍可提升
本图专属修改方案：统一节点最小宽度、内边距与层级间距；箭头端点停在节点边界，避免穿过文字和交叉；题注压缩为一条“读图结论”：MCMC工作流按箭头依次完成三步：由目标分布$\pi$构造以$\pi$为平稳分布的转移核，运行链并舍弃预热段，再以保留样本的遍历平均估计$\mathbb E\_\pi[h(X)]$。；其余教学提示另起正文段落；保留原变量命名，并在图后加入一句“先看什么、再看什么、最终得到什么”的阅读顺序
建议图宽：>=0.72\textwidth（核心图）；按版心自适应
subagent1/subagent3复核重点：阅读方向唯一、节点层级清楚、箭头端点停在边界、无回折交叉与语义歧义；图内文字、公式、符号、变量、题注和相邻正文完全一致；整页与局部渲染均无重叠、裁切、溢出、过密、过大留白或异常断行
B51｜图 32.4｜FIG-P600-01
章节：第 32 章《马尔可夫链蒙特卡罗法》；PDF物理页：707
类型：流程/网络图；严重度：低
图源：src/绘图源码/第05册\_采样方法主题模型与图排序/V5-C03/fig\_v5\_c03\_mh\_balance\_flux.tex
当前题注：图 32.4: MH 接受机制把两个方向的已接受概率流同时截为两者较小值，从而满足细致平衡；该条 件足以推出 𝜋平稳，但不是平稳性的必要条件
唯一读图结论：MH接受机制把两个方向的已接受概率流同时截为两者较小值，从而满足细致平衡；该条件足以推出 $\pi$ 平稳，但不是平稳性的必要条件
当前问题：题注偏长，图结论与使用说明混在同一题注中
本图专属修改方案：统一节点最小宽度、内边距与层级间距；箭头端点停在节点边界，避免穿过文字和交叉；题注压缩为一条“读图结论”：MH接受机制把两个方向的已接受概率流同时截为两者较小值，从而满足细致平衡；该条件足以推出 $\pi$ 平稳，但不是平稳性的必要条件；其余教学提示另起正文段落；保留原变量命名，并在图后加入一句“先看什么、再看什么、最终得到什么”的阅读顺序
建议图宽：>=0.72\textwidth（核心图）；按版心自适应
subagent1/subagent3复核重点：阅读方向唯一、节点层级清楚、箭头端点停在边界、无回折交叉与语义歧义；图内文字、公式、符号、变量、题注和相邻正文完全一致；整页与局部渲染均无重叠、裁切、溢出、过密、过大留白或异常断行
B52｜图 32.5｜FIG-P602-01
章节：第 32 章《马尔可夫链蒙特卡罗法》；PDF物理页：710
类型：概念关系图；严重度：高
图源：src/绘图源码/第05册\_采样方法主题模型与图排序/V5-C03/fig\_v5\_c03\_mh\_accept\_reject.tex
当前题注：图 32.5: 从当前状态 𝑥按 𝑞(𝑥, ⋅) 提出候选 𝑦；以 𝛼(𝑥, 𝑦) 转移到 𝑦，拒绝时把概率质量并入 𝑥处自环 并令 𝑋𝑡+1 = 𝑥
唯一读图结论：从当前状态 $x$ 按 $q(x,\cdot)$ 提出候选 $y$；以 $\alpha(x,y)$ 转移到 $y$，拒绝时把概率质量并入 $x$ 处自环并令 $X\_{t+1}=x$
当前问题：所在页存在低于6pt文字（最小约6.00pt）；所在页有11个字符低于8.5pt；题注偏长，图结论与使用说明混在同一题注中；逐图视觉复核显示可读性仍可提升
本图专属修改方案：将图内正文、刻度、图例统一提升到源级至少9.5pt；PGFPlots设置tick label style={font=\small}, legend style={font=\small}，TikZ设置every node/.style={font=\small}；图宽优先提高到0.88--0.95\textwidth；不要通过\resizebox整体缩小文字；统一节点最小宽度、内边距与层级间距；箭头端点停在节点边界，避免穿过文字和交叉；题注压缩为一条“读图结论”：从当前状态 $x$ 按 $q(x,\cdot)$ 提出候选 $y$；以 $\alpha(x,y)$ 转移到 $y$，拒绝时把概率质量并入 $x$ 处自环并令 $X\_{t+1}=x$；其余教学提示另起正文段落；保留原变量命名，并在图后加入一句“先看什么、再看什么、最终得到什么”的阅读顺序
建议图宽：>=0.72\textwidth（核心图）；按版心自适应
subagent1/subagent3复核重点：关系类型、条件方向与层级不能只靠颜色表达；概念边界与正文定义一致；图内文字、公式、符号、变量、题注和相邻正文完全一致；整页与局部渲染均无重叠、裁切、溢出、过密、过大留白或异常断行；必须评估拆图或重构，不得仅靠放大画布和整体缩放掩盖结构问题
B53｜图 32.6｜FIG-P603-01
章节：第 32 章《马尔可夫链蒙特卡罗法》；PDF物理页：712
类型：坐标/曲线图；严重度：低
图源：src/绘图源码/第05册\_采样方法主题模型与图排序/V5-C03/fig\_v5\_c03\_acceptance\_function.tex
当前题注：图 32.6: MH 接受概率是比值 𝑟的截断函数 𝛼= min{1, 𝑟}，其中 𝑟= 𝜋(𝑦)𝑞(𝑦, 𝑥)/[𝜋(𝑥)𝑞(𝑥, 𝑦)]；独立 提议时可写为 𝑟= 𝑤(𝑦)/𝑤(𝑥)
唯一读图结论：MH接受概率是比值 $r$ 的截断函数 $\alpha=\min{1,r}$，其中 $r=\pi(y)q(y,x)/[\pi(x)q(x,y)]$；独立提议时可写为 $r=w(y)/w(x)$
当前问题：题注偏长，图结论与使用说明混在同一题注中
本图专属修改方案：固定axis宽高比例，减少刻度数量；用线型+点型双编码，标注只保留极值、阈值、最终点等关键对象；题注压缩为一条“读图结论”：MH接受概率是比值 $r$ 的截断函数 $\alpha=\min{1,r}$，其中 $r=\pi(y)q(y,x)/[\pi(x)q(x,y)]$；独立提议时可写为 $r=w(y)/w(x)$；其余教学提示另起正文段落；保留原变量命名，并在图后加入一句“先看什么、再看什么、最终得到什么”的阅读顺序
建议图宽：>=0.72\textwidth（核心图）；按版心自适应
subagent1/subagent3复核重点：坐标轴、刻度、单位、图例、曲线数据与正文公式一致；线型和点型可在灰度下区分；图内文字、公式、符号、变量、题注和相邻正文完全一致；整页与局部渲染均无重叠、裁切、溢出、过密、过大留白或异常断行
B54｜图 32.7｜FIG-P605-01
章节：第 32 章《马尔可夫链蒙特卡罗法》；PDF物理页：714
类型：流程/网络图；严重度：中
图源：src/绘图源码/第05册\_采样方法主题模型与图排序/V5-C03/fig\_v5\_c03\_componentwise\_sweep.tex
当前题注：图 32.7: 分量 MH 的系统扫描与随机扫描。固定顺序的核复合通常不保证可逆；可逆坐标核的固 定权重随机混合仍保持可逆。
唯一读图结论：接受--拒绝抽样拒绝候选后不输出该候选；MH拒绝候选后把当前状态再次记入链，因此输出通常相关而非独立
当前问题：所在页存在低于7.5pt文字（最小约6.42pt）；所在页有23个字符低于8.5pt；题注偏长，图结论与使用说明混在同一题注中；逐图视觉复核显示可读性仍可提升
本图专属修改方案：将图内正文、刻度、图例统一提升到源级至少9.5pt；PGFPlots设置tick label style={font=\small}, legend style={font=\small}，TikZ设置every node/.style={font=\small}；图宽优先提高到0.88--0.95\textwidth；不要通过\resizebox整体缩小文字；统一节点最小宽度、内边距与层级间距；箭头端点停在节点边界，避免穿过文字和交叉；题注压缩为一条“读图结论”：接受--拒绝抽样拒绝候选后不输出该候选；MH拒绝候选后把当前状态再次记入链，因此输出通常相关而非独立；其余教学提示另起正文段落；保留原变量命名，并在图后加入一句“先看什么、再看什么、最终得到什么”的阅读顺序
建议图宽：>=0.72\textwidth（核心图）；按版心自适应
subagent1/subagent3复核重点：阅读方向唯一、节点层级清楚、箭头端点停在边界、无回折交叉与语义歧义；图内文字、公式、符号、变量、题注和相邻正文完全一致；整页与局部渲染均无重叠、裁切、溢出、过密、过大留白或异常断行
B55｜图 32.8｜FIG-P608-01
章节：第 32 章《马尔可夫链蒙特卡罗法》；PDF物理页：718
类型：坐标/曲线图；严重度：高
图源：src/绘图源码/第05册\_采样方法主题模型与图排序/V5-C03/fig\_v5\_c03\_trace\_running\_mean.tex
当前题注：图 32.8: 同一条固定示意序列的轨迹图与运行均值：阴影区为预热段，竖线后样本用于估计；图形 仅说明诊断读法，不构成收敛证明
唯一读图结论：分量MH的系统扫描与随机扫描。固定顺序的核复合通常不保证可逆；可逆坐标核的固定权重随机混合仍保持可逆。
当前问题：所在页存在低于7.5pt文字（最小约6.42pt）；所在页小于8.5pt字符较多（51个）；题注偏长，图结论与使用说明混在同一题注中；逐图视觉复核显示可读性仍可提升
本图专属修改方案：将图内正文、刻度、图例统一提升到源级至少9.5pt；PGFPlots设置tick label style={font=\small}, legend style={font=\small}，TikZ设置every node/.style={font=\small}；图宽优先提高到0.88--0.95\textwidth；不要通过\resizebox整体缩小文字；固定axis宽高比例，减少刻度数量；用线型+点型双编码，标注只保留极值、阈值、最终点等关键对象；题注压缩为一条“读图结论”：分量MH的系统扫描与随机扫描。固定顺序的核复合通常不保证可逆；可逆坐标核的固定权重随机混合仍保持可逆。；其余教学提示另起正文段落；保留原变量命名，并在图后加入一句“先看什么、再看什么、最终得到什么”的阅读顺序
建议图宽：>=0.72\textwidth（核心图）；按版心自适应
subagent1/subagent3复核重点：坐标轴、刻度、单位、图例、曲线数据与正文公式一致；线型和点型可在灰度下区分；图内文字、公式、符号、变量、题注和相邻正文完全一致；整页与局部渲染均无重叠、裁切、溢出、过密、过大留白或异常断行；必须评估拆图或重构，不得仅靠放大画布和整体缩放掩盖结构问题
B56｜图 32.9｜FIG-P609-01
章节：第 32 章《马尔可夫链蒙特卡罗法》；PDF物理页：718
类型：坐标/曲线图；严重度：高
图源：src/绘图源码/第05册\_采样方法主题模型与图排序/V5-C03/fig\_v5\_c03\_autocorrelation\_ess.tex
当前题注：图 32.9: 固定示意 ACF 中，相关性衰减较慢时积分自相关时间增大、同长度链的有效信息量下降； 𝜏int = 1 + 2 ∑𝑘≥1 𝜌𝑘与 𝑁eff = 𝑁/𝜏int 必须配合明确的有限样本截断规则使用，且诊断量本身不是 收敛证明
唯一读图结论：同一条固定示意序列的轨迹图与运行均值：阴影区为预热段，竖线后样本用于估计；图形仅说明诊断读法，不构成收敛证明
当前问题：所在页存在低于7.5pt文字（最小约6.42pt）；所在页小于8.5pt字符较多（51个）；题注偏长，图结论与使用说明混在同一题注中；逐图视觉复核显示可读性仍可提升
本图专属修改方案：将图内正文、刻度、图例统一提升到源级至少9.5pt；PGFPlots设置tick label style={font=\small}, legend style={font=\small}，TikZ设置every node/.style={font=\small}；图宽优先提高到0.88--0.95\textwidth；不要通过\resizebox整体缩小文字；固定axis宽高比例，减少刻度数量；用线型+点型双编码，标注只保留极值、阈值、最终点等关键对象；题注压缩为一条“读图结论”：同一条固定示意序列的轨迹图与运行均值：阴影区为预热段，竖线后样本用于估计；图形仅说明诊断读法，不构成收敛证明；其余教学提示另起正文段落；保留原变量命名，并在图后加入一句“先看什么、再看什么、最终得到什么”的阅读顺序
建议图宽：>=0.72\textwidth（核心图）；按版心自适应
subagent1/subagent3复核重点：坐标轴、刻度、单位、图例、曲线数据与正文公式一致；线型和点型可在灰度下区分；图内文字、公式、符号、变量、题注和相邻正文完全一致；整页与局部渲染均无重叠、裁切、溢出、过密、过大留白或异常断行；必须评估拆图或重构，不得仅靠放大画布和整体缩放掩盖结构问题
B57｜图 32.10｜FIG-P610-01
章节：第 32 章《马尔可夫链蒙特卡罗法》；PDF物理页：719
类型：流程/网络图；严重度：中
图源：src/绘图源码/第05册\_采样方法主题模型与图排序/V5-C03/fig\_v5\_c03\_rejection\_sampling\_comparison.tex
当前题注：图 32.10: 接受 – 拒绝抽样拒绝候选后不输出该候选； MH 拒绝候选后把当前状态再次记入链，因 此输出通常相关而非独立
唯一读图结论：固定示意ACF中，相关性衰减较慢时积分自相关时间增大、同长度链的有效信息量下降；$\tau\_{\mathrm{int}}=1+2\sum\_{k\geq1}\rho\_k$ 与 $N\_{\mathrm{eff}}=N/\tau\_{\mathrm{int}}$ 必须配合明确的有限样本截断规则使用，且诊断量本身不是收敛证明
当前问题：所在页存在低于8.5pt文字（最小约8.47pt）；所在页有21个字符低于8.5pt；题注偏长，图结论与使用说明混在同一题注中
本图专属修改方案：将图内正文、刻度、图例统一提升到源级至少9.5pt；PGFPlots设置tick label style={font=\small}, legend style={font=\small}，TikZ设置every node/.style={font=\small}；图宽优先提高到0.88--0.95\textwidth；不要通过\resizebox整体缩小文字；统一节点最小宽度、内边距与层级间距；箭头端点停在节点边界，避免穿过文字和交叉；题注压缩为一条“读图结论”：固定示意ACF中，相关性衰减较慢时积分自相关时间增大、同长度链的有效信息量下降；$\tau\_{\mathrm{int}}=1+2\sum\_{k\geq1}\rho\_k$ 与 $N\_{\mathrm{eff}}=N/\tau\_{\mathrm{int}}$ 必须配合明确的有限样本截断规则使用，且诊断量本身不是收敛证明；其余教学提示另起正文段落；保留原变量命名，并在图后加入一句“先看什么、再看什么、最终得到什么”的阅读顺序
建议图宽：>=0.72\textwidth（核心图）；按版心自适应
subagent1/subagent3复核重点：阅读方向唯一、节点层级清楚、箭头端点停在边界、无回折交叉与语义歧义；图内文字、公式、符号、变量、题注和相邻正文完全一致；整页与局部渲染均无重叠、裁切、溢出、过密、过大留白或异常断行
B58｜图 33.1｜FIG-P630-01
章节：第 33 章《Gibbs 抽样》；PDF物理页：738
类型：概念关系图；严重度：高
图源：src/绘图源码/第05册\_采样方法主题模型与图排序/V5-C04/fig\_v5\_c04\_dependency\_graph.tex
当前题注：图 33.1: 本章知识依赖从联合目标与局部因子出发，经满条件分布、单坐标核和扫描核得到相关样 本，再进入 Monte Carlo 诊断；箭头表示教学与计算依赖，不表示各条件自动保证不可约或收敛
唯一读图结论：本章知识依赖从联合目标与局部因子出发，经满条件分布、单坐标核和扫描核得到相关样本，再进入Monte Carlo诊断；箭头表示教学与计算依赖，不表示各条件自动保证不可约或收敛
当前问题：所在页存在低于7.5pt文字（最小约6.42pt）；所在页小于8.5pt字符较多（33个）；题注偏长，图结论与使用说明混在同一题注中；逐图视觉复核显示可读性仍可提升
本图专属修改方案：将图内正文、刻度、图例统一提升到源级至少9.5pt；PGFPlots设置tick label style={font=\small}, legend style={font=\small}，TikZ设置every node/.style={font=\small}；图宽优先提高到0.88--0.95\textwidth；不要通过\resizebox整体缩小文字；统一节点最小宽度、内边距与层级间距；箭头端点停在节点边界，避免穿过文字和交叉；题注压缩为一条“读图结论”：本章知识依赖从联合目标与局部因子出发，经满条件分布、单坐标核和扫描核得到相关样本，再进入Monte Carlo诊断；箭头表示教学与计算依赖，不表示各条件自动保证不可约或收敛；其余教学提示另起正文段落；保留原变量命名，并在图后加入一句“先看什么、再看什么、最终得到什么”的阅读顺序
建议图宽：>=0.72\textwidth（核心图）；按版心自适应
subagent1/subagent3复核重点：关系类型、条件方向与层级不能只靠颜色表达；概念边界与正文定义一致；图内文字、公式、符号、变量、题注和相邻正文完全一致；整页与局部渲染均无重叠、裁切、溢出、过密、过大留白或异常断行；必须评估拆图或重构，不得仅靠放大画布和整体缩放掩盖结构问题
B59｜图 33.2｜FIG-P632-01
章节：第 33 章《Gibbs 抽样》；PDF物理页：739
类型：概念关系图；严重度：低
图源：src/绘图源码/第05册\_采样方法主题模型与图排序/V5-C04/fig\_v5\_c04\_conditional\_slice.tex
当前题注：图 33.2: 联合密度的水平或竖直截面只有除以相应边缘积分后才成为满条件密度；当分母为零时 不能使用图中的密度比，必须另选正则条件分布版本
唯一读图结论：联合密度的水平或竖直截面只有除以相应边缘积分后才成为满条件密度；当分母为零时不能使用图中的密度比，必须另选正则条件分布版本
当前问题：题注偏长，图结论与使用说明混在同一题注中
本图专属修改方案：统一节点最小宽度、内边距与层级间距；箭头端点停在节点边界，避免穿过文字和交叉；题注压缩为一条“读图结论”：联合密度的水平或竖直截面只有除以相应边缘积分后才成为满条件密度；当分母为零时不能使用图中的密度比，必须另选正则条件分布版本；其余教学提示另起正文段落；保留原变量命名，并在图后加入一句“先看什么、再看什么、最终得到什么”的阅读顺序
建议图宽：>=0.72\textwidth（核心图）；按版心自适应
subagent1/subagent3复核重点：关系类型、条件方向与层级不能只靠颜色表达；概念边界与正文定义一致；图内文字、公式、符号、变量、题注和相邻正文完全一致；整页与局部渲染均无重叠、裁切、溢出、过密、过大留白或异常断行
B60｜图 33.3｜FIG-P634-01
章节：第 33 章《Gibbs 抽样》；PDF物理页：742
类型：概念关系图；严重度：高
图源：src/绘图源码/第05册\_采样方法主题模型与图排序/V5-C04/fig\_v5\_c04\_coordinate\_sweep.tex
当前题注：图 33.3: 系统扫描在一轮内依次覆盖坐标；序号、粗/点状边框、斜线/圆点记号及 “已更新/未更 新”文字共同编码更新顺序，使灰度打印时也不依赖颜色；轮内状态 𝑥[𝑗] 不得误记为一轮完成后 的样本
唯一读图结论：系统扫描在一轮内依次覆盖坐标；序号、粗/点状边框、斜线/圆点记号及“已更新/未更新”文字共同编码更新顺序，使灰度打印时也不依赖颜色；轮内状态$x^{[j]}$不得误记为一轮完成后的样本
当前问题：所在页存在低于7.5pt文字（最小约6.14pt）；所在页小于8.5pt字符较多（60个）；题注偏长，图结论与使用说明混在同一题注中；逐图视觉复核判定为优先重绘/拆图对象
本图专属修改方案：将图内正文、刻度、图例统一提升到源级至少9.5pt；PGFPlots设置tick label style={font=\small}, legend style={font=\small}，TikZ设置every node/.style={font=\small}；图宽优先提高到0.88--0.95\textwidth；不要通过\resizebox整体缩小文字；把“定义/输入”和“计算/结论”拆为两幅子图，或按(a)(b)分面；每个面板只保留一个阅读任务；减少跨面板回折箭头，采用从左到右或从上到下的单向网格；长说明移到图后正文；统一节点最小宽度、内边距与层级间距；箭头端点停在节点边界，避免穿过文字和交叉；题注压缩为一条“读图结论”：系统扫描在一轮内依次覆盖坐标；序号、粗/点状边框、斜线/圆点记号及“已更新/未更新”文字共同编码更新顺序，使灰度打印时也不依赖颜色；轮内状态$x^{[j]}$不得误记为一轮完成后的样本；其余教学提示另起正文段落；保留原变量命名，并在图后加入一句“先看什么、再看什么、最终得到什么”的阅读顺序
建议图宽：>=0.72\textwidth（核心图）；按版心自适应
subagent1/subagent3复核重点：关系类型、条件方向与层级不能只靠颜色表达；概念边界与正文定义一致；图内文字、公式、符号、变量、题注和相邻正文完全一致；整页与局部渲染均无重叠、裁切、溢出、过密、过大留白或异常断行；必须评估拆图或重构，不得仅靠放大画布和整体缩放掩盖结构问题
B61｜图 33.4｜FIG-P637-01
章节：第 33 章《Gibbs 抽样》；PDF物理页：745
类型：几何/结构示意图；严重度：低
图源：src/绘图源码/第05册\_采样方法主题模型与图排序/V5-C04/fig\_v5\_c04\_gibbs\_axis\_path.tex
当前题注：图 33.4: 二维 Gibbs 轨迹在更新 𝑥1 时水平移动、更新 𝑥2 时竖直移动；折线是固定的教学示意而非 伪造随机轨迹，倾斜狭长目标中的短轴向步揭示了强相关导致的慢混合
唯一读图结论：二维Gibbs轨迹在更新$x\_1$时水平移动、更新$x\_2$时竖直移动；折线是固定的教学示意而非伪造随机轨迹，倾斜狭长目标中的短轴向步揭示了强相关导致的慢混合
当前问题：题注偏长，图结论与使用说明混在同一题注中
本图专属修改方案：题注压缩为一条“读图结论”：二维Gibbs轨迹在更新$x\_1$时水平移动、更新$x\_2$时竖直移动；折线是固定的教学示意而非伪造随机轨迹，倾斜狭长目标中的短轴向步揭示了强相关导致的慢混合；其余教学提示另起正文段落；保留原变量命名，并在图后加入一句“先看什么、再看什么、最终得到什么”的阅读顺序
建议图宽：>=0.72\textwidth（核心图）；按版心自适应
subagent1/subagent3复核重点：几何关系、角度、投影、邻接或空间归属必须准确，示意不能误导比例关系；图内文字、公式、符号、变量、题注和相邻正文完全一致；整页与局部渲染均无重叠、裁切、溢出、过密、过大留白或异常断行
B62｜图 33.5｜FIG-P638-01
章节：第 33 章《Gibbs 抽样》；PDF物理页：746
类型：概念关系图；严重度：中
图源：src/绘图源码/第05册\_采样方法主题模型与图排序/V5-C04/fig\_v5\_c04\_gibbs\_vs\_mh.tex
当前题注：图 33.5: 精确满条件分布作为单坐标提议时，正流分支的 Metropolis–Hastings 比值恒为 1， Gibbs 更新无需拒绝；若提议只近似满条件或改用其他分布，则必须恢复接受率校正和拒绝自环
唯一读图结论：精确满条件分布作为单坐标提议时，正流分支的Metropolis--Hastings比值恒为1，Gibbs更新无需拒绝；若提议只近似满条件或改用其他分布，则必须恢复接受率校正和拒绝自环
当前问题：所在页存在低于7.5pt文字（最小约6.42pt）；所在页有20个字符低于8.5pt；题注偏长，图结论与使用说明混在同一题注中；逐图视觉复核显示可读性仍可提升
本图专属修改方案：将图内正文、刻度、图例统一提升到源级至少9.5pt；PGFPlots设置tick label style={font=\small}, legend style={font=\small}，TikZ设置every node/.style={font=\small}；图宽优先提高到0.88--0.95\textwidth；不要通过\resizebox整体缩小文字；统一节点最小宽度、内边距与层级间距；箭头端点停在节点边界，避免穿过文字和交叉；题注压缩为一条“读图结论”：精确满条件分布作为单坐标提议时，正流分支的Metropolis--Hastings比值恒为1，Gibbs更新无需拒绝；若提议只近似满条件或改用其他分布，则必须恢复接受率校正和拒绝自环；其余教学提示另起正文段落；保留原变量命名，并在图后加入一句“先看什么、再看什么、最终得到什么”的阅读顺序
建议图宽：>=0.72\textwidth（核心图）；按版心自适应
subagent1/subagent3复核重点：关系类型、条件方向与层级不能只靠颜色表达；概念边界与正文定义一致；图内文字、公式、符号、变量、题注和相邻正文完全一致；整页与局部渲染均无重叠、裁切、溢出、过密、过大留白或异常断行
B63｜图 33.6｜FIG-P639-01
章节：第 33 章《Gibbs 抽样》；PDF物理页：747
类型：坐标/曲线图；严重度：低
图源：src/绘图源码/第05册\_采样方法主题模型与图排序/V5-C04/fig\_v5\_c04\_bivariate\_normal\_conditionals.tex
当前题注：图 33.6: 取 𝜌= 0.6、𝑎= 1、𝑏= 0.75 时，两个满条件分布分别为 𝑁(0.45, 0.64) 与 𝑁(0.60, 0.64)；图 中曲线按同一组参数直接计算。
唯一读图结论：取$\rho=0.6$、$a=1$、$b=0.75$时，两个满条件分布分别为$N(0.45,0.64)$与$N(0.60,0.64)$；图中曲线按同一组参数直接计算。
当前问题：题注偏长，图结论与使用说明混在同一题注中
本图专属修改方案：固定axis宽高比例，减少刻度数量；用线型+点型双编码，标注只保留极值、阈值、最终点等关键对象；题注压缩为一条“读图结论”：取$\rho=0.6$、$a=1$、$b=0.75$时，两个满条件分布分别为$N(0.45,0.64)$与$N(0.60,0.64)$；图中曲线按同一组参数直接计算。；其余教学提示另起正文段落；保留原变量命名，并在图后加入一句“先看什么、再看什么、最终得到什么”的阅读顺序
建议图宽：>=0.72\textwidth（核心图）；按版心自适应
subagent1/subagent3复核重点：坐标轴、刻度、单位、图例、曲线数据与正文公式一致；线型和点型可在灰度下区分；图内文字、公式、符号、变量、题注和相邻正文完全一致；整页与局部渲染均无重叠、裁切、溢出、过密、过大留白或异常断行
B64｜图 33.7｜FIG-P640-01
章节：第 33 章《Gibbs 抽样》；PDF物理页：747
类型：坐标/曲线图；严重度：高
图源：src/绘图源码/第05册\_采样方法主题模型与图排序/V5-C04/fig\_v5\_c04\_mixing\_rho\_comparison.tex
当前题注：图 33.7: 二元正态系统 Gibbs 的解析自相关为 𝜌2𝑘，有效样本比例为 (1 −𝜌2)/(1 + 𝜌2)；当 |𝜌| 接近 1 时相关性衰减缓慢，即使内核正确且接受率为 1，固定长度链的统计效率仍会显著下降
唯一读图结论：因子图中更新$\theta$只需读取与$\theta$相连的两个因子$p(\theta\mid\alpha)$和$p(z,y\mid\theta)$；Markov毯变量为$\alpha,z,y$，而与$\theta$无关的因子$p(\alpha)$可从满条件核中消去
当前问题：题注偏长，图结论与使用说明混在同一题注中；逐图视觉复核判定为优先重绘/拆图对象
本图专属修改方案：把“定义/输入”和“计算/结论”拆为两幅子图，或按(a)(b)分面；每个面板只保留一个阅读任务；减少跨面板回折箭头，采用从左到右或从上到下的单向网格；长说明移到图后正文；固定axis宽高比例，减少刻度数量；用线型+点型双编码，标注只保留极值、阈值、最终点等关键对象；题注压缩为一条“读图结论”：因子图中更新$\theta$只需读取与$\theta$相连的两个因子$p(\theta\mid\alpha)$和$p(z,y\mid\theta)$；Markov毯变量为$\alpha,z,y$，而与$\theta$无关的因子$p(\alpha)$可从满条件核中消去；其余教学提示另起正文段落；保留原变量命名，并在图后加入一句“先看什么、再看什么、最终得到什么”的阅读顺序
建议图宽：>=0.72\textwidth（核心图）；按版心自适应
subagent1/subagent3复核重点：坐标轴、刻度、单位、图例、曲线数据与正文公式一致；线型和点型可在灰度下区分；图内文字、公式、符号、变量、题注和相邻正文完全一致；整页与局部渲染均无重叠、裁切、溢出、过密、过大留白或异常断行；必须评估拆图或重构，不得仅靠放大画布和整体缩放掩盖结构问题
B65｜图 33.8｜FIG-P641-01
章节：第 33 章《Gibbs 抽样》；PDF物理页：749
类型：流程/网络图；严重度：低
图源：src/绘图源码/第05册\_采样方法主题模型与图排序/V5-C04/fig\_v5\_c04\_bayes\_markov\_blanket.tex
当前题注：图 33.8: 因子图中更新 𝜃只需读取与 𝜃相连的两个因子 𝑝(𝜃∣𝛼) 和 𝑝(𝑧, 𝑦∣𝜃)； Markov 毯变量为 𝛼, 𝑧, 𝑦，而与 𝜃无关的因子 𝑝(𝛼) 可从满条件核中消去
唯一读图结论：二元正态系统Gibbs的解析自相关为$\rho^{2k}$，有效样本比例为$(1-\rho^2)/(1+\rho^2)$；当$|\rho|$接近1时相关性衰减缓慢，即使内核正确且接受率为1，固定长度链的统计效率仍会显著下降
当前问题：题注偏长，图结论与使用说明混在同一题注中
本图专属修改方案：统一节点最小宽度、内边距与层级间距；箭头端点停在节点边界，避免穿过文字和交叉；题注压缩为一条“读图结论”：二元正态系统Gibbs的解析自相关为$\rho^{2k}$，有效样本比例为$(1-\rho^2)/(1+\rho^2)$；当$|\rho|$接近1时相关性衰减缓慢，即使内核正确且接受率为1，固定长度链的统计效率仍会显著下降；其余教学提示另起正文段落；保留原变量命名，并在图后加入一句“先看什么、再看什么、最终得到什么”的阅读顺序
建议图宽：>=0.72\textwidth（核心图）；按版心自适应
subagent1/subagent3复核重点：阅读方向唯一、节点层级清楚、箭头端点停在边界、无回折交叉与语义歧义；图内文字、公式、符号、变量、题注和相邻正文完全一致；整页与局部渲染均无重叠、裁切、溢出、过密、过大留白或异常断行
B66｜图 34.1｜FIG-P654-01
章节：第 34 章《狄利克雷分布与共轭先验》；PDF物理页：763
类型：流程/网络图；严重度：中
图源：src/绘图源码/第05册\_采样方法主题模型与图排序/V5-C05/fig\_v5\_c05\_dependency\_graph.tex
当前题注：图 34.1: 本章从类别计数与 Gamma–Beta 归一化两条前置线索进入多项分布和 Dirichlet 分布，通 过指数相加先得到共轭后验，再由后验均值得到类别预测概率；单纯形几何、均值浓度和对数矩 用于解释参数，而下游主题模型只表示应用去向
唯一读图结论：本章从类别计数与Gamma--Beta归一化两条前置线索进入多项分布和Dirichlet分布，通过指数相加先得到共轭后验，再由后验均值得到类别预测概率；单纯形几何、均值浓度和对数矩用于解释参数，而下游主题模型只表示应用去向
当前问题：所在页存在低于7.5pt文字（最小约6.69pt）；所在页有6个字符低于8.5pt；题注偏长，图结论与使用说明混在同一题注中；逐图视觉复核显示可读性仍可提升
本图专属修改方案：将图内正文、刻度、图例统一提升到源级至少9.5pt；PGFPlots设置tick label style={font=\small}, legend style={font=\small}，TikZ设置every node/.style={font=\small}；图宽优先提高到0.88--0.95\textwidth；不要通过\resizebox整体缩小文字；统一节点最小宽度、内边距与层级间距；箭头端点停在节点边界，避免穿过文字和交叉；题注压缩为一条“读图结论”：本章从类别计数与Gamma--Beta归一化两条前置线索进入多项分布和Dirichlet分布，通过指数相加先得到共轭后验，再由后验均值得到类别预测概率；单纯形几何、均值浓度和对数矩用于解释参数，而下游主题模型只表示应用去向；其余教学提示另起正文段落；保留原变量命名，并在图后加入一句“先看什么、再看什么、最终得到什么”的阅读顺序
建议图宽：>=0.72\textwidth（核心图）；按版心自适应
subagent1/subagent3复核重点：阅读方向唯一、节点层级清楚、箭头端点停在边界、无回折交叉与语义歧义；图内文字、公式、符号、变量、题注和相邻正文完全一致；整页与局部渲染均无重叠、裁切、溢出、过密、过大留白或异常断行
B67｜图 34.2｜FIG-P656-01
章节：第 34 章《狄利克雷分布与共轭先验》；PDF物理页：764
类型：概念关系图；严重度：低
图源：src/绘图源码/第05册\_采样方法主题模型与图排序/V5-C05/fig\_v5\_c05\_multinomial\_counts.tex
当前题注：图 34.2: 多项分布把有序的独立类别试验压缩为计数向量；多项系数统计产生同一计数的不同序 列数，支持集同时要求非负整数约束和总计数约束，不能把计数向量误当作概率向量
唯一读图结论：多项分布把有序的独立类别试验压缩为计数向量；多项系数统计产生同一计数的不同序列数，支持集同时要求非负整数约束和总计数约束，不能把计数向量误当作概率向量
当前问题：题注偏长，图结论与使用说明混在同一题注中
本图专属修改方案：统一节点最小宽度、内边距与层级间距；箭头端点停在节点边界，避免穿过文字和交叉；题注压缩为一条“读图结论”：多项分布把有序的独立类别试验压缩为计数向量；多项系数统计产生同一计数的不同序列数，支持集同时要求非负整数约束和总计数约束，不能把计数向量误当作概率向量；其余教学提示另起正文段落；保留原变量命名，并在图后加入一句“先看什么、再看什么、最终得到什么”的阅读顺序
建议图宽：>=0.72\textwidth（核心图）；按版心自适应
subagent1/subagent3复核重点：关系类型、条件方向与层级不能只靠颜色表达；概念边界与正文定义一致；图内文字、公式、符号、变量、题注和相邻正文完全一致；整页与局部渲染均无重叠、裁切、溢出、过密、过大留白或异常断行
B68｜图 34.3｜FIG-P657-01
章节：第 34 章《狄利克雷分布与共轭先验》；PDF物理页：765
类型：流程/网络图；严重度：中
图源：src/绘图源码/第05册\_采样方法主题模型与图排序/V5-C05/fig\_v5\_c05\_distribution\_relations.tex
当前题注：图 34.3: 六个常用分布之间同时存在特殊情形关系和共轭关系： Beta 是二维 Dirichlet，二项是二 维多项，类别分布是单次多项， Bernoulli 同时是单次二项；粗箭头表示共轭先验而不是集合包含
唯一读图结论：六个常用分布之间同时存在特殊情形关系和共轭关系：Beta是二维Dirichlet，二项是二维多项，类别分布是单次多项，Bernoulli同时是单次二项；粗箭头表示共轭先验而不是集合包含
当前问题：所在页存在低于7.5pt文字（最小约6.42pt）；所在页有10个字符低于8.5pt；题注偏长，图结论与使用说明混在同一题注中；逐图视觉复核显示可读性仍可提升
本图专属修改方案：将图内正文、刻度、图例统一提升到源级至少9.5pt；PGFPlots设置tick label style={font=\small}, legend style={font=\small}，TikZ设置every node/.style={font=\small}；图宽优先提高到0.88--0.95\textwidth；不要通过\resizebox整体缩小文字；统一节点最小宽度、内边距与层级间距；箭头端点停在节点边界，避免穿过文字和交叉；题注压缩为一条“读图结论”：六个常用分布之间同时存在特殊情形关系和共轭关系：Beta是二维Dirichlet，二项是二维多项，类别分布是单次多项，Bernoulli同时是单次二项；粗箭头表示共轭先验而不是集合包含；其余教学提示另起正文段落；保留原变量命名，并在图后加入一句“先看什么、再看什么、最终得到什么”的阅读顺序
建议图宽：>=0.72\textwidth（核心图）；按版心自适应
subagent1/subagent3复核重点：阅读方向唯一、节点层级清楚、箭头端点停在边界、无回折交叉与语义歧义；图内文字、公式、符号、变量、题注和相邻正文完全一致；整页与局部渲染均无重叠、裁切、溢出、过密、过大留白或异常断行
B69｜图 34.4｜FIG-P660-01
章节：第 34 章《狄利克雷分布与共轭先验》；PDF物理页：768
类型：概念关系图；严重度：低
图源：src/绘图源码/第05册\_采样方法主题模型与图排序/V5-C05/fig\_v5\_c05\_simplex\_geometry.tex
当前题注：图 34.4: 三类别概率向量位于二维单纯形上，三个顶点分别代表一个类别概率为 1；内部点的重心 坐标就是三个类别概率，因此 Dirichlet 分布虽写在三维坐标中，实际支撑集只有二维
唯一读图结论：独立且具有共同率参数的Gamma变量除以其总和后得到Dirichlet随机向量；总量与归一化比例相互独立，二维情形退化为Beta分布，这一构造同时给出可复现的Dirichlet抽样方法
当前问题：题注偏长，图结论与使用说明混在同一题注中
本图专属修改方案：统一节点最小宽度、内边距与层级间距；箭头端点停在节点边界，避免穿过文字和交叉；题注压缩为一条“读图结论”：独立且具有共同率参数的Gamma变量除以其总和后得到Dirichlet随机向量；总量与归一化比例相互独立，二维情形退化为Beta分布，这一构造同时给出可复现的Dirichlet抽样方法；其余教学提示另起正文段落；保留原变量命名，并在图后加入一句“先看什么、再看什么、最终得到什么”的阅读顺序
建议图宽：>=0.72\textwidth（核心图）；按版心自适应
subagent1/subagent3复核重点：关系类型、条件方向与层级不能只靠颜色表达；概念边界与正文定义一致；图内文字、公式、符号、变量、题注和相邻正文完全一致；整页与局部渲染均无重叠、裁切、溢出、过密、过大留白或异常断行
B70｜图 34.5｜FIG-P662-01
章节：第 34 章《狄利克雷分布与共轭先验》；PDF物理页：769
类型：流程/网络图；严重度：中
图源：src/绘图源码/第05册\_采样方法主题模型与图排序/V5-C05/fig\_v5\_c05\_gamma\_normalization.tex
当前题注：图 34.5: 独立且具有共同率参数的 Gamma 变量除以其总和后得到 Dirichlet 随机向量；总量与归 一化比例相互独立，二维情形退化为 Beta 分布，这一构造同时给出可复现的 Dirichlet 抽样方法
唯一读图结论：三类别概率向量位于二维单纯形上，三个顶点分别代表一个类别概率为1；内部点的重心坐标就是三个类别概率，因此Dirichlet分布虽写在三维坐标中，实际支撑集只有二维
当前问题：所在页存在低于7.5pt文字（最小约6.07pt）；所在页有12个字符低于8.5pt；题注偏长，图结论与使用说明混在同一题注中；逐图视觉复核显示可读性仍可提升
本图专属修改方案：将图内正文、刻度、图例统一提升到源级至少9.5pt；PGFPlots设置tick label style={font=\small}, legend style={font=\small}，TikZ设置every node/.style={font=\small}；图宽优先提高到0.88--0.95\textwidth；不要通过\resizebox整体缩小文字；统一节点最小宽度、内边距与层级间距；箭头端点停在节点边界，避免穿过文字和交叉；题注压缩为一条“读图结论”：三类别概率向量位于二维单纯形上，三个顶点分别代表一个类别概率为1；内部点的重心坐标就是三个类别概率，因此Dirichlet分布虽写在三维坐标中，实际支撑集只有二维；其余教学提示另起正文段落；保留原变量命名，并在图后加入一句“先看什么、再看什么、最终得到什么”的阅读顺序
建议图宽：>=0.72\textwidth（核心图）；按版心自适应
subagent1/subagent3复核重点：阅读方向唯一、节点层级清楚、箭头端点停在边界、无回折交叉与语义歧义；图内文字、公式、符号、变量、题注和相邻正文完全一致；整页与局部渲染均无重叠、裁切、溢出、过密、过大留白或异常断行
B71｜图 34.6｜FIG-P665-01
章节：第 34 章《狄利克雷分布与共轭先验》；PDF物理页：772
类型：概念关系图；严重度：低
图源：src/绘图源码/第05册\_采样方法主题模型与图排序/V5-C05/fig\_v5\_c05\_exponential\_family\_moments.tex
当前题注：图 34.6: 把 Dirichlet 分布写成指数族后，充分统计量是 log 𝜃𝑘，对数配分函数对 𝛼𝑘的导数给出 𝔼[log Θ𝑘] = 𝜓(𝛼𝑘) −𝜓(𝛼0)；该对数矩不能用均值取对数替代
唯一读图结论：六组三元Dirichlet参数的精确均值与总浓度对照。图中不使用手工轮廓冒充由这些参数计算的密度等高线。
当前问题：题注偏长，图结论与使用说明混在同一题注中
本图专属修改方案：统一节点最小宽度、内边距与层级间距；箭头端点停在节点边界，避免穿过文字和交叉；题注压缩为一条“读图结论”：六组三元Dirichlet参数的精确均值与总浓度对照。图中不使用手工轮廓冒充由这些参数计算的密度等高线。；其余教学提示另起正文段落；保留原变量命名，并在图后加入一句“先看什么、再看什么、最终得到什么”的阅读顺序
建议图宽：>=0.72\textwidth（核心图）；按版心自适应
subagent1/subagent3复核重点：关系类型、条件方向与层级不能只靠颜色表达；概念边界与正文定义一致；图内文字、公式、符号、变量、题注和相邻正文完全一致；整页与局部渲染均无重叠、裁切、溢出、过密、过大留白或异常断行
B72｜图 34.7｜FIG-P667-01
章节：第 34 章《狄利克雷分布与共轭先验》；PDF物理页：774
类型：矩阵/表格式示意图；严重度：低
图源：src/绘图源码/第05册\_采样方法主题模型与图排序/V5-C05/fig\_v5\_c05\_conjugate\_update.tex
当前题注：图 34.7: Dirichlet– 多项共轭来自先验核与多项似然核中同一组 log 𝜃𝑖充分统计量：相乘只把指数 逐分量相加，因此后验参数是 𝛼+ 𝑛；保留归一化常数还可得到 Dirichlet– 多项边缘分布
唯一读图结论：Dirichlet参数可分解为均值方向$m=\alpha/\alpha\_0$和总浓度$\alpha\_0$：沿同一射线缩放参数不改变均值，却按$1/(\alpha\_0+1)$缩小方差与负协方差；负协方差来自各分量之和恒为1
当前问题：题注偏长，图结论与使用说明混在同一题注中
本图专属修改方案：按行列对齐，突出当前更新块；非关键数字改为省略号或在正文表格中给出；题注压缩为一条“读图结论”：Dirichlet参数可分解为均值方向$m=\alpha/\alpha\_0$和总浓度$\alpha\_0$：沿同一射线缩放参数不改变均值，却按$1/(\alpha\_0+1)$缩小方差与负协方差；负协方差来自各分量之和恒为1；其余教学提示另起正文段落；保留原变量命名，并在图后加入一句“先看什么、再看什么、最终得到什么”的阅读顺序
建议图宽：>=0.72\textwidth（核心图）；按版心自适应
subagent1/subagent3复核重点：行列语义、对齐、标题和分组层级清楚，避免把整张表缩成不可读图片；图内文字、公式、符号、变量、题注和相邻正文完全一致；整页与局部渲染均无重叠、裁切、溢出、过密、过大留白或异常断行
B73｜图 34.8｜FIG-P668-01
章节：第 34 章《狄利克雷分布与共轭先验》；PDF物理页：775
类型：概念关系图；严重度：高
图源：src/绘图源码/第05册\_采样方法主题模型与图排序/V5-C05/fig\_v5\_c05\_dirichlet\_shape\_atlas.tex
当前题注：图 34.8: 六组三元 Dirichlet 参数的精确均值与总浓度对照。图中不使用手工轮廓冒充由这些参数 计算的密度等高线。
唯一读图结论：Dirichlet--多项共轭来自先验核与多项似然核中同一组$\log\theta\_i$充分统计量：相乘只把指数逐分量相加，因此后验参数是$\boldsymbol\alpha+\boldsymbol n$；保留归一化常数还可得到Dirichlet--多项边缘分布
当前问题：所在页存在低于6pt文字（最小约4.68pt）；所在页小于8.5pt字符较多（41个）；题注偏长，图结论与使用说明混在同一题注中；逐图视觉复核判定为优先重绘/拆图对象
本图专属修改方案：将图内正文、刻度、图例统一提升到源级至少9.5pt；PGFPlots设置tick label style={font=\small}, legend style={font=\small}，TikZ设置every node/.style={font=\small}；图宽优先提高到0.88--0.95\textwidth；不要通过\resizebox整体缩小文字；把“定义/输入”和“计算/结论”拆为两幅子图，或按(a)(b)分面；每个面板只保留一个阅读任务；减少跨面板回折箭头，采用从左到右或从上到下的单向网格；长说明移到图后正文；统一节点最小宽度、内边距与层级间距；箭头端点停在节点边界，避免穿过文字和交叉；题注压缩为一条“读图结论”：Dirichlet--多项共轭来自先验核与多项似然核中同一组$\log\theta\_i$充分统计量：相乘只把指数逐分量相加，因此后验参数是$\boldsymbol\alpha+\boldsymbol n$；保留归一化常数还可得到Dirichlet--多项边缘分布；其余教学提示另起正文段落；保留原变量命名，并在图后加入一句“先看什么、再看什么、最终得到什么”的阅读顺序
建议图宽：>=0.72\textwidth（核心图）；按版心自适应
subagent1/subagent3复核重点：关系类型、条件方向与层级不能只靠颜色表达；概念边界与正文定义一致；图内文字、公式、符号、变量、题注和相邻正文完全一致；整页与局部渲染均无重叠、裁切、溢出、过密、过大留白或异常断行；必须评估拆图或重构，不得仅靠放大画布和整体缩放掩盖结构问题
B74｜图 34.9｜FIG-P669-01
章节：第 34 章《狄利克雷分布与共轭先验》；PDF物理页：775
类型：流程/网络图；严重度：高
图源：src/绘图源码/第05册\_采样方法主题模型与图排序/V5-C05/fig\_v5\_c05\_concentration\_mean.tex
当前题注：图 34.9: Dirichlet 参数可分解为均值方向 𝑚= 𝛼/𝛼0 和总浓度 𝛼0：沿同一射线缩放参数不改变均 值，却按 1/(𝛼0 + 1) 缩小方差与负协方差；负协方差来自各分量之和恒为 1
唯一读图结论：积分消去$\theta$后，下一类别的后验预测概率等于当前伪计数占总伪计数的比例；观测到类别$j$只增加该类计数，因而实现平滑并产生可顺序更新的强化预测，但这不是固定参数下的独立同分布序列
当前问题：所在页存在低于6pt文字（最小约4.68pt）；所在页小于8.5pt字符较多（41个）；题注偏长，图结论与使用说明混在同一题注中；逐图视觉复核判定为优先重绘/拆图对象
本图专属修改方案：将图内正文、刻度、图例统一提升到源级至少9.5pt；PGFPlots设置tick label style={font=\small}, legend style={font=\small}，TikZ设置every node/.style={font=\small}；图宽优先提高到0.88--0.95\textwidth；不要通过\resizebox整体缩小文字；把“定义/输入”和“计算/结论”拆为两幅子图，或按(a)(b)分面；每个面板只保留一个阅读任务；减少跨面板回折箭头，采用从左到右或从上到下的单向网格；长说明移到图后正文；统一节点最小宽度、内边距与层级间距；箭头端点停在节点边界，避免穿过文字和交叉；题注压缩为一条“读图结论”：积分消去$\theta$后，下一类别的后验预测概率等于当前伪计数占总伪计数的比例；观测到类别$j$只增加该类计数，因而实现平滑并产生可顺序更新的强化预测，但这不是固定参数下的独立同分布序列；其余教学提示另起正文段落；保留原变量命名，并在图后加入一句“先看什么、再看什么、最终得到什么”的阅读顺序
建议图宽：>=0.72\textwidth（核心图）；按版心自适应
subagent1/subagent3复核重点：阅读方向唯一、节点层级清楚、箭头端点停在边界、无回折交叉与语义歧义；图内文字、公式、符号、变量、题注和相邻正文完全一致；整页与局部渲染均无重叠、裁切、溢出、过密、过大留白或异常断行；必须评估拆图或重构，不得仅靠放大画布和整体缩放掩盖结构问题
B75｜图 34.10｜FIG-P670-01
章节：第 34 章《狄利克雷分布与共轭先验》；PDF物理页：777
类型：流程/网络图；严重度：中
图源：src/绘图源码/第05册\_采样方法主题模型与图排序/V5-C05/fig\_v5\_c05\_posterior\_predictive.tex
当前题注：图 34.10: 积分消去 𝜃后，下一类别的后验预测概率等于当前伪计数占总伪计数的比例；观测到类 别 𝑗只增加该类计数，因而实现平滑并产生可顺序更新的强化预测，但这不是固定参数下的独立 同分布序列
唯一读图结论：把Dirichlet分布写成指数族后，充分统计量是$\log\theta\_k$，对数配分函数对$\alpha\_k$的导数给出$\mathbb E[\log\Theta\_k]=\psi(\alpha\_k)-\psi(\alpha\_0)$；该对数矩不能用均值取对数替代
当前问题：所在页存在低于7.5pt文字（最小约6.42pt）；所在页有10个字符低于8.5pt；题注偏长，图结论与使用说明混在同一题注中；逐图视觉复核显示可读性仍可提升
本图专属修改方案：将图内正文、刻度、图例统一提升到源级至少9.5pt；PGFPlots设置tick label style={font=\small}, legend style={font=\small}，TikZ设置every node/.style={font=\small}；图宽优先提高到0.88--0.95\textwidth；不要通过\resizebox整体缩小文字；统一节点最小宽度、内边距与层级间距；箭头端点停在节点边界，避免穿过文字和交叉；题注压缩为一条“读图结论”：把Dirichlet分布写成指数族后，充分统计量是$\log\theta\_k$，对数配分函数对$\alpha\_k$的导数给出$\mathbb E[\log\Theta\_k]=\psi(\alpha\_k)-\psi(\alpha\_0)$；该对数矩不能用均值取对数替代；其余教学提示另起正文段落；保留原变量命名，并在图后加入一句“先看什么、再看什么、最终得到什么”的阅读顺序
建议图宽：>=0.72\textwidth（核心图）；按版心自适应
subagent1/subagent3复核重点：阅读方向唯一、节点层级清楚、箭头端点停在边界、无回折交叉与语义歧义；图内文字、公式、符号、变量、题注和相邻正文完全一致；整页与局部渲染均无重叠、裁切、溢出、过密、过大留白或异常断行
B76｜图 35.1｜FIG-P680-01
章节：第 35 章《潜在狄利克雷分配》；PDF物理页：789
类型：流程/网络图；严重度：低
图源：src/绘图源码/第05册\_采样方法主题模型与图排序/V5-C06/fig\_v5\_c06\_dependency\_graph.tex
当前题注：图 35.1: 本章从共享的文档 – 主题 – 单词条件结构分出两个模型目标：完整 Bayes LDA 由折叠 Gibbs 推断，点参数 LDA 变体由平均场变分 EM 估计；箭头表示学习依赖，不表示两个后验相同
唯一读图结论：本章从共享的文档--主题--单词条件结构分出两个模型目标：完整Bayes LDA由折叠Gibbs推断，点参数LDA变体由平均场变分EM估计；箭头表示学习依赖，不表示两个后验相同
当前问题：题注偏长，图结论与使用说明混在同一题注中
本图专属修改方案：统一节点最小宽度、内边距与层级间距；箭头端点停在节点边界，避免穿过文字和交叉；题注压缩为一条“读图结论”：本章从共享的文档--主题--单词条件结构分出两个模型目标：完整Bayes LDA由折叠Gibbs推断，点参数LDA变体由平均场变分EM估计；箭头表示学习依赖，不表示两个后验相同；其余教学提示另起正文段落；保留原变量命名，并在图后加入一句“先看什么、再看什么、最终得到什么”的阅读顺序
建议图宽：>=0.72\textwidth（核心图）；按版心自适应
subagent1/subagent3复核重点：阅读方向唯一、节点层级清楚、箭头端点停在边界、无回折交叉与语义歧义；图内文字、公式、符号、变量、题注和相邻正文完全一致；整页与局部渲染均无重叠、裁切、溢出、过密、过大留白或异常断行
B77｜图 35.2｜FIG-P683-01
章节：第 35 章《潜在狄利克雷分配》；PDF物理页：792
类型：流程/网络图；严重度：低
图源：src/绘图源码/第05册\_采样方法主题模型与图排序/V5-C06/fig\_v5\_c06\_plate\_graph.tex
当前题注：图 35.2: 完整 Bayes LDA 盘式图把超参数、潜变量和观测变量分开：每篇文档共享一个主题比例， 每个词位拥有一个主题指派，所有文档共享带 Dirichlet 先验的主题词分布；盘框标明重复次数， 箭头只表示条件依赖方向
唯一读图结论：完整Bayes LDA生成过程先为每个主题抽取主题--单词分布，再为每篇文档抽取主题比例，最后在每个词位先抽主题指派再抽观测单词；点参数变分EM使用的相关变体则把主题--单词分布视为待估参数
当前问题：题注偏长，图结论与使用说明混在同一题注中
本图专属修改方案：统一节点最小宽度、内边距与层级间距；箭头端点停在节点边界，避免穿过文字和交叉；题注压缩为一条“读图结论”：完整Bayes LDA生成过程先为每个主题抽取主题--单词分布，再为每篇文档抽取主题比例，最后在每个词位先抽主题指派再抽观测单词；点参数变分EM使用的相关变体则把主题--单词分布视为待估参数；其余教学提示另起正文段落；保留原变量命名，并在图后加入一句“先看什么、再看什么、最终得到什么”的阅读顺序
建议图宽：>=0.72\textwidth（核心图）；按版心自适应
subagent1/subagent3复核重点：阅读方向唯一、节点层级清楚、箭头端点停在边界、无回折交叉与语义歧义；图内文字、公式、符号、变量、题注和相邻正文完全一致；整页与局部渲染均无重叠、裁切、溢出、过密、过大留白或异常断行
B78｜图 35.3｜FIG-P684-01
章节：第 35 章《潜在狄利克雷分配》；PDF物理页：794
类型：流程/网络图；严重度：高
图源：src/绘图源码/第05册\_采样方法主题模型与图排序/V5-C06/fig\_v5\_c06\_generative\_process.tex
当前题注：图 35.3: 完整 Bayes LDA 生成过程先为每个主题抽取主题 – 单词分布，再为每篇文档抽取主题比 例，最后在每个词位先抽主题指派再抽观测单词；点参数变分 EM 使用的相关变体则把主题 – 单 词分布视为待估参数
唯一读图结论：完整Bayes LDA盘式图把超参数、潜变量和观测变量分开：每篇文档共享一个主题比例，每个词位拥有一个主题指派，所有文档共享带Dirichlet先验的主题词分布；盘框标明重复次数，箭头只表示条件依赖方向
当前问题：所在页存在低于6pt文字（最小约4.58pt）；所在页有19个字符低于8.5pt；题注偏长，图结论与使用说明混在同一题注中；逐图视觉复核判定为优先重绘/拆图对象
本图专属修改方案：将图内正文、刻度、图例统一提升到源级至少9.5pt；PGFPlots设置tick label style={font=\small}, legend style={font=\small}，TikZ设置every node/.style={font=\small}；图宽优先提高到0.88--0.95\textwidth；不要通过\resizebox整体缩小文字；把“定义/输入”和“计算/结论”拆为两幅子图，或按(a)(b)分面；每个面板只保留一个阅读任务；减少跨面板回折箭头，采用从左到右或从上到下的单向网格；长说明移到图后正文；统一节点最小宽度、内边距与层级间距；箭头端点停在节点边界，避免穿过文字和交叉；题注压缩为一条“读图结论”：完整Bayes LDA盘式图把超参数、潜变量和观测变量分开：每篇文档共享一个主题比例，每个词位拥有一个主题指派，所有文档共享带Dirichlet先验的主题词分布；盘框标明重复次数，箭头只表示条件依赖方向；其余教学提示另起正文段落；保留原变量命名，并在图后加入一句“先看什么、再看什么、最终得到什么”的阅读顺序
建议图宽：>=0.72\textwidth（核心图）；按版心自适应
subagent1/subagent3复核重点：阅读方向唯一、节点层级清楚、箭头端点停在边界、无回折交叉与语义歧义；图内文字、公式、符号、变量、题注和相邻正文完全一致；整页与局部渲染均无重叠、裁切、溢出、过密、过大留白或异常断行；必须评估拆图或重构，不得仅靠放大画布和整体缩放掩盖结构问题
B79｜图 35.4｜FIG-P687-01
章节：第 35 章《潜在狄利克雷分配》；PDF物理页：798
类型：流程/网络图；严重度：低
图源：src/绘图源码/第05册\_采样方法主题模型与图排序/V5-C06/fig\_v5\_c06\_collapsed\_gibbs\_counts.tex
当前题注：图 35.4: 折叠 Gibbs 更新先临时移除当前词位，再把文档 – 主题偏好与主题 – 单词证据相乘形成满 条件分布，最后抽取新主题并恢复计数；上标负 𝑖防止当前词位对自身产生重复计数
唯一读图结论：折叠Gibbs更新先临时移除当前词位，再把文档--主题偏好与主题--单词证据相乘形成满条件分布，最后抽取新主题并恢复计数；上标负$i$防止当前词位对自身产生重复计数
当前问题：题注偏长，图结论与使用说明混在同一题注中
本图专属修改方案：统一节点最小宽度、内边距与层级间距；箭头端点停在节点边界，避免穿过文字和交叉；题注压缩为一条“读图结论”：折叠Gibbs更新先临时移除当前词位，再把文档--主题偏好与主题--单词证据相乘形成满条件分布，最后抽取新主题并恢复计数；上标负$i$防止当前词位对自身产生重复计数；其余教学提示另起正文段落；保留原变量命名，并在图后加入一句“先看什么、再看什么、最终得到什么”的阅读顺序
建议图宽：>=0.72\textwidth（核心图）；按版心自适应
subagent1/subagent3复核重点：阅读方向唯一、节点层级清楚、箭头端点停在边界、无回折交叉与语义歧义；图内文字、公式、符号、变量、题注和相邻正文完全一致；整页与局部渲染均无重叠、裁切、溢出、过密、过大留白或异常断行
B80｜图 35.5｜FIG-P689-01
章节：第 35 章《潜在狄利克雷分配》；PDF物理页：801
类型：坐标/曲线图；严重度：低
图源：src/绘图源码/第05册\_采样方法主题模型与图排序/V5-C06/fig\_v5\_c06\_elbo\_geometry.tex
当前题注：图 35.5: 观测对数证据等于 ELBO 与变分分布到真实后验的 KL 散度之和；平均场坐标更新可使 ELBO 逐步不降，但非凸目标下有限运行通常只得到坐标稳定点或局部驻点，多启动比较也不构 成全局最优证明
唯一读图结论：观测对数证据等于ELBO与变分分布到真实后验的KL散度之和；平均场坐标更新可使ELBO逐步不降，但非凸目标下有限运行通常只得到坐标稳定点或局部驻点，多启动比较也不构成全局最优证明
当前问题：题注偏长，图结论与使用说明混在同一题注中
本图专属修改方案：固定axis宽高比例，减少刻度数量；用线型+点型双编码，标注只保留极值、阈值、最终点等关键对象；题注压缩为一条“读图结论”：观测对数证据等于ELBO与变分分布到真实后验的KL散度之和；平均场坐标更新可使ELBO逐步不降，但非凸目标下有限运行通常只得到坐标稳定点或局部驻点，多启动比较也不构成全局最优证明；其余教学提示另起正文段落；保留原变量命名，并在图后加入一句“先看什么、再看什么、最终得到什么”的阅读顺序
建议图宽：>=0.72\textwidth（核心图）；按版心自适应
subagent1/subagent3复核重点：坐标轴、刻度、单位、图例、曲线数据与正文公式一致；线型和点型可在灰度下区分；图内文字、公式、符号、变量、题注和相邻正文完全一致；整页与局部渲染均无重叠、裁切、溢出、过密、过大留白或异常断行
B81｜图 35.6｜FIG-P690-01
章节：第 35 章《潜在狄利克雷分配》；PDF物理页：801
类型：流程/网络图；严重度：低
图源：src/绘图源码/第05册\_采样方法主题模型与图排序/V5-C06/fig\_v5\_c06\_mean\_field\_graph.tex
当前题注：图 35.6: 固定主题 – 词参数 𝜑时，平均场近似把单文档后验中耦合的 𝜃𝑚与 𝑧𝑚𝑛替换为两个变分 因子族；被切断的是近似后验中的直接依赖，固定参数仍通过词似然进入责任度更新
唯一读图结论：固定主题--词参数$\boldsymbol\varphi$时，平均场近似把单文档后验中耦合的$\boldsymbol\theta\_m$与$z\_{mn}$替换为两个变分因子族；被切断的是近似后验中的直接依赖，固定参数仍通过词似然进入责任度更新
当前问题：题注偏长，图结论与使用说明混在同一题注中
本图专属修改方案：统一节点最小宽度、内边距与层级间距；箭头端点停在节点边界，避免穿过文字和交叉；题注压缩为一条“读图结论”：固定主题--词参数$\boldsymbol\varphi$时，平均场近似把单文档后验中耦合的$\boldsymbol\theta\_m$与$z\_{mn}$替换为两个变分因子族；被切断的是近似后验中的直接依赖，固定参数仍通过词似然进入责任度更新；其余教学提示另起正文段落；保留原变量命名，并在图后加入一句“先看什么、再看什么、最终得到什么”的阅读顺序
建议图宽：>=0.72\textwidth（核心图）；按版心自适应
subagent1/subagent3复核重点：阅读方向唯一、节点层级清楚、箭头端点停在边界、无回折交叉与语义歧义；图内文字、公式、符号、变量、题注和相邻正文完全一致；整页与局部渲染均无重叠、裁切、溢出、过密、过大留白或异常断行
B82｜图 35.7｜FIG-P694-01
章节：第 35 章《潜在狄利克雷分配》；PDF物理页：805
类型：流程/网络图；严重度：高
图源：src/绘图源码/第05册\_采样方法主题模型与图排序/V5-C06/fig\_v5\_c06\_variational\_updates.tex
当前题注：图 35.7: 点估计 LDA 变分 EM 含两层迭代：（a）每篇文档内交替更新责任度 𝜂𝑚与 Dirichlet 参数 𝛾𝑚直至局部收敛；（b）汇总全语料期望计数更新 𝜑，并以受保护 Newton 步更新 𝛼；两层均检查 ELBO 和硬迭代上限。
唯一读图结论：点估计LDA变分EM含两层迭代：（a）每篇文档内交替更新责任度$\boldsymbol\eta\_m$与Dirichlet参数$\boldsymbol\gamma\_m$直至局部收敛；（b）汇总全语料期望计数更新$\boldsymbol\varphi$，并以受保护Newton步更新$\boldsymbol\alpha$；两层均检查ELBO和硬迭代上限。
当前问题：题注偏长，图结论与使用说明混在同一题注中；逐图视觉复核判定为优先重绘/拆图对象
本图专属修改方案：把“定义/输入”和“计算/结论”拆为两幅子图，或按(a)(b)分面；每个面板只保留一个阅读任务；减少跨面板回折箭头，采用从左到右或从上到下的单向网格；长说明移到图后正文；统一节点最小宽度、内边距与层级间距；箭头端点停在节点边界，避免穿过文字和交叉；题注压缩为一条“读图结论”：点估计LDA变分EM含两层迭代：（a）每篇文档内交替更新责任度$\boldsymbol\eta\_m$与Dirichlet参数$\boldsymbol\gamma\_m$直至局部收敛；（b）汇总全语料期望计数更新$\boldsymbol\varphi$，并以受保护Newton步更新$\boldsymbol\alpha$；两层均检查ELBO和硬迭代上限。；其余教学提示另起正文段落；保留原变量命名，并在图后加入一句“先看什么、再看什么、最终得到什么”的阅读顺序
建议图宽：>=0.72\textwidth（核心图）；按版心自适应
subagent1/subagent3复核重点：阅读方向唯一、节点层级清楚、箭头端点停在边界、无回折交叉与语义歧义；图内文字、公式、符号、变量、题注和相邻正文完全一致；整页与局部渲染均无重叠、裁切、溢出、过密、过大留白或异常断行；必须评估拆图或重构，不得仅靠放大画布和整体缩放掩盖结构问题
B83｜图 35.8｜FIG-P695-01
章节：第 35 章《潜在狄利克雷分配》；PDF物理页：805
类型：概念关系图；严重度：高
图源：src/绘图源码/第05册\_采样方法主题模型与图排序/V5-C06/fig\_v5\_c06\_method\_comparison.tex
当前题注：图 35.8: 两条 LDA 推断路线并不针对同一后验：折叠 Gibbs 对完整 Bayes LDA 后验抽样；平均场变 分 EM 对不含主题词先验的点参数变体优化 ELBO。比较结果时须同时报告模型差异与推断差异。
唯一读图结论：两条LDA推断路线并不针对同一后验：折叠Gibbs对完整Bayes LDA后验抽样；平均场变分EM对不含主题词先验的点参数变体优化ELBO。比较结果时须同时报告模型差异与推断差异。
当前问题：题注偏长，图结论与使用说明混在同一题注中；逐图视觉复核判定为优先重绘/拆图对象
本图专属修改方案：把“定义/输入”和“计算/结论”拆为两幅子图，或按(a)(b)分面；每个面板只保留一个阅读任务；减少跨面板回折箭头，采用从左到右或从上到下的单向网格；长说明移到图后正文；统一节点最小宽度、内边距与层级间距；箭头端点停在节点边界，避免穿过文字和交叉；题注压缩为一条“读图结论”：两条LDA推断路线并不针对同一后验：折叠Gibbs对完整Bayes LDA后验抽样；平均场变分EM对不含主题词先验的点参数变体优化ELBO。比较结果时须同时报告模型差异与推断差异。；其余教学提示另起正文段落；保留原变量命名，并在图后加入一句“先看什么、再看什么、最终得到什么”的阅读顺序
建议图宽：>=0.72\textwidth（核心图）；按版心自适应
subagent1/subagent3复核重点：关系类型、条件方向与层级不能只靠颜色表达；概念边界与正文定义一致；图内文字、公式、符号、变量、题注和相邻正文完全一致；整页与局部渲染均无重叠、裁切、溢出、过密、过大留白或异常断行；必须评估拆图或重构，不得仅靠放大画布和整体缩放掩盖结构问题
B84｜图 36.1｜FIG-P713-01
章节：第 36 章《PageRank 算法》；PDF物理页：824
类型：概念关系图；严重度：中
图源：src/绘图源码/第05册\_采样方法主题模型与图排序/V5-C07/dependency\_graph.tex
当前题注：图 36.1: PageRank 的知识依赖：随机游走、平稳分布与幂法共同支撑图排序
唯一读图结论：PageRank的知识依赖：随机游走、平稳分布与幂法共同支撑图排序
当前问题：所在页存在低于7.5pt文字（最小约6.56pt）；所在页有9个字符低于8.5pt
本图专属修改方案：将图内正文、刻度、图例统一提升到源级至少9.5pt；PGFPlots设置tick label style={font=\small}, legend style={font=\small}，TikZ设置every node/.style={font=\small}；图宽优先提高到0.88--0.95\textwidth；不要通过\resizebox整体缩小文字；统一节点最小宽度、内边距与层级间距；箭头端点停在节点边界，避免穿过文字和交叉；保留原变量命名，并在图后加入一句“先看什么、再看什么、最终得到什么”的阅读顺序
建议图宽：>=0.72\textwidth（核心图）；按版心自适应
subagent1/subagent3复核重点：关系类型、条件方向与层级不能只靠颜色表达；概念边界与正文定义一致；图内文字、公式、符号、变量、题注和相邻正文完全一致；整页与局部渲染均无重叠、裁切、溢出、过密、过大留白或异常断行
B85｜图 36.2｜FIG-P715-01
章节：第 36 章《PageRank 算法》；PDF物理页：826
类型：流程/网络图；严重度：中
图源：src/绘图源码/第05册\_采样方法主题模型与图排序/V5-C07/web\_random\_walk.tex
当前题注：图 36.2: 列随机约定下的网页有向图，并给出与行随机马尔可夫链约定的显式转置桥。
唯一读图结论：列随机约定下的网页有向图，并给出与行随机马尔可夫链约定的显式转置桥。
当前问题：所在页存在低于7.5pt文字（最小约6.42pt）；所在页小于8.5pt字符较多（37个）；逐图视觉复核显示可读性仍可提升
本图专属修改方案：将图内正文、刻度、图例统一提升到源级至少9.5pt；PGFPlots设置tick label style={font=\small}, legend style={font=\small}，TikZ设置every node/.style={font=\small}；图宽优先提高到0.88--0.95\textwidth；不要通过\resizebox整体缩小文字；统一节点最小宽度、内边距与层级间距；箭头端点停在节点边界，避免穿过文字和交叉；保留原变量命名，并在图后加入一句“先看什么、再看什么、最终得到什么”的阅读顺序
建议图宽：>=0.72\textwidth（核心图）；按版心自适应
subagent1/subagent3复核重点：阅读方向唯一、节点层级清楚、箭头端点停在边界、无回折交叉与语义歧义；图内文字、公式、符号、变量、题注和相邻正文完全一致；整页与局部渲染均无重叠、裁切、溢出、过密、过大留白或异常断行
B86｜图 36.3｜FIG-P716-01
章节：第 36 章《PageRank 算法》；PDF物理页：829
类型：流程/网络图；严重度：中
图源：src/绘图源码/第05册\_采样方法主题模型与图排序/V5-C07/periodic\_dangling\_failures.tex
当前题注：图 36.3: 基本 PageRank 的两类结构性故障：周期振荡与悬挂零列
唯一读图结论：基本PageRank的两类结构性故障：周期振荡与悬挂零列
当前问题：所在页存在低于7.5pt文字（最小约6.42pt）；所在页有4个字符低于8.5pt
本图专属修改方案：将图内正文、刻度、图例统一提升到源级至少9.5pt；PGFPlots设置tick label style={font=\small}, legend style={font=\small}，TikZ设置every node/.style={font=\small}；图宽优先提高到0.88--0.95\textwidth；不要通过\resizebox整体缩小文字；统一节点最小宽度、内边距与层级间距；箭头端点停在节点边界，避免穿过文字和交叉；保留原变量命名，并在图后加入一句“先看什么、再看什么、最终得到什么”的阅读顺序
建议图宽：>=0.72\textwidth（核心图）；按版心自适应
subagent1/subagent3复核重点：阅读方向唯一、节点层级清楚、箭头端点停在边界、无回折交叉与语义歧义；图内文字、公式、符号、变量、题注和相邻正文完全一致；整页与局部渲染均无重叠、裁切、溢出、过密、过大留白或异常断行
B87｜图 36.4｜FIG-P717-01
章节：第 36 章《PageRank 算法》；PDF物理页：830
类型：概念关系图；严重度：高
图源：src/绘图源码/第05册\_采样方法主题模型与图排序/V5-C07/inbound\_contribution.tex
当前题注：图 36.4: 基本 PageRank 由入链贡献累加得到
唯一读图结论：基本PageRank由入链贡献累加得到
当前问题：所在页存在低于6pt文字（最小约4.58pt）；所在页小于8.5pt字符较多（45个）；逐图视觉复核判定为优先重绘/拆图对象
本图专属修改方案：将图内正文、刻度、图例统一提升到源级至少9.5pt；PGFPlots设置tick label style={font=\small}, legend style={font=\small}，TikZ设置every node/.style={font=\small}；图宽优先提高到0.88--0.95\textwidth；不要通过\resizebox整体缩小文字；把“定义/输入”和“计算/结论”拆为两幅子图，或按(a)(b)分面；每个面板只保留一个阅读任务；减少跨面板回折箭头，采用从左到右或从上到下的单向网格；长说明移到图后正文；统一节点最小宽度、内边距与层级间距；箭头端点停在节点边界，避免穿过文字和交叉；保留原变量命名，并在图后加入一句“先看什么、再看什么、最终得到什么”的阅读顺序
建议图宽：>=0.72\textwidth（核心图）；按版心自适应
subagent1/subagent3复核重点：关系类型、条件方向与层级不能只靠颜色表达；概念边界与正文定义一致；图内文字、公式、符号、变量、题注和相邻正文完全一致；整页与局部渲染均无重叠、裁切、溢出、过密、过大留白或异常断行；必须评估拆图或重构，不得仅靠放大画布和整体缩放掩盖结构问题
B88｜图 36.5｜FIG-P719-01
章节：第 36 章《PageRank 算法》；PDF物理页：831
类型：流程/网络图；严重度：中
图源：src/绘图源码/第05册\_采样方法主题模型与图排序/V5-C07/damping\_teleportation.tex
当前题注：图 36.5: 一般 PageRank 先修复悬挂列，再混合沿链转移与随机跳转
唯一读图结论：一般PageRank先修复悬挂列，再混合沿链转移与随机跳转
当前问题：所在页存在低于7.5pt文字（最小约6.21pt）；所在页小于8.5pt字符较多（30个）；逐图视觉复核显示可读性仍可提升
本图专属修改方案：将图内正文、刻度、图例统一提升到源级至少9.5pt；PGFPlots设置tick label style={font=\small}, legend style={font=\small}，TikZ设置every node/.style={font=\small}；图宽优先提高到0.88--0.95\textwidth；不要通过\resizebox整体缩小文字；统一节点最小宽度、内边距与层级间距；箭头端点停在节点边界，避免穿过文字和交叉；保留原变量命名，并在图后加入一句“先看什么、再看什么、最终得到什么”的阅读顺序
建议图宽：>=0.72\textwidth（核心图）；按版心自适应
subagent1/subagent3复核重点：阅读方向唯一、节点层级清楚、箭头端点停在边界、无回折交叉与语义歧义；图内文字、公式、符号、变量、题注和相邻正文完全一致；整页与局部渲染均无重叠、裁切、溢出、过密、过大留白或异常断行
B89｜图 36.6｜FIG-P720-01
章节：第 36 章《PageRank 算法》；PDF物理页：832
类型：流程/网络图；严重度：中
图源：src/绘图源码/第05册\_采样方法主题模型与图排序/V5-C07/simplex\_stationary\_contraction.tex
当前题注：图 36.6: 阻尼 PageRank 在概率单纯形上的压缩迭代与唯一平稳点
唯一读图结论：阻尼PageRank在概率单纯形上的压缩迭代与唯一平稳点
当前问题：所在页存在低于7.5pt文字（最小约6.42pt）；所在页有18个字符低于8.5pt；逐图视觉复核显示可读性仍可提升
本图专属修改方案：将图内正文、刻度、图例统一提升到源级至少9.5pt；PGFPlots设置tick label style={font=\small}, legend style={font=\small}，TikZ设置every node/.style={font=\small}；图宽优先提高到0.88--0.95\textwidth；不要通过\resizebox整体缩小文字；统一节点最小宽度、内边距与层级间距；箭头端点停在节点边界，避免穿过文字和交叉；保留原变量命名，并在图后加入一句“先看什么、再看什么、最终得到什么”的阅读顺序
建议图宽：>=0.72\textwidth（核心图）；按版心自适应
subagent1/subagent3复核重点：阅读方向唯一、节点层级清楚、箭头端点停在边界、无回折交叉与语义歧义；图内文字、公式、符号、变量、题注和相邻正文完全一致；整页与局部渲染均无重叠、裁切、溢出、过密、过大留白或异常断行
B90｜图 36.7｜FIG-P721-01
章节：第 36 章《PageRank 算法》；PDF物理页：834
类型：坐标/曲线图；严重度：高
图源：src/绘图源码/第05册\_采样方法主题模型与图排序/V5-C07/numerical\_rank\_trajectory.tex
当前题注：图 36.7: 数值例中 PageRank 迭代轨迹与最终排序
唯一读图结论：PageRank稀疏幂法依次执行输入检查、悬挂质量回填、稀疏乘法与阻尼更新，并以$\delta\_t=\lVert r^{(t+1)}-r^{(t)}\rVert\_1\le(1-d)\varepsilon$作为$\ell\_1$误差证书；不满足时继续迭代或按预算停止。
当前问题：所在页存在低于7.5pt文字（最小约6.42pt）；所在页有15个字符低于8.5pt；逐图视觉复核判定为优先重绘/拆图对象
本图专属修改方案：将图内正文、刻度、图例统一提升到源级至少9.5pt；PGFPlots设置tick label style={font=\small}, legend style={font=\small}，TikZ设置every node/.style={font=\small}；图宽优先提高到0.88--0.95\textwidth；不要通过\resizebox整体缩小文字；把“定义/输入”和“计算/结论”拆为两幅子图，或按(a)(b)分面；每个面板只保留一个阅读任务；减少跨面板回折箭头，采用从左到右或从上到下的单向网格；长说明移到图后正文；固定axis宽高比例，减少刻度数量；用线型+点型双编码，标注只保留极值、阈值、最终点等关键对象；保留原变量命名，并在图后加入一句“先看什么、再看什么、最终得到什么”的阅读顺序
建议图宽：>=0.72\textwidth（核心图）；按版心自适应
subagent1/subagent3复核重点：坐标轴、刻度、单位、图例、曲线数据与正文公式一致；线型和点型可在灰度下区分；图内文字、公式、符号、变量、题注和相邻正文完全一致；整页与局部渲染均无重叠、裁切、溢出、过密、过大留白或异常断行；必须评估拆图或重构，不得仅靠放大画布和整体缩放掩盖结构问题
B91｜图 36.8｜FIG-P722-01
章节：第 36 章《PageRank 算法》；PDF物理页：833
类型：流程/网络图；严重度：低
图源：src/绘图源码/第05册\_采样方法主题模型与图排序/V5-C07/power\_method\_flow\_convergence.tex
当前题注：图 36.8: PageRank 稀疏幂法依次执行输入检查、悬挂质量回填、稀疏乘法与阻尼更新，并以 𝛿𝑡= ‖𝑟(𝑡+1) −𝑟(𝑡)‖1 ≤(1 −𝑑)𝜀作为 ℓ1 误差证书；不满足时继续迭代或按预算停止。
唯一读图结论：数值例中PageRank迭代轨迹与最终排序
当前问题：题注偏长，图结论与使用说明混在同一题注中
本图专属修改方案：统一节点最小宽度、内边距与层级间距；箭头端点停在节点边界，避免穿过文字和交叉；题注压缩为一条“读图结论”：数值例中PageRank迭代轨迹与最终排序；其余教学提示另起正文段落；保留原变量命名，并在图后加入一句“先看什么、再看什么、最终得到什么”的阅读顺序
建议图宽：>=0.72\textwidth（核心图）；按版心自适应
subagent1/subagent3复核重点：阅读方向唯一、节点层级清楚、箭头端点停在边界、无回折交叉与语义歧义；图内文字、公式、符号、变量、题注和相邻正文完全一致；整页与局部渲染均无重叠、裁切、溢出、过密、过大留白或异常断行
B92｜图 37.1｜FIG-P734-01
章节：第 37 章《无监督学习方法总结》；PDF物理页：850
类型：流程/网络图；严重度：无
图源：src/绘图源码/第05册\_采样方法主题模型与图排序/V5-C08/dependency\_graph.tex
当前题注：图 37.1: 无监督学习方法总结的知识依赖：任务与数据结构共同约束表示、推断和模型选择
唯一读图结论：无监督学习方法总结的知识依赖：任务与数据结构共同约束表示、推断和模型选择
当前问题：未发现明显缺图、裁切、重叠或变量不一致；仍建议保留常规灰度与字号复核
本图专属修改方案：统一节点最小宽度、内边距与层级间距；箭头端点停在节点边界，避免穿过文字和交叉；保留原变量命名，并在图后加入一句“先看什么、再看什么、最终得到什么”的阅读顺序
建议图宽：>=0.72\textwidth（核心图）；按版心自适应
subagent1/subagent3复核重点：阅读方向唯一、节点层级清楚、箭头端点停在边界、无回折交叉与语义歧义；图内文字、公式、符号、变量、题注和相邻正文完全一致；整页与局部渲染均无重叠、裁切、溢出、过密、过大留白或异常断行
B93｜图 37.2｜FIG-P736-01
章节：第 37 章《无监督学习方法总结》；PDF物理页：852
类型：流程/网络图；严重度：高
图源：src/绘图源码/第05册\_采样方法主题模型与图排序/V5-C08/method\_family\_relationships.tex
当前题注：图 37.2: 无监督学习方法族与基础计算引擎的关系：聚类、降维、话题与图分析由不同假设组织， 并复用 SVD、 EM、后验推断与幂法
唯一读图结论：无监督学习方法族与基础计算引擎的关系：聚类、降维、话题与图分析由不同假设组织，并复用SVD、EM、后验推断与幂法
当前问题：题注偏长，图结论与使用说明混在同一题注中；逐图视觉复核判定为优先重绘/拆图对象
本图专属修改方案：把“定义/输入”和“计算/结论”拆为两幅子图，或按(a)(b)分面；每个面板只保留一个阅读任务；减少跨面板回折箭头，采用从左到右或从上到下的单向网格；长说明移到图后正文；统一节点最小宽度、内边距与层级间距；箭头端点停在节点边界，避免穿过文字和交叉；题注压缩为一条“读图结论”：无监督学习方法族与基础计算引擎的关系：聚类、降维、话题与图分析由不同假设组织，并复用SVD、EM、后验推断与幂法；其余教学提示另起正文段落；保留原变量命名，并在图后加入一句“先看什么、再看什么、最终得到什么”的阅读顺序
建议图宽：>=0.72\textwidth（核心图）；按版心自适应
subagent1/subagent3复核重点：阅读方向唯一、节点层级清楚、箭头端点停在边界、无回折交叉与语义歧义；图内文字、公式、符号、变量、题注和相邻正文完全一致；整页与局部渲染均无重叠、裁切、溢出、过密、过大留白或异常断行；必须评估拆图或重构，不得仅靠放大画布和整体缩放掩盖结构问题
B94｜图 37.3｜FIG-P737-01
章节：第 37 章《无监督学习方法总结》；PDF物理页：852
类型：流程/网络图；严重度：高
图源：src/绘图源码/第05册\_采样方法主题模型与图排序/V5-C08/task\_representation\_inference\_cube.tex
当前题注：图 37.3: 任务-表示-推断三轴分类：方法由三元组 (𝑇, 𝑅, 𝐼) 而非单一名称定义，选择时必须同时核 对输出语义、信息结构和计算路线
唯一读图结论：任务-表示-推断三轴分类：方法由三元组$(T,R,I)$而非单一名称定义，选择时必须同时核对输出语义、信息结构和计算路线
当前问题：题注偏长，图结论与使用说明混在同一题注中；逐图视觉复核判定为优先重绘/拆图对象
本图专属修改方案：把“定义/输入”和“计算/结论”拆为两幅子图，或按(a)(b)分面；每个面板只保留一个阅读任务；减少跨面板回折箭头，采用从左到右或从上到下的单向网格；长说明移到图后正文；统一节点最小宽度、内边距与层级间距；箭头端点停在节点边界，避免穿过文字和交叉；题注压缩为一条“读图结论”：任务-表示-推断三轴分类：方法由三元组$(T,R,I)$而非单一名称定义，选择时必须同时核对输出语义、信息结构和计算路线；其余教学提示另起正文段落；保留原变量命名，并在图后加入一句“先看什么、再看什么、最终得到什么”的阅读顺序
建议图宽：>=0.72\textwidth（核心图）；按版心自适应
subagent1/subagent3复核重点：阅读方向唯一、节点层级清楚、箭头端点停在边界、无回折交叉与语义歧义；图内文字、公式、符号、变量、题注和相邻正文完全一致；整页与局部渲染均无重叠、裁切、溢出、过密、过大留白或异常断行；必须评估拆图或重构，不得仅靠放大画布和整体缩放掩盖结构问题
B95｜图 37.4｜FIG-P740-01
章节：第 37 章《无监督学习方法总结》；PDF物理页：854
类型：流程/网络图；严重度：高
图源：src/绘图源码/第05册\_采样方法主题模型与图排序/V5-C08/matrix\_probability\_bridge.tex
当前题注：图 37.4: 矩阵分解与概率模型的桥接：低秩乘积是共同表示，损失、约束、归一化和先验决定模型 语义；下层条件高斯因子图给出 LSA/NMF 的一种概率解释
唯一读图结论：矩阵分解与概率模型的桥接：低秩乘积是共同表示，损失、约束、归一化和先验决定模型语义；右侧条件高斯因子图给出LSA/NMF的一种概率解释
当前问题：所在页存在低于7.5pt文字（最小约6.42pt）；所在页有6个字符低于8.5pt；题注偏长，图结论与使用说明混在同一题注中；逐图视觉复核判定为优先重绘/拆图对象
本图专属修改方案：将图内正文、刻度、图例统一提升到源级至少9.5pt；PGFPlots设置tick label style={font=\small}, legend style={font=\small}，TikZ设置every node/.style={font=\small}；图宽优先提高到0.88--0.95\textwidth；不要通过\resizebox整体缩小文字；把“定义/输入”和“计算/结论”拆为两幅子图，或按(a)(b)分面；每个面板只保留一个阅读任务；减少跨面板回折箭头，采用从左到右或从上到下的单向网格；长说明移到图后正文；统一节点最小宽度、内边距与层级间距；箭头端点停在节点边界，避免穿过文字和交叉；题注压缩为一条“读图结论”：矩阵分解与概率模型的桥接：低秩乘积是共同表示，损失、约束、归一化和先验决定模型语义；右侧条件高斯因子图给出LSA/NMF的一种概率解释；其余教学提示另起正文段落；保留原变量命名，并在图后加入一句“先看什么、再看什么、最终得到什么”的阅读顺序
建议图宽：>=0.72\textwidth（核心图）；按版心自适应
subagent1/subagent3复核重点：阅读方向唯一、节点层级清楚、箭头端点停在边界、无回折交叉与语义歧义；图内文字、公式、符号、变量、题注和相邻正文完全一致；整页与局部渲染均无重叠、裁切、溢出、过密、过大留白或异常断行；必须评估拆图或重构，不得仅靠放大画布和整体缩放掩盖结构问题
B96｜图 37.5｜FIG-P745-01
章节：第 37 章《无监督学习方法总结》；PDF物理页：857
类型：流程/网络图；严重度：高
图源：src/绘图源码/第05册\_采样方法主题模型与图排序/V5-C08/fig\_v5\_c08\_validation\_protocols.tex
当前题注：图 37.5: 两种无泄漏评价协议的数据流；左侧对应算法 37.1，右侧是另一个完整协议。
唯一读图结论：无泄漏的嵌套交叉验证：每个外层折只在$D\_{-k}$内完成内层模型与超参数选择，隔离的$D\_k$仅产生一次外层分数，最终汇总$K$个外层分数。
当前问题：逐图视觉复核判定为优先重绘/拆图对象
本图专属修改方案：把“定义/输入”和“计算/结论”拆为两幅子图，或按(a)(b)分面；每个面板只保留一个阅读任务；减少跨面板回折箭头，采用从左到右或从上到下的单向网格；长说明移到图后正文；统一节点最小宽度、内边距与层级间距；箭头端点停在节点边界，避免穿过文字和交叉；保留原变量命名，并在图后加入一句“先看什么、再看什么、最终得到什么”的阅读顺序
建议图宽：>=0.72\textwidth（核心图）；按版心自适应
subagent1/subagent3复核重点：阅读方向唯一、节点层级清楚、箭头端点停在边界、无回折交叉与语义歧义；图内文字、公式、符号、变量、题注和相邻正文完全一致；整页与局部渲染均无重叠、裁切、溢出、过密、过大留白或异常断行；必须评估拆图或重构，不得仅靠放大画布和整体缩放掩盖结构问题
B97｜图 37.6｜FIG-P748-01
章节：第 37 章《无监督学习方法总结》；PDF物理页：860
类型：概念关系图；严重度：高
图源：src/绘图源码/第05册\_采样方法主题模型与图排序/V5-C08/evaluation\_dashboard.tex
当前题注：图 37.6: 无监督学习的多证据评价面板：拟合、任务效用、稳定性、可解释性与计算代价需联合 报告
唯一读图结论：无监督学习的多证据评价面板：拟合、任务效用、稳定性、可解释性与计算代价需联合报告
当前问题：逐图视觉复核判定为优先重绘/拆图对象
本图专属修改方案：把“定义/输入”和“计算/结论”拆为两幅子图，或按(a)(b)分面；每个面板只保留一个阅读任务；减少跨面板回折箭头，采用从左到右或从上到下的单向网格；长说明移到图后正文；统一节点最小宽度、内边距与层级间距；箭头端点停在节点边界，避免穿过文字和交叉；保留原变量命名，并在图后加入一句“先看什么、再看什么、最终得到什么”的阅读顺序
建议图宽：>=0.72\textwidth（核心图）；按版心自适应
subagent1/subagent3复核重点：关系类型、条件方向与层级不能只靠颜色表达；概念边界与正文定义一致；图内文字、公式、符号、变量、题注和相邻正文完全一致；整页与局部渲染均无重叠、裁切、溢出、过密、过大留白或异常断行；必须评估拆图或重构，不得仅靠放大画布和整体缩放掩盖结构问题
B98｜图 37.7｜FIG-P750-01
章节：第 37 章《无监督学习方法总结》；PDF物理页：861
类型：流程/网络图；严重度：高
图源：src/绘图源码/第05册\_采样方法主题模型与图排序/V5-C08/method\_selection\_decision\_map.tex
当前题注：图 37.7: 方法选择地图的阅读顺序：先由首要任务确定输出语义与必要约束，再形成候选方法族， 最后以验证协议、计算预算和失败模式作二次筛选。
唯一读图结论：方法选择地图的阅读顺序：先由首要任务确定输出语义与必要约束，再形成候选方法族，最后以验证协议、计算预算和失败模式作二次筛选。
当前问题：题注偏长，图结论与使用说明混在同一题注中；逐图视觉复核判定为优先重绘/拆图对象
本图专属修改方案：把“定义/输入”和“计算/结论”拆为两幅子图，或按(a)(b)分面；每个面板只保留一个阅读任务；减少跨面板回折箭头，采用从左到右或从上到下的单向网格；长说明移到图后正文；统一节点最小宽度、内边距与层级间距；箭头端点停在节点边界，避免穿过文字和交叉；题注压缩为一条“读图结论”：方法选择地图的阅读顺序：先由首要任务确定输出语义与必要约束，再形成候选方法族，最后以验证协议、计算预算和失败模式作二次筛选。；其余教学提示另起正文段落；保留原变量命名，并在图后加入一句“先看什么、再看什么、最终得到什么”的阅读顺序
建议图宽：>=0.72\textwidth（核心图）；按版心自适应
subagent1/subagent3复核重点：阅读方向唯一、节点层级清楚、箭头端点停在边界、无回折交叉与语义歧义；图内文字、公式、符号、变量、题注和相邻正文完全一致；整页与局部渲染均无重叠、裁切、溢出、过密、过大留白或异常断行；必须评估拆图或重构，不得仅靠放大画布和整体缩放掩盖结构问题
B99｜图 37.8｜FIG-P756-01
章节：第 37 章《无监督学习方法总结》；PDF物理页：866
类型：流程/网络图；严重度：高
图源：src/绘图源码/第05册\_采样方法主题模型与图排序/V5-C08/full\_course\_synthesis\_map.tex
当前题注：图 37.8: 全书统计学习闭环分为两层：（a）问题定义、建模、计算、证据与边界构成五步主闭 环；（b）监督路线连接优化与线性代数，无监督路线连接概率推断，二者最终进入同一隔离 验证与可复现报告。
唯一读图结论：全书统计学习闭环分为两层：（a）问题定义、建模、计算、证据与边界构成五步主闭环；（b）监督路线连接优化与线性代数，无监督路线连接概率推断，二者最终进入同一隔离验证与可复现报告。
当前问题：题注偏长，图结论与使用说明混在同一题注中；逐图视觉复核判定为优先重绘/拆图对象
本图专属修改方案：把“定义/输入”和“计算/结论”拆为两幅子图，或按(a)(b)分面；每个面板只保留一个阅读任务；减少跨面板回折箭头，采用从左到右或从上到下的单向网格；长说明移到图后正文；统一节点最小宽度、内边距与层级间距；箭头端点停在节点边界，避免穿过文字和交叉；题注压缩为一条“读图结论”：全书统计学习闭环分为两层：（a）问题定义、建模、计算、证据与边界构成五步主闭环；（b）监督路线连接优化与线性代数，无监督路线连接概率推断，二者最终进入同一隔离验证与可复现报告。；其余教学提示另起正文段落；保留原变量命名，并在图后加入一句“先看什么、再看什么、最终得到什么”的阅读顺序
建议图宽：>=0.72\textwidth（核心图）；按版心自适应
subagent1/subagent3复核重点：阅读方向唯一、节点层级清楚、箭头端点停在边界、无回折交叉与语义歧义；图内文字、公式、符号、变量、题注和相邻正文完全一致；整页与局部渲染均无重叠、裁切、溢出、过密、过大留白或异常断行；必须评估拆图或重构，不得仅靠放大画布和整体缩放掩盖结构问题
附录 C｜66 道正文例题逐题执行索引
附录 C 只列任务路线；正式数学公式必须从原 LaTeX 和逐例题文件中恢复并重新计算。每题完成后在源码中只保留一组不重复的核验与一个最终结论。
C01｜例题 1.1：三样本数据的类型核对
章节：第 1 章《数学语言、符号约定与学习路线》；PDF物理页：17
源码：src/讲义源码/第01册\_数学基础与统计学习基本理论/chapters/V1-C01.tex，约第 121 行
严重度：无
当前问题：未发现明显结构性问题；建议把现有解答的开头改为本题专属方法触发语。
推荐解题路线：先声明对象、定义域和维数，再执行计算；每一步都检查运算合法性，并把结果代回原条件。
推荐核验：检查每个矩阵乘法的内侧维数，随后把结果代回原式；若有投影/分解，再检查正交性或重构关系。
C02｜例题 2.1：二维投影与残差
章节：第 2 章《线性代数基础》；PDF物理页：30
源码：src/讲义源码/第01册\_数学基础与统计学习基本理论/chapters/V1-C02.tex，约第 149 行
严重度：无
当前问题：未发现明显结构性问题；建议把现有解答的开头改为本题专属方法触发语。
推荐解题路线：把投影点写成标量倍数，先求投影系数，再求残差；用“残差与子空间正交”和勾股关系双重核验。
推荐核验：检查每个矩阵乘法的内侧维数，随后把结果代回原式；若有投影/分解，再检查正交性或重构关系。
C03｜例题 3.1：二元二次函数
章节：第 3 章《多元微积分与矩阵微分》；PDF物理页：50
源码：src/讲义源码/第01册\_数学基础与统计学习基本理论/chapters/V1-C03.tex，约第 157 行
严重度：低
当前问题：开头使用批量模板，需改为本题专属题意翻译
推荐解题路线：逐项求偏导并组装Hessian；先验证驻点，再用正定性、特征值或配方法判断极值性质。
推荐核验：检查每个矩阵乘法的内侧维数，随后把结果代回原式；若有投影/分解，再检查正交性或重构关系。
C04｜例题 4.1：骰子事件并集的两种核验
章节：第 4 章《概率论基础》；PDF物理页：65
源码：src/讲义源码/第01册\_数学基础与统计学习基本理论/chapters/V1-C04.tex，约第 90 行
严重度：低
当前问题：开头使用批量模板，需改为本题专属题意翻译
推荐解题路线：先写支持集、参数范围或定义域，再按定义逐项计算；最后检查归一化、非负性或边界条件。
推荐核验：将最终结果代回题面条件，检查数值、符号、边界和所求对象是否全部回答。
C05｜例题 4.2：方差分解
章节：第 4 章《概率论基础》；PDF物理页：68
源码：src/讲义源码/第01册\_数学基础与统计学习基本理论/chapters/V1-C04.tex，约第 237 行
严重度：低
当前问题：开头使用批量模板，需改为本题专属题意翻译
推荐解题路线：直接使用全方差公式，把组内方差与组间均值方差分别算清，再用二阶矩公式独立核验。
推荐核验：将最终结果代回题面条件，检查数值、符号、边界和所求对象是否全部回答。
C06｜例题 4.3：医学筛查的基率效应
章节：第 4 章《概率论基础》；PDF物理页：71
源码：src/讲义源码/第01册\_数学基础与统计学习基本理论/chapters/V1-C04.tex，约第 354 行
严重度：低
当前问题：开头使用批量模板，需改为本题专属题意翻译
推荐解题路线：先定义事件与互斥完备来源，写出证据概率，再用贝叶斯公式归一化；最后检查后验概率之和或赔率结果。
推荐核验：检查所有概率或权重非负，且在规定维度上求和为1；若有条件概率，再确认分母严格为正。
C07｜例题 5.1：十次伯努利试验的极大似然
章节：第 5 章《常用分布与统计推断》；PDF物理页：86
源码：src/讲义源码/第01册\_数学基础与统计学习基本理论/chapters/V1-C05.tex，约第 242 行
严重度：低
当前问题：开头使用批量模板，需改为本题专属题意翻译
推荐解题路线：先把独立伯努利样本的联合概率写成似然，取对数把乘积化为和；在参数区间内求驻点，并单独检查全成功或全失败时的边界解。
推荐核验：把候选参数代回得分方程；再检查其属于[0,1]，并与边界对数似然比较，确认取得最大值而非仅是驻点。
C08｜例题 6.1：二元分布的双向KL比较
章节：第 6 章《信息论基础》；PDF物理页：104
源码：src/讲义源码/第01册\_数学基础与统计学习基本理论/chapters/V1-C06.tex，约第 273 行
严重度：低
当前问题：开头使用批量模板，需改为本题专属题意翻译
推荐解题路线：按KL定义逐项代入两个方向的概率比，分别计算D(P∥Q)与D(Q∥P)；把非对称性归因于期望所用分布不同，而不是计算误差。
推荐核验：核对P、Q均为合法概率分布，所有被除概率为正；结果应非负，且两个方向一般不相等。
C09｜例题 7.1：带非负约束的二次问题
章节：第 7 章《凸优化与拉格朗日对偶》；PDF物理页：122
源码：src/讲义源码/第01册\_数学基础与统计学习基本理论/chapters/V1-C07.tex，约第 231 行
严重度：无
当前问题：未发现明显结构性问题；建议把现有解答的开头改为本题专属方法触发语。
推荐解题路线：把约束统一为标准方向，写出拉格朗日函数，依次检查原始可行、对偶可行、驻点与互补松弛，最后解释活动约束。
推荐核验：把候选解代回可行性与一阶条件；有约束时逐项核对KKT，有二阶信息时检查曲率或目标值。
C10｜例题 7.2：原点到半空间的KKT投影
章节：第 7 章《凸优化与拉格朗日对偶》；PDF物理页：130
源码：src/讲义源码/第01册\_数学基础与统计学习基本理论/chapters/V1-C07.tex，约第 554 行
严重度：无
当前问题：未发现明显结构性问题；建议把现有解答的开头改为本题专属方法触发语。
推荐解题路线：把约束写成g(x)=b-a^{T}x≤0，建立拉格朗日函数；由驻点得x=λa，再用活动约束a^{T}x=b求λ，最后逐项验证KKT。
推荐核验：核对原始可行性a^{T}x≥b、λ≥0、驻点x-λa=0与互补松弛λ(b-a^{T}x)=0，并确认目标值最小。
C11｜例题 8.1：正定二次函数的一步Newton更新
章节：第 8 章《数值优化方法》；PDF物理页：141
源码：src/讲义源码/第01册\_数学基础与统计学习基本理论/chapters/V1-C08.tex，约第 197 行
严重度：低
当前问题：解答夹带实现状态码，首次阅读主线可能被工程语义打断
推荐解题路线：先求梯度与Hessian，再代入Newton公式x^{+}=x-H^{-1}∇f(x)；利用正定二次函数的常Hessian说明一步到达唯一极小点。
推荐核验：把新点代回梯度，确认∇f(x^{+})=0；同时检查Hessian正定，从而驻点是唯一全局极小点。
C12｜例题 8.2：病态二次函数的三种尺度处理
章节：第 8 章《数值优化方法》；PDF物理页：151
源码：src/讲义源码/第01册\_数学基础与统计学习基本理论/chapters/V1-C08.tex，约第 570 行
严重度：无
当前问题：未发现明显结构性问题；建议把现有解答的开头改为本题专属方法触发语。
推荐解题路线：先比较Hessian两个特征方向的曲率比；固定步长梯度法受最大曲率限制，Newton用H^{-1}消除尺度，BFGS则通过割线信息逐步学习逆曲率。
推荐核验：分别检查固定步长的稳定范围、Newton更新后的零梯度，以及BFGS更新是否满足割线条件并保持正定近似。
C13｜例题 9.1：两个候选分类规则的经验比较
章节：第 9 章《统计学习的基本框架》；PDF物理页：162
源码：src/讲义源码/第01册\_数学基础与统计学习基本理论/chapters/V1-C09.tex，约第 172 行
严重度：无
当前问题：未发现明显结构性问题；建议把现有解答的开头改为本题专属方法触发语。
推荐解题路线：对每个候选规则逐样本计算0–1损失并求平均经验风险；最后严格执行题面预先规定的并列规则，不能事后改规则。
推荐核验：复查四个样本的预测表，确认错误计数与风险一致；若风险并列，再确认选择结果完全由题设并列规则决定。
C14｜例题 10.1：训练—测试错误率差距
章节：第 10 章《模型评估、选择与泛化》；PDF物理页：179
源码：src/讲义源码/第01册\_数学基础与统计学习基本理论/chapters/V1-C10.tex，约第 205 行
严重度：无
当前问题：未发现明显结构性问题；建议把现有解答的开头改为本题专属方法触发语。
推荐解题路线：分别用“错分数/样本数”计算训练与测试错误率，再作同一方向的差；最后区分观测到的误差差距与真实泛化差距。
推荐核验：核对两个分母分别是200与80，错误率均在[0,1]；差值的正负与文字解释保持一致，且不把一次测试差距当作必然规律。
C15｜例题 10.2：验证误差选择多项式次数
章节：第 10 章《模型评估、选择与泛化》；PDF物理页：181
源码：src/讲义源码/第01册\_数学基础与统计学习基本理论/chapters/V1-C10.tex，约第 282 行
严重度：中
当前问题：结论重复输出
推荐解题路线：把每个多项式次数的验证误差放在同一验证协议下比较，按最小验证误差选次数；若并列，使用预先约定的复杂度优先规则。
推荐核验：确认选择过程只使用训练/验证数据；测试集不得参与次数选择，最终只对选定模型评估一次。
C16｜例题 11.1：混淆矩阵的四项分类指标
章节：第 11 章《监督学习任务与应用》；PDF物理页：198
源码：src/讲义源码/第01册\_数学基础与统计学习基本理论/chapters/V1-C11.tex，约第 173 行
严重度：中
当前问题：把“混淆矩阵”误套为矩阵乘法/维数题模板
推荐解题路线：先固定“正类”的含义，再由TP、FP、FN、TN写出四个指标的分子和分母；逐项代入，最后用样本总数与F1调和平均式核验。
推荐核验：检查TP+FP+FN+TN等于总样本数；精确率与召回率分母均非零；F1应等于2PR/(P+R)且位于[0,1]。
C17｜例题 12.1：一次误分类更新
章节：第 12 章《感知机》；PDF物理页：215
源码：src/讲义源码/第02册\_基础监督学习方法/chapters/V2-C01.tex，约第 242 行
严重度：低
当前问题：开头使用批量模板，需改为本题专属题意翻译
推荐解题路线：按给定样本顺序逐点计算带符号分数；只在误分类时更新参数，并在结束时对全部样本重新计算带符号分数，确认整轮不再更新。
推荐核验：对全部给定样本重新计算预测或带符号分数，确认分类、计数与最终指标一致。
C18｜例题 12.2：原始形式的手工执行
章节：第 12 章《感知机》；PDF物理页：217
源码：src/讲义源码/第02册\_基础监督学习方法/chapters/V2-C01.tex，约第 347 行
严重度：中
当前问题：感知机手算题误套为候选模型与数据隔离模板；解答夹带实现状态码，首次阅读主线可能被工程语义打断
推荐解题路线：按给定样本顺序逐点计算带符号分数；只在误分类时更新参数，并在结束时对全部样本重新计算带符号分数，确认整轮不再更新。
推荐核验：对全部给定样本重新计算预测或带符号分数，确认分类、计数与最终指标一致。
C19｜例题 12.3：线性不可分的异或结构
章节：第 12 章《感知机》；PDF物理页：224
源码：src/讲义源码/第02册\_基础监督学习方法/chapters/V2-C01.tex，约第 593 行
严重度：低
当前问题：开头使用批量模板，需改为本题专属题意翻译
推荐解题路线：假设存在二维线性分类器，对四个异或点分别写出带符号不等式；把相应不等式相加，推出互相矛盾的条件，从而否定线性可分。
推荐核验：确认反证只使用同一个w,b；把四个标签逐点代回，检查矛盾来自异或结构而不是某个点抄错。
C20｜例题 13.1：距离阶数改变近邻
章节：第 13 章《法》；PDF物理页：236
源码：src/讲义源码/第02册\_基础监督学习方法/chapters/V2-C02.tex，约第 211 行
严重度：低
当前问题：开头使用批量模板，需改为本题专属题意翻译
推荐解题路线：分别计算查询点到两个候选点的L1距离与L2距离；每一种度量独立排序，比较距离阶数改变后最近邻是否翻转。
推荐核验：检查每个距离都满足非负性，并逐项展开绝对值或平方；同一度量下只比较同量纲结果。
C21｜例题 13.2：六点平衡kd树
章节：第 13 章《法》；PDF物理页：241
源码：src/讲义源码/第02册\_基础监督学习方法/chapters/V2-C02.tex，约第 424 行
严重度：低
当前问题：开头使用批量模板，需改为本题专属题意翻译
推荐解题路线：按题设切分轴规则选择中位点作为结点，递归构造左右子树；完成后检查每层切分轴、子树点集与树的平衡性。
推荐核验：中序/区域核对每个样本恰出现一次；每个左、右子树都满足对应切分不等式，树高与六点规模相符。
C22｜例题 13.3：不同$L\_p$距离下的最近邻
章节：第 13 章《法》；PDF物理页：246
源码：src/讲义源码/第02册\_基础监督学习方法/chapters/V2-C02.tex，约第 593 行
严重度：低
当前问题：开头使用批量模板，需改为本题专属题意翻译
推荐解题路线：把两候选距离写成4与3·2^{1/p}，先解二者相等的临界p，再分p区间判断谁更近；不要只凭二维图形猜测。
推荐核验：代入p=1、p=2及一个大p作三点核验；临界值两侧的大小关系必须与2^{1/p}随p递减一致。
C23｜例题 14.1：加一平滑后的朴素Bayes分类
章节：第 14 章《朴素贝叶斯法》；PDF物理页：262
源码：src/讲义源码/第02册\_基础监督学习方法/chapters/V2-C03.tex，约第 440 行
严重度：低
当前问题：开头使用批量模板，需改为本题专属题意翻译
推荐解题路线：先用加一平滑计算类别先验和各条件概率，再把每类的未归一化后验分数写成乘积或对数和；比较分数确定类别。
推荐核验：检查每个类别下的条件概率按特征取值归一化，平滑后无零概率；用同一公共分母比较两个后验分数。
C24｜例题 15.1：八样本二叉划分的信息增益
章节：第 15 章《决策树》；PDF物理页：278
源码：src/讲义源码/第02册\_基础监督学习方法/chapters/V2-C04.tex，约第 320 行
严重度：低
当前问题：开头使用批量模板，需改为本题专属题意翻译
推荐解题路线：先算父结点经验熵，再按候选特征分组计算条件熵；信息增益等于二者之差，按增益最大选择划分。
推荐核验：检查各子集权重之和为1，条件熵是加权平均；信息增益非负且不超过父结点熵。
C25｜例题 15.2：信息增益与基尼一致选择纯划分
章节：第 15 章《决策树》；PDF物理页：290
源码：src/讲义源码/第02册\_基础监督学习方法/chapters/V2-C04.tex，约第 840 行
严重度：低
当前问题：开头使用批量模板，需改为本题专属题意翻译
推荐解题路线：对每个候选划分分别计算信息增益和加权基尼指数；前者取大、后者取小，并说明二者为何在纯划分上给出同一选择。
推荐核验：核对每个子结点类别比例归一化；纯结点的熵和基尼均为0，两个准则的排序方向不能写反。
C26｜例题 16.1：一次概率预测与阈值决策
章节：第 16 章《逻辑斯谛回归》；PDF物理页：309
源码：src/讲义源码/第02册\_基础监督学习方法/chapters/V2-C05.tex，约第 478 行
严重度：低
当前问题：开头使用批量模板，需改为本题专属题意翻译
推荐解题路线：先算线性预测量，再经逻辑斯谛函数得到概率；明确阈值与标签规则，并检查概率在(0,1)内。
推荐核验：检查所有概率或权重非负，且在规定维度上求和为1；若有条件概率，再确认分母严格为正。
C27｜例题 17.1：两事件约束的最大熵分布
章节：第 17 章《最大熵模型》；PDF物理页：331
源码：src/讲义源码/第03册\_优化模型与序列模型/chapters/V3-C01.tex，约第 566 行
严重度：低
当前问题：开头使用批量模板，需改为本题专属题意翻译
推荐解题路线：列出有限样本空间上的概率变量与线性约束，用拉格朗日乘子求指数族形式；利用对称性或约束方程确定参数。
推荐核验：检查所得概率全部非负且和为1，满足两项事件约束；再与其他可行分布比较或用严格凹性确认熵最大。
C28｜例题 18.1：一维软间隔状态判定
章节：第 18 章《支持向量机》；PDF物理页：361
源码：src/讲义源码/第03册\_优化模型与序列模型/chapters/V3-C02.tex，约第 795 行
严重度：无
当前问题：未发现明显结构性问题；建议把现有解答的开头改为本题专属方法触发语。
推荐解题路线：把约束统一为标准方向，写出拉格朗日函数，依次检查原始可行、对偶可行、驻点与互补松弛，最后解释活动约束。
推荐核验：把候选解代回可行性与一阶条件；有约束时逐项核对KKT，有二阶信息时检查曲率或目标值。
C29｜例题 19.1：两轮AdaBoost的完整计算
章节：第 19 章《提升方法》；PDF物理页：390
源码：src/讲义源码/第03册\_优化模型与序列模型/chapters/V3-C03.tex，约第 707 行
严重度：低
当前问题：解答信息密度较高，初学者阅读时需要分段
推荐解题路线：逐轮计算加权错误率、分类器权重和样本权重归一化，再形成加法模型；每轮都检查权重和为1。
推荐核验：检查所有概率或权重非负，且在规定维度上求和为1；若有条件概率，再确认分母严格为正。
C30｜例题 20.1：责任度加权的高斯混合M步
章节：第 20 章《EM算法及其推广》；PDF物理页：413
源码：src/讲义源码/第03册\_优化模型与序列模型/chapters/V3-C04.tex，约第 602 行
严重度：低
当前问题：开头使用批量模板，需改为本题专属题意翻译
推荐解题路线：把责任度视为每个样本对各高斯成分的软计数；对混合权重、均值和方差分别用加权充分统计量更新。
推荐核验：每个样本的责任度和为1，更新后的混合权重和为1、方差非负；把新参数代回检查维数与加权计数。
C31｜例题 20.2：三硬币模型的一轮EM
章节：第 20 章《EM算法及其推广》；PDF物理页：424
源码：src/讲义源码/第03册\_优化模型与序列模型/chapters/V3-C04.tex，约第 1025 行
严重度：低
当前问题：开头使用批量模板，需改为本题专属题意翻译
推荐解题路线：E步计算每次观测由隐含硬币产生的后验概率；M步用这些后验软计数更新三枚硬币参数，并清楚区分旧参数与新参数。
推荐核验：检查所有责任度在[0,1]，新参数由合法计数比得到；复算观测对数似然，确认一轮EM不降低它。
C32｜例题 21.1：两状态HMM的前向概率
章节：第 21 章《隐马尔可夫模型》；PDF物理页：443
源码：src/讲义源码/第03册\_优化模型与序列模型/chapters/V3-C05.tex，约第 513 行
严重度：低
当前问题：开头使用批量模板，需改为本题专属题意翻译
推荐解题路线：按初始分布×发射概率初始化前向量，再执行“上一时刻前向量×转移×当前发射”的递推；最后对终态求和得到观测序列概率。
推荐核验：前向量分量应非负；其分量和是前缀观测概率而不是1。可枚举全部隐藏路径，核对总概率一致。
C33｜例题 21.2：两状态HMM的Viterbi路径
章节：第 21 章《隐马尔可夫模型》；PDF物理页：455
源码：src/讲义源码/第03册\_优化模型与序列模型/chapters/V3-C05.tex，约第 1031 行
严重度：低
当前问题：开头使用批量模板，需改为本题专属题意翻译
推荐解题路线：初始化每个状态的最优前缀概率，递推时对前驱取最大并记录回溯指针；终止后从最大终态沿指针反向恢复整条路径。
推荐核验：把得到的路径逐项代入初始、转移与发射概率求联合概率；与所有候选路径或动态规划终值比较，确认确为最大。
C34｜例题 22.1：手工执行三步Viterbi
章节：第 22 章《条件随机场》；PDF物理页：478
源码：src/讲义源码/第03册\_优化模型与序列模型/chapters/V3-C06.tex，约第 665 行
严重度：低
当前问题：开头使用批量模板，需改为本题专属题意翻译
推荐解题路线：把线性链CRF的局部特征加权和写成路径得分；按Viterbi递推取最大并保存前驱，最后回溯得到最优标记序列。
推荐核验：直接计算返回路径的总得分，并与动态规划终值一致；小规模例可枚举全部标记序列作独立核验。
C35｜例题 23.1：代价与资源共同约束下的方法选择
章节：第 23 章《监督学习方法总结》；PDF物理页：494
源码：src/讲义源码/第03册\_优化模型与序列模型/chapters/V3-C07.tex，约第 329 行
严重度：无
当前问题：未发现明显结构性问题；建议把现有解答的开头改为本题专属方法触发语。
推荐解题路线：先用延迟上限筛掉不可部署的方法，再在可行候选中比较召回率；当差异不超过题设容差时，按资源更低或模型更简单的预先规则选择。
推荐核验：确认核模型因18毫秒被排除；其余候选的召回差是否落在0.02容差内，并明确最终选择满足延迟约束。
C36｜例题 24.1：两个候选表示维数的选择
章节：第 24 章《无监督学习概论》；PDF物理页：514
源码：src/讲义源码/第04册\_无监督学习与矩阵分解/chapters/V4-C01.tex，约第 460 行
严重度：高
当前问题：表示维数选择题误套为矩阵乘法/投影模板；结论重复输出
推荐解题路线：先固定验证损失、稳定性和复杂度三项指标的方向及权重，再按同一评分公式计算d=2与d=10；选择总分较小者并同时报告原始指标。
推荐核验：直接计算两总分之差核对排序；确认权重在比较前已登记，测试集未参与表示维数选择，结论只输出一次。
C37｜例题 25.1：五点的k均值计算
章节：第 25 章《聚类方法》；PDF物理页：536
源码：src/讲义源码/第04册\_无监督学习与矩阵分解/chapters/V4-C02.tex，约第 759 行
严重度：低
当前问题：开头使用批量模板，需改为本题专属题意翻译
推荐解题路线：每轮先按平方欧氏距离把每个点分配给最近中心，并按题设规则处理并列；再用簇内样本均值更新中心，重复到分配不变。
推荐核验：稳定时每个中心必须等于所属点的均值，且所有点重新分配后类别不变；计算簇内平方和核对目标值。
C38｜例题 26.1：零矩阵回归例
章节：第 26 章《奇异值分解》；PDF物理页：549
源码：src/讲义源码/第04册\_无监督学习与矩阵分解/chapters/V4-C03.tex，约第 368 行
严重度：低
当前问题：解答夹带实现状态码，首次阅读主线可能被工程语义打断
推荐解题路线：先判断零矩阵的秩为0，因此紧SVD没有正奇异值列；写清U\_r、Σ\_r、V\_r的空维数，并解释算法为何应返回退化但合法的结果。
推荐核验：核对U\_rΣ\_rV\_r^T仍重构零矩阵；任何需要除以正奇异值的步骤都必须因r=0而跳过，不能产生0/0。
C39｜例题 26.2：一个长矩阵的完整、紧与截断SVD
章节：第 26 章《奇异值分解》；PDF物理页：558
源码：src/讲义源码/第04册\_无监督学习与矩阵分解/chapters/V4-C03.tex，约第 791 行
严重度：无
当前问题：未发现明显结构性问题；建议把现有解答的开头改为本题专属方法触发语。
推荐解题路线：先由A^TA求右奇异向量和奇异值，再构造左奇异向量；区分完整、紧与秩1截断SVD，并用Eckart–Young结论给误差。
推荐核验：检查U、V列正交且UΣV^T=A；秩1近似的谱范数误差为下一奇异值，Frobenius误差为被舍弃奇异值平方和的平方根。
C40｜例题 27.1：二维PCA投影与重构
章节：第 27 章《主成分分析》；PDF物理页：582
源码：src/讲义源码/第04册\_无监督学习与矩阵分解/chapters/V4-C04.tex，约第 644 行
严重度：无
当前问题：未发现明显结构性问题；建议把现有解答的开头改为本题专属方法触发语。
推荐解题路线：先求协方差矩阵最大特征值及单位特征向量，计算方差贡献率；将样本中心化后投影到主轴，再映射回原空间并加回均值。
推荐核验：核对主轴单位化、特征方程成立；重构点减均值后应位于第一主轴张成空间，残差与主轴正交。
C41｜例题 28.1：一次平方NMF顺序更新
章节：第 28 章《潜在语义分析与非负矩阵分解》；PDF物理页：608
源码：src/讲义源码/第04册\_无监督学习与矩阵分解/chapters/V4-C05.tex，约第 805 行
严重度：无
当前问题：未发现明显结构性问题；建议把现有解答的开头改为本题专属方法触发语。
推荐解题路线：严格按“先更新W、再用新W更新H”的乘法更新顺序计算；零元素只在固定支持面内保持零，最后计算新重构和平方损失。
推荐核验：检查W^{(1)},H^{(1)}非负，零锁定位置未被误改；用更新后的两个因子重算损失，并确认在适用边界下不增。
C42｜例题 29.1：一次完整E步与M步
章节：第 29 章《概率潜在语义分析》；PDF物理页：631
源码：src/讲义源码/第04册\_无监督学习与矩阵分解/chapters/V4-C06.tex，约第 710 行
严重度：中
当前问题：PLSA的E/M步误套为矩阵乘法/形状核验模板
推荐解题路线：E步先计算每个隐变量状态的后验责任度；M步用责任度加权充分统计量更新参数；最后检查责任度和参数归一化。
推荐核验：检查所有概率或权重非负，且在规定维度上求和为1；若有条件概率，再确认分母严格为正。
C43｜例题 30.1：周期链、惰性化与平稳性的数值辨析
章节：第 30 章《马尔可夫链基础》；PDF物理页：658
源码：src/讲义源码/第05册\_采样方法主题模型与图排序/chapters/V5-C01.tex，约第 689 行
严重度：无
当前问题：未发现明显结构性问题；建议把现有解答的开头改为本题专属方法触发语。
推荐解题路线：先计算ρ0C与ρ0C^2展示周期振荡，再解ρ=ρC求平稳分布并检验细致平衡；最后比较惰性化后对角自环如何消除周期。
推荐核验：核对每行概率和为1，平稳分布非负且和为1；原链分布逐步不收敛但时间平均可稳定，惰性链逐步收敛。
C44｜例题 30.2：一条两状态链的完整审计
章节：第 30 章《马尔可夫链基础》；PDF物理页：663
源码：src/讲义源码/第05册\_采样方法主题模型与图排序/chapters/V5-C01.tex，约第 896 行
严重度：低
当前问题：开头使用批量模板，需改为本题专属题意翻译
推荐解题路线：依次完成转移矩阵合法性、两步分布、平稳方程、不可约性、周期性与细致平衡检查，最后据条件判断是否逐步收敛。
推荐核验：核对ρ\_t各分量和为1、ρ=ρA；用双向流验证可逆性，并明确“不可约+非周期”才保证从任意初始分布逐步收敛。
C45｜例题 31.1：稀有事件下的重要性抽样高方差
章节：第 31 章《蒙特卡罗方法与直接采样》；PDF物理页：686
源码：src/讲义源码/第05册\_采样方法主题模型与图排序/chapters/V5-C02.tex，约第 522 行
严重度：无
当前问题：未发现明显结构性问题；建议把现有解答的开头改为本题专属方法触发语。
推荐解题路线：把重要性随机变量写成Z=h(X)p(X)/q(X)，先算E\_qZ=I，再算E\_qZ^2-I^2；随后分析稀有状态长期不被抽到时估计与样本ESS为何同时失真。
推荐核验：检查q在p的支持上严格为正；理论方差应由两个状态精确求和。固定样本全为0时，不能用表面相等权重断言提议分布良好。
C46｜例题 31.2：固定样本下的蒙特卡罗估计与误差审计
章节：第 31 章《蒙特卡罗方法与直接采样》；PDF物理页：696
源码：src/讲义源码/第05册\_采样方法主题模型与图排序/chapters/V5-C02.tex，约第 874 行
严重度：低
当前问题：开头使用批量模板，需改为本题专属题意翻译
推荐解题路线：对四个固定样本先计算h(u\_i)=u\_i^2及样本均值，再用n-1分母求样本方差，标准误为s/√n；最后与真值1/3比较。
推荐核验：复核四个平方值、样本方差分母和标准误公式；误差是本次固定样本的实现，不等同于总体偏差。
C47｜例题 32.1：单向提议造成的支持连通缺口
章节：第 32 章《马尔可夫链蒙特卡罗法》；PDF物理页：719
源码：src/讲义源码/第05册\_采样方法主题模型与图排序/chapters/V5-C03.tex，约第 676 行
严重度：无
当前问题：未发现明显结构性问题；建议把现有解答的开头改为本题专属方法触发语。
推荐解题路线：逐条计算MH比值π(y)q(y,x)/[π(x)q(x,y)]；若反向提议为0，则正向提议也会被拒绝。由此写出核并检查支持连通性。
推荐核验：核对每行和为1、π满足详细平衡；若链退化为自环或不可约性失败，就不能仅凭提议图有出边宣称可用。
C48｜例题 32.2：由非对称提议构造完整MH核
章节：第 32 章《马尔可夫链蒙特卡罗法》；PDF物理页：725
源码：src/讲义源码/第05册\_采样方法主题模型与图排序/chapters/V5-C03.tex，约第 953 行
严重度：无
当前问题：未发现明显结构性问题；建议把现有解答的开头改为本题专属方法触发语。
推荐解题路线：对每条双向非对角边计算接受率，把拒绝概率补到对角线形成完整核；再验证双向概率流、不可约/非周期，并执行两次固定输入转移。
推荐核验：检查K每行和为1、π\_iK\_{ij}=π\_jK\_{ji}；固定测试中每次接受/拒绝都按对应α与u判断，第二步从第一步的新状态出发。
C49｜例题 33.1：先会执行：二元正态的一轮Gibbs
章节：第 33 章《Gibbs 抽样》；PDF物理页：739
源码：src/讲义源码/第05册\_采样方法主题模型与图排序/chapters/V5-C04.tex，约第 151 行
严重度：无
当前问题：未发现明显结构性问题；建议把现有解答的开头改为本题专属方法触发语。
推荐解题路线：把两个满条件写成“条件均值+条件标准差×固定创新”；系统扫描先更新X1，再用同轮新X1更新X2。
推荐核验：检查第二步没有误用旧X1；将固定创新代回两个条件分布的标准化形式，逐项复算轮末状态。
C50｜例题 33.2：两轮确定性更新测试
章节：第 33 章《Gibbs 抽样》；PDF物理页：747
源码：src/讲义源码/第05册\_采样方法主题模型与图排序/chapters/V5-C04.tex，约第 441 行
严重度：中
当前问题：Gibbs顺序更新题误套为候选模型选择模板
推荐解题路线：逐轮执行X1^{(t)}=ρX2^{(t-1)}+σε\_{1t}，再执行X2^{(t)}=ρX1^{(t)}+σε\_{2t}；完整保留每个中间值。
推荐核验：第二坐标必须使用同轮新第一坐标；两轮都用给定确定性创新复算。该测试只验证更新次序与公式，不证明随机链已收敛。
C51｜例题 33.3：五分类模型的可复算Gibbs目标
章节：第 33 章《Gibbs 抽样》；PDF物理页：752
源码：src/讲义源码/第05册\_采样方法主题模型与图排序/chapters/V5-C04.tex，约第 647 行
严重度：低
当前问题：解答信息密度较高，初学者阅读时需要分段
推荐解题路线：先把多项计数似然与D上的均匀先验相乘得到后验核；固定一个参数后展开另一参数的多项式，识别为有限个Beta型分量并归一化，两个方向同理。
推荐核验：检查后验核在D上非负可积，两个满条件的混合权重和为1；用解析积分得到的矩与数值积分或有限求和基准一致。
C52｜例题 34.1：三分类先验的矩、更新与预测
章节：第 34 章《狄利克雷分布与共轭先验》；PDF物理页：777
源码：src/讲义源码/第05册\_采样方法主题模型与图排序/chapters/V5-C05.tex，约第 725 行
严重度：低
当前问题：开头使用批量模板，需改为本题专属题意翻译
推荐解题路线：用Dirichlet矩公式求先验均值；观察计数后将参数更新为α+n，再求后验均值、预测与MAP；序列/无序事件分别用预测连乘和多项系数处理。
推荐核验：检查后验参数全部为正、各均值与预测概率和为1；MAP只在相应参数条件下使用，序列概率与计数概率的组合系数不能混淆。
C53｜例题 34.2：Beta特例与Bernoulli更新
章节：第 34 章《狄利克雷分布与共轭先验》；PDF物理页：781
源码：src/讲义源码/第05册\_采样方法主题模型与图排序/chapters/V5-C05.tex，约第 924 行
严重度：低
当前问题：开头使用批量模板，需改为本题专属题意翻译
推荐解题路线：先用Beta函数核验归一化并计算均值方差；把成功、失败计数分别加到两个形状参数，得到后验与后验预测。
推荐核验：检查后验为Beta(2+3,3+1)，预测成功率等于后验均值；归一化常数、均值和方差均落在合法范围。
C54｜例题 34.3：Gamma归一化的确定性测试
章节：第 34 章《狄利克雷分布与共轭先验》；PDF物理页：782
源码：src/讲义源码/第05册\_采样方法主题模型与图排序/chapters/V5-C05.tex，约第 956 行
严重度：低
当前问题：开头使用批量模板，需改为本题专属题意翻译
推荐解题路线：将给定正Gamma样本按总和s归一化为θ\_i=g\_i/s；把“确定性输入测试”与“随机生成分布证明”分开说明。
推荐核验：核对s>0、每个θ\_i>0且分量和为1。单个固定三元组只能验证归一化与支持处理，不能证明θ服从Dirichlet分布。
C55｜例题 34.4：计数证据与序列证据
章节：第 34 章《狄利克雷分布与共轭先验》；PDF物理页：782
源码：src/讲义源码/第05册\_采样方法主题模型与图排序/chapters/V5-C05.tex，约第 981 行
严重度：低
当前问题：开头使用批量模板，需改为本题专属题意翻译
推荐解题路线：先做Dirichlet–多项共轭更新，再用后验预测求下一类概率；计数向量边际含多项系数，指定顺序的序列边际不含该系数。
推荐核验：检查后验预测和为1；计数概率应等于相应所有不同顺序序列概率之和，二者差一个多项系数。
C56｜例题 35.1：一次折叠Gibbs更新
章节：第 35 章《潜在狄利克雷分配》；PDF物理页：813
源码：src/讲义源码/第05册\_采样方法主题模型与图排序/chapters/V5-C06.tex，约第 1232 行
严重度：无
当前问题：未发现明显结构性问题；建议把现有解答的开头改为本题专属方法触发语。
推荐解题路线：更新某个词元前先从文档—主题和主题—词计数中删除它的旧主题贡献；用删除后的计数计算K个未归一化满条件质量，归一化后再恢复到新主题。
推荐核验：检查未归一化质量非负、归一化概率和为1；旧计数只删除一次，采样/选择新主题后只恢复一次，避免自计数。
C57｜例题 35.2：一次平均场责任度更新
章节：第 35 章《潜在狄利克雷分配》；PDF物理页：814
源码：src/讲义源码/第05册\_采样方法主题模型与图排序/chapters/V5-C06.tex，约第 1259 行
严重度：低
当前问题：开头使用批量模板，需改为本题专属题意翻译
推荐解题路线：对两个主题分别计算exp{ψ(γ\_k)-ψ(Σγ)+logφ\_{kv}}的未归一化责任度，再统一归一化得到η\_n。
推荐核验：检查两个责任度均非负且和为1；公共项是否正确抵消，并用未归一化比值核对最终概率比。
C58｜例题 35.3：留出困惑度
章节：第 35 章《潜在狄利克雷分配》；PDF物理页：814
源码：src/讲义源码/第05册\_采样方法主题模型与图排序/chapters/V5-C06.tex，约第 1290 行
严重度：低
当前问题：开头使用批量模板，需改为本题专属题意翻译
推荐解题路线：使用冻结模型对两个留出词的预测概率计算平均负对数似然，再指数化得到每词困惑度；训练后重估概率属于另一评估协议，不能混比。
推荐核验：两组概率必须针对同一留出词、同一冻结参数与同一对数底；更小的训练后重估数值因数据泄漏不能作为可比改进。
C59｜例题 36.1：四结点基本PageRank复算
章节：第 36 章《PageRank 算法》；PDF物理页：840
源码：src/讲义源码/第05册\_采样方法主题模型与图排序/chapters/V5-C07.tex，约第 838 行
严重度：无
当前问题：未发现明显结构性问题；建议把现有解答的开头改为本题专属方法触发语。
推荐解题路线：按列随机约定计算r^{(1)}=Mr^{(0)}，再把给定极限向量代入Mr=r；从分量大小读出排序。
推荐核验：核对每列和为1，r^{(1)}及极限r非负且和为1；计算∥Mr-r∥\_1确认平稳残差为0。
C60｜例题 36.2：删除一条边后的概率质量流失
章节：第 36 章《PageRank 算法》；PDF物理页：841
源码：src/讲义源码/第05册\_采样方法主题模型与图排序/chapters/V5-C07.tex，约第 873 行
严重度：低
当前问题：开头使用批量模板，需改为本题专属题意翻译
推荐解题路线：指出零列使列和小于1，直接乘法会把该列上的概率质量丢掉；计算一次总质量变化，并说明必须先修复悬挂列。
推荐核验：检查迭代后分量和是否仍为1；若小于1，则结果不是概率分布，不能称为合法PageRank。
C61｜例题 36.3：四结点阻尼PageRank
章节：第 36 章《PageRank 算法》；PDF物理页：842
源码：src/讲义源码/第05册\_采样方法主题模型与图排序/chapters/V5-C07.tex，约第 899 行
严重度：低
当前问题：开头使用批量模板，需改为本题专属题意翻译
推荐解题路线：构造G=dS+(1-d)v1^T，解(I-dS)r=(1-d)v；最后按分量排序并说明阻尼带来的唯一性。
推荐核验：核对r非负且和为1，并计算∥Gr-r∥\_1或线性方程残差；排序只按最终分量而非中间迭代值。
C62｜例题 36.4：三结点幂法与概率归一化
章节：第 36 章《PageRank 算法》；PDF物理页：842
源码：src/讲义源码/第05册\_采样方法主题模型与图排序/chapters/V5-C07.tex，约第 932 行
严重度：低
当前问题：开头使用批量模板，需改为本题专属题意翻译
推荐解题路线：先解r=dSr+(1-d)v得到概率平稳向量；若幂法先按最大分量归一化，只得到比例方向，最后必须再除以分量和。
推荐核验：检查最终向量非负、分量和为1且满足Gr=r；比较两种归一化结果应只差一个正比例常数。
C63｜例题 37.1：两候选、两折的完整选择轮次
章节：第 37 章《无监督学习方法总结》；PDF物理页：856
源码：src/讲义源码/第05册\_采样方法主题模型与图排序/chapters/V5-C08.tex，约第 410 行
严重度：无
当前问题：未发现明显结构性问题；建议把现有解答的开头改为本题专属方法触发语。
推荐解题路线：先按预先声明的“两折都成功”规则判定候选资格，再只在合格候选间比较平均验证损失；选定后重拟合，并只做一次锁定测试。
推荐核验：失败候选不得用单折好成绩参与比较；测试损失0.47只能在选择与重拟合全部完成后报告，不能反馈到选择。
C64｜例题 37.2：对象、目标与求解器分层
章节：第 37 章《无监督学习方法总结》；PDF物理页：864
源码：src/讲义源码/第05册\_采样方法主题模型与图排序/chapters/V5-C08.tex，约第 756 行
严重度：低
当前问题：结论回收不够显式
推荐解题路线：把口号拆成六项规格：观测数据与预处理、潜变量/模型、目标联合或后验分布、Gibbs满条件与扫描顺序、初始化/燃烧/保留预算、诊断与最终输出。
推荐核验：检查“对象—目标—求解器”三层没有混淆：Gibbs只是求解器；任务还必须明确模型、估计量、停止/诊断和评价指标。
C65｜例题 37.3：LSA因子维数纠错
章节：第 37 章《无监督学习方法总结》；PDF物理页：865
源码：src/讲义源码/第05册\_采样方法主题模型与图排序/chapters/V5-C08.tex，约第 783 行
严重度：无
当前问题：未发现明显结构性问题；建议把现有解答的开头改为本题专属方法触发语。
推荐解题路线：先写X的尺寸6×4与截断秩K=2，据此确定U\_K、Σ\_K、V\_K的维数；再区分V\_K列正交与文档系数矩阵行/列的关系。
推荐核验：矩阵乘积U\_KΣ\_KV\_K^T应恢复6×4尺寸；正交性只由V\_K^TV\_K=I\_2保证，不能推出任意两个文档系数列正交。
C66｜例题 37.4：锁定测试的条件无偏
章节：第 37 章《无监督学习方法总结》；PDF物理页：866
源码：src/讲义源码/第05册\_采样方法主题模型与图排序/chapters/V5-C08.tex，约第 824 行
严重度：无
当前问题：未发现明显结构性问题；建议把现有解答的开头改为本题专属方法触发语。
推荐解题路线：先指出命题的条件是“测试前模型已固定”；若在20个秩中选测试误差最小者，选中模型依赖测试噪声，因此条件无偏结论不再适用。
推荐核验：用验证集或嵌套交叉验证完成秩选择，再对唯一锁定模型评测一次；测试结果不得回流到候选选择。
附录 D｜索引文件逐项读取顺序
按以下顺序完成附属任务表：
全量索引库.xlsx 的“全局问题台账”；
“阅读阻塞残留”935 行；
“例题索引”66 行；
“知识点索引”596 行；
“定理定义索引”192 行；
“核心推导索引”59 行；
“绘图索引”99 行（仅分对话 A）；
“页级视觉问题”139 行；
“章末练习覆盖”37 章；
视觉证据包中的 8 张逐页总览与 11 张逐图核对图。
分对话 A/B 每完成一项更新各自本地状态文件并在交接中报告；只有主对话可更新 STATE\_ROOT\CURRENT\_STATUS.md。不得把索引中的旧“已完成”字段直接视为 v2.7.0 结论；所有对象都要以当前候选 PDF 和源码重新确认。
立即开始
主对话现在进入 Goal 模式：

切换到 D:\Users\ASUS\Desktop\机器学习，定位七个输入，建立 INTEGRATION\_WORKTREE 的共同基线；

创建 DIALOGUE\_A\_WORKTREE 与 DIALOGUE\_B\_WORKTREE，确认三个写域互斥；

物化并发送两份自包含提示词，启动两个独立对话：

对话 A 执行 99 幅绘图、严格视觉证据和图源局部修复；

对话 B 执行正文数学内容、例题、知识点、练习、算法和非图局部源码修复；

主对话同时只处理 M01、M10 和共享/全局单写任务，不得进入 A/B 专属写域；

两个分对话完成后，各自输出包含“修改文件、关键结论、测试结果、未解决问题、补丁/分支、共享请求”的交接摘要与交接文件，并写入 HANDOFF\_ROOT 的独占目录；

主对话实际读取两份交接，按第 4.12 节统一合并、检查、返工、全书重建、最终验收和交付。

两个分对话上下文不会自动合并；不得只在聊天中说“已传回”。必须有可读取的交接文件和真实文件变更。任何公共宏、字体、全局编号、索引、构建入口、权威问题库和权威状态文件始终由主对话单写。逐图视觉验收继续严格执行第 9.2.1 节：任何 1 个经裁决确认的真实非法重叠像素都必须返修，只有全部硬指标满足才可通过。最终 PDF、LaTeX 源码 ZIP 与全部交付文件 ZIP 必须由主对话保存到 D:\Users\ASUS\Desktop\机器学习\v2.7.0。不要停在计划阶段。