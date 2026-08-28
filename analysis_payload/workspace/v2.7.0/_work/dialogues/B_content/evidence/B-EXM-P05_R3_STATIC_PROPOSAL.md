# B-EXM-P05 R3 非 TeX 静态论证与最小方案

- 状态：`PROPOSAL_ONLY`。
- 本证据只读检查源码与 TeX Live 定义；未修改业务源码，未启动 LuaLaTeX/latexmk。
- 前提：R2 页338、454的150 dpi PNG分别与R1逐字节完全相同，两处异常标题—solution框间距未闭合。

## 根因链

1. 合并总册入口 `src/讲义源码/合并总册/main.tex:47` 与 `:71` 在正文/分册边界显式执行 `\flushbottom`。
2. 共享标题宏 `statlearnbook.sty:511--516` 的相关尾部为：

```tex
\par\needspace{4\baselineskip}
\noindent\textbf{例题~\ref{#1}~解答}\par\nobreak\smallskip
```

3. LaTeX 内核 `latex.ltx:9391--9394` 定义 `\smallskip` 为 `\vspace\smallskipamount`，并把 `\smallskipamount` 设为 `3pt plus 1pt minus 1pt`；11pt 类文件 `bk11.clo:92` 重申同一可伸缩量。
4. `solution` 框自身在 `statlearnbook.sty:497--502` 使用固定的 `before skip=2pt`。因此标题之后直接可见的可伸缩竖直胶来自 `\smallskip`。
5. R2 只在两个调用点把 lowercase `\needspace` 映射为 uppercase `\Needspace`；它没有改变标题宏尾部仍执行的可伸缩 `\smallskip`。R1/R2 两页字节和 bbox 坐标完全相同，实证该替换未改变最终排版。

结论：在显式 `\flushbottom` 下，剩余可伸缩 `\smallskipamount` 是当前最小且与证据一致的根因；不应再把问题归因于 lowercase `\needspace` 已被替换这一点。

## 仅局部刚性 smallskip 方案

在既有两个局部组中仅把 `\smallskipamount` 固定为其 nominal 值 `3pt`：

```tex
{\let\needspace\Needspace\setlength{\smallskipamount}{3pt}\SLExampleSolutionHeading{exm:V3-C02-kkt-state}}
```

```tex
{\let\needspace\Needspace\setlength{\smallskipamount}{3pt}\SLExampleSolutionHeading{exm:V3-C07-selection}}
```

性质：

- 只涉及 V3-C02.tex 与 V3-C07.tex 各一行。
- 组内赋值，离开标题调用后自动恢复，不修改共享宏。
- 保留 nominal `3pt` 正间距，只去掉 `plus 1pt minus 1pt`；不是负 `vspace`，也不删除标题—框的正常间距。
- 不改题目、答案、数学、标签、引用或环境边界。
- 若主线授权，先执行精确两行 diff、`git diff --check`、既有9 tests、70/70与环境栈静态门；只有另获唯一 R3 构建槽后才进行一次受控构建。

## 请求

需要 R3：R2 视觉仍为 blocking FAIL，不能进入 fresh SA1/SA3、提交或 P06。请求主线仅授权上述两行局部刚性 smallskip 源码范围，并另行决定是否授予唯一 R3 构建槽。
