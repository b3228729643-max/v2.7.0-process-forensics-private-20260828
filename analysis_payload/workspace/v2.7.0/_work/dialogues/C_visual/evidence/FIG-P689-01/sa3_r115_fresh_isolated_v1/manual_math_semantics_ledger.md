# Manual mathematics and semantics ledger

Evidence used: current figure source, exact current chapter around the inclusion, extracted text from official physical page 739, native figure/caption, and critical ROIs.

| Claim | Independent validation | Verdict |
|---|---|---|
| Log-evidence decomposition | Under the chapter's stated assumptions, `KL(q||p(h|w)) = log p(w)-L(q)`, hence the displayed `log p(w)=L(q)+KL(q(h)||p(h|w))` is correct. | PASS |
| KL nonnegativity | `KL>=0` implies `L(q)<=log p(w)`; equality requires q equal to the exact posterior almost everywhere. The figure's positive-gap statement for a restricted variational family is correct. | PASS |
| Coordinate-update progression | Source coordinates `(0,.12),(1,.34),(2,.50),(3,.64),(4,.73),(5,.79),(6,.80)` are nondecreasing. The rendered step curve contains no descending segment. | PASS |
| Finite-run claim | Caption says finite running usually reaches only coordinate stability or a local stationary point under a nonconvex optimization setting. It does not assert finite-run convergence to a global optimum. | PASS |
| Multi-start claim | Caption explicitly says multi-start comparison is not a proof of global optimality. This is mathematically safe. | PASS |
| Unknown-limit semantics | The dashed line is labelled “未知全局上限”; it is visibly above the finite staircase and is not presented as attained. Together with the left-panel evidence bound and caption, it does not falsely identify the last iterate as the global optimum or evidence. | PASS |
| Restricted-family semantics | The preceding chapter sentence states that the optimal q in a restricted family can retain positive KL distance from the true posterior and that “E-step ELBO equals evidence” is generally wrong. The figure and caption agree. | PASS |
| Caption consistency | Caption matches the rendered decomposition, monotone staircase, local/stable endpoint, and absence of a global-optimum guarantee. | PASS |

MATH_SEMANTICS_PASS=true
TEXT_CONSISTENCY_PASS=true
