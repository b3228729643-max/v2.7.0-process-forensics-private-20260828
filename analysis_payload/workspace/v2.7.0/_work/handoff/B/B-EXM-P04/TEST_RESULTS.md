# TEST_RESULTS

## 精确内容域回归

```powershell
python -m unittest src.tests.test_style_term_solution_contracts src.tests.test_layout_source_contracts
```

最终源码变更后结果：`Ran 9 tests in 0.536s`，`OK`，0 skipped/failures/errors，exit 0。

## 差异门

```text
git diff --check
exit_code=0
files=7
diff_stat=85 insertions, 77 deletions
objects=13.1,13.2,14.1,15.1,16.1,20.1,20.2,21.1,21.2,22.1
stage_macros=70/70 exact order
forbidden_scope_changes=0
```

## 最终构建/PDF 门

```powershell
powershell -ExecutionPolicy Bypass -File D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\B_content\tools\run_background_build.ps1 `
  -Worktree D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\worktrees\dialogue_B_content `
  -OutputDir D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\worktrees\dialogue_B_content\build\dialogue_B_content\B-EXM-P04-R3-RESUME `
  -ControlDir D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\worktrees\dialogue_B_content\build\dialogue_B_content\B-EXM-P04-R3-CONTROL `
  -Resume
```

```text
wrapper_exit=0
child_latexmk_exit=0
result=PASS
pages=814
page_size=A4
rotation=0
bytes=4947493
hard_errors=0
missing_or_io_errors=0
memory_exhausted=0
undefined_references=0
overfull=0
underfull=0
active_tex_processes_after_terminal=0
output_files=19
output_files_outside_authorized_dirs=0
R4_started=false
```

日志另有 3 条第 5 册既有 PGF Lua `slpivtarget` 非致命回退提示；最终目标为 up-to-date，PDF 正常完成。

## 视觉门

```text
final_pages=223,227,228,247,248,262,263,291,292,382,389,390,406,407,416,417,437,438
rendered_pages=18
visual_result=PASS
clipping=0
overlap=0
abnormal_justification=0
broken_continuations=0
malformed_formulas=0
```

- R1 识别页 437 长行 overfull；R2 识别 `\linebreak` 字距拉伸；R3 以 `\newline` 收敛。
- R3 页 437--438 由根级、SA1 与主线分别独立视觉确认 PASS。

## 独立审查

- SA1：十题数学、术语、70/70 结构与 18 页完整视觉终审 PASS，findings `NONE`。
- SA3 blind：`FINAL_DECISION=PASS`；十题独立复算、写域/引用、PDF/log 与 18/18 视觉全部 PASS，findings `NONE`。

最终 one-token 源码在 9 项静态门后冻结；R3 构建/视觉和 SA3 期间未变化，按 lean execution 不重复运行已通过门。
