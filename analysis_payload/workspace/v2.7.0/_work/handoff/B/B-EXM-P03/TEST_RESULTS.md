# TEST_RESULTS

## 精确内容域回归

```powershell
python -m unittest src.tests.test_style_term_solution_contracts src.tests.test_layout_source_contracts
```

结果：`Ran 9 tests in 0.308s`，`OK`，0 skipped/failures/errors，exit 0。

## 差异门

```text
git diff --check
exit_code=0
files=7
diff_stat=82 insertions, 48 deletions
all_hunks_inside_ten_solution_blocks=true
forbidden_scope_changes=0
```

## 构建/PDF 门

```powershell
powershell -ExecutionPolicy Bypass -File D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\B_content\tools\run_background_build.ps1 `
  -Worktree D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\worktrees\dialogue_B_content `
  -OutputDir D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\worktrees\dialogue_B_content\build\dialogue_B_content\B-EXM-P03-R1-RESUME `
  -ControlDir D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\worktrees\dialogue_B_content\build\dialogue_B_content\B-EXM-P03-R1-CONTROL `
  -Resume
```

```text
wrapper_child_exit=0
pages=814
page_size=A4
bytes=4943198
hard_errors=0
memory_errors=0
undefined_refs_or_rerun=0
overfull_underfull=0
active_tex_processes_after_terminal=0
```

## 视觉门

```text
rendered_pdf_pages=17,18,29,30,48,49,62,65,67,68,81,99,100,115,116,121,122
rendered_pages=17
visual_result=PASS
clipping=0
overlap=0
broken_continuations=0
malformed_formulas=0
```

## 独立审查

- SA1：十题独立复算、70/70 结构与写域 PASS，findings `NONE`。
- SA3 blind：`FINAL_DECISION=PASS`；十题数学、70/70 结构、17/17 视觉、PDF/log/写域全部 PASS，findings `NONE`。

源码在静态门后冻结；构建、视觉和 SA3 期间未变化，按 lean execution 不重复运行 9 项静态门。
