# Independent ACF/ESS recomputation

- Candidate: official R109, physical page 661, printed page 648, Figure 32.9.
- Plotted empirical ACF values: `rho_0=1`, and `rho_1..rho_6=(0.86,0.74,0.64,0.55,0.47,0.40)`.
- The formula correctly excludes `rho_0` from the correction sum and includes exactly the preset window `k=1..6`; no post-window stems are drawn.
- `sum_{k=1}^6 rho_k = 3.66`.
- `sum_{k=1}^6 k rho_k = 11.21`.
- Therefore `sum_{k=1}^6 (1-k/n)rho_k = 3.66-11.21/n` and `tauhat_{6,n}=8.32-22.42/n`.
- Because the figure states `K=6<n`, the smallest integer case is `n=7`, for which `tauhat_{6,7}=5.117142857...>1`; it remains positive and greater than one for every `n>6`.
- Thus `Nhat_eff=n/tauhat_{6,n}` is positive and smaller than `n`, exactly matching the caption's claim for this fixed positive-ACF example.
- The explicit conditions `tauhat_{K,n}>0`, `K=6<n`, the finite-sample weights `(1-k/n)`, and the warning that this is not a convergence proof are all semantically necessary and correctly shown.

Manual semantic conclusion: no wrong sign, index, weight, normalization, truncation, or convergence claim was found.
