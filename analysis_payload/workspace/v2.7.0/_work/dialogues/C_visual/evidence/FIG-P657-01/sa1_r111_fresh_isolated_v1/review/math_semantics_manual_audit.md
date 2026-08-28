# Manual mathematical-semantics audit

## Distribution nodes

- `N01 PASS` — Dirichlet is correctly presented as the general prior on a K-category probability vector.
- `N02 PASS` — Beta is the binary (`K=2`) specialization of Dirichlet.
- `N03 PASS` — multinomial is correctly presented as the general count likelihood.
- `N04 PASS` — binomial is the binary (`K=2`) specialization of multinomial.
- `N05 PASS` — categorical is correctly marked as a single multinomial trial (`N=1`).
- `N06 PASS` — Bernoulli is correctly marked with both restrictions, `K=2,N=1`.

## Seven relations

- `R01 PASS` — Dirichlet→Beta points from the general family to the `K=2` special case; it is thin with an open arrowhead.
- `R02 PASS` — multinomial→binomial points from the general family to the `K=2` special case; it is thin/open.
- `R03 PASS` — multinomial→categorical is vertical and explicitly labeled `N=1`.
- `R04 PASS` — binomial→Bernoulli is vertical and explicitly labeled `N=1`.
- `R05 PASS` — categorical→Bernoulli is horizontal and explicitly labeled `K=2`.
- `R06 PASS` — Dirichlet→multinomial is a thick/filled downward arrow encoding prior–likelihood conjugacy, not set inclusion.
- `R07 PASS` — Beta→binomial is a thick/filled downward arrow encoding prior–likelihood conjugacy, not set inclusion.

## Legend and caption

- `L01 PASS` — the legend’s thick filled arrow exactly matches both conjugacy arrows.
- `L02 PASS` — the legend’s thin open arrow exactly matches all five special-case arrows.
- `C01 PASS` — the caption names all five specializations and explicitly warns that thick arrows denote conjugate priors rather than set containment.
- `A01 PASS` — the source `alt` text carries the same object–relation–conclusion semantics as the visible figure.

Overall semantic decision: `PASS`. The six nodes and all seven relations are mathematically correct and visually unambiguous.

