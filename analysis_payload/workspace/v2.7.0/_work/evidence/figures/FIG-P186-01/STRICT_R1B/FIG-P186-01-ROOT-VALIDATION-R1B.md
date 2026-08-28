# FIG-P186-01 — root validation of independent SA1 R1B

Root reviewed the independent report and the native 1:1 ROIs `roi/boundary_label_native_1x.png` and `roi/misclassified_triangle_native_1x.png`.

- The separator passes within approximately 1 px of `w^T x+b=0`, below the 3 px text-to-line minimum.
- The teal triangle identified at `(2.10,-1.05)` is visibly on the positive side of the separator. The source-level recomputation `0.68(2.10)-1.05-0.2=0.178>0` confirms the semantic contradiction.
- Four direct labels are declared at 9.2 pt, below the 9.5 pt source gate.

Root decision: the independent `RESULT: FAIL` is confirmed for official R91 page 200. No source or central acceptance state is changed here; next role is the figure-specific SA2.
