# Math, geometry, caption, and grayscale semantic ledger

| Check | Independent validation | Result |
|---|---|---|
| KL--ELBO identity | Current source lines 25--27 and chapter theorem lines 547--568 both state `log p(w)=L(q)+KL(q(h)||p(h|w))`; ROI05 shows the correct rendered relation and codepoints. | PASS |
| KL nonnegativity and lower bound | Current source line 29 and chapter theorem/proof lines 568 and 584 give `KL>=0`, hence `L(q)<=log p(w)`. The direction shown in ROI06 is correct. | PASS |
| Coordinate-update monotonicity | Current plot values are `0.12, 0.34, 0.50, 0.64, 0.73, 0.79, 0.80`; successive changes are `+0.22,+0.16,+0.14,+0.09,+0.06,+0.01`, all nonnegative. The rendered constant plot is a nondecreasing staircase. | PASS |
| Finite running is not global optimality | Caption and right annotation limit the conclusion to a coordinate-stable point or local stationary point; chapter proposition/limitation lines 728--756 explicitly deny a global-optimum guarantee and state that multiple starts are only a comparison. | PASS |
| Upper bound/limit status | Dashed unmarked line is labeled `未知全局上限`; neither plot nor caption claims its numerical value or that the finite trace reached it. | PASS |
| Color plus non-color encoding | The ELBO trajectory is solid with circular marks; the unknown bound is dashed and unmarked. In grayscale the two remain distinct by both line and mark encoding. | PASS |
| Length decomposition | Left bar shows observed log evidence as ELBO plus KL gap; KL is nonnegative and the restricted-family gap may remain positive. | PASS |
| Caption consistency | Exact current caption matches source line 53, chapter statement at lines 587--589, and the two panels without adding a stronger conclusion. | PASS |
| Page integration | Figure 35.5 is introduced immediately above it, followed immediately by the next derivation. It is centered, proportional to the text block, has balanced whitespace, and causes no orphan, clipping, or collision on physical page 739. | PASS |

Final semantic result: `MATH_SEMANTICS_PASS=true`, `TEXT_CONSISTENCY_PASS=true`, `GRAYSCALE_PASS=true`, `PAGE_INTEGRATION_PASS=true`.
