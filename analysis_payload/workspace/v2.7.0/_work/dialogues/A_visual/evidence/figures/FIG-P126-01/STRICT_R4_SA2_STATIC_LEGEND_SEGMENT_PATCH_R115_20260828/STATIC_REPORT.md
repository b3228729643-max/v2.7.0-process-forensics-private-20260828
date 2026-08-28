# FIG-P126-01 static legend-segment patch

- HANDOFF_ID: `A-R115-P126-SA2-STATIC-LEGEND-SEGMENT-PATCH-20260828`
- ROLE: `SA2`
- RESULT: `STATIC_ONLY_NOT_RENDERED_NOT_PASS`
- Sole source: `src/绘图源码/第01册_数学基础与统计学习基本理论/V1-C08/fig_v1_c08_coordinate.tex`
- Before: 4224 bytes, SHA-256 `366C905854F0F3952225600D5BD66AAB706B637A453FD23DDF9611E4C002AC20`
- After: 4356 bytes, SHA-256 `3185834A7D4DEAC1595C244DA626FF52B5308E733AFD851E8FF508037C51ED75`

## Exact scope

Only the current `x_2` `\addlegendimage` declaration changed. Its short periodic dash declaration was replaced by a local `legend image code/.code` that draws four explicitly disconnected `SLTeal` horizontal segments. Replacing the new block in memory with the authorized old declaration reconstructs the exact 4224-byte authorized-before SHA, proving all other bytes are unchanged relative to the R494 baseline.

The aggregate worktree diff remains exactly one file, with index empty and `git diff --check` PASS. The aggregate 32+/26- includes the previously accepted coordinate-quadratic patch; the new authorized-before-to-after legend-only delta is 7+/1-.

## Segment and gap proof

The four segments are `[0,.08]`, `[.18,.26]`, `[.36,.44]`, and `[.54,.62]` cm. Total sample width is 0.62 cm. All three designed gaps are 0.10 cm = 11.8110 px at 300 dpi. Even subtracting a full 1.05 pt line width as a conservative cap allowance leaves 0.06310 cm = 7.4524 px, exceeding the required 0.05 cm = 5.9055 px.

## Static TeX syntax assessment

`\addlegendimage{legend image code/.code={...}}` locally supplies the image code for this one legend sample. The inner `\draw` uses the existing `SLTeal` color and 1.05 pt width and contains four coordinate-pair subpaths terminated by one semicolon. Braces are balanced; no shared style, font, text, trajectory, axis, contour, coordinate, marker, caption, alt text, chapter, or build token changed.

No TeX or render was run. The new PDF must independently prove disconnected grayscale-visible segments and all figure regressions.
