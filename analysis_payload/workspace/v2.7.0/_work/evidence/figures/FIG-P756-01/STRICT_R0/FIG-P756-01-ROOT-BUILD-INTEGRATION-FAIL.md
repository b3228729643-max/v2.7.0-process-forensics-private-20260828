# FIG-P756-01｜ROOT BUILD INTEGRATION FAIL

RESULT: **FAIL**  
NEXT_ROLE: **NEW_INDEPENDENT_SA1**

## 失败事实

- 2026-08-23 使用唯一入口 `src/讲义源码/合并总册/main_full.tex` 与 TeX Live 2026 LuaLaTeX 重建当前工作树。
- 有 `-halt-on-error` 的官方构建在 `main.tex:157 \backmatter` 终止：`LaTeX Error: Float(s) lost.`，没有形成合格全书候选。
- 去掉 `-halt-on-error` 仅用于定位的诊断构建写出 813 页 PDF，但日志仍保留同一错误，因此不得发布或判整书 PASS。
- 当前 AUX 含图 37.1--37.7 的标签，不含 `fig:V5-C08-course-map`；PDF 后端同时报告未引用目的地 `figure.37.8`。缺失浮动体由此唯一定位为 FIG-P756-01。

## 源码原因

`V5-C08.tex:804` 开启 `\begin{solution}`，在该环境尚未关闭时于 `:825` 输入 `full_course_synthesis_map.tex`，直到 `:830` 才 `\end{solution}`。公共样式把 `solution` 定义为 `breakable` 的 `tcolorbox`；FIG-P756-01 图源自身使用 `\begin{figure}[htbp]`。浮动 `figure` 被置于盒环境内部，无法在真实全书输出例程中落版。

单图/page wrapper 把同一图放在普通文档流中，能够编译；它不能证明图在真实章节的 `solution` 盒内可集成。这正是旧局部验收漏掉、连续全书构建捕获的差异。

## 建议白名单修复

专属 SA2 只需调整 `src/讲义源码/第05册_采样方法主题模型与图排序/chapters/V5-C08.tex`：在 holdout 例题解答的结论后立即关闭 `solution`，再放置图 37.8、`\FloatBarrier` 与读图检查；删除图后原有的重复 `\end{solution}`。不得修改数学结论、图源、题注、标签、编号或公共样式。

该建议必须先由全新、独立 SA1 按新 Goal 对 FIG-P756-01 复核并返回 FAIL，之后才进入 SA2；修复后需要重新全书构建、300 dpi 全证据、新 SA1 与隔离 SA3。
