# B-EXM-P03 SA1 pre-review

- Scope: examples 1.1, 2.1, 3.1, 4.1, 4.2, 4.3, 5.1, 6.1, 7.1, 7.2.
- Review mode: source-only pre-review; no source files were changed in this step.
- Verdict: all ten mathematical solutions are correct, but all ten need a structure edit before acceptance.
- Shared finding: preserve the existing derivations, replace generic reading/method/check text with problem-specific text, and make all seven stages occur exactly once: `\SLReadTranslation`, `\SolGiven`, `\SLMethodTrigger`, `\SolPlan`, `\SolDerive`, `\SolCheck`, `\SolAnswer`.

## Object findings

### 1.1 — three-sample type check

- File: `src/讲义源码/第01册_数学基础与统计学习基本理论/chapters/V1-C01.tex`.
- Current solution begins at the `exm:V1-C01-small` heading.
- Preserve: dimension calculation and the two independent products.
- Required plan: verify `(3 x 2)(2 x 1)`, evaluate the three row inner products, then recompute as `2X_{:1}-X_{:2}`.
- Check certificate: both routes give `(2,3,-1)^T`; the result has three rows, matching the three samples and `y in R^3`.
- Answer: `Xw=(2,3,-1)^T in R^3`.

### 2.1 — two-dimensional projection and residual

- File: `src/讲义源码/第01册_数学基础与统计学习基本理论/chapters/V1-C02.tex`.
- Preserve: projection coefficient, projected point, residual, orthogonality and Pythagorean check.
- Required plan: compute `a=(u^T x)/(u^T u)`, set `p=au`, form `r=x-p`, and obtain the distance from `||r||_2`.
- Check certificate: `u^T r=0` and `||x||_2^2=||p||_2^2+||r||_2^2=10`.
- Answer: `a=2`, `p=(2,2)^T`, `r=(1,-1)^T`, distance `sqrt(2)`.

### 3.1 — bivariate quadratic

- File: `src/讲义源码/第01册_数学基础与统计学习基本理论/chapters/V1-C03.tex`.
- Preserve: gradient, Hessian, Sylvester test, and completed-square argument.
- Required plan: differentiate componentwise, test the leading principal minors, then use a completed square as an independent global check.
- Check certificate: the principal minors are `2` and `8`, while `f=(x_1+x_2)^2+2x_2^2` vanishes only at the origin.
- Answer: `grad f=(2x_1+2x_2, 2x_1+6x_2)^T`, `H=[[2,2],[2,6]]`; the origin is the unique global minimizer and the minimum is `0`.

### 4.1 — die-event union

- File: `src/讲义源码/第01册_数学基础与统计学习基本理论/chapters/V1-C04.tex`.
- Preserve: inclusion-exclusion calculation and direct counting.
- Required plan: compute the intersection and union explicitly, apply inclusion-exclusion, then count the union directly.
- Check certificate: `A cap B={4,6}` and `A cup B={2,4,5,6}`; direct counting gives `4/6`.
- Answer: `P(A cup B)=2/3`.

### 4.2 — total-variance decomposition

- File: `src/讲义源码/第01册_数学基础与统计学习基本理论/chapters/V1-C04.tex`.
- Preserve: within-group and between-group terms plus the second-moment calculation.
- Required plan: evaluate both terms in the law of total variance, then independently compute `E[X]` and `E[X^2]`.
- Check certificate: within-group variance is `1`, between-group variance is `1`, `E[X]=1`, and `E[X^2]=3`.
- Answer: `Var(X)=2`, with equal contributions `1+1` from within-group and between-group variation.

### 4.3 — base-rate effect in screening

- File: `src/讲义源码/第01册_数学基础与统计学习基本理论/chapters/V1-C04.tex`.
- Preserve: evidence probability, Bayes calculation and odds check.
- Required plan: compute `P(+)`, normalize `P(D,+)`, and verify the posterior with prior odds times the likelihood ratio.
- Check certificate: `P(+)=0.059`; prior odds `1:99` multiplied by likelihood ratio `19` gives posterior odds `19:99`.
- Answer: `P(D|+)=19/118 approximately 0.1610`, about `16.1%`.

### 5.1 — Bernoulli maximum likelihood

- File: `src/讲义源码/第01册_数学基础与统计学习基本理论/chapters/V1-C05.tex`.
- Preserve: score equation, strict concavity and boundary comparison.
- Required plan: write the log-likelihood on `[0,1]`, solve the interior score equation, certify the maximum, and compare the two requested candidates.
- Check certificate: `ell''(p)<0`, both endpoints have zero likelihood, and `ell(0.7)-ell(0.5) approximately 0.82283 > 0`.
- Answer: the unique MLE is `p-hat=0.7`; candidate `0.7` has the larger log-likelihood.

### 6.1 — two-way KL comparison

- File: `src/讲义源码/第01册_数学基础与统计学习基本理论/chapters/V1-C06.tex`.
- Preserve: both KL sums and the total-variation/Pinsker check.
- Required plan: confirm common positive support, calculate the two ordered divergences separately, and compare them against a direction-independent lower bound.
- Check certificate: total variation is `0.2`, so Pinsker gives the lower bound `0.08` in both directions.
- Answer: `D_KL(P||Q) approximately 0.09152` and `D_KL(Q||P) approximately 0.10465`; they differ, so KL is asymmetric.

### 7.1 — nonnegative quadratic KKT cases

- File: `src/讲义源码/第01册_数学基础与统计学习基本理论/chapters/V1-C07.tex`.
- Preserve: the two KKT systems and the direct one-dimensional comparison.
- Required plan: write `-x<=0`, solve stationarity/feasibility/complementarity for each objective, and confirm activity by comparing the unconstrained minimizer with `[0,infinity)`.
- Check certificate: the first unconstrained minimizer is feasible; the second objective is increasing on the feasible interval and therefore minimizes at the boundary.
- Answer: `(x*,alpha*)=(2,0)` for the inactive case and `(0,2)` for the active case.

### 7.2 — projection of the origin onto a halfspace

- File: `src/讲义源码/第01册_数学基础与统计学习基本理论/chapters/V1-C07.tex`.
- Preserve: KKT derivation, strict-convexity uniqueness, and the Cauchy--Schwarz check.
- Required plan: express the constraint as `b-a^T x<=0`, solve stationarity and complementarity, then certify the norm lower bound independently.
- Check certificate: every feasible point satisfies `||x||_2 >= b/||a||_2`, with equality at the candidate.
- Answer: `x*=ba/||a||_2^2`, `alpha*=b/||a||_2^2`, and the optimum is `b^2/(2||a||_2^2)`.

## Edit boundary

- Only the ten local `solution` blocks above are in scope for P03.
- Do not change example statements, figure inputs, shared macros/styles, tests, build entry points, indexes, global numbering, or authority/state files.
- P03 source editing remains gated on P02's completed build/visual/SA3/commit/handoff.
