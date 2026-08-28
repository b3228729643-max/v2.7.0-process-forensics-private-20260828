# Path, math-rule and accent coverage audit

- `drawing_path_coverage.csv` enumerates 38 drawing/path rows: 36 visible foreground paths are each `MAPPED_FOREGROUND`, while exactly two non-foreground fills (`B001` plot-region fill and `B002` opaque node interior) are explicitly `EXCLUDED_BACKGROUND_FILL`. The machine cross-check reports `unassigned_foreground_path_count=0`.
- The only TeX mathematical horizontal rules visible outside texttrace are independently retained as foreground objects:
  - `R001`, drawing 82, `GRAPHIC/MATH_RULE`, parent `T019` (the `k/n` fraction rule).
  - `R002`, drawing 83, `GRAPHIC/MATH_RULE`, parent `T020` (the `n/\widehat\tau_{K,n}` fraction rule).
  Their native 1x original/overlay/mask and 8x nearest cards were manually opened. Neither was merged into text, an axis, or any other path.
- Rawdict-to-rendered mathematics is bidirectionally accounted for:
  - `A001`: `GL035 -> GL036`, rotated `\widehat\rho_k` axis label.
  - `A002`: `GL080 -> GL081`, `\widehat\rho_k` in formula `T019`.
  - `A003`: `GL090 -> GL091`, `\widehat\tau_{K,n}` denominator in `T020`.
  - `A004`: `GL096 -> GL097`, positivity condition `\widehat\tau_{K,n}>0`.
  - `A005`: rendered visible circumflex `GL083 -> GL084` in `\widehat N_{\mathrm{eff}}`.

The four rawdict U+0302 controls have no independent visible mask by design; their combined native masks were manually reviewed on the named association cards. A005's roof is a separate pure visible component of its named base and excludes the adjacent `e` subscript. This coverage result does not waive the nine independent glyph hard failures recorded in `glyph_ledger.csv`.
