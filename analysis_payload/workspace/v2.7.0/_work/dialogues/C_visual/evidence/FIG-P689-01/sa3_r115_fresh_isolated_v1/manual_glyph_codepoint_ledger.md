# Manual glyph and codepoint ledger

This ledger was authored after opening the native 300 dpi crop and the seven nearest-neighbor 8x ROIs.

| Check | Observed rendering | Verdict |
|---|---|---|
| `\mathcal L(q)` | Calligraphic L and parentheses are intact in bar, identity, and inequality. | PASS |
| `\log p(w)` | `log`, italic p/w, parentheses, and spacing are intact. | PASS |
| `\operatorname{KL}` | Upright `KL` is intact in formula and caption. | PASS |
| Divergence separator `\|` | Renders as a double parallel bar `∥`, not a single conditional bar or missing glyph. | PASS |
| Conditional separator `\mid` | Renders as the single conditional bar `∣` inside `p(h∣w)`. | PASS |
| Inequalities | `≥` and `≤` are the correct codepoints and are not degraded or substituted. | PASS |
| Chinese slash | `坐标稳定／局部驻点` contains the intended fullwidth slash `／`, clearly rendered. | PASS |
| Tick sequence | Exactly `0,1,2,3,4,5,6`; no missing, duplicated, or substituted digit. | PASS |
| Chinese figure labels | All titles, annotations, axis label, and caption glyphs are intact; no tofu squares or missing strokes at nearest8x. | PASS |
| Caption label | `图 35.5` is correctly rendered and visually distinct from the caption body. | PASS |

GLYPH_CODEPOINT_PASS=true
MISSING_OR_TOFU_COUNT=0
WRONG_CODEPOINT_COUNT=0
