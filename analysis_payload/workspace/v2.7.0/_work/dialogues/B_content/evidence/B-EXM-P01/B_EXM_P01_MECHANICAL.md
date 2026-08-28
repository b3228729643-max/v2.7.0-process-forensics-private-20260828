# B-EXM-P01 机械构建与渲染

- HANDOFF_ID: `B-EXM-P01-MECH-R1`
- OWNER_DIALOGUE: `B_content`
- decision: `PASS`
- source_write: none
- subagents: none

## 回归与差异门

```text
python -m unittest src.tests.test_style_term_solution_contracts src.tests.test_navigation_registry src.tests.test_nav_contracts src.tests.test_footer_navigation src.tests.test_layout_source_contracts
Ran 32 tests
OK (skipped=1)
exit_code=0

git diff --check
exit_code=0
```

最终 `git status --short` 仅含协调者冻结的 31 个授权局部 `.tex` 修改；没有新增源码或非 build 变更。

## L1 合并总册构建

```powershell
powershell -ExecutionPolicy Bypass -File .\build_v2.7.0.ps1 -Engine lualatex -OutputDir build\dialogue_B_content\B-EXM-P01 -NoPublish
```

- exit_code: 0
- engine: LuaLaTeX
- PDF: `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\worktrees\dialogue_B_content\build\dialogue_B_content\B-EXM-P01\main_full.pdf`
- pages: 814
- bytes: 4,940,266
- LaTeX/Fatal/Emergency: 0
- undefined references: 0
- missing index: 0
- bookmark hard errors: 0
- overfull/underfull: 0
- remaining warnings: 1 LaTeX warning、11 package warnings，均非硬错误

## PDF 例题页视觉检查

- 10.2：PDF 页 170，题目与解答块完整。
- 11.1：PDF 页 186，解答块完整。
- 12.2：PDF 页 204–205，题目跨页至解答，分页正常。
- 24.1：PDF 页 471，题目与解答块完整。
- 29.1：PDF 页 578，题目与解答块完整。
- 33.2：PDF 页 689，题目与解答块完整。

7 张 PNG 位于工作树 `build/dialogue_B_content/B-EXM-P01/qa`。逐页未见裁切、重叠、黑块、不可读字形、异常分页或解答块破损。
