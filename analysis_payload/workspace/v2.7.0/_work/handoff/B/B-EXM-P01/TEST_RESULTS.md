# TEST_RESULTS

## 精确内容域回归

```text
python -m unittest src.tests.test_style_term_solution_contracts src.tests.test_navigation_registry src.tests.test_nav_contracts src.tests.test_footer_navigation src.tests.test_layout_source_contracts
Ran 32 tests
OK (skipped=1)
exit_code=0
```

跳过项仅为仓库未提供历史 v1.8 footer smoke PDF，不影响本批。

## 差异门

```text
git diff --check
exit_code=0
```

## 构建门

```text
powershell -ExecutionPolicy Bypass -File .\build_v2.7.0.ps1 -Engine lualatex -OutputDir build\dialogue_B_content\B-EXM-P01 -NoPublish
exit_code=0
pages=814
bytes=4940266
hard_errors=0
undefined_references=0
index_missing=0
bookmark_hard_errors=0
overfull_underfull=0
```

## 独立审查

- SA1 R1：PASS，0 findings。
- SA1 R2：PASS，0 findings。
- 机械构建/渲染：PASS。
- SA3 blind：PASS，0 findings。
