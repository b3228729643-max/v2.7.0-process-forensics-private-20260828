# B-EXM-P05 R2 源码窄修复与静态证据

- 时间：2026-08-25T04:06:04+08:00。
- 基线：P05 R1 九文件未提交差异与冻结构建/SA3 证据。
- 主线路由：`B_P05_R2_SOURCE_SCOPE_GRANTED / TEX_NOT_YET_GRANTED`。
- 结论：`STATIC_READY`；R2 TeX 未获授权且未启动。

## 四处精确修改

1. `V2-C01.tex:617--618`：仅把现有 `\Needspace{6\baselineskip}` 从 `\SLSourceBookExercises` 后移到其前。
2. `V2-C02.tex:620--621`：执行同一顺序移动。
3. `V3-C02.tex:717`：仅将目标标题改为 `{\let\needspace\Needspace\SLExampleSolutionHeading{exm:V3-C02-kkt-state}}`。
4. `V3-C07.tex:314`：仅将目标标题改为 `{\let\needspace\Needspace\SLExampleSolutionHeading{exm:V3-C07-selection}}`。

R2 增量为四个文件中的 `4 insertions(+), 4 deletions(-)`；P05 总差异由 R1 的 `71 insertions(+), 92 deletions(-)` 变为 `75 insertions(+), 96 deletions(-)`。未改负 `vspace`、共享宏、文字、数学、标签、引用或其他业务源码。

精确相关 diff：

```diff
+\Needspace{6\baselineskip}
 \SLSourceBookExercises
-\Needspace{6\baselineskip}

-\SLExampleSolutionHeading{exm:V3-C02-kkt-state}
+{\let\needspace\Needspace\SLExampleSolutionHeading{exm:V3-C02-kkt-state}}

-\SLExampleSolutionHeading{exm:V3-C07-selection}
+{\let\needspace\Needspace\SLExampleSolutionHeading{exm:V3-C07-selection}}
```

第一组三行分别在 V2-C01 与 V2-C02 各出现一次。

## 静态门

```powershell
git diff --check
```

结果：PASS，无输出。

```powershell
python -m unittest src.tests.test_style_term_solution_contracts src.tests.test_layout_source_contracts
```

结果：`Ran 9 tests`，`OK`，0 failures，0 errors。

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\B_content\tools\check_p05_r2_static.ps1 -Worktree D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\worktrees\dialogue_B_content
```

结果：

```text
P05_R2_STATIC=PASS
TARGET_SOLUTIONS=10
STAGE_MACROS=70/70
TARGET_NESTED_RUNNING_EXAMPLE=0
ENVIRONMENT_STACKS=BALANCED
SOURCE_BOOK_HEADING_GUARDS=2/2
LOCAL_NEEDSPACE_WRAPPERS=2/2
```

## 构建边界

- 本轮未启动 LuaLaTeX、latexmk、luatex 或 luahbtex；检查时相关进程为 NONE。
- R2 构建槽仍待主线显式授予；不得从进程 NONE 推断转授。
- 获授权后的覆盖范围必须包括页211/232及各自相邻页、338--339、454和分页顺延；随后必须执行 fresh post-fix SA1 与全新隔离 SA3。
