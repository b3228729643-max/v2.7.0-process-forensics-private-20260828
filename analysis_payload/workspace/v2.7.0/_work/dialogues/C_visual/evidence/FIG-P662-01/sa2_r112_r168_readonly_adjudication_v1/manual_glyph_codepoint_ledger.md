# Manual glyph/codepoint and legibility ledger

The native figure, text overlay, extracted text, and nearest8× glyph ROI were compared after rendering. The machine table contains 78 non-whitespace PDF spans and reports no U+FFFD replacement, U+25A1 white-square, or U+25A0 black-square token inside the figure/caption crop. Page-710 fonts used by the figure/caption are embedded, subsetted, and Unicode-mapped.

| Scope | Manual observation |
|---|---|
| Gamma inputs | `Y`, relation `~`, `Gamma`, alpha, lambda, digits 1/2, and italic K all render as the intended glyphs. Relation strokes are thin by design but plainly recognizable in the native view. |
| Total block | `S`, equals, summation, upper K, lower `k=1`, and `Y_k` are correct; no limit is lost or merged. |
| Normalization | The division sign and `S` are distinct; there is no colon/tofu substitution. |
| Proportion block | Uppercase Theta, subscript k, equals, `Y_k`, slash, and `S` are correctly ordered and legible. |
| Dirichlet block | Uppercase Theta, distribution relation, `Dir(alpha)`, summation, lower k, `Theta_k`, equals, and 1 all render correctly. |
| Independence result | The source `perp` pair renders as two adjacent perpendicular signs denoting independence; it is not a missing-glyph box. `alpha_0` uses the correct zero subscript and lambda is correct. |
| Beta special case | Italic K, digit 2, uppercase Theta, subscript 1, relation, `Beta`, and parameters `alpha_1,alpha_2` are correct and distinguishable. |
| Chinese annotations/caption | `总量`, `比例`, `单纯形点`, `相互独立、共同率参数`, `特例`, and the complete caption have no missing strokes, tofu, wrong character, or unreadable compression. |
| Badges | White numerals 1, 2, and 3 are centered, intact, and high contrast. |

Advisory machine ink heights range from 9 to 44 native pixels. The 9-pixel values are the shallow strokes of the four relation tildes, not character-body heights; each is plainly recognizable at native 300 dpi. Main Latin/math bodies are approximately 26–39 px, natural scripts 19–22 px, and Chinese spans 31–42 px. Under R168 these numbers are corroborating evidence, not standalone fail triggers.

Manual glyph/codepoint decision: no missing glyph, tofu, wrong codepoint, or actual unreadability.
