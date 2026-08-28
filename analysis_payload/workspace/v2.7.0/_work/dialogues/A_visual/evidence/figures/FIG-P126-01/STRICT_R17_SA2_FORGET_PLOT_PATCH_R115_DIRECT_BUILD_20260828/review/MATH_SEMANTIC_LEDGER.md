# P126 R17 mathematics and semantics ledger

| ID | Manual check | Decision |
|---|---|---|
| M01 | Contours satisfy the common quadratic level family `(x+y)^2+y^2=r^2`; no per-level visual rotation inconsistency | PASS |
| M02 | For `f(x,y)=x^2/2+xy+y^2`, Hessian `[[1,1],[1,2]]` has determinant1 and positive eigenvalues `(3±sqrt(5))/2` | PASS |
| M03 | q0=(-3.2,2.2) to q1=(-3.2,1.6): x fixed and `df/dy=x+2y=0` at q1 | PASS |
| M04 | q1 to q2=(-1.6,1.6): y fixed and `df/dx=x+y=0` at q2 | PASS |
| M05 | q2 to q3=(-1.6,.8): x fixed and `df/dy=0` at q3 | PASS |
| M06 | q3 to q4=(-.8,.8): y fixed and `df/dx=0` at q4 | PASS |
| M07 | q4 to q5=(-.8,.4): x fixed and `df/dy=0` at q5 | PASS |
| M08 | q5 to q6=(-.4,.4): y fixed and `df/dx=0` at q6 | PASS |
| M09 | q6 to q7=(-.4,.2): x fixed and `df/dy=0` at q7 | PASS |
| M10 | Objective sequence is `2.92, 2.56, 1.28, .64, .32, .16, .08, .04`, strictly decreasing | PASS |
| M11 | x* at (0,0) is the unique minimizer; q7 is visibly an approximation, not mislabeled as x* | PASS |
| M12 | Legend roles match blue horizontal x1 updates and teal vertical x2 updates; grayscale remains distinguishable as solid versus four disconnected segments | PASS |
| M13 | Source caption says each substep changes one coordinate and the axis-aligned polyline approaches the optimum; figure agrees | PASS |
| M14 | Standalone wrapper intentionally suppresses caption text while preserving centered A4 page integration; no content is clipped | PASS |

Mathematics/semantic/page checks: 14/14 PASS; errors/unresolved: 0/0.
