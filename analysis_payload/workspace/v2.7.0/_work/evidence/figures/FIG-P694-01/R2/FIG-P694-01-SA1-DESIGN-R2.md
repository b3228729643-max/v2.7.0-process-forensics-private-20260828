# FIG-P694-01 — SA1-R2 只读设计

## 结论

- `DESIGN_READY=YES`
- `SPLIT_REQUIRED=YES`：**仅在同一正式图号、同一 canonical UID `FIG-P694-01` 内重构为两个物理面板**；保留 `fig:V5-C06-variational-updates`、`FIG-V5-C06-07` 与既有图号，不新增 UID、图号或浮动体。
- `BLOCKERS=NO`：可以交给唯一 SA2 实施。下文的“预算记录与最终模型”语义需在根线程 R3 与邻近正文同步核验，不能被旧图或旧读图句抵消。
- 当前中央 `figure_numeric_manifest_v16.json` 中不存在 `FIG-P694-01` 或 `fig:V5-C06-variational-updates` 记录；应由根线程按单写者规则新增可复核的符号/分支契约记录。

## 已读输入与已确认约束

1. `AGENTS.md`：原书/任务要求/精修前 PDF 只读；公共状态、索引、构建、权威库与状态文件单写者；本任务只设计，不构建。
2. `R1/FIG-P694-01-SA1-R1.md`：原图失败原因是局部预算/失败越级到 `C_{kv}`，外层预算伪装为完成，未遍历 `m=1,\ldots,M`，缺双证书/失败门且可见字号为 9.2pt。
3. 当前 `fig_v5_c06_variational_updates.tex`：一张嵌套大框把“局部 `是／预算到`”直接连到全语料 `C_{kv}`，又把“外层 `是／预算到`”接到同一输出；这正是本次必须消除的错误。
4. `V5-C06.tex` 的正式契约：
   - 局部 VI 输入固定严格正 `\alpha,\varphi`、`T_{\rm loc}` 与 ELBO/参数容差；更新 `\eta_{mnk}`、`\gamma_{mk}`，并以 ELBO 相对增量和参数变化作双证书。
   - 完整 VEM 必须先遍历全部文档；任一局部 `budget_stop`/失败时带标签退出，**不得执行 M 步**。随后才可构造 `C_{kv}^+`、更新严格正 `\varphi^+`、以至多 `J_{\rm ls}` 个回溯候选保护 Newton `\alpha^+`，并在全候选有限且不异常下降后原子提交外层轮。
   - `\varepsilon_{\rm loc},\varepsilon_{\rm out}` 是局部/外层 ELBO 相对增量阈值；`T_{\rm loc},T_{\rm out}` 是硬上限；`J_{\rm ls}` 是每次 Newton 的最大回溯候选数。
5. 当前首引处只在同一句中提到本图和方法比较图，随后连续输入两图，没有本图专属 `\FloatBarrier` 与读图句。当前 page wrapper 也仍把“达到硬上限沿退出边继续”写成易误读的描述；standalone/page wrapper 元数据仍为 v2.6.0。
6. `V5-C06/figure_sources.json` 对象为 `FIG-V5-C06-07`，目前 caption、teaching objective 和 alt 仍把两类“预算到”写成普通停止条件，须由根线程同步。

## 不可协商的流程语义

### 状态分层

- **局部成功态**：空文档的 `\mathtt{completed}`，或非空文档双证书成立的 `\mathtt{converged}`。只有这两态可产生 `\mathrm{LocalOK}_m`，进入语料级汇总。
- **局部非成功态**：`\mathtt{budget\_stop}`、`\mathtt{invalid\_input}`、`\mathtt{numerical\_failure}`。它们只写入该文档/启动的最后合法状态、计数和诊断；**没有任何边连接到 `C_{kv}`、`\varphi`、Newton、`\mathcal S_{\rm acc}` 或跨启动选择**。
- **外层收敛候选**：外层 ELBO 与参数双证书同时成立的 `\mathtt{converged}`；它作为绿色“收敛候选”进入 `\mathcal S_{\rm acc}`。
- **外层预算候选**：若一个启动已经完整通过每轮的局部成功门、M 步 / Newton / ELBO 门并保持 `\mathtt{feasible}=\mathtt{true}`，但在 `T_{\rm out}` 耗尽前未满足外层双证书，则以 `\mathtt{budget\_stop}` 写入 `\mathtt{record}[s]`。它可作为橙色虚线“预算候选/未收敛”进入 `\mathcal S_{\rm acc}`，但状态必须保持 `\mathtt{budget\_stop}`，绝不能改写为 completed/converged。
- **外层失败态**：`\mathtt{invalid\_input}`、`\mathtt{numerical\_failure}`、`\mathtt{line\_search\_failed}`、`\mathtt{random\_source\_failure}`，以及由局部预算/失败传播而来的启动失败，均只进入 `\mathtt{record}[s]`，不进入 `\mathcal S_{\rm acc}`。
- 跨启动候选集合严格使用正文第 1047 行的口径：
  \[
  \mathcal S_{\rm acc}=\{s:\mathtt{record}[s].\mathtt{feasible}=\mathtt{true},\
  \mathtt{record}[s].\mathtt{status}\in\{\mathtt{converged},\mathtt{budget\_stop}\}\}.
  \]
  若集合非空，在同口径最终 ELBO 与冻结并列规则下选最佳最后合法参数，输出必须携带所选的原始 `status`；若所选者为 `budget_stop`，节点和题注均写“预算候选/未收敛”。若集合为空，才返回“无可选模型 + 全部状态/诊断记录”。

这一区分遵从当前权威算法：外层 `budget_stop` 是**可行但未收敛的候选**，并非失败或正常完成；局部 `budget_stop`/任何失败仍禁止 C/M 步。图、题注、alt 与读图句必须逐字保留这种差异，根线程 R3 以 `\mathcal S_{\rm acc}` 的正式定义复核。

## 目标版式：同图号的上下双面板

使用一个不缩放的 `tikzpicture`，上下堆叠两个等宽圆角面板，而不是用一个嵌套大框。这样在 A4 正文宽度内可让两面板都使用显式 `\fontsize{9.6pt}{11.5pt}\selectfont`（所有可见文字不低于 9.5pt），并给失败出口留出独立走线。

通用视觉语法如下。

- 蓝色实线箭头：候选/成功主链；深蓝实线“成功令牌”是唯一跨节点提交通路。
- 深灰或蓝黑 `densely dashed` 回边：尚有预算时的下一轮；回边也须至少 `0.80pt`。
- 绿色实线圆角终点 + `✓`：合法成功态；橙色 `dashed` 八角/停止标记：硬预算耗尽；红色 `dash dot` 带 `×` 终点：数值/输入失败。线型、形状和文字状态必须同时编码，不能只靠颜色。
- 主箭头 `\ge .85pt`、反馈/失败箭头 `\ge .80pt`、节点边框 `\ge .75pt`；不使用 `scale`、`transform shape` 或整体 `resizebox`。
- 面板标题直接写 `(a) 单文档局部 VI 循环`、`(b) 语料级外层 VEM 循环`，而不是仅用颜色框暗示层级。

### 面板 (a)：单文档局部 VI 循环

**输入节点（左上）**

`文档 w_m=(w_{m1},…,w_{mN_m}); 固定 α>0, φ_{k\cdot}∈ri(Δ^{V−1}); T_loc; ε_loc^L, ε_loc^γ`。

输入旁用小的前置门明确：词索引在训练活动词表、每个目标词的 `\varphi_{k,w_{mn}}>0`、容差/预算合法。失败边为
`\mathtt{invalid\_input}(\mathtt{support\_failure}) → 记录最后合法状态/诊断，停止（不汇总）`。

**主链节点（从左至右）**

1. `N_m=0?` 决策。是：
   `γ_m=α, η_m=∅, s_done=p_done=0, status=completed`，以绿色成功令牌送往面板 (b) 的“全部文档门”。
2. 否：初始化
   `η_{mnk}^{(0)}=1/K; γ_{mk}^{(0)}=α_k+N_m/K; L_m^{(0)} 有限`。
3. “临时局部 E 块”框（单一完整轮，而非逐节点半提交）：
   \[
   a_{mnk}=\log\varphi_{k,w_{mn}}+\psi(\gamma_{mk})-\psi\!\left(\sum_\ell\gamma_{m\ell}\right),\quad
   \eta_{mnk}^{+}=\frac{e^{a_{mnk}}}{\sum_{\ell=1}^{K}e^{a_{mn\ell}}},\quad
   \gamma_{mk}^{+}=\alpha_k+\sum_{n=1}^{N_m}\eta_{mnk}^{+}.
   \]
   标签须写“log-sum-exp；对全部 `n=1,…,N_m` 同步形成候选”。
4. “可行/单调门”菱形：`η^+∈ri(Δ), γ^+>0, L_m^+ 有限且不下降？`。
   - 否：`rollback last legal (γ_m,η_m,L_m); status=numerical_failure; diag=(s,n,gate)` 红色终点，文字附“**不汇总 C / 不执行 M 步**”。
   - 是：`原子提交；s_done←s_done+1, p_done←p_done+N_m`。
5. “局部双证书”菱形：
   \[
   \delta_{\mathcal L,m}=\frac{|\mathcal L_m^+-\mathcal L_m|}{1+|\mathcal L_m|}\le\varepsilon^{\mathcal L}_{\rm loc},\qquad
   \delta_{\gamma,m}=\max_k\frac{|\gamma^+_{mk}-\gamma_{mk}|}{1+|\gamma_{mk}|}\le\varepsilon^{\gamma}_{\rm loc}.
   \]
   是：`status=converged; LocalOK_m=(γ_m,η_m,L_m,s_done,p_done,diag)`，绿色成功令牌。
6. 否后进入“硬局部预算”菱形 `s_done=T_loc?`。
   - 是：`status=budget_stop; 保留 last legal + 计数/诊断；停止`，橙色出口并明写“**不送 LocalOK；不汇总 C / 不执行 M 步**”。
   - 否：深灰虚线回到“临时局部 E 块”，边标为“否：下一局部轮”。

面板 (a) 只有 `completed` 与 `converged` 两条绿线可在面板底部汇入一个标为
`LocalOK_m，仅 status∈{completed,converged}` 的端口。三个非成功出口要落在该端口之外，且没有穿过/触碰它的边。

### 面板 (b)：语料级外层 VEM 循环

**输入/启动节点（左上）**

`D={w_m}_{m=1}^M; K; α^(0)>0; φ^(0)_{k·}∈ri(Δ^{V−1}); T_out; ε_out^L, ε_out^Θ; T_loc; R_start; J_ls`。

节点附 `start s`、`r_done=0`、`record[s]`。启动随机源失败或基线 ELBO 非有限分别走
`random_source_failure` / `numerical_failure` 到 `record[s]`，并终止该启动。

**主链节点（从左至右）**

1. `对 m=1,…,M 调用面板(a)`；用一个窄的文档栈/计数标识表示“全部文档”，而非一条文档的箭头。每次调用保存 `(status_m,γ_m,η_m,L_m,diag_m)`。
2. 决策门：`∀m: status_m∈{completed,converged}?`。
   - 否：`record[s] ← first local non-success + last legal global state + (s,r,m,diag)`；标明 `budget_stop / invalid_input / numerical_failure`；红/橙出口到“启动停止”，并在边旁写“**禁止 C 与 M 步**”。
   - 是：唯一蓝色实线进入 `C_{kv}^+=\sum_{m=1}^{M}\sum_{n=1}^{N_m}\eta_{mnk}\,\mathbf1\{w_{mn}=v\}`。
3. “期望计数/主题词门”：先核验所有 `C_{kv}^+` 有限、`C_{k\cdot}^+>0` 且每个 `C_{kv}^+>0`；通过才形成
   `\varphi_{kv}^+=C_{kv}^+/C_{k\cdot}^+`，并标注“逐主题严格正、按 `v` 归一化”。任何 nonfinite / empty_topic / support_collapse 都到 `numerical_failure → record[s]`，不进入 Newton。
4. “受保护 Newton”框：
   \[
   H(\alpha)\Delta=g(\alpha),\qquad
   \alpha^+=\alpha-\rho\Delta,\quad
   \rho\in\{1,\tfrac12,\tfrac14,\ldots\},\ j\le J_{\rm ls}.
   \]
   接受门必须清楚写为 `min_k α_k^+>0` **且** `\mathcal L^+\ge\mathcal L`（同时有限）；`J_ls` 个候选无一通过时唯一出口为
   `line_search_failed; rollback last legal; record[s]; 停止`，不能把它画成“下一轮”或一般成功。
5. “完整候选/原子提交”框：只有 `\alpha^+,\varphi^+,{\gamma_m^+,\eta_m^+},\mathcal L^+` 同时可行、有限且 ELBO 不异常下降，才
   `commit; r_done←r_done+1`。任何门失败到 `numerical_failure → record[s]`。
6. “外层双证书”菱形：
   \[
   \delta_{\mathcal L}=\frac{|\mathcal L^+-\mathcal L|}{1+|\mathcal L|}\le\varepsilon^{\mathcal L}_{\rm out},\qquad
   \delta_{\Theta}=\max\!\left\{\max_k\frac{|\alpha_k^+-\alpha_k|}{1+|\alpha_k|},\max_{k,v}|\varphi_{kv}^+-\varphi_{kv}|\right\}\le\varepsilon^{\Theta}_{\rm out}.
   \]
   - 是：`status=converged; record[s].feasible=true; ConvergedCandidate_s`，以绿色实线进入 `\mathcal S_{\rm acc}`。
   - 否：进 `r_done=T_out?`。
     - 是：`status=budget_stop; last legal + r_done + diagnostics → record[s]; feasible=true`，以橙色虚线“预算候选/未收敛”进入 `\mathcal S_{\rm acc}`；状态文字不可改成 converged。
     - 否：虚线“否：下一外层轮”回到 `m=1,…,M`，并明确每轮重新完成全部局部调用。
7. 面板右下的跨启动后处理接受两种状态已明确区分的候选：
   \[
   \mathcal S_{\rm acc}=\{s:\mathtt{record}[s].\mathtt{feasible}=\mathtt{true},\
   \mathtt{record}[s].\mathtt{status}\in\{\mathtt{converged},\mathtt{budget\_stop}\}\}.
   \]
   若集合非空，按冻结并列规则和同口径最终 ELBO 从中选择；唯一“最佳最后合法参数”节点输出
   `\widehat\alpha,\widehat\varphi,{\widehat\gamma_m,\widehat\eta_m},\mathcal L, s_{\rm done},r_{\rm done},m_{\rm done},k_{\rm done},j_{\rm done}, status\in\{converged,budget_stop\}, diagnostics`。
   节点必须附可见状态徽标：选择 `converged` 时为绿色“收敛”；选择 `budget_stop` 时为橙色“预算候选/未收敛”。两者可返回最佳最后合法参数，但绝不可共用“已收敛”文本或符号。
   若集合为空，单独灰/红终点写 `无可选模型；返回 record[1:R_start] 的状态、最后合法审计快照和诊断`。它不得与候选选择节点共用箭头。

### 面板间接口与边的禁令

- 面板 (a) 的 `LocalOK_m` 是面板 (b) 的唯一局部输入，必须标出 `m=1,…,M` 全部到齐。
- 局部 `budget_stop`、`invalid_input`、`numerical_failure` 与全部外层失败态 `invalid_input/numerical_failure/line_search_failed/random_source_failure` 均终止于“记录/停止”节点；它们不能合流成蓝色主链，不能触发 `C_{kv}`，不能跳过局部门去 M 步，也不能进入 `\mathcal S_{\rm acc}`。
- `completed`（仅空文档）和 `converged` 的局部状态可进 `LocalOK_m`。只有完成全部局部成功门、完成可行外层轮、并在 `T_{\rm out}` 耗尽时仍 `feasible=true` 的**外层** `budget_stop`，可由橙色虚线“预算候选/未收敛”从 `record[s]` 进入 `\mathcal S_{\rm acc}`；它绝不倒流到 C/M 步，也绝不获得绿色收敛符号。
- “最后合法状态”在失败审计记录中仅用于回滚证据；在从 `\mathcal S_{\rm acc}` 选出的预算候选中可作为返回参数，但输出框必须把 `status=budget_stop` 与“预算候选/未收敛”并列、以不同颜色/线型/形状显示。

## 图文、题注与可访问性契约

### 短题注（替换现题注）

> 点参数 LDA 的两层变分 EM：只有每篇局部 VI 以 `completed/converged` 成功后，才可汇总 \(C_{kv}\) 并执行 M 步；局部预算或任何失败均止于记录，外层可行的 `budget_stop` 仅以“预算候选/未收敛”及原 status 参加同口径选择，绝不冒充收敛。

### 专属 alt text

> 对象—关系—结论：图分为单文档局部 VI 与语料级外层 VEM 两面板。局部面板交替更新责任度 η 和伪计数 γ，只有空文档 completed 或双证书 converged 才产生 LocalOK；局部预算耗尽、支持/数值失败只记录并停止。外层面板只有收齐全部 LocalOK 后才汇总 \(C_{kv}\)、归一化 \varphi、进行正域和 ELBO 门保护的 Newton \(\alpha\) 更新；可行外层 budget_stop 以“预算候选/未收敛”身份连同原 status 进入 \(\mathcal S_{\rm acc}\)，line-search 或数值失败不进入该集合；最终选择可来自 converged 或可行 budget_stop，但绝不把后者标成收敛。

### Teaching objective

> 读图应能逐边回答：哪两个局部状态允许进入 \(C_{kv}\)？为什么任何局部失败或局部预算耗尽都不能执行 M 步？受保护 Newton 要同时满足什么正域/ELBO 门？为什么可行的 \(T_{\rm out}\) 耗尽可作为“预算候选/未收敛”进入 \(\mathcal S_{\rm acc}\)，却必须保留 \(status=budget\_stop\) 而不能伪称收敛？

### 首引、图、屏障、专属读图句

SA2 在 `V5-C06.tex` 的首次引用位置使用如下顺序，根线程在 wrapper 中镜像同一语义。

1. 先写仅指向本图的首引：`图\ref{fig:V5-C06-variational-updates}把点参数 LDA 的局部 VI 成功门与语料级 VEM 提交门分开；局部预算或失败不拥有通往 M 步的边。`
2. 紧接本图的 `\input{.../fig_v5_c06_variational_updates.tex}`。
3. 紧接 `\FloatBarrier`。
4. 紧接专属读图句：`\textbf{读图检查。}先沿 (a) 逐文档确认只有 \mathtt{completed}/\mathtt{converged} 形成 LocalOK，局部预算或失败不进 C/M 步；再沿 (b) 核对全部 LocalOK 到齐后才可进入 C、\varphi 与受保护 Newton。外层 \mathtt{budget\_stop} 只有在该启动仍 feasible 时才以“预算候选/未收敛”进入 \mathcal S_{\rm acc}，其余失败终点只留记录。`
5. 方法比较图的首引/输入与本图专属读图句分开，避免读者把两张图视为同一流程节点。

## 唯一 SA2 可改文件清单

SA2 是图源/本图邻近正文的唯一写作者，且只可改下列三项：

1. `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\绘图源码\第05册_采样方法主题模型与图排序\V5-C06\fig_v5_c06_variational_updates.tex`
   - 重构为上述同 UID 上下双面板；源头设置 `\fontsize{9.6pt}{11.5pt}\selectfont`（或更大），不整体缩放；替换 title/alt/caption。
2. `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\讲义源码\第05册_采样方法主题模型与图排序\chapters\V5-C06.tex`
   - 只改本图首次引用、紧邻输入、`\FloatBarrier` 与专属读图句的最小相邻块；不改算法主体、全局宏、索引或其他图。
3. `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\evidence\figures\FIG-P694-01\R2\FIG-P694-01-SA2-R2.md`
   - 记录实现文件、确切状态图/边、字体声明、未触碰文件以及 L0 自检结果。

SA2 **不得**修改 wrapper、`figure_sources.json`、中央 numeric manifest、中央 CSV、状态文件、构建入口或公共宏。它们均由根线程单写。

## 根线程单写集成与 R3 核验点

### 根线程集成

- 将 page/standalone wrapper 元数据升至当前 v2.7.0，并使 page wrapper 的首引、`\FloatBarrier`、专属读图句与正文逐字同义；不得沿用“预算退出边继续”的旧表述。
- 更新 V5-C06 `figure_sources.json` 的 `caption`、`teaching_objective`、`accessibility.alt_texts`，保持 `figure_id`、source path、label 和 knowledge IDs 不变。
- 在 `figure_numeric_manifest_v16.json` 增加 P694 的符号复核记录：局部 `\eta/\gamma` 更新、`C_{kv}` 聚合、`\varphi` 归一、Newton 正域/ELBO 接受门、局部/外层双证书、局部禁止边，以及正文第 1047 行的 `\mathcal S_{\rm acc}`（仅 feasible 且 status 为 `converged` 或外层 `budget_stop`）。记录必须断言：预算候选返回时保留原 status/“未收敛”标签，局部预算与所有失败永不进入该集合。该图无数值曲线，不应伪造数值扫描；记录应把它标为可复核的算法语义契约。
- 仅在两名独立复审都通过后，更新中央 figure CSV、状态和接受记录。

### R3 必须逐项判定

1. **身份/引用**：仍是 `FIG-P694-01`、`FIG-V5-C06-07`、`fig:V5-C06-variational-updates`，图号保持原正式编号；FLS 只引用当前图源与当前 wrapper。
2. **局部语义**：`completed/converged` 是 `LocalOK_m` 的唯一入口；`budget_stop/invalid_input/numerical_failure` 到记录/停止，图上不存在其到 `C_{kv}`、`\varphi`、Newton、最终模型的路径。
3. **全语料门**：`m=1,…,M` 与 `∀m status_m∈{completed,converged}` 明确可见；只有该门的通过边进入 `C_{kv}^+`。
4. **M 步公式与域**：`C_{kv}^+` 求和、`C_{k\cdot}^+` 检查、`\varphi_{kv}^+=C_{kv}^+/C_{k\cdot}^+`、严格正归一和 `empty_topic/support_collapse/nonfinite_count` 出口都正确。
5. **Newton/外层**：逐个回溯候选不多于 `J_{\rm ls}`；仅 `\min_k\alpha_k^+>0` 且 ELBO 通过才接受；无合格步仅至 `line_search_failed`；外层双证书与 `T_{\rm out}` 硬预算分开。
6. **跨启动选择与返回**：`\mathcal S_{\rm acc}` 必须精确包含 `feasible=true` 且 `status∈{converged,budget_stop}` 的两类候选；`converged` 以绿色“收敛候选”显示，外层 `budget_stop` 以橙色虚线“预算候选/未收敛”显示。选择结果返回最佳最后合法参数时必须携带原 status；局部预算和所有失败均不在 `\mathcal S_{\rm acc}`，绝无通往该选择或参数返回的箭头。
7. **图文一致**：题注、alt、teaching objective、首次引用、`\FloatBarrier`、专属读图句和 page wrapper 都讲“成功门/禁止越级/预算不是收敛”，且未把本图与方法比较图混为一个流程。
8. **字体与无障碍**：源中每个 node、label、caption 的显式可见字体至少 9.5pt；无整体缩放；颜色外还使用实/虚/点划线、`✓/×/停止` 形状和状态文字。主/反馈线宽满足设计值。
9. **L0/L1 产物**：standalone 与 page wrapper 均一次干净编译；日志无 hard error、undefined control/reference、runaway、over/underfull 警告；AUX 的 page/figure/caption 身份正确，PDF 嵌入字体。
10. **视觉实看**：对 color page、300 dpi grayscale page 与 standalone 逐张查看。验收：两面板完整、不裁切；每条失败出口可追踪到终点；局部和外层反馈线不碰节点/文字；公式无重叠；灰度下成功/预算/失败仍互异；题注和专属读图句均在同页可读。

## 唯一下一步

启动唯一 SA2，严格只按本报告的三文件写入范围实施双面板；之后由根线程完成单写集成、R3 构建与两名独立复审。
