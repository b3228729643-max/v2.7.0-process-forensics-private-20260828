# B-EXM-P07 fresh post-fix SA1

## Role freshness

- New isolated read-only SA1 for the final P07 post-fix source.
- Read the lean-execution skill, `TASK_PACKET_B.md`, current four source files/diff, and necessary referenced chapter definitions.
- Did not read P07 evidence, CURRENT_STATE, root/main conclusions, the failed SA1 output, or another agent's result.
- Did not write files, run TeX, stage/commit, or enter P08. `files_changed=[]`.

## Independent recomputation

1. 33.1: with `sigma=sqrt(1-rho^2)`, `x1^(1)=sigma` and `x2^(1)=rho sigma`; the second conditional correctly reads the same-sweep new `x1^(1)`. PASS.
2. 34.1: prior mean `(1/5,3/10,1/2)`; posterior `Dir(6,4,5)`, mean/predictive `(2/5,4/15,1/3)`, and legal interior MAP `(5/12,1/4,1/3)`. Ordered `(1,2)` probability `1/10`; unordered one-each probability `1/5`. PASS.
3. 34.2: `B(2,3)=1/12`, density `12 theta(1-theta)^2`, mean `2/5`, variance `1/25`; three successes and one failure give `Beta(5,4)` and predictive `5/9`. PASS.
4. 34.3: `s=10`, normalized vector `(1/5,3/10,1/2)`, positive, sums to one, and reconstructs `(2,3,5)`. The deterministic interface test is correctly distinguished from a distributional generator proof. PASS.
5. 34.4: posterior `Dir(3,2,2)`, predictive `(3/7,2/7,2/7)`, specified-sequence evidence `1/180`, and count-vector evidence `12/180=1/15`. PASS.
6. 35.1: after leave-one-out deletion, `r1=(4/13)(3/8)=3/26`, `r2=(2/11)(5/8)=5/44`; normalization gives `(66/131,65/131)`. The source correctly says to subtract from both old-topic tables before calculation and add once to both new-topic tables after sampling. PASS.
7. 35.2: digamma differences are `-7/12,-13/12`; weights are about `(0.3348,0.0677)`, ratio `3 exp(1/2)`, and normalized responsibility about `(0.832,0.168)`. PASS.
8. 35.3: frozen-model perplexity is `1/sqrt(.25*.5)=2 sqrt(2)`; the smaller value from holdout-informed refitting is a different, leaked protocol and is not comparable. PASS.
9. 36.1: the first iterate is `(3/8,5/24,5/24,5/24)^T`; the proposed probability vector is a fixed point. The graph is strongly connected and has length-two and length-three cycles, so it is irreducible and aperiodic; the limit and ranking `A > B=C=D` follow. PASS.
10. 36.2: column sums are `(1,1,0,1)`, hence for every nonnegative vector `1^T Mx=1^T x-x_C` and `S_(t+1)=S_t-r_C^(t)`. Independent iterates have masses `3/4,13/24,19/48`; moreover `||M^3||_1=7/12<1`, proving convergence to zero. The zero vector is not a PageRank probability distribution. PASS.

Result: mathematics/content `10/10 PASS`; `FINDINGS=[]`.

## Structure and scope

- Parent HEAD: `bc713ff1505a84b8fd72f2a56a6386bc4dd84a50`.
- Exact current diff: four authorized files, `70 insertions / 80 deletions`; nothing staged.
- Ten labels are unique; each matching `\SLExampleSolutionHeading` is unique.
- Each target has exactly one ordered sequence of `\SLReadTranslation`, `\SolGiven`, `\SLMethodTrigger`, `\SolPlan`, `\SolDerive`, `\SolCheck`, and `\SolAnswer`: total `70/70`.
- Full-file `solution`/`SLRunningExample` stacks are balanced.
- Referenced equation/theorem/example labels resolve uniquely.
- No shared macro/style, drawing source, test, index, build entry, state, or other forbidden source domain changed.

## Decision

- `FINDINGS=[]`
- `FINAL_DECISION=PASS`
- `LOCAL_STATUS=B_LOCAL_PASS`
- `files_changed=[]`
- `unresolved=[]`

