# Independent mathematics and semantics recomputation

## Model and algebra

Let `theta` lie in the `(K-1)`-simplex, let every `alpha_i>0`, and let `n_i>=0` with `sum_i n_i=N`. The two normalized factors are

`p(theta|alpha) = B(alpha)^(-1) product_i theta_i^(alpha_i-1)`

and

`p(n|theta) = N!/(product_i n_i!) product_i theta_i^(n_i)`.

Multiplication gives a theta-dependent kernel

`product_i theta_i^(alpha_i+n_i-1)`.

Because every `alpha_i+n_i>0`, this kernel normalizes with `B(alpha+n)`, so

`theta | n,alpha ~ Dir(alpha+n)`.

Integrating the joint distribution over the simplex independently gives

`p(n|alpha) = N!/(product_i n_i!) * B(alpha+n)/B(alpha)`.

These are exactly the three formula rows, the posterior result node, and the marginal branch shown in R114.

## Sufficient-statistic statement

The caption's statement that prior and likelihood use the same group of `log theta_i` sufficient statistics is correct: after taking logarithms, their theta-dependent terms are `(alpha_i-1) log theta_i` and `n_i log theta_i`. Product in density space is addition in log-kernel space, hence componentwise exponent addition.

## Arrow and flow semantics

- The multiplication sign between the first two strips denotes prior-kernel times likelihood-kernel.
- The brace groups only those first two strips and labels their componentwise exponent addition.
- The posterior-kernel row points rightward to `Dir(alpha+n)`; the direction is correct.
- The dashed downward branch to the marginal formula is explicitly qualified by `保留归一化常数`; it does not assert that a posterior draw generates the marginal evidence.
- No arrow reverses conditioning, changes the role of `n` and `alpha`, or turns parameter addition into addition of probability vectors.

## Caption and current V5-C05 prose

The immediately preceding prose says that prior shape, observed counts, and posterior shape are aligned componentwise and that addition occurs in parameters rather than between probability vectors. The caption repeats the same conclusion and adds the normalization-constant consequence. Both agree with the theorem and proof on the page and with the recomputation above.

## Independent conclusion

No mathematical-meaning, conditioning, direction, caption, or adjacent-prose inconsistency is present.
