# Independent mathematics and semantics recomputation

## Model reconstructed from the current source and necessary V5-C05 prose

For `K>=2`, `alpha_k>0`, and `alpha_0=sum_k alpha_k`, the Dirichlet density on the simplex is

`p(theta|alpha) = 1/B(alpha) * product_k theta_k^(alpha_k-1)`.

Writing

- `h(theta)=1_{Delta^(K-1)}(theta)`,
- `eta_k=alpha_k-1`, and
- `T_k(theta)=log theta_k`,

gives

`p(theta|alpha)=h(theta) exp{sum_k eta_k T_k(theta)-A(alpha)}`

with

`A(alpha)=log B(alpha)=sum_k log Gamma(alpha_k)-log Gamma(alpha_0)`.

The open/closed-simplex boundary convention in the indicator changes only a measure-zero boundary and does not alter the density or moment identity in the current context.

## Derivative recomputation

Because `alpha_0=sum_j alpha_j`, `partial alpha_0/partial alpha_k=1`. Therefore

`partial A/partial alpha_k = psi(alpha_k)-psi(alpha_0)`.

In this parameterization `eta_k=alpha_k-1` has unit derivative, so the exponential-family identity gives

`partial A/partial alpha_k = partial A/partial eta_k = E[T_k(Theta)] = E[log Theta_k]`.

Thus the displayed result

`E[log Theta_k]=psi(alpha_k)-psi(alpha_0)`

is mathematically correct. The source chapter's nearby proposition and proof give the same identity by differentiating `log B(alpha)` under the integral, so the figure, caption, and current prose agree.

## Warning recomputation

The logarithm is strictly concave. For a nondegenerate Dirichlet component `Theta_k`, Jensen's inequality gives

`E[log Theta_k] < log E[Theta_k]`.

The figure states the weaker but correct `not equal` relation. It does not interchange expectation and logarithm and therefore prevents the intended misconception.

## Semantic correspondence checks

- Lowercase `theta` is the density argument; uppercase `Theta` is the random variable inside the expectation. This case change is intentional.
- The switch from index `i` in the surrounding proposition to dummy index `k` in the figure is semantically neutral.
- `A(alpha)` is `log B(alpha)`, not its negative; the displayed minus sign in the density exponent and the two terms of `A` are consistent.
- The arrow reads from log-partition function to derivative to expected log moment, then to the noncommutation warning; the reading order is mathematically causal and unambiguous.
- No normalization factor, sign, subscript, Gamma/digamma symbol, or conditioning variable is missing.

Manual mathematics disposition: `MATH_SEMANTICS_CLEAR`.
