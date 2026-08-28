# Independent ACF/ESS semantic recomputation

The plotted positive empirical autocorrelations for lags 1 through 6 are

`0.86, 0.74, 0.64, 0.55, 0.47, 0.40`.

Their sum is `3.66`, and the lag-weighted sum is

`1(0.86)+2(0.74)+3(0.64)+4(0.55)+5(0.47)+6(0.40)=11.21`.

Therefore the displayed predeclared-window rule gives

`tau_hat_(6,n) = 1 + 2 sum_{k=1}^6 (1-k/n) rho_hat_k = 8.32 - 22.42/n`.

Because the panel explicitly requires `K=6<n`, every included weight is positive. For every integer `n>6`, `tau_hat_(6,n)>1`, hence `N_eff_hat=n/tau_hat_(6,n)<n`. Thus the plot, the finite-sample weighted formula, the caption, and the adjacent reading sentence all agree: positive empirical correlations in the fixed window increase the variance weight and reduce effective sample size for the same trajectory length.

The graphic also correctly states the diagnostic boundary: later lags are neither drawn nor included, the denominator must be positive, and a finite-trajectory diagnostic is not a convergence proof. Lag zero is shown as the ACF normalization value 1 but is correctly excluded from the sum beginning at k=1.

