# TEST_RESULTS

## 精确内容域回归

```text
python -m unittest src.tests.test_style_term_solution_contracts src.tests.test_layout_source_contracts
Ran 9 tests
OK
exit_code=0
```

该门在源码冻结后完成；机械构建、视觉检查和 SA3 期间没有章节源码变化，按 lean execution 不重复运行。

## 差异门

```text
git diff --check
exit_code=0
staged_files=5
unstaged_files=0
diff_stat=60 insertions, 60 deletions
```

## 构建/PDF 门

```text
powershell -ExecutionPolicy Bypass -File .\build_v2.7.0.ps1 -Engine lualatex -OutputDir D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\worktrees\dialogue_B_content\build\dialogue_B_content\B-EXM-P02-R7-RESUME -NoPublish -Resume
pdf_log_result=PASS
pages=814
page_size=A4
bytes=4941530
hard_errors=0
memory_errors=0
overfull_underfull=0
active_build_processes_after_terminal=0
outer_wrapper_exit=1
outer_wrapper_diagnostic=Perl locale warning promoted to NativeCommandError; false negative, not a TeX/PDF failure
```

完整诊断见 `B-EXM-P02_MECHANICAL_EVIDENCE.md`；没有把外层 exit 伪写为 0。

## 视觉门

```text
rendered_pdf_pages=133,361,362,502,503,692,693,694,799,800
visual_result=PASS
clipping=0
overlap=0
broken_continuations=0
malformed_formulas=0
```

## 独立审查

- SA1 R1：3 个定向 findings，均已局部修复。
- SA1 R2：PASS，0 open findings。
- SA3 blind：`FINAL_DECISION=PASS`，findings `NONE`。
