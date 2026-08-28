# FIG-P067-01 source-level typography audit

The current P067 source was read directly and remained unchanged. No `scale`, `scalebox`, `resizebox`, `transform shape`, `tiny`, `scriptsize`, `footnotesize`, `small`, or other cumulative graphics scaling occurs in the local figure source; therefore the declared local point sizes below are also the effective local point sizes.

| Source role | Declaration | Effective pt | Same-role consistency | R168 disposition |
|---|---|---:|---|---|
| CDF tick labels | `\fontsize{8.8pt}{10.5pt}` | 8.8 | Uniform within CDF panel | Advisory below the legacy 9.5 pt reference; actually readable |
| PMF tick labels and manual `0.3` | `\fontsize{8.6pt}{10.3pt}` | 8.6 | Uniform within PMF panel | Advisory below the legacy 9.5 pt reference; actually readable |
| Both axis labels | `\fontsize{9.4pt}{11.2pt}` | 9.4 | Ratio 1.000 across panels | Advisory by 0.1 pt only; actually readable |
| `p_1`-`p_4` mass labels | `\fontsize{9.2pt}{11.0pt}` | 9.2 | Uniform source declaration | Advisory below the legacy 9.5 pt reference; actually readable |
| Both explanatory notes | `\fontsize{9.2pt}{11.2pt}` | 9.2 | Ratio 1.000 across panels | Advisory below the legacy 9.5 pt reference; actually readable |
| Caption | inherited caption style; PDF span | 9.963 PDF pt | Uniform caption line | Readable and naturally subordinate to plot |

Cross-panel tick-label effective-size ratio is `8.8 / 8.6 = 1.0233`, within the 1.05 cross-panel reference. Axis labels, explanatory notes, and their role pairs are source-identical. The PDF glyph medians are consistent by role: ordinary tick digits are approximately 24-26 px, note CJK glyphs approximately 34-35 px, base math labels approximately 25-29 px, and caption CJK glyphs approximately 37-39 px. The nine strict-reference height/taxonomy exceptions are G018, G020, G022, G039, G044, G046, G052, G053, and G057; each was opened in its contact sheet and is fully legible. Under R168 these micro font/pixel/taxonomy differences are advisory rather than a hard failure.

`FONT_VISUAL_HARMONY_PASS=true`: neither panel is visually dominant, axis/tick hierarchy is coherent, the two annotations are balanced, and no text appears actually unreadable, cramped, oversized, or conspicuously inconsistent.

