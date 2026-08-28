# Strict protocol thresholds used

- Direct final PDF render at 300 dpi; no resize for measurement. Full page also reviewed at 200 dpi.
- Effective reader text >=9.5 pt; legal TeX scripts derive from a compliant base formula.
- Ink floors at luminance/color difference >=20/255: CJK/fullwidth >=30 px; Latin capitals/digits >=24 px; lowercase/Greek >=17 px; math bodies >=22 px; legal scripts >=15 px.
- Same-role source size: within-panel max/min <=1.03 and absolute difference <=0.25 pt; cross-panel <=1.05. Homologous actual pixel medians cross-panel <=1.10.
- Role hierarchy: formula/core relation [1.00,1.18] of node-label BASE; ordinary note/caption [0.95,1.10]; justified emphasis remains [0.90,1.25].
- Illegal independent foreground overlap =0 px; text-text >=4 px; text/formula-line/arrow >=3 px; node text-border >=5 px; text-image edge >=6 px; adjacent-panel reader elements >=8 px; clip pixels=0.
- Visual views: full page 200 dpi, figure crop 300 dpi, standalone 300 dpi, grayscale 300 dpi, plus protan/deutan/tritan simulations.

All thresholds are applied without rounding a failing value upward. Plates/fills are background; every allowed edge-border endpoint is nevertheless individually named and source-anchored.
