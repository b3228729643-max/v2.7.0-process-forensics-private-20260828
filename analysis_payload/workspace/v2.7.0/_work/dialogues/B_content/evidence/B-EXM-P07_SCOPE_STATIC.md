# B-EXM-P07 source/static freeze

## Scope

- Parent HEAD: `bc713ff1505a84b8fd72f2a56a6386bc4dd84a50`.
- Authoritative remaining-example inventory contained 15 unreviewed examples. P07 freezes the next ten in natural order: 33.1, 34.1--34.4, 35.1--35.3, and 36.1--36.2.
- Exact labels:
  - `exm:V5-C04-bridge-bvn`
  - `exm:V5-C05-three-category`
  - `exm:V5-C05-beta-update`
  - `exm:V5-C05-gamma-interface`
  - `exm:V5-C05-evidence`
  - `exm:V5-C06-gibbs-step`
  - `exm:V5-C06-vi-step`
  - `exm:V5-C06-perplexity`
  - `exm:V5-C07-basic-four`
  - `exm:V5-C07-dangling-loss`
- Exact business-source write scope: V5-C04.tex, V5-C05.tex, V5-C06.tex, and V5-C07.tex. Only the ten matching `solution` bodies changed.
- Current post-fix diff: 4 files, 70 insertions, 80 deletions; nothing staged.

## Root independent mathematics/content audit

1. 33.1: with `sigma=sqrt(1-rho^2)`, system scan gives `x1^(1)=sigma` and then `x2^(1)=rho sigma`; the second update uses the same-sweep new `x1^(1)`. The standardized residuals are exactly `1,0`. PASS.
2. 34.1: prior mean is `(1/5,3/10,1/2)`; posterior is `Dir(6,4,5)`, posterior mean/predictive `(2/5,4/15,1/3)`, and interior MAP `(5/12,1/4,1/3)`. Ordered future `(1,2)` has probability `(6/15)(4/16)=1/10`; adding the reverse order gives unordered probability `1/5`. PASS.
3. 34.2: `B(2,3)=1/12`, so the prior density is `12 theta(1-theta)^2`; mean `2/5`, variance `1/25`. Three successes and one failure give `Beta(5,4)` and predictive success probability `5/9`. PASS.
4. 34.3: `s=2+3+5=10` and normalized vector `(1/5,3/10,1/2)` is strictly positive and sums to one; multiplying by `s` reconstructs the input. A fixed input tests the interface but cannot prove a Dirichlet random generator. PASS.
5. 34.4: posterior is `Dir(3,2,2)` and predictive is `(3/7,2/7,2/7)`. `B(1,1,1)=1/2`, `B(3,2,2)=1/360`; specified sequence evidence is `1/180`, while the count-vector evidence multiplies by `4!/(2!1!1!)=12` and equals `1/15`. PASS.
6. 35.1: after deleting the current token, `r1=3/26=66/572` and `r2=5/44=65/572`, so normalized probabilities are `(66/131,65/131)`. Deleting from both count tables before calculation and adding to the sampled new topic afterward preserves the token total. PASS.
7. 35.2: `psi(3)-psi(5)=-7/12`, `psi(2)-psi(5)=-13/12`; weights are about `(0.3348,0.0677)`, their ratio is `3 exp(1/2)`, and normalization gives approximately `(0.832,0.168)`. PASS.
8. 35.3: frozen-model perplexity is `exp[-(log .25+log .5)/2]=2 sqrt(2)`; `1/sqrt(.4)` uses probabilities re-estimated with holdout information and is not comparable under the frozen evaluation protocol. PASS.
9. 36.1: direct multiplication gives first iterate `(3/8,5/24,5/24,5/24)^T`, whose sum is one. The candidate `(1/3,2/9,2/9,2/9)^T` is a probability fixed point. The graph is irreducible and has cycles of coprime lengths, hence is aperiodic; convergence and ranking `A > B=C=D` follow. PASS.
10. 36.2: after deleting C's only outgoing edge, the C column sum is zero and the other column sums are one. For every nonnegative vector, `1^T Mx=1^T x-x_C`, hence `S_(t+1)=S_t-r_C^(t)`. From the uniform start the successive losses are `1/4,5/24,7/48`, giving post-update masses `3/4,13/24,19/48`. Every state can send mass to C, so the substochastic iteration keeps leaking and tends to zero; zero is not a PageRank probability vector. PASS after the post-SA1 correction described below.

Root result: `10/10 PASS`; no mathematics/content finding.

## Static gates

```text
git diff --check: PASS
python -m unittest src.tests.test_style_term_solution_contracts src.tests.test_layout_source_contracts:
  Ran 9 tests in 0.390s
  OK
check_p07_static.ps1:
  P07_STATIC=PASS
  TARGET_SOLUTIONS=10
  STAGE_MACROS=70/70
  TARGET_LABELS_AND_HEADINGS=10/10
  TARGET_NESTED_RUNNING_EXAMPLE=0
  ENVIRONMENT_STACKS=BALANCED
  HANDWRITTEN_CHECK_ANSWER_HEADINGS=0
```

- The first static pass caught one handwritten `Dirichlet--多项` term variant and a local checker escaping defect. The source now uses the existing `\DirichletMultinomial{}` canonical macro; the checker was aligned with the already-proven P06 checker. The complete gate was then rerun and passed.
- The first fresh SA1 independently found one blocking mathematical wording defect in 36.2: `1-x_C` had been described as if it were valid across later subprobability iterates. The source now states the general identity `1^T Mx=1^T x-x_C`, the recursion `S_(t+1)=S_t-r_C^(t)`, and the exact three losses. The same local correction also makes 35.1 explicitly say “add once to each new-topic table,” eliminating any old-topic interpretation of “restore.” No other source or object changed.
- All static gates were rerun after this correction and passed with the final 4-file `70+/80-` diff.
- No label, reference, example heading, question text, shared macro/style, test, drawing source, index, build entry, or authority state was changed.
- TeX/LuaLaTeX/latexmk was not started. Source remains frozen pending a fresh read-only SA1 and explicit main build-slot grant.

## Current decision

- Root static/content status: `PASS`.
- First fresh SA1: `FAIL` solely on the corrected 36.2 cross-round identity; the other nine examples and all scope/structure gates passed.
- Another fresh post-fix SA1 independently returned `FINAL_DECISION=PASS`, `LOCAL_STATUS=B_LOCAL_PASS`, mathematics `10/10`, structure/scope PASS, and `FINDINGS=[]`; report: `B-EXM-P07_SA1_POSTFIX_FRESH.md`.
- Commit: forbidden before build/visual/SA3 closure.
- P08: forbidden.
- TeX: disabled.
