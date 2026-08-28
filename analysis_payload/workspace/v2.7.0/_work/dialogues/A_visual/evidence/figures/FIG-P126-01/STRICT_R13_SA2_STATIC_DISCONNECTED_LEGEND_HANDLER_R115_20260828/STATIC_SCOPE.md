# P126 R13 static-only scope

- HANDOFF: `A-R115-P126-SA2-STATIC-DISCONNECTED-LEGEND-HANDLER-20260828`
- UID: `FIG-P126-01`
- role: `SA2`
- status: `STATIC_ONLY_NOT_RENDERED_NOT_PASS`
- source: `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\worktrees\dialogue_A_visual\src\绘图源码\第01册_数学基础与统计学习基本理论\V1-C08\fig_v1_c08_coordinate.tex`
- authorized before: 4,373 bytes / SHA-256 `81EFC188FA5E4827CAAB034C1EA3F7F4AFE25375DEE4046CD46F3FF49B0789BD`
- static after: 4,626 bytes / SHA-256 `6CBAEBE50574E541A04B2FDCC74B432C49AF2590B579C6A85721EDF536912502`
- hard defect addressed statically: `HARD-LEGEND-X2-CONTINUOUS`

Only the current x2 legend-image declaration was replaced, with one adjacent figure-local pgfplots style. The style installs a custom `/pgfplots/legend image code` that issues four separate `\draw` commands. This does not use the default line-legend path, `only marks`, or a dash pattern applied to the default path.

All contours, q0--q7 coordinates, arrows, markers, label nodes/backgrounds, axes/ranges/names, x1 legend, legend text/placement/font, quadratic/math, caption/label/alt, figure width, shared macros, other sources, and build entry remain unchanged by this incremental patch.

No TeX or build was run. This static candidate is not a rendered PASS and requests one separately authorized controlled direct LuaLaTeX slot after Main review.
