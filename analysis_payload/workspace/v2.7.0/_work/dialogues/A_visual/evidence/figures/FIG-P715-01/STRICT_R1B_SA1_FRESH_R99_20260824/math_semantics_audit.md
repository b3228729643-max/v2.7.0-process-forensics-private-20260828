# FIG-P715-01 fresh R99 mathematical-semantic audit

- R99 physical PDF page independently located by the exact caption/title text: 763 (printed page 750); the legacy task-card physical page 826 is not valid for this 814-page candidate.
- Directed graph: i→j, j→i, j→h, h→i. With row=destination and column=source, A columns are (0,1,0)^T, (1,0,1)^T, (1,0,0)^T.
- Therefore c=(1,2,1), M=A diag(c)^{-1} is column-stochastic, and the shown P=M^T is row-stochastic. P_{ji}=M_{ij}, Pr(X_{t+1}=i|X_t=j), p^{(t+1)}=Mp^{(t)}, and rho_{t+1}=rho_tP with rho_t=(p^{(t)})^T agree.
- RESULT: PASS for mathematical semantics.
