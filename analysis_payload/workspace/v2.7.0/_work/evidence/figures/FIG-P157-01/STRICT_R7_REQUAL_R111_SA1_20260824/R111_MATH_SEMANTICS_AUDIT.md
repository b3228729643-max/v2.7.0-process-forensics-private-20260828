# FIG-P157-01 R111 mathematical and teaching-semantics audit

The current source is `fig_v1_c10_complexity.tex`. It defines training error at lines 33--34 as `0.36 + 3.35 exp(-0.34x)` and validation error at lines 35--37 as `1.08 + 0.105(x-5.25)^2`, each over `x=0..10`.

- The training function is strictly decreasing on the displayed domain.
- The validation function is U-shaped and has its minimum at `(5.25, 1.08)`.
- The direct source calculation recorded in `R111_CURVE_RAW_RECHECK.json` finds no function crossing; its smallest vertical gap is `0.020103...` data units at `x=3.717666...`, approximately `4.1501 px` at the rendered scale.
- The combined rendered curve stroke radius is approximately `4.2708 px`; hence the mathematical curves remain distinct while their visible stroke envelopes merge. This is a representation-semantic error, not a claim that the source functions algebraically intersect.

The reader-visible labels and caption were checked against the source and the printed PDF through `R111_SEMANTIC_SOURCE_MAP.csv`: training annotation says monotone decrease, validation annotation says first decreases then increases, the gold marker label identifies minimum validation error, and the selected-complexity reference is consistent with the vertex. The caption repeats the same correct teaching conclusion. These text and mathematical statements are internally consistent.

However, the canonical peer-independent final-visible masks for the two semantically independent data curves intersect in 139 native pixels with clearance 0. A reader can therefore encounter a merged line envelope in a plot whose teaching claim requires two distinct curves. This fails mathematical/visual semantic fidelity even though the underlying functions and all labels are correct.

`TEXT_CONSISTENCY_PASS=true`.

`MATH_SEMANTICS_PASS=false` because `O-G001` and `O-G002` must be visibly separable but are not.
