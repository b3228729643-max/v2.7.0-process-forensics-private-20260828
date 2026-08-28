# Independent localization and context check

Searching text inside the single exact official PDF located the figure on physical PDF page 717, printed page 704. The figure and complete caption are present on that page; the preceding page contains the posterior-predictive explanation and points forward to this figure.

The exact chapter source states the one-step posterior predictive result

`Pr(Y_(N+1)=i | n, alpha)=(alpha_i+n_i)/(alpha_0+N)`

and explains that after integrating out theta, observing a category adds one unit to that category's predictive mass and to the total mass. The current figure source expresses the same update using a frozen three-category example.

Independent semantic recomputation:

- Current pseudo-count vector: `(4,3,2)`, total `9`.
- Visible left token count: four class-1, three class-2, two class-3 tokens.
- Left probabilities: `4/9, 3/9, 2/9`; sum `1`.
- Observation: `j=2`.
- Updated vector: `(4,4,2)`, total `10`; only the second component changes.
- Visible right token count: four class-1, four class-2, two class-3 tokens; the new class-2 token is additionally encoded by hatching.
- Right probabilities: `4/10, 4/10, 2/10`; sum `1`.
- Update formula: `n_2 <- n_2+1` and `alpha_0+N <- alpha_0+N+1`.
- The exchangeability/reinforcement statement is correct: integrating over theta yields an exchangeable dependent predictive sequence, not a fixed-parameter iid sequence.

The shorter conditioning notation `P(Y_(N+1)=k | n)` in the graphic treats alpha as fixed, while the numerator and title explicitly retain alpha. This is consistent with the adjacent chapter statement and does not change the mathematical object.

