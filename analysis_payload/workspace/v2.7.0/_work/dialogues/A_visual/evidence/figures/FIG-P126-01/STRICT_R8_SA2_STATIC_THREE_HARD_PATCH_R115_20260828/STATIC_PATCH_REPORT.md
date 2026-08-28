# FIG-P126-01 R8 static patch report

- HANDOFF_ID: `A-R115-P126-SA2-STATIC-THREE-HARD-PATCH-20260828`
- UID / role / candidate: `FIG-P126-01` / `SA2` / `R115`
- Status: `STATIC_ONLY_NOT_RENDERED_NOT_PASS`
- Sole source: `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\worktrees\dialogue_A_visual\src\绘图源码\第01册_数学基础与统计学习基本理论\V1-C08\fig_v1_c08_coordinate.tex`
- Authorized before: 4,366 bytes / SHA-256 `20671687B41E0DD6C8D36774A7E669B0ABC55C5BBE8955BE39FA69137F52F279`
- Static after: 4,361 bytes / SHA-256 `85FA5D73BD816149EE77968512C708C58CEE1AB90D59EDEBBDA550F232EE0D81`
- Reverse reconstruction: exact authorized-before bytes and SHA recovered from the current source by reversing only the three incremental edits.
- Incremental diff: 6 insertions / 9 deletions.
- Aggregate Git diff against branch parent: one file, 29 insertions / 26 deletions; index empty; `git diff --check` PASS.

## Narrow changes

1. `HARD-LEGEND-X2-CONTINUOUS`: replace the ineffective custom key-definition block with the actual default line-legend handler plus `dash pattern=on .06cm off .09cm,line cap=butt`. The default 0.6 cm sample therefore contains four 0.06 cm teal runs separated by three full 0.09 cm design gaps.
2. `HARD-LABEL6-AXIS-CONTOUR-OVERLAP`: keep q6 and text/font unchanged; move numeral 6 to q6's upper-left using `anchor=south east,xshift=-6pt,yshift=10pt` and add an opaque white 0.8 pt local protection margin.
3. `HARD-LABEL7-MARKER-ARROW-OCCLUSION`: keep q7 and text/font unchanged; move numeral 7 left of q7 using `anchor=east,xshift=-8pt,yshift=-2pt` and add the same opaque white 0.8 pt local protection margin.

## Frozen content

The quadratic form, all four contours, q0--q7 coordinates, update arrows, markers, axis limits and labels, x1 legend, caption, figure label, alt text, colors, font declarations, figure width, shared macros, chapter/build entry, and every other token remain unchanged from the authorized 4,366-byte input.

## Static-only boundary

No TeX or render was run. Pixel gaps below are projections, not PASS evidence. A single controlled standalone/direct LuaLaTeX build and a full new-PDF regression are required.
