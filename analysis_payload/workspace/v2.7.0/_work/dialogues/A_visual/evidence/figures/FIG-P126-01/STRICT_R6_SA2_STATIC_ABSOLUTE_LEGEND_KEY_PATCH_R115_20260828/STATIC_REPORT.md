# P126 R6 static absolute-key patch report

HANDOFF: `A-R115-P126-SA2-STATIC-ABSOLUTE-LEGEND-KEY-PATCH-20260828`.

Only the authorized x2 legend key changed:

`\addlegendimage{legend image code/.code={`

became

`\addlegendimage{/pgfplots/legend image code/.code={`.

Source identity changed from 4,356 bytes/SHA-256 `3185834A7D4DEAC1595C244DA626FF52B5308E733AFD851E8FF508037C51ED75` to 4,366 bytes/SHA-256 `20671687B41E0DD6C8D36774A7E669B0ABC55C5BBE8955BE39FA69137F52F279`. In-memory reverse substitution reconstructs the exact before byte count and SHA with mismatch0.

Git remains limited to the single P126 source; index is empty; aggregate numstat is 32+/26- and `git diff --check` passes. The R505 incremental delta is exactly one insertion and one deletion. The four segment coordinates, three designed 0.10cm gaps, SLTeal color, line width, x1 legend, legend text/font/position, axis/contours/q0--q7/trajectory dash/markers/labels/math/caption/alt/shared macros and all other tokens are unchanged.

Installed `pgfplots.code.tex` shows the default line legend draws one continuous 0--0.6cm sample and that `#2` legend-image options are parsed before a later `/pgfplots/.cd`. The absolute `/pgfplots/legend image code/.code` key therefore statically targets the intended handler; expected native300 gaps are about 11.81px each.

No TeX/build/commit/fresh role/second UID/central/process action occurred. Status remains `STATIC_ONLY_NOT_RENDERED_NOT_PASS`; a unique controlled standalone/direct LuaLaTeX build slot is requested.
