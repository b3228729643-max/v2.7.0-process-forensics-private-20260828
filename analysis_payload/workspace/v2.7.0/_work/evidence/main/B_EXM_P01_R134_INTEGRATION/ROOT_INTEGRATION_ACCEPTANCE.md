# B-EXM-P01 主线集成验收

- timestamp: `2026-08-24T21:49:49+08:00`
- handoff: `_work/handoff/B/B-EXM-P01`
- B branch: `v2.7.0/dialogue-b-content`
- B commit: `b2801d2ec38b7d1aabf65bf8374454abf480517c`
- integration branch: `v2.7.0/integration`
- integration commit: `c89c28c2b4dd152d7b073b1d334cd1490cf8e956`
- result: `PASS_INTEGRATED`

## 交接身份与写域

- B 工作树和主线工作树在合并前均为 clean。
- `CHANGED_FILES.csv` 与 `git diff 7f65bd7..b2801d2` 精确集合核对：expected=31、actual=31、missing=0、extra=0。
- `git diff --check 7f65bd7..b2801d2` 通过。
- 31 项全部为章节或局部合并页 `.tex`；图源、共享宏/样式、测试、manifest、索引、构建入口、A 域和主线状态均未进入提交。

## 合并

```text
git merge --no-ff b2801d2ec38b7d1aabf65bf8374454abf480517c -m "integrate B content batch B-EXM-P01"
Merge made by the 'ort' strategy.
31 files changed, 111 insertions(+), 109 deletions(-)
```

无冲突，合并后集成工作树 clean。

## 主线独立回归

```text
python -m unittest src.tests.test_style_term_solution_contracts src.tests.test_navigation_registry src.tests.test_nav_contracts src.tests.test_footer_navigation src.tests.test_layout_source_contracts src.tests.test_release_package_contracts
Ran 37 tests in 1.839s
OK (skipped=1)
```

发布包契约的临时实包复核同时通过：

- ZIP entries: 200
- chapters: 37
- numbered figures: 99
- unnumbered figures: 2
- figure sources present: 101
- forbidden entries: 0
- extracted DryRun: PASS

## 边界

本记录只接受 `B-EXM-P01` 进入主线，不声明 B 长期 Goal、A 视觉 Goal、最终候选或 v2.7.0 全局发布完成。B 继续后续对象批次；官方候选仍为 R98。
