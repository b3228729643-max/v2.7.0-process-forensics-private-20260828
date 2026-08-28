# Frozen visible-object denominator

The figure-internal denominator is 18 semantic objects. Page integration adds the caption label and caption body, producing a frozen page-scoped denominator of 20 objects and exactly `C(20,2)=190` unordered pairs. This denominator was fixed before pair adjudication.

- `O01 PASS` — row heading “先验族”; intact blue bold text left of the prior row.
- `O02 PASS` — Dirichlet node; rounded teal border, pale fill, centered “Dirichlet分布”.
- `O03 PASS` — Beta node; centered “Beta分布” with a separate `K=2` line.
- `O04 PASS` — row heading “似然族”; intact blue bold text left of the likelihood row.
- `O05 PASS` — multinomial node; centered “多项分布”.
- `O06 PASS` — binomial node; centered “二项分布” with a separate `K=2` line.
- `O07 PASS` — row heading “单次试验”; intact blue bold text left of the single-trial row.
- `O08 PASS` — categorical node; gray special-case styling and `N=1` second line.
- `O09 PASS` — Bernoulli node; gray special-case styling and `K=2,N=1` second line.
- `O10 PASS` — thin/open Dirichlet→Beta special-case relation and “特殊情形” label.
- `O11 PASS` — thin/open multinomial→binomial special-case relation and “特殊情形” label.
- `O12 PASS` — thin/open multinomial→categorical relation with `N=1` label.
- `O13 PASS` — thin/open binomial→Bernoulli relation with `N=1` label.
- `O14 PASS` — thin/open categorical→Bernoulli relation with `K=2` label.
- `O15 PASS` — thick/filled Dirichlet→multinomial conjugacy arrow.
- `O16 PASS` — thick/filled Beta→binomial conjugacy arrow.
- `O17 PASS` — legend sample “thick filled arrow = 共轭”.
- `O18 PASS` — legend sample “thin open arrow = 特殊情形”.
- `O19 PASS` — bold caption label “图34.3”.
- `O20 PASS` — two-line caption body ending in “粗箭头表示共轭先验而不是集合包含”.

Manual denominator decision: `PASS`; no visible object is missing, duplicated, merged, or excluded.

