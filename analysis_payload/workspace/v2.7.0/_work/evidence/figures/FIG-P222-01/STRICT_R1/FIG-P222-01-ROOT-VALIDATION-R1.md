# FIG-P222-01 — root validation of independent SA1 R1

Root reviewed the formal report and the native 1:1 `X_{d-1}` node ROI plus its text/border mask overlay.

- Twenty-three reader-visible figure elements inherit a 9.20 pt source baseline, below the 9.50 pt hard floor.
- The semantic continuation `\cdots` has only 6 px native ink height, below the 22 px base-symbol floor.
- Annotation and formula-baseline role ratios are 1.1786 and 0.9643, outside their required bands.
- `X_{d-1}` is visibly cramped inside its circle; the nearest text-to-own-border distance is 4.472136 px, below the 5 px minimum, with 0 overlap.
- The diagram uses subscripted feature indices while the adjacent formal definition uses superscripts for feature coordinates, creating a figure-text notation mismatch.

Root decision: the independent `RESULT: FAIL` is confirmed for official R91 physical page 240. The figure must not enter SA3; next role is the figure-specific SA2.
