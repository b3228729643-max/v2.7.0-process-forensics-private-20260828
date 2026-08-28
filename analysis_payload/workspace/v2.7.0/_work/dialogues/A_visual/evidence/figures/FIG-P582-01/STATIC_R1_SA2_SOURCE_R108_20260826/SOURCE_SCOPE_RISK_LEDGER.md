# FIG-P582-01 static source scope and risk ledger

## Exact source change

Only explicit font size/leading declarations change:

- six `9.2pt/11pt` declarations become `9.5pt/11.4pt`;
- two `8.6pt/10.3pt` tick-label declarations become `9.5pt/11.4pt`;
- four `8.5pt/10.2pt` numeric-value declarations become `9.5pt/11.4pt`;
- two existing `9.6pt/11.5pt` axis-label declarations remain unchanged.

The resulting 14 explicit font declarations have minimum size 9.5pt. There is no `resizebox`, `scalebox`, or `transform shape` mechanism.

## Preserved source semantics and geometry

Both coordinate series, the `1/3` truth line, the four sample values, four running means, axis limits, all ticks and labels, annotation coordinates, markers, strokes, colors, formula, caption, label, and page relationship are byte-identical outside the twelve font declarations. The current body continues to describe the fixed four-value example as a non-monotone running mean.

## Build-time risks

1. The `.380`/down-arrow pair is currently collision-free but has only about 3.5858 native white pixels. Both roles grow in the new source, so this is the first mandatory native1x/8x check after a build.
2. Four numeric labels widen from 8.5pt to 9.5pt. Recheck their marker/curve clearances, especially `.640` and `.380`.
3. Tick labels widen from 8.6pt to 9.5pt. Recheck axis-border clearance and the x-axis title gap.
4. No geometry was pre-emptively changed because R108 has no true collision; any later geometry adjustment requires evidence from the newly built PDF.

No TeX invocation or commit is part of this static scope.
