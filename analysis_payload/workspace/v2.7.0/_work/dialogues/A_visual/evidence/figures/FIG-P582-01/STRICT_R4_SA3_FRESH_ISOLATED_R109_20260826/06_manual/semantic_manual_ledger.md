# Independent semantic recomputation

- Reviewer: SA3_FRESH_ISOLATED
- Observation completed: 2026-08-26T15:48:00Z
- Official location: physical page 632; printed page 619; Figure 31.7.
- Fixed sample sequence read from current source and caption: `U=(0.8,0.1,0.7,0.4)`.
- Independent square calculation: `(0.64,0.01,0.49,0.16)`.
- Independent cumulative sums: `(0.64,0.65,1.14,1.30)`.
- Independent running means: `(0.64,0.325,0.38,0.325)`.
- Independent trend: down from 0.64 to 0.325; up to 0.38; down to 0.325.
- True reference: `E[U^2]=1/3` for `U` uniform on `[0,1]`; dashed line and label match.
- Source coordinates, visible value labels, curve vertices, annotations, formula `h(U_i)=U_i^2`, and current caption agree with the recomputation.
- The active-goal card text that described importance-sampling support is stale/misassigned for this figure and was rejected rather than used as semantic authority.

Semantic decision: **PASS**. The overall SA3 result is nevertheless FAIL because critical pair P05555 is a true illegal glyph overlap.
