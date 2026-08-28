# Manual codepoint and tofu ledger

This ledger was authored after opening the native 300 dpi crop and all five native1x/nearest8x risk pairs. `codepoint_audit_machine.csv` is the machine extraction; the entries below are the independent visual/codepoint decisions.

| Object | Manual decision | Decisive codepoint check |
|---|---|---|
| O01 | EXACT | Chinese title plus Latin `Dirichlet` render as intended; no replacement character or square placeholder. |
| O02 | EXACT | Mathematical italic `𝑝` U+1D45D, `𝜃` U+1D703, conditional bar `∣` U+2223, `𝛼` U+1D6FC, Planck-style italic `ℎ` U+210E, summation `∑` U+2211, `𝜂` U+1D702, `𝑇` U+1D447, minus `−` U+2212, and `𝐴` U+1D434 all appear in their correct semantic positions. |
| O04 | EXACT | All Chinese characters in “三项与对数配分函数共同确定密度” are present; nearest8x shows ordinary glyph outlines, not tofu. |
| O06 | EXACT | `ℎ` U+210E, `𝜃` U+1D703, digit `1` U+0031, `Δ` U+0394, mathematical `𝐾` U+1D43E, minus U+2212, and the `K-1` superscript are intact. |
| O08 | EXACT | `𝜂` U+1D702, `𝑘` U+1D458, `𝛼` U+1D6FC, minus U+2212, and digit 1 are present and ordered as `eta_k=alpha_k-1`. |
| O10 | EXACT | `𝑇` U+1D447, `𝑘` U+1D458, `𝜃` U+1D703, Latin `log`, and the second subscript `k` are all distinct. |
| O12 | EXACT | Right-panel Chinese title has no missing or substituted character. |
| O13 | EXACT | `𝐴`, `𝛼`, `∑`, subscript `𝑘`, `Γ` U+0393, minus U+2212, and `alpha_0` are all rendered; the zero is a subscript digit, not the letter O. |
| O14 | EXACT | Down double arrow `⇓` U+21D3 is visible with complete arrowhead and stems. |
| O15 | EXACT | Partial-derivative symbol `∂` U+2202 appears in numerator and denominator; `𝐴`, `𝛼`, and subscript `𝑘` are present and correctly stacked. |
| O17 | EXACT | Double-struck expectation `𝔼` U+1D53C, capital Theta `Θ` U+0398, subscript `𝑘`, `𝜓` U+1D713/psi glyph, equality, minus, `alpha_k`, and `alpha_0` are visually complete. |
| O19 | EXACT | The same expectation/Theta/log symbols are present on both sides, joined by the intended not-equal sign `≠` U+2260; there is no accidental equality or missing slash. |
| O20 | EXACT | Caption label `图 34.6` is complete; digits and decimal point are distinct. |
| O21 | EXACT | Mixed Chinese, Latin `Dirichlet`/`log`, theta, alpha, and subscript `k` render without substitution; the line ends at “给出” as intended. |
| O22 | EXACT | Expected-log identity repeats the same mathematical symbols as O17, followed by the complete Chinese warning; semicolon and final phrase are intact. |

Machine extraction counted zero U+FFFD/replacement or square/tofu candidates, and the opened raster views confirmed zero actual tofu, missing glyph, or wrong-codepoint defects.
