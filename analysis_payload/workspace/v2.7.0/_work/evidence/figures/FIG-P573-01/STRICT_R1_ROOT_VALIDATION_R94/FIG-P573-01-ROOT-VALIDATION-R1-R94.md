# FIG-P573-01 root validation — R94 / strict R1

- Official candidate: `strict_current_r94_fullbook/main_full.pdf`
- Physical page / printed page / figure: 620 / 607 / 31.2
- Audit evidence: `STRICT_R1/SA1_20260824_R1`
- Root decision: **FAIL → SA2**

## Root-independent checks

- Reconciled the source, `audit_metrics.json`, terminal CSV/JSON/Markdown, final consistency check, font/pixel/D/E CSVs, vector inventory, all-pairs table, edge table, and glyph evidence packs.
- Source-font hard failure is direct: twelve PGFPlots x/y tick objects inherit `8.6pt` at source line 8, below the 9.5pt floor.
- Native final-PDF evidence is on the 2481×3508 physical-page grid at 300dpi; the figure crop is an integer crop without resize.
- Coverage closes at 18 semantic text objects, 148 glyph records, 20 vector objects, 15 independent final-visible vector pair components, and 423 required relations (`C(18,2)+18×15`).
- Geometry passes in this failing round: illegal overlap 0px/0 pairs, clip 0, minimum actual raw clearance 16px. The formula-node fill is background; its final-visible border stroke is independently measured. The formula internal fraction rule is correctly merged into the formula semantic foreground and is not self-paired.
- Inspected the native figure, whole page, and representative 1:1/8× glyph evidence. The sampled independent masks contain only the target decimal point, equals sign, natural-script digit, or fullwidth punctuation—not neighbouring ink or vector inflation.
- Pixel hard failures: 24 literal glyphs/semantic substrings. D same-class failures: 2. E role-to-BASE failures: 3. Font visual harmony and overall visual harmony fail because the tick typography is below the hard floor and inconsistent with the figure hierarchy.
- Mathematical recomputation passes: sample mean `0.8567456002 → 0.8567`; integral `0.8556243919 → 0.8556`. Caption/text consistency, grayscale, reading order, and page integration pass.
- Machine terminal and final cross-file consistency pass; all 24 failed-glyph packages are present.

## Routing

Route to a dedicated SA2 only after the current P634 source writer has stopped; the project permits only one business-source writer at a time. After repair, root must build a new official candidate and create a new independent per-figure SA1 instance. The current auditor had prior task history, so its evidence is used only to establish this conservative FAIL routing and may not serve as a future PASS instance.
