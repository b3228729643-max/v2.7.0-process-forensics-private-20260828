# FIG-P262-01-SA1-STRICT-R1

RESULT: **FAIL**

The frozen official R92 full-book candidate contains 图16.1 on physical PDF page **284** (printed page 271). This is an independent SA1 read-only review. It used only the frozen candidate PDF, the direct figure source, and direct adjacent chapter lines; no prior SA1/SA2/SA3/root report or central inventory was read.

The result is a hard fail before any discretionary visual judgment: source line 19 sets tick labels to 8.7pt and source lines 5/9/12/54--57 set the ordinary figure labels/formulae to 9.2pt. The required effective minimum is 9.5pt. The raw 300 dpi measurement further finds mathematical operators/prime below the 22px operator threshold. In addition, final-page semantic masks quantify 241 illegal text–graphic foreground pixels: y-label $\sigma(z)$ / y=1 reference, y=1 tick / reference, and “中心斜率” / z=a guide. Complete unique ELEMENT_ID records, source lines, native bboxes, thresholds, and repair direction are in `strict_failure_register.csv` plus the three required audit CSVs.

Direct semantic validation is otherwise favorable: the curve is the intended sigmoid; $\sigma(-z)=1-\sigma(z)$, the $(0,1/2)$ symmetry, guides, points, and tangent slope $1/4$ agree with source, caption, and immediate body text. Clipping is zero, but it cannot cure the source-font, pixel-height, or three text–graphic-overlap failures.

Required minimum source repair: increase all reader-visible figure text—including PGFPlots ticks and every direct/note/formula annotation—to a true effective >=9.5pt, re-layout locally to preserve clearances, rebuild the official full-book candidate, and regenerate all evidence. Do **not** launch SA3 from this failing SA1.
