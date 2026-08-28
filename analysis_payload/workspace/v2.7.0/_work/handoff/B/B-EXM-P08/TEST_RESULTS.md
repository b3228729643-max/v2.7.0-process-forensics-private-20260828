# TEST_RESULTS

## 精确内容域回归

```powershell
python -B -m unittest src.tests.test_style_term_solution_contracts src.tests.test_layout_source_contracts
```

主线precommit独立结果：`Ran 9 tests`，`OK`，0 failures/errors，exit 0。

## 差异与结构门

```text
git diff --check: PASS
files=2
diff_stat=78 insertions, 75 deletions
objects=36.3,36.4,37.1,37.3,37.4
stage_macros=35/35 exact order
target_labels_and_headings=5/5
nested_running_example=0
environment_stacks=BALANCED
handwritten_check_answer_headings=0
uncertified_36_4_approximation=0
holdout_conditional_boundary=PASS
holdout_equality_boundaries=PASS
forbidden_scope_changes=0
```

专用命令：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\B_content\tools\check_p08_static.ps1 `
  -Worktree D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\worktrees\dialogue_B_content
```

结果：`P08_STATIC=PASS`，`TARGET_SOLUTIONS=5`，`STAGE_MACROS=35/35`，`TARGET_LABELS_AND_HEADINGS=5/5`，`ENVIRONMENT_STACKS=BALANCED`。

## 最终构建/PDF门

```text
workflow=run_background_build.ps1 -Resume
output=B-EXM-P08-R1-RESUME
control=B-EXM-P08-R1-CONTROL
started=2026-08-25T12:48:00.5146338+08:00
finished=2026-08-25T12:58:07.7048225+08:00
wrapper_exit=0
child_latexmk_exit=0
result=PASS
pages=817
page_size=A4
rotation=0
pdf_version=1.7
encrypted=false
bytes=4962906
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
second_invocation=false
```

非硬错误信息仅为已知Perl locale fallback、六条范围外PDF-string token-removal warning、两条非阻断imakeidx提醒及Windows Unicode路径下Poppler的file-size显示异常；实际PDF字节由文件系统与两遍LuaLaTeX输出共同确认。

## 视觉门

```text
final_page_ranges=778-781,793-796,802-805
rendered_pages=12
visual_result=PASS
orphan_headings=0
clipping=0
overlap=0
abnormal_spacing=0
broken_frames=0
missing_glyphs=0
```

fresh post-build SA1与fresh isolated SA3均各自独立新渲染并打开上述12页，均为12/12 PASS。

## fresh角色门

- post-build SA1：5/5数学、35/35、两文件写域、R1机械、独立新渲染12/12均PASS；`findings=[]`、`files_changed=[]`。
- isolated SA3：隔离SA1/root/主线旧结论后独立终验5/5、35/35、写域/引用/环境、R1机械、独立300dpi重绘12/12均PASS；`FINAL_DECISION=PASS`、`findings=[]`、`files_changed=[]`。
