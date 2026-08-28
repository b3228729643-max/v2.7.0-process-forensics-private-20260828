# TEST_RESULTS

## 精确内容域回归

```powershell
python -m unittest src.tests.test_style_term_solution_contracts src.tests.test_layout_source_contracts
```

最终R2源码结果：`Ran 9 tests in 2.132s`，`OK`，0 skipped/failures/errors，exit 0。

## 差异与结构门

```text
git diff --check: PASS
files=4
diff_stat=71 insertions, 82 deletions
objects=33.1,34.1,34.2,34.3,34.4,35.1,35.2,35.3,36.1,36.2
stage_macros=70/70 exact order
target_labels_and_headings=10/10
nested_running_example=0
environment_stacks=BALANCED
handwritten_check_answer_headings=0
KN-V5-C34-ALGORITHM_IDEA-001=1
KN-V5-C34-ALGORITHM_IDEA-002=1
selfcheck_topic=1
forbidden_scope_changes=0
```

专用命令：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\B_content\tools\check_p07_static.ps1 `
  -Worktree D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\worktrees\dialogue_B_content
```

结果：`P07_STATIC=PASS`，`TARGET_SOLUTIONS=10`，`STAGE_MACROS=70/70`，`TARGET_LABELS_AND_HEADINGS=10/10`，`ENVIRONMENT_STACKS=BALANCED`。

## 最终构建/PDF门

```text
workflow=run_background_build.ps1 -Resume
output=B-EXM-P07-R2-RESUME
control=B-EXM-P07-R2-CONTROL
started=2026-08-25T10:56:51.6629361+08:00
finished=2026-08-25T11:10:53.6939021+08:00
wrapper_exit=0
child_latexmk_exit=0
result=PASS
pages=817
page_size=A4
rotation=0
bytes=4958381
log_bytes=249757
hard_errors=0
undefined_controls=0
undefined_references_or_citations=0
duplicate_labels=0
final_rerun_requests=0
missing_characters=0
overfull=0
underfull=0
main_index=731 accepted / 0 rejected / 0 warnings
symbol_index=355 accepted / 0 rejected / 0 warnings
active_tex_processes_after_terminal=0
R3_started=false
```

stderr仅含已知Perl locale fallback、首遍缺少toc/ind的自然提示和makeindex正常输出；最终遍次全部闭合。

## 视觉门

```text
final_page_ranges=681-684,716-724,750-754,776-780
rendered_pages=23
visual_result=PASS
orphan_headings=0
clipping=0
overlap=0
abnormal_spacing=0
broken_continuations=0
malformed_formulas=0
```

- 物理页718--721逐页PASS。
- 物理页719仅一个合并自检段，紧接完整算法34.1；R1两段极端空白完全消失。
- R1视觉FAIL只保留为历史，不是最终验收对象。

## fresh角色门

- post-fix SA1：10/10、70/70、KN/自检语义、R2机械、独立新渲染23/23均PASS；`findings=[]`、`files_changed=[]`。
- isolated SA3：绝对隔离输入边界下独立终验10/10、70/70、写域/引用、KN语义、R2机械、独立新渲染23/23均PASS；`FINAL_DECISION=PASS`、`findings=[]`、`files_changed=[]`。
