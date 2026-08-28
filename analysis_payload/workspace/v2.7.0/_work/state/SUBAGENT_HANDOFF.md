# 最近代理交接

## 最新续跑检查点（优先于下方历史记录）

- 时间：`2026-08-23T12:19:06+08:00`；对应 `CURRENT_STATUS.md` revision85。
- 99图初始SA1证据覆盖仍是99/99，但正式完成仅28图。已关闭且禁止重开：P547/P577/P578/P580/P596/P602/P608/P609/P630/P634/P640/P654/P668/P669/P684/P694/P695/P715/P716/P717/P721/P736/P737/P740/P745/P748/P750/P756；剩余71图。
- P596经专属SA2、根R3.1、全新隔离SA1与替代隔离SA3b共同判`PASS / SPLIT_REQUIRED=NO / NEW_ISSUE=NONE`。page/standalone为63,402/47,320 bytes，A4单页，图32.1/页595，硬日志0；三张300dpi视图、细致平衡作用域、结构/收敛分支、独立核反例、10条箭头与字体门均通过。中央CSV为“通过”，根接受报告已固化，禁止重开或重复构建。
- P596首个SA3因递归JSON定位意外输出非P596嵌套对象而隔离失效；已中断且不参与放行。有效证书为`FIG-P596-01-SA1-R3.1.md`与`FIG-P596-01-SA3-R3.1b.md`。
- 下一唯一正文写者对象为P632；新的专属SA2只可改V5-C04的 `fig_v5_c04_conditional_slice.tex`、P632首次引用/图后屏障邻域与R2报告，禁止触碰所有已关闭对象、wrapper、JSON、CSV、numeric、state与build。
- P632须用同一可归一化二元正态生成联合等高线、两个原始截面、边缘积分和满条件密度；建议`ρ=0.6,a=1,b=0.8`，条件均值`0.48/0.60`、方差`0.64`。普通文字至少9.6pt、无整体缩放、图后专属读图句与`FloatBarrier`，保留零分母正则条件版本；不拆图。
- P632 SA2交权后，根线程单写同步wrapper/source JSON/numeric JSON/CSV并执行局部R3；再启动新的隔离SA1/SA3作最终独立复核。
  下方旧“当前代理状态/逐图下一次交接”只作历史，不得覆盖本节。

## 已完成的最近任务

- `M02-SA2-R2` 的 10 条短候选已获批准并由根线程单写者应用：只改 ordinal 83、100、162、377、409、447、484、523、780、785，完整 record 其余 925 条不变；L0 与唯一 clean L1 均 PASS，最终 805 页 PDF 日志硬诊断全 0。
- 一个独立只读 subagent 已完成 M02 post-apply 复核：权威冻结与源码 935/935 同步，十项字段范围与应用前基线一致，结论 PASS；未写文件、未构建。
- 全新独立 `M02-SA1-R2` 已判 `FAIL`：映射/源码/L0/L1 全部 PASS，唯一阻断是 ordinal 523 缺 `G`-Markov、局部硬约束与合法四配置前提，ordinal 780 缺细致平衡等式及几乎处处条件；正式证据为 `R03_M02_SA1_R2_20260822.md`。
- 99 图缺口已独立核清：47 份正式报告，52 个缺口为 17 recoverable、3 render-only、32 manifest-only；精确列表见 `R03_FIGURE_SA1_GAP_MAP_20260822.md`，不可用摘要冒充完整报告。
- `M02-SA2-R3` 已仅修523/780并通过L0与一次统一增量L1：余933完整记录不变、源码回读935/935、PDF805页/4,851,007 bytes、日志硬门全0；后续全新SA1-R3与盲审SA3均PASS，根线程已接受。
- `FIG-P639-01-SA1-R1` 已落盘并判 `FAIL / SPLIT_REQUIRED=NO`；正式图报告现48份，原52缺口余51。
- `M02-SA1-R3` 与全新盲审 `M02-SA3` 均 PASS；根线程已正式接受 M02，证据为 `R03_M02_ROOT_ACCEPTANCE_20260822.md`。
- `FIG-P641-01`、`FIG-P654-01` 正式报告已落盘，均 `FAIL / SPLIT_REQUIRED=NO`；render-only三图全部补齐，正式图报告现50份，缺口余49。
- `FIG-P736-01` 已由不读取恢复摘要的独立实例审完并落盘，判 `FAIL / SPLIT_REQUIRED=NO`；正式图报告现51份，缺口余48。`FIG-P737-01` 正由另一名此前未审图的独立实例处理。
- `FIG-P737-01` 已审完并落盘，判 `FAIL / SPLIT_REQUIRED=NO`；正式图报告现52份，缺口余47。`FIG-P740-01` 正由第三名此前未审图的独立实例处理。
- `FIG-P740-01` 已审完并落盘，判 `FAIL / SPLIT_REQUIRED=NO`；正式图报告现53份，缺口余46。`FIG-P745-01` 正由另一名此前未审图的独立实例处理。
- `FIG-P745-01` 已审完并落盘，判 `FAIL / SPLIT_REQUIRED=NO`；正式图报告现54份，缺口余45。`FIG-P748-01` 正由另一名此前未审图的独立实例处理。
- `FIG-P748-01` 已审完并落盘，判 `FAIL / SPLIT_REQUIRED=NO`；正式图报告现55份，缺口余44。`FIG-P750-01` 正由此前仅审M01、未审图的独立实例处理。
- `FIG-P750-01` 已审完并落盘，判 `FAIL / SPLIT_REQUIRED=NO`；正式图报告现56份，缺口余43。`FIG-P756-01` 正由此前仅审M07、未审图的独立实例处理。
- `FIG-P756-01` 已审完并落盘，判 `FAIL / SPLIT_REQUIRED=NO`；正式图报告现57份，缺口余42。七个带旧局部渲染的recoverable对象已全补齐，`FIG-P033-01` 正由新独立实例处理。
- `FIG-P033-01` 已审完并落盘，判 `FAIL / SPLIT_REQUIRED=NO`；正式图报告现58份，缺口余41。`FIG-P049-01` 正由另一名未审图实例处理。
- P049 首个重开实例因工具排除失效意外看到恢复摘要一行，已按 D-009 中断且全部未落盘结果作废；当前 P049 实例从显式命名范围重新独立取证。
- P049 全新实例已审完并落盘，判 `FAIL / SPLIT_REQUIRED=NO`，精确点积错误为 `1/750`；正式图报告现59份、缺口40份。P067 正由其原专属代理固化完整原始回传或从头复核。
- P067 原专属代理已恢复并落盘完整八栏报告，判 `FAIL / SPLIT_REQUIRED=NO`；正式图报告现60份、缺口39份。P077 正按相同流程处理。
- P077 原专属代理已恢复并落盘完整八栏报告，判 `FAIL / SPLIT_REQUIRED=NO`；正式图报告现61份、缺口38份。P092 正按相同流程处理。
- P092 原专属代理已恢复并落盘完整八栏报告，判 `FAIL / SPLIT_REQUIRED=NO`；正式图报告现62份、缺口37份。P126 正按相同流程处理。
- P126 原专属代理已恢复并落盘完整八栏报告，判 `FAIL / SPLIT_REQUIRED=NO`；正式图报告现63份、缺口36份。P142 正按相同流程处理。
- P142 原专属代理已恢复并落盘完整八栏报告，判 `FAIL / SPLIT_REQUIRED=NO`；正式图报告现64份、缺口35份。P206 正按相同流程处理。
- P206 原专属代理已恢复并落盘完整八栏报告，判 `FAIL / SPLIT_REQUIRED=NO`；正式图报告现65份、缺口34份。P222 正按相同流程处理。
- P222 原专属代理已恢复并落盘完整八栏报告，判 `FAIL / SPLIT_REQUIRED=NO`；正式图报告现66份、缺口33份。P242 正按相同流程处理。
- P242已恢复落盘；17个recoverable与3个render-only缺口全部关闭。正式报告现67份，余32个manifest-only对象，当前P020由原专属代理处理。
- manifest-only首批P020/P109/P157/P172/P186/P210均已固化并回读；正式报告现73份、缺口26份。下一批P346/P412/P429/P467/P482/P556-02。
- manifest-only第二批P346/P412/P429/P467/P482/P556-02均已固化并回读；正式报告现79份、缺口20份。下一批P556-03/P656/P657/P660/P662/P665。
- manifest-only第三批P556-03/P656/P657/P660/P662/P665均已由各自原专属代理固化并回读；正式报告现85份、缺口14份。下一批P667/P670/P680/P683/P687/P689。
- manifest-only第四批P667/P670/P680/P683/P687/P689均已由各自原专属代理固化并回读；正式报告现91份、缺口8份。最后一批P690/P713/P715/P716/P719/P720/P722/P734。
- 最后8个manifest-only对象P690/P713/P715/P716/P719/P720/P722/P734已全部固化并回读；P722由原代理返回完整全文、根线程按持续授权落盘。manifest与报告均为99个唯一UID，双向集合差0。
- 根线程已接受初始SA1证据覆盖99/99；接受记录为`R03_FIGURE_SA1_RECOVERY_ROOT_ACCEPTANCE_20260822.md`，不代表图件质量通过。
- P715原SA2代理已固化正式设计，根线程完成图源/正文/wrapper/两份manifest/中央清单应用；R2首次像素检查发现底部等式挤压后，SA2又给出最小版面补丁，根线程已应用并重建。
- P715最终R2局部门PASS：A/c/M/P精确复算残差0、无悬挂、standalone/page LuaLaTeX日志硬诊断0、PDF图区最小9.46pt、彩色/灰度/局部/standalone像素均实看无重叠裁切。根报告为`FIG-P715-01-ROOT-APPLY-R2.md`，尚非独立放行。
- P715全新独立SA1-R2判`FAIL / SPLIT_REQUIRED=NO`，唯一阻塞是正式章节专属读图句在图输入之前；其余数学、视觉、字号、灰度、日志和wrapper均PASS。根线程R3只移动该句至图后，顺序179<181<183，并在独立R3目录重建两份PDF与四份像素证据，全部局部门PASS；根报告为`FIG-P715-01-ROOT-APPLY-R3.md`。
- P715全新独立SA1-R3已按权威A--I/B85判`PASS / SPLIT_REQUIRED=NO`。其初版曾将主提示词未要求的tagged-PDF/Alt能力误升为硬门；代理重读权威条款并检索执行包后已在同一报告透明勘误，保留事实但降为非阻塞未来增强。
- P715全新盲审SA3已判`PASS / SPLIT_REQUIRED=NO`；根线程已签署`FIG-P715-01-ROOT-ACCEPTANCE-R3.md`并把中央清单更新为“通过”，该图当前闭环关闭。
- P547专属SA2已完成图源与章节修复；根线程已同步两个wrapper、两份JSON和中央清单，并在全新R3目录重建及实看。根局部门PASS：页码578、顺序183<184<186、两份日志硬诊断0、矩阵/边映射残差0、四份像素证据通过；报告为`FIG-P547-01-ROOT-APPLY-R3.md`。
- P547全新独立SA1-R3已判`PASS / SPLIT_REQUIRED=NO`，9,926-byte报告逐栏覆盖A--I/B33、数学、四张PNG、两份PDF/log/fls、元数据与AUX标签；根线程已完整回读。当前另一全新盲审SA3正在独立复核。
- P547全新盲审SA3已判`PASS / SPLIT_REQUIRED=NO`；报告控制字符已由原代理等价清理并验证归零。根线程已固化最终接受报告、中央清单为“通过”，P547当前闭环关闭。
- P602初始SA1报告已回读：硬阻断为接受率计算节点/`g>0`条件缺失、8.6/9.2pt字号、冗余输出链/长题注和图后读图句缺失；接受/拒绝/自环方向正确且无需拆图。专属SA2已获两文件写权。
- P602专属SA2已判`FIXED / SPLIT_REQUIRED=NO`；根线程同步wrapper/JSON/CSV并在R3新目录重建。一次像素检查发现浮动体让读图句越过图体，根线程在章节与page wrapper加入`\FloatBarrier`后定向重建，最终standalone/page为36,565/57,467 bytes、硬诊断0、页码636、四图实看通过；根局部报告已固化。
- P602全新独立SA1-R3与全新盲审SA3-R3均判`PASS / SPLIT_REQUIRED=NO`、无阻断；根线程已完整回读、固化`FIG-P602-01-ROOT-ACCEPTANCE-R3.md`并把中央清单更新为“通过”。P602当前闭环关闭。
- P654专属SA2已判`FIXED / SPLIT_REQUIRED=NO`；根线程同步wrapper/JSON/CSV，消除源级`scale=`，并在全新R3目录定向重建。最终standalone/page为40,918/59,977 bytes、硬诊断0、页685/图34.1；四图实看、PDF顺序90<804<832、99×19中央清单均通过，根局部报告已固化。
- P654全新独立SA1-R3与全新盲审SA3-R3均判`PASS / SPLIT_REQUIRED=NO`、无阻断；根线程已完整回读、固化`FIG-P654-01-ROOT-ACCEPTANCE-R3.md`并把中央清单更新为“通过”。P654当前闭环关闭。
- P608专属SA2已判`FIXED / SPLIT_REQUIRED=NO`；根线程完成wrapper/JSON/CSV/numeric单写同步与R3构建。最终standalone/page为32,428/60,026 bytes、页643/图32.8、两日志硬诊断0；15/15运行均值、五类像素证据和顺序178<936<984通过，根局部报告已固化。
- P608全新隔离SA1-R3已判`PASS / SPLIT_REQUIRED=NO`、无阻断；13,620-byte报告完整覆盖A--I、数值、视觉、身份与日志，根线程已完整回读。当前盲审SA3从当前原始对象和R3原始证据独立取证。
- P608全新盲审SA3-R3已判`PASS / SPLIT_REQUIRED=NO`、无阻断；根线程已完整回读、固化`FIG-P608-01-ROOT-ACCEPTANCE-R3.md`并把中央清单更新为“通过”与`RESOLVED_EVIDENCE_CLEAR`。P608当前闭环关闭。
- P630专属SA2已判`FIXED / SPLIT_REQUIRED=NO`；根线程同步图源身份、两个wrapper、V5-C04 JSON与中央CSV后完成R3局部构建。standalone/page为43,428/65,921 bytes、页662/图33.1、两日志硬诊断0，四张彩色/灰度证据均实看通过；根局部报告已固化。
- P630全新独立SA1已从未审过本图的既有代理实例启动；严格禁止读取本图旧报告与状态。盲审SA3因当前三条持久子线程上限排队，不能使用已看过P630的SA2代理冒充。
- P609唯一专属SA2已启动，只可改本图图源、V5-C03相邻块和R2证据；禁止触碰已关闭的P602/P608及所有中央清单。
- P609已完成专属SA2、根线程R3、全新SA1与盲审SA3；根接受报告`FIG-P609-01-ROOT-ACCEPTANCE-R3.md`判PASS，中央清单为“通过”与`RESOLVED_EVIDENCE_CLEAR`，当前闭环关闭。
- P630全新SA1与盲审SA3均判PASS；根接受报告`FIG-P630-01-ROOT-ACCEPTANCE-R3.md`已固化，中央清单为“通过”与`RESOLVED_EVIDENCE_CLEAR`，当前闭环关闭。
- P634全新独立SA1与隔离SA3均判`PASS / SPLIT_REQUIRED=NO`；根线程已完整回读、固化`FIG-P634-01-ROOT-ACCEPTANCE-R3.md`并把中央清单更新为“通过”与`RESOLVED_EVIDENCE_CLEAR`。P634当前闭环关闭，禁止重建。
- P640专属SA2已判`FIXED / SPLIT_REQUIRED=NO`；根线程同步图源身份、两个wrapper、V5-C04 JSON、numeric manifest与中央CSV后完成R3局部构建。最终standalone/page为40,372/68,100 bytes、页671/图33.7、两日志硬诊断0；三张300dpi证据实看通过，`.99`非零端点直接标为`(.99,.010)`，根局部报告已固化。
- P640全新独立SA1-R3与隔离SA3-R3均判`PASS / SPLIT_REQUIRED=NO`、无阻断；根线程已完整回读并固化`FIG-P640-01-ROOT-ACCEPTANCE-R3.md`，中央清单为“通过”与`RESOLVED_EVIDENCE_CLEAR`，P640当前闭环关闭。
- P668/P669联合只读设计已判`DESIGN_READY=YES`并由根线程独立复算确认；根接受报告为`FIG-P668-P669-ROOT-DESIGN-ACCEPTANCE-R2.md`。保持99 UID，P668承担真实密度边界、P669承担固定均值浓度—协方差；下一步仅允许唯一SA2写两图源、V5-C05相邻正文与指定R2报告。
- P694只读设计经根线程核对V5-C06第1047行后完成语义纠偏并接受：同一UID内双面板，局部budget/失败禁止进C/M，外层feasible budget_stop作为“预算候选/未收敛”进入S_acc且保留status。根确认报告为`FIG-P694-01-ROOT-DESIGN-ACCEPTANCE-R2.md`。
- `FIG-P262-01-SA1-R1`、`FIG-P282-01-SA1-R1`、`FIG-P309-01-SA1-R1`、`FIG-P324-01-SA1-R1`（5.6terra/max，只读）：均判 FAIL、SPLIT_REQUIRED=NO；正式报告已落盘到各自 `evidence/figures/<UID>/R1/`。
- 高优先级21图初始 SA1 已全部完成；只有 FIG-P668-01 与 FIG-P694-01 要求拆图。
- 正式逐图SA1-R1现有99份、缺口0份；下一阶段为每幅FAIL图的专属SA2、根线程单写应用、全新SA1与SA3。

## 当前代理状态

`p668_p669_sa2_r2`、`p668_p669_sa1_r3`与`p668_p669_sa3_r3`均已完成，两图已根接受关闭。当前仅`p694_sa2_r2`因首次R3版式FAIL重启R2.1，只改P694图源与追加原报告，禁止构建及触碰wrapper/JSON/CSV/状态。根线程继续单写中央文件；P721待该写槽释放后启动专属SA2。

## M02 下一次精确交接

M02 已关闭；若恢复，只从 `R03_M02_ROOT_ACCEPTANCE_20260822.md` 读取结论，禁止重复构建或重开已通过角色。

## 逐图下一次精确交接

初始SA1证据恢复已结束，99/99仅表示证据覆盖。P547/P602/P608/P609/P630/P634/P640/P654/P668/P669/P715共11图已接受关闭，禁止重开，剩余88图。P694首轮R3原位页为3页并有6处Overfull与严重碰撞，已退回同一SA2作R2.1；根线程不得在返工重建通过前放行。P721为下一张，R1唯一数学阻塞是`t=6`无停止证书，建议明确为展示截断/非收敛判定并同步字号与图文链。

## Revision 87 新 Goal 交接（覆盖上方旧“关闭/禁止重开”口径）

- 权威 Goal：`D:\Users\ASUS\Desktop\机器学习\v2.7.0\GPT_Pro_统计学习方法讲义_v2.7.0_Codex_Goal主提示词.md`，SHA-256 `51BA862B1EEBCD6765565FEE6243BD2BC8BF2611D586115B52623668711928C2`。
- 规范路径：`D:\Users\ASUS\Desktop\机器学习\v2.7.0_work`，它是指向现有 `v2.7.0\_work` 的 Junction；必须继续原树，禁止复制或从零重建。
- 旧 99/99 初审覆盖和旧 28 图根接受仅为历史。新协议五类 `after_*` 产物当前均为 0/99；每图必须重新资格认定，但应复用旧源码、数学复算和布局成果。
- 所有新 SA1/SA3 必须按 Goal 第 9.2.1 节从原始 300 dpi 证据独立取证：一般可见文字有效字号至少 9.5pt；逐元素字高、同类/角色/跨面板比例、灰度、页面融合、数学与文字一致性全查；`OVERLAP_PIXEL_COUNT=0`、`CLIP_PIXEL_COUNT=0`，F4 净空全达标。任一未知/缺文件/失败即 FAIL。
- 每图专属 SA1=`gpt-5.6-terra/max` 只读；专属 SA2=`gpt-5.6-sol/max` 严格白名单写；专属 SA3=`gpt-5.6-terra/max` 隔离独立二审。代理不得再创建代理；根线程单写 wrapper、中央 JSON/CSV、状态和发布文件。
- P632 R3.8 已由旧 SA1/SA3 共同判几何 FAIL（2px 与 8px 净空问题），下一唯一源码写者仍为 P632 专属 SA2。并行只读槽用于两个不同既往通过图的独立新协议 SA1，不得批量审多图。
- P580 R3.4 是可复用中间候选，不计新 PASS；其旧 SA2 R2.5 源码成果保留，须按新协议生成五类证据并经过独立 SA1/SA3。
- 新报告必须返回逐 ELEMENT_ID 失败/通过明细、像素坐标与量测方法，不得使用“基本可读”“轻微重叠”“肉眼可接受”替代硬门。

## Revision 89 代理交接（最新）

- 最新 Goal 身份：`cf14964e-b5d2-474a-a753-eb49e993ff9d/goal-objective.md`，SHA-256 `B60E2436C422BDEF817F8D3316C7AD0AB5E1B340256ED3DFBE86DFFDEBEB3BF9`；与上一 Goal 仅 Markdown 转义不同。
- P020 新独立 SA1 已 FAIL：R4 的 14.4458pt 文本箭头造成角色比 1.450003 与视觉协调失败。下一唯一写者为 P020 SA2 R5，只改一份图源并使用图形箭头。
- P033/P049/P067 新独立 SA1 均已 FAIL，正式报告在各自 `STRICT_R1/`；按 P033→P049→P067 串行进入 SA2，不得并发源码写者。
- P578 SA2 R3 candidate3 已完成源码定向修复并释放写槽；构建、300dpi 主视图与 PARTIAL 报告已固化在 `FIG-P578-01/STRICT_R3/`。未补齐全图正式掩膜/H_ink/灰度前不得交 SA3。
- 后续所有 SA1/SA3 任务必须明确：在原始 300dpi 像素上放大到 1:1 检查每个文字—文字、文字—线/箭头/标记、文字—边框关系，并把字体大小与同类/角色协调列为硬门；可以适当缩小突兀文字，但不得低于 9.5pt 或破坏像素下限与整体可读性。

## Revision 90 代理交接（最新）

- 官方连续对象为 `strict_current_r90_fullbook/main_full.pdf`（813 页、4,933,727 bytes、硬日志 0）。逐图代理不得使用 standalone 或旧接受页冒充官方页。
- P020 R5：新 SA1 已 PASS，隔离 SA3 正在运行；只允许新增 `SA3_*` 证据，禁止读取旧角色结论、修改图源或中央状态。即使 PASS 也仅是候选，根线程签发前不得关闭。
- P578：根线程正式判 FAIL。初始化节点文字—下边框为 0px，求值节点为 2px，门槛 5px；下一唯一源码写者为专属 SA2，只可改 `V5-C02/fig_v5_c02_rejection_flow.tex`，目标至少 8px，禁止改算法、拓扑、节点/分支数量和中央文件。
- P109/P126 新独立 SA1 均 FAIL，进入 SA2 队列；P033/P049/P067/P077/P092 同样等待串行修复。
- 所有新 SA1/SA3 都必须自行从官方 PDF 提取原生 300dpi 页，在 1:1 像素级逐元素审查。字体可以因视觉协调适当缩小，但有效字号、各字符类别像素下限、同类/角色比例、硬净空与整体可读性必须同时通过；任何未知即 FAIL。

## Revision 91 代理交接（最新）

- 最新官方对象：`strict_current_r91_fullbook/main_full.pdf`，813 页、4,933,714 bytes、硬日志 0。后续任务不得再把 R90 当作包含 P578 R4 的官方候选。
- P020 已完成新 SA1/隔离 SA3/根签发并成为 `STRICT_PASS`；只有该图源或共享样式受后续变更影响时才重验。
- P578 R4：专属 SA2 已交权，局部 page/standalone 的 init/evaluate 下边净空均 18px；官方 R91 物理页626上的全新 SA1正在运行。该 SA1禁止读取任何旧报告/掩膜，必须重建全元素五类证据；PASS后仍需隔离 SA3和根签发。
- P142 新 SA1 FAIL：20/23 源级文字低于9.5pt、`new`下标13px、反馈角色比0.9394；几何无重叠/裁切。进入 SA2 队列。
- P157/P172 正在只读审查；槽位释放后按 P186/P206/P210 继续。所有源码修复保持唯一 SA2 写者，中央文件仍仅根线程写。

## Revision 92 代理交接（最新）

- 最高 Goal 已切换为 `e9427863-0663-4847-93b3-d9c784a212b5/pasted-text.txt`，SHA-256 `51BA862B1EEBCD6765565FEE6243BD2BC8BF2611D586115B52623668711928C2`；它与上一 Goal 实质相同，不改变任何正在运行代理的标准或白名单。
- P157 独立 SA1 已 FAIL：文字—验证曲线非法重叠 134px、净空 0，且正文所述圆/三角标记未实现；下一角色 SA2。
- P172 独立 SA1 已 FAIL：9.2pt 源级小字、4px 省略号、自然脚本比例 0.885、四个节点 2--3px 内净空；重叠/裁切 0。R91 页与取证页逐字节一致；下一角色 SA2。
- P186 的替代独立实例与 P578 官方 R91 全新 SA1 继续运行；下一释放只读槽用于 P206。源码修复仍保持唯一 SA2 写者，中央库存与状态仅由根线程写。
- P186 替代独立实例现已完成并 FAIL：4 个 9.2pt 标签、边界公式到线 1px、一个标为负类的三角点实际 `g=+0.178`。根线程已查看 1:1 ROI 并确认，库存下一角色为 SA2；此前受污染的 `STRICT_R1` 仍不可用。
- P206、P210 已分别启动独立严格 SA1；二者只能读取各自官方页、图源与直接正文，只能写各自 `STRICT_R1` 证据。P578 官方 R91 SA1 仍运行。

## Revision 93 代理交接（最新）

- P210 独立 SA1 已 FAIL：42/51 可见文本低于 9.5pt，D/`3:x` 有 1px 非法重叠且净空 0，F/`2:y` 净空 0，第三层切分与 kd 树拓扑矛盾；根线程已看 1:1 ROI，下一角色 SA2。
- P578 官方 R91 独立 SA1 已 FAIL：17 个基础运算符 H_ink=11--18px<22px，precheck 公式—箭头净空 2px<3px，且“立即”异常断行。禁止进入 SA3，下一角色 SA2。
- P157 为当前唯一源码写者；只改图中验证标签位置和图后真实编码描述，正在 `STRICT_R2` 本地构建/复测，未交 FIXED 前不得启动官方构建。
- P206 独立 SA1 已 FAIL：8.5/9.2pt 字号、五个运算符像素、四处共 134px 刻度—曲线非法重叠、q1/q2 净空 2.2/0px，以及题注承诺未编码的训练点进入顺序；根线程已看 1:1 ROI，下一角色 SA2。
- 新释放的只读槽已交 P222。它必须从官方 R91 页生成未缩放 300dpi 五类证据，逐元素测量；不得读取旧报告、修改源码或中央状态。

## Revision 94 代理交接（最新）

- P157 SA2 R2 已 FIXED 并交权；本地证据全部通过但不具最终签发资格。根线程已构建官方 R92：813 页、4,933,704 bytes、硬日志 0；P157 位于物理页 170。
- 新 P157 独立 SA1 只能读取 R92 官方 PDF、当前图源与直接正文，只能写 `FIG-P157-01/STRICT_R3_SA1_R92/`；禁止读取任何 P157 R1/R2/SA2/root 证据。全门 PASS 后仍须隔离 SA3。
- P222/P242 的旧通过图审查继续运行；两者仍以 R91 为各自启动时冻结的官方对象，不得混入 R92 或彼此证据。其审查结论针对未受 P157 两文件影响的图源，仍可用于当前候选。
- P222 已 FAIL：23 个 9.20pt、6px 省略号、角色比、`X_{d-1}` 内净空 4.472136px、图文索引上下标不一致；下一角色 SA2。
- P242 已 FAIL：23 个 8.70--9.30pt、两个 `否` 与箭头分别重叠 10px/2px、同类/角色比例失败；下一角色 SA2。
- 两个旧通过图只读槽已轮转到 P262/P282，均使用当前官方 R92，继续严格隔离和原生 300dpi 逐元素审查。

## Revision 95 代理交接（最新）

- P157 R92 SA1 的首版掩膜方法已作废；有效重算证实 T02 到两曲线均 0 overlap、163.125px 净空。唯一 FAIL 为 T04 `选择复杂度` 到 G06 x轴 1.2361px<3px。
- P157 当前唯一源码写者为专属 SA2 R4；白名单仅 `V1-C10/fig_v1_c10_complexity.tex`，且只能移动/重锚 T04，目标>=8px。所有其他源码、正文、中央文件和 build 禁写。
- P262/P282 继续只读审查当前官方 R92；不得读取旧报告或彼此证据。

## Revision 96 代理交接（最新）

- P157 SA2 R4 已交权，唯一源码变化为 T04 y=`-.02→-.07`；本地独立掩膜净空 19px、overlap0、162/162关系全过。根线程已构建官方 R93（813页、4,933,710 bytes、硬日志0）并启动全新盲审 SA1 R5，只能写 `FIG-P157-01/STRICT_R5_SA1_R93/`。
- P262 严格 SA1 FAIL：23个低字号、7个像素失败、三处共241px非法文字—图形交叠；P282 严格 SA1 FAIL：19个低字号、6个11/13px等号。两图均由根线程看过原生1:1 ROI，下一角色 SA2，禁止启动SA3。
- 两个旧通过图只读审查槽现为 P309/P324，冻结读取 R92；禁止读取各自旧报告、修改源码或中央状态。
- 严格最终仍为3/99。当前源码无 SA2 写者；若 P157 SA1 PASS，下一角色只能是隔离 SA3；若 FAIL，按其精确阻塞返回唯一 SA2。

## Revision 97 代理交接（最新）

- P157 官方 R93 独立 SA1 R5 已 PASS，根线程已回读全部 CSV 并查看四视图/关键原生 1:1 ROI。旧 T03—G04 4px 量测已因 mask 污染标 `SUPERSEDED`；当前 overlap0、净空15px。65 个独立 text-text 的 bbox 最小36.541667px，84个 text-graphic 最小15px，clip0。当前唯一合法下一角色为全新隔离 SA3 R6，正在运行；它禁止读取任何 P157 旧 evidence/角色结论，只能写 `FIG-P157-01/STRICT_R6_SA3_R93/`。
- P309/P324 严格 SA1 均 FAIL并已由根确认，下一角色均为 SA2；不得启动 SA3。P324 的独立文字 bbox 净空0px是硬失败，即使前景像素相距6px也不能抵消。
- 两个旧通过图只读槽现为 P346/P372，均固定5.6terra/max、官方R93、原生300dpi逐对象审查。两者须显式输出 text-text bbox clearance、边缘/裁切、字体视觉协调证据；缺失即FAIL。
- 严格最终仍为3/99，源码当前无SA2写者。P157 SA3若PASS则交根最终签发；若FAIL则返回唯一P157 SA2。P346/P372任一完成后继续轮转旧通过图。

## Revision 98 代理交接（最新）

- 新附件 Goal 已完整读完并核验与发布副本逐字一致；平台 Goal 已由旧读取占位目标切换为完整 v2.7.0 Goal，状态 active。磁盘工作树、权威 Goal 和已有证据不复制、不迁移、不重建。
- P346/P372 严格 SA1 均 FAIL且根已复核；P346 为 50px 曲线穿字及字号/比例失败，P372 为 82/89 字号失败、角色失衡与三个 3px 基准减号。二者下一角色 SA2，禁止 SA3。
- P412 严格 SA1 FAIL且根已复核：11个图源文字为9.0/9.2/9.4pt。原161px反馈线结果已标作方法假阳性；真实PDF dash+白底绘制顺序下 overlap0、净空7px。题注共享链约9.962640pt通过，SA2不得修改公共题注样式。
- P157 隔离 SA3 R6 仍运行；P392 与新补位 P429 为当前两个旧通过图盲审槽。三者均只读各自白名单与专属证据目录。
- P157 槽释放后优先启动 P634 专属 SA2；P392/P429 任一完成后用下一旧通过图补位。严格最终仍为3/99；根签发前不得增加。

## Revision 99 代理交接（最新）

- P157 官方 R93 隔离 SA3 R6 与根复核均 PASS；最终证据在 `FIG-P157-01/STRICT_R6_SA3_R93/`。12字号、12像素、210关系、27边缘行全过，overlap0、clip0、文字—图形最小15px、文字—文字bbox最小35px。P157 已 `STRICT_PASS/CLOSED`，新严格计数为4/99。
- P392 官方 R93 严格 SA1 FAIL并经根确认：85/98源字号、12字形像素失败；末端 `y_{n+1}` 与双环重叠31+8=39px、净空0。下一角色SA2，禁止SA3。
- 当前两个旧通过图盲审槽为 P429/P445；两者必须继续原生300dpi 1:1逐字形/逐对象检查，包含基础运算符独立子串、bbox净空、字体协调和四视图。
- P634 专属 SA2 已启动，白名单仅 `V5-C04/fig_v5_c04_coordinate_sweep.tex` 与 `FIG-P634-01/STRICT_R2_SA2/`；允许 `NO_CHANGE_REQUIRED`，不得修改中央文件、公共样式、正文或构建输出。交权后由根决定官方构建与新 SA1。
- 后续唯一 SA2 队列优先含 P412/P346/P372/P392及既有失败图。P547/P602/P608/P609/P630/P654/P715 仍禁止重开。

## Revision 100 代理交接（最新）

- P482/P504/P521 已完成新严格 SA1 与根复核，均 FAIL→SA2：P482 为 435px 四对真实文字—图形碰撞及字号/比例；P504 为字号/字形/角色比/0px文字bbox净空及二维 `K=2` 残差矛盾；P521 为字号/字形/比例、全局 `phi_z` plate 作用域和 `N_d`/`L_j` 记号错误。不得启动 SA3。
- P634 最终独立 SA1 R3/R93 已 FAIL：SOURCE_FONT/ROLE/FONT_HARMONY/SEMANTICS/OVERLAP/CLIP 均通过，但 31 个独立字面运算符/标点 `H_ink` 与一类题注全角逗号比例失败。专属 SA2 是当前唯一源码写者，白名单仅 `V5-C04/fig_v5_c04_coordinate_sweep.tex` 与 `FIG-P634-01/STRICT_R4_SA2/`；必须结构化修复，禁止 `scale y`、整体缩放、巨大突兀标点、公共样式/正文/中央状态写入。
- 当前两个只读旧图槽为 P525/P544，均只读官方 R93 和各自新证据目录。P525 要复算主题单纯形下参数唯一性条件；P544 要核对依赖图的行/列向量固定点约定。两者仍须完整逐字形、全 pair、四视图后才可交结论。
- `STRICT_FIGURE_EVIDENCE_SCHEMA.md` 已加入 `FONT_VISUAL_HARMONY_PASS`、可缩小边界、原生300dpi 1:1 双mask/ROI和同题注自然行流规则。所有后续 SA1/SA3 必须执行；任何缺失/UNKNOWN=FAIL。
- 严格最终仍为4/99。P547/P602/P608/P609/P630/P654/P715 禁止重开；中央 inventory/state/wrapper/build 仍仅根线程单写。

## Revision 101 代理交接（最新）

- 用户指定 Goal 附件/发布副本仍为 SHA-256 `51BA862B1EEBCD6765565FEE6243BD2BC8BF2611D586115B52623668711928C2`。平台当前执行镜像 `3cad37cf-9e33-47b2-aea3-7ff46f3a6153/goal-objective.md` 为 2,275 行、287,029 bytes、SHA-256 `B60E2436C422BDEF817F8D3316C7AD0AB5E1B340256ED3DFBE86DFFDEBEB3BF9`；规范化去除 Markdown 转义并统一换行后逐字符一致，故不重建、不重置。
- P544 严格 SA1 已根确认 FAIL→SA2：显式8.8pt图例/边标签、像素与角色协调失败，虚线图例箭头真实重叠6px、净空0，且固定点行/列记号与正文冲突。
- P525 SA1 恢复时必须纠正源字号：公共 `every node/.append style={font=\small}` 使普通节点/公式约10.0pt；仅显式8.8pt图例属于源字号失败。所有依赖 CSV/JSON/报告计数与角色比必须重算，旧错误行不得保留为有效结论。
- P552 SA1 从现有证据目录继续，保持完整原生300dpi、1:1无膨胀双mask/ROI、逐字形、全pair、字体视觉协调和数学/正文一致性门。
- P634 SA2 R4 从现有结构化候选继续，仅完成证据与交接；不得写中央状态或构建官方全书。根线程验收唯一图源差异后才构建R94并启动全新SA1。
- 严格最终仍为4/99；P547/P602/P608/P609/P630/P654/P715继续禁止重开。中央 inventory/state/wrapper/build 仍仅根线程单写。

## Revision 102 代理交接（最新）

- 官方连续候选已更新为 `src/build/strict_current_r94_fullbook/main_full.pdf`：813页、4,934,451 bytes、全页A4、硬日志模式0。P634唯一定位为物理682／印刷669／图33.3；逐图代理不得使用R93、standalone或旧局部候选冒充官方R94。
- P634 SA2 R4 已完成唯一图源修改与正式交权，当前没有源码写者。全新隔离 P634 SA1 正在只读 R94 并只能写 `FIG-P634-01/STRICT_R5_SA1_R94/`；禁止读取任何旧 P634 evidence/报告。自然脚本像素门按当前 Goal 为15px。若PASS，必须再创建全新的隔离SA3，不能复用SA1/SA2实例。
- P525/P552/P556-01/P556-02/P556-03 已被新严格SA1和root确认FAIL→SA2；其中P556-03为字号84/14、像素13/6、D 10/20组和E 3/20组失败，overlap/clip为0且语义通过。任何几何通过都不能抵消字号/比例/和谐失败。
- 两个旧通过图盲审槽当前为P558与P570；P570使用R94，P558现有任务完成后由root核对其冻结候选。两槽都必须整页native300dpi后像素切片、逐字raw H、全部独立前景pair、1:1和8×nearest临界证据，并显式给出字体视觉和谐；字体可适度缩小但不得低于9.5pt或破坏整图观看。
- 中央inventory/state/build/public style仍仅root单写；任一时刻最多一个SA2业务源码写者。严格最终仍为4/99；P547/P602/P608/P609/P630/P654/P715继续禁止重开。

## Revision 103 代理交接（最新）

- 官方候选继续固定为 `src/build/strict_current_r94_fullbook/main_full.pdf`（813页、4,934,451 bytes、A4、硬日志模式0）；所有运行中的 SA1 只能从该 PDF 自行定位物理页并直接生成 native300dpi 整页。
- P558/P570 均已完成严格 SA1 与 root 验收并 `FAIL→SA2`。P570 的 `REL_0274` 是原生真实 0px 净空：最右“绝”字与最终可见虚线框不交叠但像素相贴；relation/pair/clearance 各1项失败。该数值已由底层CSV、93组临界证据和机器终检一致确认，不得恢复为PASS。
- 统一 `STRICT_FIGURE_EVIDENCE_SCHEMA.md` 已新增强制条款：1:1原生mask唯一计数；8×nearest只供人工看像素；文字mask不得混邻字/同色图形；节点边框与真实halo分pre/halo/final-visible；机器终检必须交叉核对唯一/非空mask、全部pair、失败证据和CSV/JSON/Markdown。
- 当前三个只读实例分别为：P634 官方R94全新SA1（返工证据口径与caption链）、P573全新SA1、P575全新SA1。每图实例与证据目录独立，禁止读取各自旧报告，禁止修改业务源码、中央库存、状态或构建。
- 当前没有业务源码写者。若P634 FAIL，下一源码角色优先为其专属SA2；若PASS，只能启动新的隔离SA3。P573/P575完成后由root先验收再以新的独立SA1实例轮转库存。
- 中央库存99行：4 CLOSED、39 SA2、56 SA1；严格最终仍为4/99。P547/P602/P608/P609/P630/P654/P715继续禁止重开。

## Revision 104 代理交接（最新）

- P634 R94 SA1与root均判FAIL→SA2：11枚CJK `一` 像素门失败、D23、E3；`EL-035-CARD1_STATE-MATH_SCRIPT`到`G-CARD1-BORDER`为overlap0但final-visible raw净空2.162px<5px。机器终检闭合452 mask、145 pair对象、10,440 pair。新的专属P634 SA2是当前唯一业务源码写者，只可改`V5-C04/fig_v5_c04_coordinate_sweep.tex`并写`STRICT_R6_SA2`；必须保持普通字号>=9.5pt和整图协调，禁止遮盖/虚构halo/中央写入/官方构建。
- P573 R94 SA1与root均判FAIL→SA2：12个8.6pt刻度、24个字形像素、D2、E3和字体协调失败；423关系overlap0、clip0、最小净空16px，数学与题注通过。P573不得在P634交权前启动源码修复；后续PASS必须来自全新逐图SA1。
- P575仍为全新独立R94 SA1；P577已用另一全新独立R94 SA1补位。二者只写各自证据，不得改业务源码/中央状态/官方PDF，必须原生300dpi、1:1分离raw mask、8×人工核像素、完整字体协调和机器终检。
- 中央库存99行：4 CLOSED、41 SA2、54 SA1；严格最终仍为4/99。官方仍为R94。P547/P602/P608/P609/P630/P654/P715继续禁止重开。

## Revision 105 代理交接（最新）

- P575 R94 SA1与root均判FAIL→SA2：28/31语义字号、26/151真实pixel-height、D10、E16失败；1378 pair中非法overlap0、clip0，4个TEXT_TEXT PDF/vector bbox净空失败（PAIR_0171/0406/0533/0977），最小bbox0px、raw ink6.708px。初版204px graphic误计和3px颜色污染均已纠正，最终机器终检PASS。
- P575已停止写入，槽位由全新独立P580 SA1补位。P580只读R94/图源/正文并写自己证据；必须记录Goal B44把支持覆盖图的“唯一读图结论”误写为接受--拒绝流程的卡片冲突，以实际图源与正文审数学/文本，不改Goal。
- P634仍是唯一业务源码写者；其局部双遍构建已成功，源码可见CJK`一`已为0，字号最小仍9.6pt，首卡目标净空预测约18px，但全量D/E/关系终检未完，不得据此宣告PASS或构建官方R95。
- 当前另一个只读槽为P577 R94 SA1。中央库存99行：4 CLOSED、42 SA2、53 SA1；严格最终仍4/99。禁止重开P547/P602/P608/P609/P630/P654/P715。

## Revision 106 代理交接（最新）

- P634 专属 SA2 R6 已完成唯一图源修改并正式停止写入；局部终检193 glyph、58 semantic、39 graphic/background、4656 pairs，D0、E0、overlap0、clearance0、clip0，最小普通字号9.6pt，EL035脚本/字面到卡片边框分别16/18px。其结论只允许作为修复交接，不能代替官方PDF独立审查。
- root 已冻结官方 `strict_current_r95_fullbook/main_full.pdf`：813页、4,934,184 bytes、全页A4、14字体全嵌入/子集/Unicode、19类硬日志0。P634在物理682页／印刷669页／图33.3；root native300dpi整页/彩色/灰度查看仅为预检。
- 新的 P634 SA1 必须是全新隔离实例，只读R95、当前图源/邻文/公共样式，禁止读取全部历史P634 evidence/报告/角色结论；只能写新的专属目录。它须逐字形测像素，完整D/E、全关系/全pair、独立raw mask、pre/halo/final-visible、字体协调和数学语义，且机器terminal与CSV/JSON/Markdown一致。
- P577/P580继续作为两个互相独立的R94 SA1。P577已接近正式FAIL交接但尚未结束；P580仍在复测以剔除数学拆分与半透明底伪阳性。只有正式交接并经root回读才更新库存。
- 中央库存99行当前为4 CLOSED、41 SA2、54 SA1；严格最终仍4/99。当前没有业务源码写者；P573/P575/P558/P570等保持串行SA2队列。禁止重开P547/P602/P608/P609/P630/P654/P715。

## Revision 107 代理交接（最新）

- 最新 Goal 与用户后续“全部已通过绘图重新检查”要求覆盖早期七图豁免：P547/P602/P608/P609/P630/P654/P715 的旧 PASS 只作历史，必须按新 9.2.1 协议重新资格认定。P020/P157/P632/P756 已按新协议闭合且未受源/共享样式变化，严格最终仍 4/99。
- P580 当前只认可新的 `RUN7_TEXT_ISOLATION_R2/`。05:30 终态/stop 已显式 WITHDRAWN/SUPERSEDED；R2 必须为 236 个 MAP_ID 生成同 bbox 的 ORIGINAL、唯一红色 TARGET OVERLAY、MASK ONLY 三视图，并逐行实际打开填写人工 ledger。全局布尔批量 PASS、pending、空 mask、污染、缺笔或终态矛盾均禁止。已知边界标签遮挡 `q_L=2/5` 是决定性 FAIL，但仍须完成全图审查。
- P634 当前只认可 `PATH_ISOLATED_R3_SAFE/`。R2 因 Windows 冒号 ADS 与缺笔掩膜无效；R3 必须 safe filename、普通文件可枚举/打开、实际 fill/opacity/underlay、100% final-visible 笔画完整、193 字形三视图与逐行人工 ledger。不得使用 95% 完整容差或全局 manual 开关批量放行。
- P577 R1 已被 root 以 `T022_G01` 假括号掩膜否决；槽释放后需新的逐图只读实例写非覆盖 R2，并重做 342 字符及 TG304/TG317/TG457。
- 当前没有业务源码写者。任一 SA1 正式交接后，root 必须回读所有底层表与 contact/临界证据，只有稳定结果才能更新中央 4 CLOSED／41 SA2／54 SA1 库存。

## Revision 108 代理交接（最新）

- P577 R2 接管实例不合规：它仍是原 P634 SA2 canonical 实例，无法证明 fresh `gpt-5.6-terra/max` SA1 身份，已在仅产生两张页面渲染图后停笔。`FIG-P577-01/STRICT_R1/SA1_20260824_R2/ROLE_MISMATCH_SUPERSEDED.md` 是唯一有效说明；后续不得读取/继承该目录。新实例须同时读 `ROOT_STRICT_R2_TASK_SPEC.md` 与 `ROOT_STRICT_R3_TASK_SPEC.md`，只写 `SA1_20260824_R3/`。
- P580 当前仅认可其下一次新生成的纠偏目录；`RUN7_TEXT_ISOLATION_R2` 05:56 输出仍是 superseded interim。运行前须由实际 final mask 派生 qL 隐藏/残片分类，并闭合 G0061/支撑点、左右 p 标签/曲线、纹理标签/曲线的分层证据；236逐字/子串人工行与63视觉和谐行必须逐项填写。
- P634 当前目标输出改为 `PATH_ISOLATED_R4_PDF_REPLAY_SAFE/`。R4 必须把原88px逐个归属到具体非文字纹理 path/seqno 或真实遮挡，给全193 glyph 的 final-visible missing=0/foreign=0、safe普通文件、三联图与193人工行；此前R2/R3均非终态。
- root 暂不更新中央库存。当前没有业务源码写者；稳定 SA1 结果必须先经 root 全量回读。

## Revision 109 代理交接（最新）

- P580 当前有效终态仅为 `FIG-P580-01/STRICT_R1/SA1_20260824_R1/RUN7_TEXT_ISOLATION_R2/`，`STRICT_R1_FINAL.md` 与最后写入的 `WRITE_STOPPED.md` 一致给出 `FAIL→SA2`。234/234 contact、15/15 sheets、63/63 视觉行、2145/2145 pair 和机器闭合均完成；决定性真实缺陷包括 `q_L=2/5` 后缀被白底遮掉、青色方块吞“线”、8 个不透明底和 3 个半透明底遮图形，并有像素/D/E/净空/协调失败。root 已看完全部 50 个 1:1 与 8×关系包；不得把 overlap=0 单项误写为整图 PASS。
- P634 当前有效终态仅为 `FIG-P634-01/STRICT_R7_SA1_R95/PATH_ISOLATED_R8_CID_KNOCKOUT_AUTHORITY_SAFE/`。证据完整性 PASS，但 9 个原生高度失败导致图本身 `FAIL→SA2`；193 glyph、14 sheets、192 四视图行、1891 pair、1681 关系、1544 mask 均闭合，无污染、ADS、重叠、净空或裁切问题。字体视觉协调为 FAIL，旧 SA2 局部 PASS 与 root 预检均已被独立 SA1 取代。
- 中央库存为 4 CLOSED／43 SA2／52 SA1；严格最终仍 4/99。当前无业务源码写者，P577 R3 继续只读。
- 下一唯一源码角色为新的 P580 专属 SA2。白名单仅 `V5-C02/fig_v5_c02_is_support.tex` 与其新 SA2 证据目录；必须恢复被遮文字、移除/重排遮图底色和标记、修复逐字像素/D/E/净空，且字号允许适度缩小但仍须满足 9.5pt、原生像素和整体协调门。不得写中央状态、公共样式、正文、官方全书构建或其他图源。

## Revision 110 代理交接（最新）

- P020/P157/P632/P756 的旧终局证据均早于当前 schema，且各自终局目录没有 100% glyph contact sheet、逐格 reviewer ledger 或 final mask-integrity 闭合文件；旧证书已撤销为历史，四图全部回 `SA1`。中央库存现为 0 CLOSED／43 SA2／56 SA1，严格最终为 0/99。
- P577 当前 R3 已由 root 实际打开 35/35 原字形 contact 及新增失败包；真实失败包括 TG457 的 2px<5px、5个 opacity-1 白底对象覆盖 p(y) 曲线（PRE∩GROUND 共3825原生像素），以及逐字像素/D/E门。初始色投影大数是 `SUPERSEDED`，终态不得引用。
- P582 当前 R1 已由 root 打开 final 12/12 glyph contact 与 P0717 1×/8×双方 mask；箭头尖端与 `.380` 的末位0有3个真实共享像素。真实碰撞不属于 mask 污染；角色 E 门必须按 final glyph H_INK 的 PANEL×ROLE×SCRIPT_CLASS 计算，PDF span pt proxy 已禁用。
- P580 仍是唯一 Sol/max SA2 和唯一业务源码写者。权威条款明确语义标点必须独立 substring/raw mask 并按自身 H_INK 判门；图号`.`、题注`；/。`若低于对应门，不能 local PASS，且不得越权修改全局 caption 样式。
- P577/P582 释放后，各用独立 Terra/max 只读实例进入历史通过图重新资格认定队列；证据必须写新目录，不得复制旧结论。

## Revision 111 代理交接（最新）

- 低轮廓标点采用同 codepoint/字体/字重/有效字号的原生300dpi H_INK+面积双比例校准门；不得继续把正常句点、逗号、分号按22px/30px机械判FAIL，也不得借父行高度。无现成参照时须保存独立校准source/raw/1×/8×证据。
- 数学运算符、关系号继续22px；stacked fraction的分子/分母/主体也为22px，只有真正TeX上下标/上下限可用15px。P580两个`5/2` tick的四个20px数字仍是真FAIL，应改结构而不是改分类。
- P577/P582/P580 在WRITE_STOPPED前必须重算受影响行并同步CSV/JSON/Markdown/terminal；图本身既有真实遮挡/碰撞/字号等失败不因本分类修正自动消失。

## Revision 112 代理交接（最新）

- P577 R3 图本身已由 root 验收 `FAIL→SA2`，但其 evidence integrity 因两份 CSV 重复表头降为 FAIL；不得引用代理 terminal 的 evidence PASS。可用返修事实仅为 TG457 2px＜5px 与五个 opacity=1 白底共覆盖曲线3825px，低轮廓标点旧机械行已被 revision111 排除。
- 中央库存为 0 CLOSED／44 SA2／55 SA1，严格最终0/99。P580仍是唯一源码写者；P577只进入SA2等待队列，不得并发改源。
- 原 P577 Terra/max 实例现只读重审 P020，写全新非覆盖证据，禁止读取/继承旧 PASS。P582完成并经root验收后转审P157，形成用户要求的两条历史通过图独立复审线。

## Revision 113 代理交接（最新）

- P582 R1 已封存并经 root 验收：证据完整性 PASS，图形硬门 FAIL→SA2。真实缺陷为 E014 箭头与 E016 `.380` 末位 `0` 原生 300dpi 共享 3px、净空0px＜4px，另有源字号29/45、合并字形门68/139、D3、E2及字体协调失败。
- P582 代理不得再写原证据目录；其实例立即转为独立只读 P157 旧通过图重审。新目录必须是 `FIG-P157-01/STRICT_R7_REQUAL_R111_SA1_20260824`，不得放入或读取旧 `STRICT_FINAL`，不得继承旧 PASS/terminal。
- P020 与 P157 两线都须原生300dpi 1:1计数、8×nearest逐像素人工检查、100% glyph三联 contact与逐格ledger、全pair/必审关系、pre/halo/final-visible遮挡反演、低轮廓标点校准、字号/同角色/灰度/整页协调闭合。允许适度缩小，但不得低于硬门或影响整体观看。
- 中央库存为0 CLOSED／45 SA2／54 SA1，严格最终0/99。P580仍是唯一业务源码写者；所有其他图源修改串行等待。

## Revision 114 代理交接（最新）

- P020 当前图形结论为 root 确认 `FAIL→SA2`，唯一直接证实硬门是题注 CJK `一` 原生H_INK=5px＜30px；108 glyph/18 contact/关系与遮挡未显示其他图缺陷。其 evidence integrity 因 `WRITE_STOPPED` 后仍写两份terminal JSON被降为FAIL。
- 原P020审查实例已转入P632盲审，新目录 `FIG-P632-01/STRICT_R8_REQUAL_R111_SA1_20260824`；不得读取旧P632 evidence/PASS/截图结论。P157第二条线继续独立运行。
- 后续代理必须先写完terminal JSON/MD，最后才写`WRITE_STOPPED.md`，并在stop后绝对停止；若顺序不符，即使底表可解析也判evidence integrity FAIL。
- 中央库存0 CLOSED／46 SA2／53 SA1，严格最终0/99；P580唯一业务源码写者约束不变。

## Revision 115 代理交接（最新）

- P157当前schema重新资格认定已由root签发：evidence integrity PASS、figure hard gates FAIL→SA2。80 glyph/10 sheets全部实际打开；五个低轮廓校准、E门8 glyph和P0155独立曲线139px共享为返修事实，旧516px/37px结论禁止恢复。
- P632当前schema重新资格认定已由root签发：evidence integrity FAIL、figure hard gates FAIL→SA2。413 glyph/42 sheets已由root打开；30像素字号、D13/E12、36净空失败为图形返修事实，R0046只是一致性FAIL而非物理失败。G204–G209父级、413行raw role-ratio和stop最后写入不可证明必须重新闭合。
- 中央库存为0 CLOSED／48 SA2／51 SA1，严格最终0/99。原P157与P632审查实例已分别转为只读P756与P582-02盲审；两者只写新证据目录，禁止旧PASS/旧terminal迁移，必须100% glyph原生1×/8×、全关系/遮挡和字号/字重/颜色/灰度/页面协调闭合。
- P580仍是唯一Sol/max业务源码写者。其封存前必须给53个关键关系逐包实际打开，并对GR004_GR025、GR020_GR022、GR020_GR024三行写非空证据路径、验证11个必需PNG存在可解码；root local acceptance与官方R96均尚未发生。
- P547/P602/P608/P609/P630/P654/P715按用户最新明确边界冻结，不为它们创建新的重开任务。它们的现有库存行和历史证据保留，但不得冒充当前schema新PASS。

## Revision 116 代理交接（最新）

- 用户重新指定完整 Goal 附件为最高目标；其与发布目录主提示词逐字一致。附件要求 99 图无旧通过豁免，故 P547/P602/P608/P609/P630/P654/P715 重新进入当前 schema 资格认定队列。Revision115末尾的冻结句仅保留为历史，已被 D-026 覆盖。
- 不打断当前已分配任务：P580继续唯一Sol/max业务源码写者；P756与P582-02继续独立Terra/max只读盲审。七图在审查槽释放后逐图创建新实例，不复制旧PASS/terminal，不并发修改源码。
- 其余门不变：100% glyph、native 1×唯一计数、8×nearest逐像素人工核验、全关系/遮挡、字号/字重/颜色/灰度/页面协调、完整底表与 `WRITE_STOPPED` 最后写入；任何缺证或硬FAIL不得PASS。

## Revision 117 代理交接（最新）

- P580 SA2 已封存并由root完成本地验收；root随后通过唯一入口构建官方R96。R96为813页、4,933,724 bytes、A4、14字体全嵌入/子集/Unicode、19类最终日志硬模式0，SHA-256 `8EED8765A4856C4C197262DEA06E283790FBA8DA906C70C26FC7BD56F6F7E5E8`。P580定位物理628／印刷615／图31.6；root原生300dpi预检不等于最终PASS。
- 新P580 Terra/max SA1只读R96、当前图源和直接正文，只写`FIG-P580-01/STRICT_R4_SA1_R96_20260824`，禁止读取任何P580旧evidence或root结论。PASS后仍只能转新的隔离SA3；FAIL回唯一P580 SA2。
- P756 R95新协议SA1已封存且root接受FAIL事实：P1408两条独立路线边界重叠792px/净空0，3个CJK`口`为29px<30px；证据完整性PASS，下一角色SA2。
- P582-02 R95新协议SA1已封存且root接受FAIL事实：67/149字号<9.5pt、`=`12px、`≈`18px、题注`一`9px，另有21个低轮廓标点校准未闭合；证据完整性FAIL、图形硬门FAIL，下一角色SA2。
- 两条历史旧PASS审查线现为P547与P602，各由新的Terra/max实例从R96重建100% glyph、全pair、遮挡、字号协调和数学证据，禁止读取各自旧PASS。当前无业务源码写者；中央库存0 CLOSED／49 SA2／50 SA1，严格最终0/99。

## Revision 118 代理交接（最新）

- 原 P547/P580/P602 三个只读 SA1 因平台额度中断，均未写 `WRITE_STOPPED`，不得引用为封存终态。其目录中的任何初步FAIL/PASS仅作待验证机器材料。
- 新的独立 Terra/max 接管实例分别审 P547、P580、P602，只写各自 `STRICT_R5...CONT_20260824` 新目录；三者已完成 Goal/schema/直接正文全读及 R96 PDF、页码、图源哈希核验，不得读取或继承更早历史PASS。
- P547须独立复测多处`=`、箭头和CJK`一`候选像素失败；P580必须彻底排除首轮颜色投影误并的32个非结论FAIL并用PDF矢量边界重建正式pair；P602须独立闭合175 glyph/20 contact、35对象/595 pair和破折号/顿号低轮廓校准。
- 所有报告使用规范路径 `v2.7.0/_work/...`；`v2.7.0_work`仅为同一物理树junction。terminal/manifest必须先完成，`WRITE_STOPPED`最后写且之后绝不修改。
- root验收完成后，PASS只进入全新隔离SA3，FAIL进入唯一SA2串行队列。下一源码写者优先P756 SA2；当前无业务源码写者，严格最终0/99。

## Revision 119 代理交接（最新）

- P580 R5 CONT SA1已封存全门PASS并经root逐像素验收，仅路由至全新隔离 `p580_sa3_blind_r96`；SA3只写 `FIG-P580-01/STRICT_R7_SA3_BLIND_R96_20260824`，禁止读旧P580证据、库存与状态，未回root前不计关闭。
- P602 R5 CONT SA1已封存且root接受FAIL→SA2：175 glyph中23个失败（10硬高度、15 mask纯度、2交集）。P547 R5 CONT SA1也由root接受FAIL→SA2：至少17硬高度与4个1px净距失败；C0153 mask另含第三外来分量，旧manual mask-purity PASS及该行低轮廓测量不得复用。
- P756专属Sol/max SA2是当前唯一业务源码写者，只可修改 `V5-C08/full_course_synthesis_map.tex`。其他代理均不得写业务源码；P547/P602专属SA2须等P756释放后再串行创建。
- root中央库存已同步为0 CLOSED／50 SA2／48 SA1／1 SA3，严格最终0/99。下一只读审查应从P608/P609/P630/P654/P715及其余旧PASS逐图选择独立实例；仍须100% glyph、全pair/遮挡、原生1×与8×nearest、字体协调、terminal→manifest→WRITE_STOPPED。

## Revision 120 代理交接（最新）

- P756 SA2局部包已root验收，root已冻结官方R97：813页、4,933,735 bytes、SHA-256 `062AD81020CB19A5C6688A45C73E00965F5060E0960A69AF820D7DC154DEE814`、A4、14字体合规、19类最终日志硬模式0。P756定位物理801／印刷788／图37.8；root四视图预检只允许启动新SA1。
- 全新 `p756_sa1_fresh_r97` 只读R97和当前P756源，只写 `STRICT_R15_SA1_REQUAL_R97_20260824`；禁止旧P756证据/冻结结论。旧通过P608由未处理过P608的独立实例只写 `STRICT_R1_SA1_REQUAL_R97_20260824`；两者均须100% glyph、完整对象pair、原生1×与每个临界区8×nearest逐像素、字体协调及逐格人工ledger。
- P580 R7隔离SA3的`PASS_TO_ROOT`已被root拒绝：234/235漏`U+0338`且`U+226A` mask混入该斜线；`record_manual()`批量写全部glyph/pair PASS，缺schema逐格ledger；45对象/990 pair未与SA1 260对象/33,670 pair闭合。根记录在 `STRICT_R8_ROOT_REJECT_SA3_R96_20260824/`。P580回SA2，禁止迁移R7 PASS字段。
- 当前中央库存0 CLOSED／50 SA2／49 SA1／0 SA3，严格最终0/99。无业务源码写者；下一独立Sol/max实例只能从P580/P547/P602选一图占用源码写者，其余等待。任何SA1 PASS仍须新的隔离SA3和root签发。

## Revision 121 代理交接（最新）

- P547专属Sol/max SA2已启动，当前唯一业务源码写者仅可修改`V5-C01/fig_v5_c01_transition_graph.tex`（起始SHA-256 `638CEA4285D3A9411251DA149963CC7AE4500FA5827F0A99A51FF1FC76640D1A`），只写`FIG-P547-01/STRICT_R7_SA2_REPAIR_R97_LOCAL_20260824`。P580/P602不得并发改源。
- P547须先独立重分割C0153 `；`的污染mask，再处理12个矮`=`、3个矮`→`、C0073 CJK `一`、C0198数学主体`n`和4个1px净空关系。允许定向适度缩小或重排，但普通可见文字不得低于9.5pt，不得突兀放大、整体缩放、拉伸或用底色/halo遮问题。
- P756 `STRICT_R15_SA1_REQUAL_R97_20260824`与P608 `STRICT_R1_SA1_REQUAL_R97_20260824`继续独立只读审查。必须给出100% glyph逐格人工ledger、完整对象与无序pair分母、全部原生1×及临界8×nearest证据；脚本批量写`PASS_MANUAL`一律否决。
- root已补齐R96→R97全813页栅格身份：812页相同，仅物理页801变化；300dpi差分bbox位于P756修复区域。该证据只冻结官方候选，不替代SA1/SA3/root闭环。
- 中央库存0 CLOSED／50 SA2／49 SA1／0 SA3，严格最终0/99。任何代理终态都须terminal/manifest先完成、`WRITE_STOPPED`最后写且之后零写入；代理PASS不等于root验收。

## Revision 122 代理交接（最新）

- P608 root原生预检已确认上面板横轴与下标题`\overline X_{6:t}`的overbar前景连续、净空0；根证据在`evidence/root_work/R97_P608_PRECHECK/`。代理必须独立给双方唯一mask和exact shared pixels，确认后终态应FAIL_TO_SA2，不能被其他PASS抵消。
- P608旧机器对象账漏掉drawing[61]/[62]两条overbar，造成文字bbox假净空。中央schema第37/64行与protocol第59/73行现强制所有rawdict外数学重音/规则以`GRAPHIC/MATH_RULE`对象进入总分母、全部无序pair与四联人工账；所有活跃代理已收到重读通知。
- P756原64对象/2016 pair只是新增规则门前的中间分母；须证明39项drawing已覆盖所有可见math rule，否则扩充分母并全表重算。P547新几何`=`/`→`与全部公式规则同样执行此门。
- P608中间机器表111 glyph/99对象/4,851 pair仍有6 pixel、11 purity、26 pair候选，且人工ledger未闭合；任何PENDING或0.75低轮廓占位不得进入terminal，校准必须按H_INK与面积比`[0.92,1.08]`。
- P547仍为唯一业务源码写者；P580/P602等待。中央库存0 CLOSED／50 SA2／49 SA1／0 SA3，严格最终0/99。

## Revision 124 代理交接（最新）

- P608 R97独立SA1已由root接受`FAIL→SA2`：102对象、5,151 pair、114 glyph、110卡完整；P2315重叠16px、P3071 overbar—axis净空0px、另有5个glyph硬失败。P608在P547交权前不得改源。
- P756 R97独立SA1已封存并由root完成全包审计，只接受进入新隔离SA3。root打开16/16 glyph contact、11/11 graphic contact、32/32 critical五联卡、G030/G031 z-order与整页/图体/灰度；251 glyph、69对象、2,346 pair、overlap0、clip0、普通9.60--10.20pt。根记录在`STRICT_R16_ROOT_SA1_ACCEPTANCE_R97_20260824`，不计最终关闭。
- 新`p756_sa3_blind_r97`为全新Terra/max隔离只读实例，只写`FIG-P756-01/STRICT_R17_SA3_BLIND_R97_20260824`；不得读取任何P756旧evidence、SA1/SA2/root结论、中央库存或人工PASS标志，必须从官方R97和当前源独立重建100% glyph、完整drawing/path、对象与全pair、1×/8×、字体和封存证据。
- P547专属Sol/max SA2仍是唯一业务源码写者；P609为另一条独立R97 SA1。中央库存0 CLOSED／51 SA2／47 SA1／1 SA3，严格最终0/99。任何代理PASS都不能替代root验收。

## Revision 125 代理交接（最新）

- P547 R7 SA2局部修复及R7A长路径补封已由root接受，业务源已冻结为SHA-256 `DF3D4415EDC56D02E056CAE0F3E38830DF28E781BC67ECDFB69863C5038F1600`。root通过唯一入口构建官方R98：813页、4,934,249 bytes、SHA-256 `52FA2EF0769553C8B6FD4B8D3CBA5BE671FA0F3190591A596FB8B6512C108A41`；A4/字体/日志/来源链均通过。
- R97→R98逐页栅格隔离仅物理页591变化。root已开300/200dpi全页、图30.2彩色/灰度裁片和差分图，只有`PRECHECK_PASS_TO_FRESH_SA1_NOT_FINAL`。全新`p547_sa1_fresh_r98`禁止读旧P547 evidence/状态/结论，只写`STRICT_R10_SA1_FRESH_R98_20260824`并独立重建全协议；代理PASS也只可转新的隔离SA3。
- P609 R97 SA1包已由root验收为FAIL→SA2：GL024/026/034/045/065/072/076/088/109共9项硬失败；其他59对象/1,711 pair/40卡/2规则/5重音通过不具治愈性。根记录在`STRICT_R2_ROOT_FAIL_ACCEPTANCE_R97_20260824`。
- `p756_sa3_blind_r97`与`p630_sa1_blind_r97`继续只读，后续验收须把各自图页与R98的逐页同一性写明。当前无业务源码写者；下一个源码角色优先P608唯一SA2，须等槽释放后启动，P609等继续串行等待。
- 中央库存经99行重计为0 CLOSED／51 SA2／47 SA1／1 SA3，严格最终0/99。所有代理仍须100% glyph、全部前景drawing/math rule、N choose2全pair、原生1×与至少8×逐像素实际开图、字体协调和terminal→manifest→WRITE_STOPPED最后写入；缺一项即FAIL。

## Revision 126 代理交接（最新）

- P756隔离SA3已封存且由root接受FAIL→SA2。唯一硬失败为`GLY0215` U+FF1A：目标10/34、两个同条件官方参照均10/37，精确面积比`34/37=0.918918…<0.92`。root已开目标/参照original、overlay、mask、8×和全页/图体/灰度；不允许四舍五入或以整体美观覆盖硬门。
- P756全包root复算为113对象、6,328全pair、378可见glyph、58 graphic、129 critical；2,905载荷逐项hash/bytes/missing均0，0-byte/ADS/post-stop均0。根记录在`FIG-P756-01/STRICT_R18_ROOT_SA3_FAIL_ACCEPTANCE_R97_20260824`。R98只改物理页591，故R97物理页801的失败直接适用于R98。
- 已复用释放的代理槽启动P608唯一专属SA2；该实例当前角色仅为P608源码写者，不得再写P756。唯一业务源是`V5-C03/fig_v5_c03_trace_running_mean.tex`，起始SHA-256 `DA035C1920CB900E54D3658851C1D71D9C6446531EFF50BEE6E089B567835AE4`；只写`STRICT_R4_SA2_REPAIR_R98_LOCAL_20260824`，不得写中央状态或官方构建。
- P608须修复G008/G019、G027/G058、G063及P2311/P2315/P3071；禁止用不透明底、halo、z-order或裁切遮碰撞。局部全门PASS只允许交root构建下一候选，再由新鲜SA1与隔离SA3复核。
- P547新鲜R98 SA1与P630旧PASS重资格SA1继续只读。中央库存0 CLOSED／52 SA2／47 SA1／0 SA3，严格最终0/99；任一时刻最多一个业务源码写者。

## Revision 127 代理交接（最新）

- P630 R97全新SA1已封存并由root接受FAIL→SA2：GLYPH-013/025 U+2212均H3<22，GLYPH-022 U+22C5 H5<22。root已开三项四联/8×卡、相关sheets与全局图；123对象、7,503全pair及其余门PASS不抵消。949文件封存的两层manifest、集合、ADS和stop均由root复核通过；R98对应页像素同一。
- P630库存已改SA2；下一修复规格在`STRICT_R2_ROOT_SA2_TASK_SPEC_R98_20260824`，但P608交权前不得启动。中央库存0 CLOSED／53 SA2／46 SA1／0 SA3，严格最终0/99。
- 完成P630的代理槽现切换为P654图34.1新鲜R98 SA1；禁止读取任何旧P654 evidence/PASS/中央状态，唯一只读源SHA-256 `01EA85F46A9567D7ED6CF88C92346F9BE317FAFDDCF1F7791C07B2A3ED3858EB`，只写`FIG-P654-01/STRICT_R1_SA1_REQUAL_R98_20260824`。
- P608仍是唯一源码写者。首个diff仅将vertical sep 8.5→11.0mm、两处`=`改局部几何关系符、两处脚本`t`局部提升；必须用官方LuaLaTeX/Noto/STIX栈量测，Fandol不能签字体/字形PASS。
- P547 R98 SA1已实际打开193 glyph、40 graphic、94 critical，当前硬失败0；仍须补完1,830全pair人工账及封存，未封存前不下PASS。

## Revision 128 代理交接（最新）

- P547新鲜R98 SA1已经封存并由root接受为角色PASS：840载荷/842实际文件精确闭合，193 glyph、61语义对象、1,830全pair、71 primitive、37内部primitive pair、14源锚定端点和337项实际开图全闭合；root已亲自打开22 glyph、7 graphic、8 critical和10 global原像素视图，未见非法重叠、裁切或突兀字号。根记录为`STRICT_R11_ROOT_SA1_ACCEPTANCE_R98_20260824`，不计最终关闭。
- 新`p547_sa3_blind_r98`为全新隔离只读实例，只写`FIG-P547-01/STRICT_R12_SA3_BLIND_R98_20260824`；严禁读取任何旧P547 evidence、状态、库存或root/SA1结论，须从官方R98和当前源独立重建完整分母、全pair、native1×/8×与实际开图账。
- P608仍为唯一业务源码写者；其几何`=`宏已改为纯字母控制序列，必须以官方Noto/STIX LuaLaTeX结果闭合，不接受Fandol字体PASS。P654继续独立R98 SA1。
- 中央库存0 CLOSED／53 SA2／45 SA1／1 SA3，严格最终0/99。任何代理PASS仍须root重哈希、重算分母和逐图打开后才能路由。

## Revision 129 代理交接（最新）

- P608当前官方栈`after_final`不得PASS：纵轴G031/G062随文字旋转90度，page bbox 16×37px必须转换为local text axes；local ink-height为37px，高于主体X约30px，且为自然标题脚本G035/G074 21px的1.762倍。此前按page-H=16宣布脚本门通过是坐标错误，并造成14.3462pt突兀放大。
- root已封存original/mask/8×卡、机器表和整图于`STRICT_R5_ROOT_ROTATION_NORMALIZED_FONT_FAIL_20260824`。P608仍是唯一源码写者，须恢复自然脚本层级或作最小调整，并对所有旋转glyph给page与local两套H/W；现有R4 `after_final`标为superseded。
- P547隔离SA3与P654独立SA1继续只读。中央库存0 CLOSED／53 SA2／45 SA1／1 SA3，严格最终0/99。

## Revision 130 代理交接（新对话恢复时优先于全文历史）

- 迁移检查点已主动中断三个旧续跑实例：`p608_sa2_resume_r2`、`p654_sa1_resume_clean`、`p547_sa3_resume_blind`；三者本轮均报告未改文件。现有未封存目录保留，新对话必须新建实例接续，禁止旧新两个对话并发写同一工作树。
- P608是唯一SA2与唯一业务源码写者。当前源SHA为`7E24A58CD39F44B34FB85FFD65F83A2950913D37A009B978B75E961DB5D45297`；在既有R4目录从after_final_r2续跑，重点补真实旋转关系、hatch—全部glyph/两条MATH_RULE、低轮廓、91对象/4095全pair、纯净完整mask与实际开图封存。root接受前不得构建R99。
- P654是全新只读SA1。旧21 graphic masks、7626 pair、16 critical及PAIR_106_118已因P003混入箭头碎片全部作废；按PDF seqno逐path隔离重放并证foreign=missing=0后，从头重建分母、pair与人工账，重开G0017/G0059/G0066和9.6:11.8字号比例。
- P547是严格隔离只读SA3；禁止读任何P547 R10/R11/root/旧证据。独立闭合57对象/1596 pair、193 glyph、71 path，并用multi-owner ledger/20:1归属解决G139的1px漏笔且不得混入后续`p`像素。
- 所有实例必须完整读protocol/schema，原生300dpi 1×逐像素计量、8×nearest仅视觉；100% glyph/path/math-rule、全部无序pair、1×/8×实际开图、font harmony与terminal→manifest→WSTOP均是硬门。普通字号不得低于9.5pt且不得突兀；允许适度缩小但不能损害整体观看。
- 官方候选R98身份不变；库存45 SA1／53 SA2／1 SA3，严格最终0/99。完整恢复细节以`v2.7.0续_交接文档.md`第14节为准。

## Revision 131 顶层分对话交接（新版架构）

- 旧三个普通续跑实例由独立顶层任务 `v2.7.0支线1` 接管；其 A worktree/branch 为 `dialogue_A_visual` / `v2.7.0/dialogue-a-visual`。R130 证据保持，P608 仍是首批唯一图源写者，P654/P547 只读。
- 内容域由独立顶层任务 `v2.7.0支线2` 接管；其 B worktree/branch 为 `dialogue_B_content` / `v2.7.0/dialogue-b-content`，只写章节/局部文本与 B 自有状态证据，不得写图源/共享对象。
- 三树共同基线为 `7f65bd75ce94aee876aa25735e92214bb5ebe004`；已用 `* -text` 与原始 blob 覆盖消除 CRLF 偏移，A/B P608 源 SHA 均恢复为 `7E24A58CD39F44B34FB85FFD65F83A2950913D37A009B978B75E961DB5D45297`，status/staged 均 0 后才发 `WORKTREE_READY_VERIFIED`。
- A/B 必须通过 `handoff/A`、`handoff/B` 的真实文件与分支提交交接；主线合并顺序固定 B 后 A。聊天中的完成声明不视为交接。

## Revision 132 主线交接补充（发布包与 B 定向失败包）

- 主线发布包提交 `4c6e80f`，增强导航审计提交 `4bb1bf5`，当前可见版本扫描提交 `193d93d`。发布白名单临时 ZIP 校验 PASS，200 项、零 PDF/legacy/v240/v260，37 章、99+2 图记录与提取后 DryRun 全闭合；R98 的五册/37章/双索引/元数据/A4/链接审计也已 PASS，813页可见版本集合仅 `{v2.7.0}`。
- B 已收到 4 个内容域失败：规范术语宏、分布名空格、手写术语变体、V5-C03 NAV-007。B 必须在自身 worktree 修复并把精确复测写入 handoff；主线不得直接改 B 的章节文本。
- A 的 R130 三线已恢复且等待批准状态已解除；保持现有角色/证据与唯一 P608 写者约束。
- 后续交接仍按 B 后 A；支线以共同基线 `7f65bd7` 提交，主线在 `193d93d` 之后集成并处理冲突。主线发布脚本变更不要求反向同步到支线。

## Revision 133 主线交接补充（14 项总交付结构）

- 当前主线提交 `9eee438` 新增总交付打包器与测试。它只接受 Goal 的 13 个非空载荷并生成第 14 个总 ZIP；内部五目录和 13 个成员名称完全固定，临时根实包测试 PASS。
- 该工具属于主线独占发布域，不反向同步 A/B。A/B handoff 合入、最终候选、视觉证据、两份台账、报告、manifest 与双 max 门未闭合前只能运行 `--check`，不得正式生成总 ZIP。
- 下一集成仍按 B 后 A，当前主线基点为 `9eee438`。

## Revision 134 主线交接补充（B-EXM-P01 已集成）

- B 首批 handoff 位于 `_work/handoff/B/B-EXM-P01/`，分支提交 `b2801d2ec38b7d1aabf65bf8374454abf480517c`。主线已验证 31 文件清单与实际提交完全一致、分支及工作树清洁、无禁写域变更。
- 主线已无冲突合并为 `c89c28c2b4dd152d7b073b1d334cd1490cf8e956`，独立运行内容域 32 项与发布包 5 项，共 37 项通过（1 skipped）。源码包抽取 DryRun 继续 PASS。
- B 的 `B_LOCAL_PASS` 只关闭首批：剩余 60 道例题及其余知识点、定理/定义、推导、练习和算法契约继续分批。新的 B handoff 仍须原子提交、清单、测试、模型路由、盲审和未决项齐全。
- A 尚无正式 handoff。P608/P654/P547 继续 Revision 130 第14节断点；严格完成仍为0/99，P608 主线接受前不得构建 R99。

## Revision 135 主线交接补充（R99 与首个 A_LOCAL_PASS）

- A 的 P608 SA2 单文件提交 `e933f09e757d406954edd09f8ce0a326248c7da9` 已由主线核验并合入，主线提交 `b09f12302a75c417a4df50c0547c73ebdeb80900`。官方 R99 已成功冻结：814页、4,940,207 bytes、SHA-256 `E8D76EEF0D120C518FA94A8F339BF6777AD18AA6AF0BCC17DFB46DF6DFC49EC6`；最终构建exit0、日志硬诊断0、导航审计PASS。
- A 已启动 `A-R99-P608-SA1-FRESH-20260824`（Terra/max），严格禁止读取旧 P608 evidence/SA2/root/handoff/state/inventory；PASS也只可转全新隔离SA3。P608仍非 `A_LOCAL_PASS`。
- P715首个R99 SA1因在产证前误读state/inventory而立即作废，任何结论无效；有效替代实例为`A-R99-P715-SA1-FRESH-B-20260824`，写全新STRICT_R1B并严格隔离旧P715证据/状态。它只读，不改变P654唯一源码写者约束。
- P547 R12A 已由主线再次全量复核：1862 manifest项全部bytes/hash一致，实际1864普通文件，ADS0，WSTOP绝对最后。中央 inventory 已记 `A_LOCAL_PASS_MAIN_FINAL_RELEASE_PENDING`；A本地完成1/99，但严格最终仍0/99。
- P654 SA1 的真实字号/比例/净空失败已接受并转 SA2；P654 SA2 是当前唯一业务图源写者。中央99行分布现为45 SA1／53 SA2／0 SA3／1 A_LOCAL_PASS。
- B 已解除主线构建期间的排版暂停并继续 `B-EXM-P02`。任何新批次仍须封存、提交和 handoff 后才进入主线。

## Revision 136 主线交接补充（B-EXM-P02 已集成）

- B 第二批 handoff 位于 `_work/handoff/B/B-EXM-P02/`，原子提交 `907f65346dfca3960bad92fc36203f7242584ef5`；主线验证提交父项、5 文件清单、禁写域、B 工作树清洁、SA1 R2、隔离 SA3 与机械证据后，合入为 `a37b2ca`。
- 主线独立运行 9 项内容/布局契约全部通过，并打开检查例 8.1、19.1、26.1、33.3、37.2 覆盖的 10 个渲染页。B 内容累计已集成 11/66 道例题；其余对象继续新原子批次。
- P654 仍占用 A 侧唯一受控排版时隙。B P03 在主线确认后可进入单写源码阶段，但释放通知前不得启动新全书构建；P608/P715 继续 R99 只读取证。
- 官方候选仍为 R99且不含P02；下个候选必须覆盖主线 `a37b2ca` 及随后接受的输入。不得重算未变化的R99身份/导航门。
- 独立分册构建的 `block/itemize` 键错误已路由主线共享域，只登记、不阻塞P02，也不得由B修改共享构建入口。

### Revision 136 P715 路由增量

- `A-R99-P715-SA1-FAIL-20260824`已由主线接受；只承认R1C metadata-only reseal。主线复核833/833 manifest、835普通文件、ADS0及WSTOP严格最新全部通过。
- P715结论固定为`FAIL_TO_SA2`：N=298、44,253全pair、44 glyph失败、19 critical失败。不得启动SA3，不计A_LOCAL_PASS。
- 中央inventory现为44 SA1／54 SA2／0 SA3／1 A_LOCAL_PASS。P715进入唯一图源写者队列；显式授权前禁止改源。

## Revision 137 主线交接补充（P03/P654 集成与 R100）

- B-EXM-P03 原子提交 `475531944934b2c06e9183058829d5e42252a50f` 已集成为主线 `23de9f5db8a961e26f6614f38720e389f144134b`；7文件、10例题、主线10项契约和17页视觉均PASS。B累计21/66，P03证据保持不可变，P04源码/静态流程已解冻但当前不得启动TeX。
- P654 SA2 提交 `e392bd8e5f37dfd49f071f7251c281d46bb68ffd` 已集成为主线 `81d7c7ad150a9306ae3599fe9c15f4c8bb125d9a`；局部证据与主线视觉验收PASS，但只属于local SA2。P654全新隔离R100 SA1已派发，确认启动前仍按SA2计数。
- P608 R99 fresh SA1失败包已由主线接受并转SA2；仅两枚natural-script `t` 为10px<15px。P608现为A唯一图源写者并持有唯一受控排版时隙，不启并发TeX。
- 官方R100为814页、4,943,206 bytes、SHA-256 `5B1E4B4C5D64A0CA49833F38ED28C4397392BF5E50503431F3170614DF63D171`；build、双索引、导航及18页视觉均PASS。它不是最终发布版。
- A已明确确认`A-R100-P654-SA1-FRESH-20260825`以`gpt-5.6-sol/xhigh`启动，旧P654 evidence/角色包/root/handoff/state/inventory/聊天结论全部禁读，业务源只读且TeX禁用。中央inventory已仅切换P654角色，现为44 SA1／54 SA2／0 SA3／1 A_LOCAL_PASS。严格最终仍0/99，14项交付未闭合。

## Revision 138 主线交接补充（P608/P04 与 R101）

- P654 R100 fresh SA1的唯一 `FRM_TRIAL_005 n=21px<22px` 失败已由主线接受并转SA2。P608 R6A local SA2提交`738e079d8e85621b23f30e71017eafde37681711`已集成为`dc307eb1ef1d3c9d04dba0c91e05a2bb322234ff`，但仍不计A_LOCAL_PASS。
- B-EXM-P04提交`933fe1d00d9e0661d6a2dce6cc8e3d87b0ab649e`已集成为主线`05a5f6e21ac025fccb03f256731c6060d0a19043`；7文件/10题、10项主线契约、18页视觉、SA1/SA3均PASS。B累计31/66。
- 官方R101为814页、4,947,496 bytes、SHA-256 `0870FF226DC383875C4A1B6EABB06AAB942317DA294D90D2864B3030D46DF1A1`，构建、双索引、导航、14字体及19页视觉全部PASS。不要重复其冻结门。
- P608 R101 fresh SA1 R7虽闭合N172/C14706与机械inventory，但因循环/模板批量写全部人工True/PASS/0与模板note、并缺source SHA，被root拒绝。R7不可变，中央仍记SA1，不启SA3；全新R7A只重做逐ID真实人工账和source SHA绑定，禁止改源/TeX/迁移R7人工结论。
- P654 target-only窄SA2的两次latexmk均exit12、无PDF/像素门，固定为`BUILD_FAIL_NO_CANDIDATE`。R6非TeX预检已闭合并由主线接受：三项TEXMF变量parent/child同值，kpsewhich六检查0失败，child probe 42 bytes，source/wrapper不变。它排在B-P05 R2之后，只有新R7根+direct lualatex显式grant才可构建。
- B-P05 R1机械门通过但隔离SA3 FAIL；四处局部R2源修及静态门已PASS，当前持有唯一R2构建槽。禁止第二invocation/R3；结束后复核受影响/相邻页并走全新post-fix SA1与新隔离SA3。
- inventory为44 SA1／54 SA2／0 SA3／1 A_LOCAL_PASS；严格最终0/99。P715保持SA2队列，P547保持本地通过待最终发布。

## Revision 139 主线交接补充（P05 R2视觉失败与P654 R7）

- B-P05 R2构建机械PASS：815页A4、4,948,176 bytes、硬错及over/underfull为0。页211/232孤立练习标题已闭合，但页338/454与R1 PNG逐字节相同，异常留白未修，故R2视觉FAIL，不能进入fresh SA1/SA3。
- 主线仅授权V3-C02/V3-C07两个标题调用在局部组内固定`smallskipamount=3pt`。B已完成R3精确两行源码/静态门并冻结；在P654释放与主线显式grant前TeX禁用。
- B释放R2且主线确认TeX进程NONE后，P654已获全新R7根的唯一direct-lualatex controller；禁止latexmk/并发/retry，三项TEXMF变量同绑该根`texcache`。成功PDF才跑native300dpi N116/C6670。
- P608 R7 root拒收继续有效；审计pyc创建/删除只作为事故披露，普通文件虽未改变但根metadata mtime污染。R7永久隔离，不再写/import；全新R7A必须真实逐ID人工裁决、对象特异note并绑定source SHA。
- inventory不变，严格最终仍0/99；R101身份与已通过门不得重复。

### Revision 139 P05 R3终检增量

- R3唯一Resume自然exit0并释放，完成时间以CONTROL为准：`2026-08-25T05:00:02.9654537+08:00`。PDF 815页A4、4,948,175 bytes，硬错及over/underfull为0。
- 主线独立打开13页并PASS：页338/454异常间距消失，页211/232分页修复未回归，相邻页无裁切、重叠、断框或异常分页。
- B现只可走完全fresh post-fix SA1→另一个新隔离SA3；两角色/root封存/原子提交/handoff前不计B_LOCAL_PASS、不进P06，TeX继续禁用。

## Revision 140 主线交接补充（P05集成、P608 R7A路由）

- B-P05 sealed handoff已闭合fresh SA1与fresh isolated SA3，提交`73049af2eac24af285a29b627ad98c085bc7d699`由主线集成为`d32aa49fd44662fbe33d31c021997ca4e9024058`。主线10 tests OK、工作树clean，B累计41/66；B可启动P06源码/静态，但TeX禁用且P01--P05冻结。
- A 的P608新R7A由独立root接受为`FAIL_TO_SA2`；唯一失败`HARD-LOWPROFILE-TXT-098`的clean area ratio为`56/61=0.9180327868852459<0.92`。中央inventory已由P608 SA1转SA2，分布`43/55/0/1`。不得启SA3或计A_LOCAL_PASS。
- P654 R7因bulk/template/default/global人工账整包root拒收，sealed R7只读。P654继续SA2，只能在全新R7A做非TeX真实逐ID人工重封，主线接受前不得提交或派fresh角色。
- 当前TeX槽空闲但未授予任何任务。P608、P654、P715的业务源码均须遵守A侧唯一图源写者；B-P06构建须另行申请。
