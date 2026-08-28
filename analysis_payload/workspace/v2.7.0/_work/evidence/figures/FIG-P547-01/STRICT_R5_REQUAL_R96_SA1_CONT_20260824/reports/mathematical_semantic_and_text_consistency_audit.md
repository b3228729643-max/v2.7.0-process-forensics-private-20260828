# Mathematical and textual semantic audit

## Frozen figure values

- Left row-stochastic matrix: `A=[[0.7,0.3],[0.2,0.8]]`; both rows sum to 1.
- The explicit bridge in the figure is `P=A^T`, hence `P=[[0.7,0.2],[0.3,0.8]]`; both columns sum to 1.
- For a physical edge `i→j`, the left convention calls it `a_ij`; the right convention calls the same probability `P_ji`. The highlighted 0.3 edge is `a_12` on the left and `P_21` on the right.
- The left row-vector update `rho_(t+1)=rho_t A` and right column-vector update `p^(t+1)=P p^(t)` agree through `p^(t)=rho_t^T`.

## Direct body cross-check

The direct paragraph immediately below Figure 30.2 explicitly states the physical `i→j`, the correspondence `a_ij` / `P_ji`, and `P=A^T`; the immediately following equations state the row/column distribution bridge. The figure caption also says that it gives an explicit transpose bridge.

## Result

Semantic mapping, reading direction (left convention → transpose bridge → right convention), matrix values, and caption/body consistency: **PASS**. This semantic pass is separate from the strict raw-pixel legibility decision.
