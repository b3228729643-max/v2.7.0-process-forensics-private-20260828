# FIG-P577-01 mathematical/content audit

Result: **PASS for mathematical semantics and caption/body consistency**. This does not override the strict visual `FAIL→SA2` result.

1. `p(y)=6y(1-y)` on `[0,1]` integrates to `6(1/2−1/3)=1`; `q(y)=1` is also a density on that support.
2. `p` is maximized at `y=1/2`, with `p(1/2)=3/2`; `cq=(8/5)·1=8/5`. Hence `p≤cq` everywhere and the minimum envelope gap is `8/5−3/2=1/10`.
3. The rejection-area integral is `∫_0^1(cq-p)dy=8/5−1=3/5`.
4. The acceptance probability is `∫q(y)p(y)/(cq(y))dy=1/c=5/8`; the expected proposals per accepted value are `c=8/5`.
5. Circle: at `y=1/4`, `p=9/8`, `h=4/5`, so `U=h/(cq)=1/2≤(9/8)/(8/5)=45/64`; acceptance is correct.
6. Triangle: at `y=3/4`, `p=9/8`, `h=27/20`, so `U=27/32>45/64`; it is an ordinary rejection while remaining under `cq=8/5`, exactly as caption/body state.

Support endpoints, solid `p` curve, dashed `cq` line, area-fill semantics, point markers, title summary, caption, and adjacent `读图检查` were all reconciled against these computations.
