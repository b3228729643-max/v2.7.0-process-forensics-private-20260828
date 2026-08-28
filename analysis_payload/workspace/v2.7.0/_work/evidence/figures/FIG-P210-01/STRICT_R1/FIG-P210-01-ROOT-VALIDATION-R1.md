# FIG-P210-01 — root validation of independent SA1 R1

Root reviewed the independent report and the native 1:1 ROIs `roi_D_3x_300dpi.png` and `roi_F_2y_300dpi.png`.

- The `3:x` label visibly crowds/intersects point `D(7,2)`; the measured illegal foreground overlap is 1 px and the text-text clearance is 0 px.
- The `2:y` label directly abuts point `F(9,6)`; its text-text clearance is 0 px, below the 4 px minimum.
- The source audit records 42 of 51 reader-visible spans at 8.7 pt, 9.2 pt, or resolved `\footnotesize=9.265` pt, all below the 9.5 pt source gate; native pixel-height and ratio failures are independently present.
- Reconstructing the stated upper-median kd-tree yields root `D`, children `C/F`, and leaves `A/B/E`. The displayed third-level `x=5` and `x=9` cuts have no corresponding depth-2 split nodes and therefore contradict the tree/body semantics.

Root decision: the independent `RESULT: FAIL` is confirmed for official R91 physical page 227. No strict acceptance is granted; next role is the figure-specific SA2.
