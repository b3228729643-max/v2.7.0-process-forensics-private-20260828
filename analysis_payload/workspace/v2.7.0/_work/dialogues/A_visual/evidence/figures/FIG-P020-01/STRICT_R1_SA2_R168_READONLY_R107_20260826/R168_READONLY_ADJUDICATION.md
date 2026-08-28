# FIG-P020-01 R107 R168 SA2 read-only adjudication

## Outcome

`SA2_NO_SOURCE_CHANGE_READY_FOR_FRESH_SA1`

The current R107 figure has no R168 hard defect. The previous single-horizontal-stroke CJK height issue is preserved as an advisory observation only. No source change and no TeX invocation are justified.

## Frozen identity and independent location

- Handoff: `A-R107-P020-SA2-R168-READONLY-20260826`.
- Official PDF: 817 pages, 4,967,249 bytes, SHA-256 `8811950621E2D64A3C2A8F0F7A52DD0FAC2BDB12018F3EA052C1F58C94EF8DF3`.
- Current P020 source SHA-256: `FF006894E35D1D3E79F1C1D85D212B79735F3D11937B17F23A49D68DC97547CE`; main and A worktree copies agree.
- The current caption was independently located on physical PDF page 17, printed page 4, as the unique figure `图 1.1`. The old inventory route page 20 is not the current physical page.
- Page size is 595.276 × 841.890 pt. The direct 300-dpi figure-plus-caption crop uses `[54,260,541,386]` pt; the standalone body uses `[54,260,541,357]` pt.

## Lean source and semantic checks

The source contains four stage nodes, three forward dependency arrows and one dashed reverse-audit route. The visible node order and wording are exact: 对象声明 → 关系与映射 → 运算与逻辑 → 可核验任务. The return annotation states that task definitions are checked in reverse. The caption explains the same dependency semantics.

Stage titles use 10.5 pt and supporting text/annotation use 10.0 pt. There is no `resizebox`, `scalebox` or `transform shape`. All node borders, arrow shafts and arrowheads are visibly intact; arrows connect the intended stages; text stays inside its intended node or annotation region.

## R168 terminal visual review

The reviewer actually opened the 200-dpi full page; native 300-dpi color figure-plus-caption, standalone and grayscale views; and the native/8× nearest-neighbour target ROI for the caption glyph `一`.

No missing glyph, tofu, wrong codepoint, mathematical/diagram semantic error, unreadability, obvious severe font imbalance, real clipping, illegal overlap or geometry error was observed. The figure remains readable in color and grayscale and integrates naturally with the page.

The caption character `一` is the correct U+4E00 from the extracted text `每一条`. Its exact native 300-dpi crop is 42×45 px; at the recorded threshold its clean ink bbox is 38×5 px with 87 foreground pixels. The stroke is continuous and visibly complete, including its native terminal shape, with no neighboring ink, crop or pollution. Under R168, this expected low-profile contour and its old absolute-height ratio are advisory and cannot alone trigger a source rewrite or rebuild.

## Disposition

- R168 hard failures: 0.
- Source files changed: 0.
- TeX/LuaLaTeX/latexmk invocations: 0.
- Requested next action: main dispatches a completely fresh isolated SA1 against the current official candidate; A does not start it itself.
