# FIG-P756-01 SA2 STRICT R2

RESULT: FIXED

TASK_ID: FIG-P756-01

ASSIGNED_SCOPE: 仅修复 `V5-C08.tex` 中 P756 图块被包在 `solution` 环境内的集成错误；不修改图源、数学内容、题注、标签、编号、公共样式或构建入口。

ROOT_CAUSE: holdout 例题的 `solution` 在图块之后才结束，使自带 `figure[htbp]` 的 `full_course_synthesis_map.tex` 输入发生在 `solution` 内，导致真实全书构建出现浮动体丢失风险。

PATCH_SUMMARY: 将原来位于图后读图检查之后的同一个 `\end{solution}`，移动到 holdout 解答结论之后。图前两句、`\input`、`\FloatBarrier` 和读图检查段落本身均未改写。

精确源码改动：

```diff
 最小测试误差受到向下选择偏差。\textbf{结论。}应在开发集内部用验证折选秩，锁定秩并重拟合后，才在未查看的测试集上计算一次结果；否则测试估计不再满足命题的条件无偏前提。
+\end{solution}
 
 图\ref{fig:V5-C08-course-map}把全书方法放回“问题定义--建模--计算--证据--边界”主闭环；
 ...
 最终确认只有隔离验证后的结论能单向进入可复现报告，报告没有回流。
-\end{solution}
```

FILES_CHANGED:

- `v2.7.0/_work/source/v2.7.0/src/讲义源码/第05册_采样方法主题模型与图排序/chapters/V5-C08.tex`
- `v2.7.0/_work/evidence/figures/FIG-P756-01/STRICT_R2/FIG-P756-01-SA2-STRICT-R2.md`

WHITELIST_COMPLIANCE: PASS。除上述源码与本报告外未写入任何文件；未修改 `full_course_synthesis_map.tex`、`main_full.tex`、公共 `.sty`、wrapper、CSV/JSON、状态或索引。

VALIDATION:

- 全文件 `\begin{solution}` = 4，`\end{solution}` = 4；顺序扫描最终深度 = 0，最小深度 = 0。
- P756 `full_course_synthesis_map.tex` 输入唯一，现位于第 826 行，扫描时 `solution` 深度 = 0。
- holdout 解答结论后现为第 822 行 `\end{solution}`；图前说明、P756 `\input`、`\FloatBarrier`、读图检查均位于该结束标记之后的普通垂直流。
- 目标源码在本轮开始前为 Git 未跟踪文件（`git status --short` 为 `??`），因此没有可用的 tracked `git diff` 基线；上方精确补丁片段记录且仅记录单行结束标记的移动。
- 按根线程指令未运行全书构建。

DECISIONS: 采用唯一最小作用域修复，不扩展到图源或任何版式/数学调整。

UNRESOLVED:

- 由根线程统一执行真实全书重建，确认不再出现该处 `Float(s) lost`。
- 由根线程确认 AUX 恢复 `fig:V5-C08-course-map`，且最终 PDF 实际落图。
- 由后续严格证据流程生成并复核 300 dpi 图像及第 9.2.1 节要求的字号、像素、比例、零重叠、裁切、净空与视觉协调性证据。

NEXT_ACTION: 根线程合并本次源码移动后执行统一全书构建与 FIG-P756-01 严格 300 dpi 证据/独立复审。
