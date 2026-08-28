# TEST_RESULTS

## 精确内容域回归

```powershell
python -m unittest src.tests.test_style_term_solution_contracts src.tests.test_layout_source_contracts
```

最终源码结果：`Ran 9 tests in 0.394s`，`OK`，0 skipped/failures/errors，exit 0。

## 差异与结构门

```text
git diff --check: PASS
files=7
diff_stat=61 insertions, 55 deletions
objects=25.1,26.2,27.1,28.1,30.1,30.2,31.1,31.2,32.1,32.2
stage_macros=70/70 exact order
target_labels_and_headings=10/10
nested_running_example=0
environment_stacks=BALANCED
handwritten_check_answer_headings=0
forbidden_scope_changes=0
```

专用命令：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\B_content\tools\check_p06_static.ps1 `
  -Worktree D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\worktrees\dialogue_B_content
```

结果：`P06_STATIC=PASS`，`TARGET_SOLUTIONS=10`，`STAGE_MACROS=70/70`，`ENVIRONMENT_STACKS=BALANCED`。

## 最终构建/PDF 门

```text
workflow=run_background_build.ps1 -Resume
output=B-EXM-P06-R2-RESUME
control=B-EXM-P06-R2-CONTROL
started=2026-08-25T06:46:02.6061299+08:00
finished=2026-08-25T07:00:30.1009761+08:00
wrapper_exit=0
child_latexmk_exit=0
result=PASS
pages=816
page_size=A4
rotation=0
bytes=4953900
log_bytes=249751
hard_errors=0
undefined_controls=0
undefined_references_or_citations=0
duplicate_labels=0
final_rerun_requests=0
overfull=0
underfull=0
main_index=731 accepted / 0 rejected / 0 warnings
symbol_index=355 accepted / 0 rejected / 0 warnings
active_tex_processes_after_terminal=0
R3_started=false
```

日志中 3 次 `slpivtarget is undefined` 是既有 pgfplots Lua 表达式探测后成功回退至 TeX 后端的提示，不是未定义控制序列/引用；最终 PDF 正常完成。

## 视觉门

```text
final_page_ranges=491-494,511-514,533-536,556-559,603-606,608-611,632-634,639-641,661-664,666-669
rendered_pages=38
visual_result=PASS
orphan_headings=0
clipping=0
overlap=0
abnormal_spacing=0
broken_continuations=0
malformed_formulas=0
```

- p557 中“28.6 例题、矩阵分解计算与练习”与例题 28.1 开头同页，R1 孤立标题已闭合。
- 其余九个目标及相邻页无分页、裁切、重叠、断框或异常伸展回归。

## 独立审查

- fresh post-fix SA1：十题重新复算、七阶段、七文件写域与唯一 R2 token 移动 PASS，findings 0。
- fresh isolated SA3：`FINAL_DECISION=PASS`；十题独立复算、结构/标签/写域、R2 CONTROL/PDF/log 与关键/代表页全部 PASS，findings 0。

最终源码在角色链与静态门后原子提交；R2 后没有 R3。

