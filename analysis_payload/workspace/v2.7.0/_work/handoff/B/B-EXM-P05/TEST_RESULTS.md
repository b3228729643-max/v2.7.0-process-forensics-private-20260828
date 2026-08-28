# TEST_RESULTS

## 精确内容域回归

```powershell
python -m unittest src.tests.test_style_term_solution_contracts src.tests.test_layout_source_contracts
```

最终源码结果：`Ran 9 tests in 0.528s`，`OK`，0 skipped/failures/errors，exit 0。

## 差异与结构门

```text
git diff --check: PASS
files=9
diff_stat=75 insertions, 96 deletions
objects=8.2,9.1,10.1,12.1,12.3,13.3,15.2,17.1,18.1,23.1
stage_macros=70/70 exact order
environment_stacks=BALANCED
source_book_heading_guards=2/2
local_needspace_wrappers=2/2
forbidden_scope_changes=0
```

专用命令：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\B_content\tools\check_p05_r3_static.ps1 `
  -Worktree D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\worktrees\dialogue_B_content
```

结果：`P05_R3_STATIC=PASS`。

## 最终构建/PDF 门

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\B_content\tools\run_background_build.ps1 `
  -Worktree D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\worktrees\dialogue_B_content `
  -OutputDir D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\worktrees\dialogue_B_content\build\dialogue_B_content\B-EXM-P05-R3-RESUME `
  -ControlDir D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\worktrees\dialogue_B_content\build\dialogue_B_content\B-EXM-P05-R3-CONTROL `
  -Resume
```

```text
single_parent_latexmk=16340
natural_lualatex_children=14972,18008
wrapper_exit=0
child_latexmk_exit=0
result=PASS
pages=815
page_size=A4
rotation=0
bytes=4948175
hard_errors=0
missing_or_io_errors=0
memory_exhausted=0
undefined_references=0
missing_characters=0
overfull=0
underfull=0
main_index=731 accepted / 0 rejected / 0 warnings
symbol_index=355 accepted / 0 rejected / 0 warnings
active_tex_processes_after_terminal=0
R4_started=false
```

日志保留 3 条第 5 册既有 PGF Lua `slpivtarget` 非致命回退；最终目标 up-to-date，PDF 正常完成。

## 视觉门

```text
final_pages=210,211,212,231,232,233,337,338,339,340,453,454,455
rendered_pages=13
visual_result=PASS
clipping=0
overlap=0
abnormal_spacing=0
broken_continuations=0
malformed_formulas=0
```

- 页338标题到 solution 首词间距由 R2 的 87.113 pt 降至 26.695 pt。
- 页454相应间距由 84.094 pt 降至 26.695 pt。
- 页211/232不再出现孤立“原书练习整理”，标题与首题分别共同位于页212/233。

## 独立审查

- fresh SA1：十题重新复算、七阶段和四处排版 token 语义边界 PASS，findings 0。
- fresh isolated SA3：`FINAL_DECISION=PASS`；十题独立复算、结构/标签/写域、PDF/log 与 13/13 视觉全部 PASS，findings 0。

最终源码在角色链与静态门后原子提交；R3 后没有 R4。

