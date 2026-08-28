# FIG-P602-01｜ROOT-APPLY-R3

RESULT: PASS_LOCAL

FINAL_ACCEPTANCE: PENDING_FRESH_SA1_AND_BLIND_SA3

SPLIT_REQUIRED: NO

## scope

- 对象：FIG-P602-01，图 32.5，Metropolis--Hastings 一步接受/拒绝流程。
- 依据：主提示词附录 A 与 B52、SA1-R1 问题清单、SA2-R1 修复报告、当前章节权威公式与本轮 R3 原始证据。
- 执行策略：遵循 `codex-lean-execution`，仅做本图源码、相邻正文、两个包装器、V5-C03 图源清单和中央图清单的定向同步；未重扫 99 图、未重跑整书、未计算非关键哈希。

## source_and_context_changes

1. `fig_v5_c03_mh_accept_reject.tex`
   - 单向主链为 `X_t=x -> Y=y -> 计算 alpha -> U 判定 -> 接受/拒绝`。
   - 核心比值使用 `\widetilde\pi`，并显式限定 `g(x,y)>0`；`g=0` 分支保留在正文。
   - 拒绝节点写明 `X_{t+1}=x`，点划自环写明保留旧状态。
   - 普通可见字号 9.6pt，关键接受率 11.8pt；无 `resizebox`、`scalebox`、`adjustbox` 或整体缩放。
   - 题注压缩为：`Metropolis--Hastings 一步更新：提议、接受与拒绝自环。`
2. `V5-C03.tex`
   - 第一次专属引用、图输入、浮动屏障和专属读图句依次位于 292、293、294、295 行。
   - `\FloatBarrier` 防止读图句越过浮动体出现在图前；R3 PDF 文本顺序已验证。
3. 两个 `v260_FIG-P602-01_*` 包装器
   - 内容身份同步到 v2.7.0；页包装器同步为印刷页 636。
   - 页包装器使用 `\widetilde\pi`、`g(x,y)>0`、统一随机量 `U` 和与章节相同的图后读图句。
4. `V5-C03/figure_sources.json`
   - 同步新题注、单向流程教学目标和对象—关系—结论 alt 描述；JSON 可解析且目标记录唯一。
5. `figures/figure_manifest.csv`
   - P602 行同步页码 636、教学问题、处理动作、字号、冗余编码、灰度证据、变量一致性和新题注。
   - 当前保持 `待独立复核`，未在 SA1/SA3 前冒充最终通过。
6. `figure_numeric_manifest_v16.json`
   - 定向搜索无 P602 记录；本图为符号流程图，无冻结数值数据，故无需新增或修改 numeric manifest。

## mathematical_and_semantic_checks

- 图内公式逐项等于正文 `eq:V5-C03-mh-alpha` 的正向流分支：
  `alpha(x,y)=min{1, widetilde-pi(y)q(y,x)/[widetilde-pi(x)q(x,y)]}`，条件为 `g(x,y)>0`。
- `g(x,y)>0` 保证分母为正；没有把 `g=0` 的零流边界误写成无条件比值。
- `U~U(0,1)` 且 `U<=alpha(x,y)` 时提交候选；否则记录 `X_{t+1}=x`，与完整核的拒绝质量和自环语义一致。
- 图不宣称自身证明细致平衡、逐对最大性、可逆性或平稳性。
- 单轮更新结构在当前字号和 A4 版心中清楚容纳，拆图会割裂拒绝即自环的语义，因此 `SPLIT_REQUIRED=NO`。

## R3_build

- 工具链：TeX Live 2026 LuaLaTeX，经 `D:\texlive\2026\bin\windows\latexmk.exe` 调用。
- 缓存：`TEXMFCACHE=TEXMFVAR=C:\Users\ASUS\AppData\Local\Temp\statlearn-v2.7.0-texmf-cache`。
- 独立图：`p602_root_r3_standalone.pdf`，1 页 A4，36,565 bytes。
- 整页：`p602_root_r3_page.pdf`，1 页 A4，57,467 bytes，页码 636。
- 两个最终日志的定向硬诊断均为 0：LaTeX/Package error、fatal/emergency、undefined control/reference/citation、multiply defined、missing character、字体替代、overfull/underfull box。
- PDF metadata 均为 v2.7.0；未使用 MiKTeX 或 XeLaTeX。

## visual_review

已实际打开并复核以下四份最终人读证据：

- `p602_root_r3_standalone_300dpi.png`，165,334 bytes。
- `p602_root_r3_full_page_200dpi.png`，261,997 bytes。
- `p602_root_r3_gray_page_300dpi.png`，409,414 bytes。
- `p602_root_r3_figure_caption_guide_crop_300dpi.png`，284,214 bytes。

结论：

- 所有节点、公式、条件、箭头头部、分支标签、自环标签、题注和读图句清楚；无穿字、交叉、裁切、越界、溢出或异常断行。
- 阅读方向自上而下，末端才分为接受和拒绝；箭头均止于节点边界。
- 灰度下仍可凭虚线提议、实线接受、点划拒绝/自环、菱形判定和拒绝双框区分关系，不依赖颜色。
- 浮动屏障修复后，PDF 文本索引满足首次引用上下文 < 题注 < 图后读图句；读图句不再跨图拆分。
- 整页留白均衡，图题单行，图后读图句完整位于同页。

## machine_checks

- `figure_sources.json`：目标记录 `FIG-V5-C03-05` 恰好 1 条。
- `figure_manifest.csv`：99 行、19 列，`FIG-P602-01` 恰好 1 条。
- numeric manifest：P602 定向匹配 0，符合 `numeric_recomputation.required=false`。
- 最终源码显式字体仅为 9.6pt 和 11.8pt；禁止整体缩放命令匹配 0。
- 误置的字面量 `$r3` 临时目录已在解析绝对路径后删除；最终证据仅位于本 R3 目录。

## lean_deferment

- 当前 `build/final/main_full.pdf` 与 `main_full.aux` 是本次修订前的 805 页基线；未手工改 aux，也未为单图同步重跑整书。
- 当前局部源码、包装器与 R3 证据是本轮真值；合并后的全书页流与 aux 更新留到后续 L1 汇总构建，避免每幅图重复整书构建。

## decision

根线程局部同步、数学语义、构建、整页、局部、灰度、身份与清单门均通过。FIG-P602-01 现在可以交给全新、独立的 SA1 复核；只有 SA1 通过后才进入盲审 SA3，二者通过后再写最终根线程验收并把中央清单改为 `通过`。
