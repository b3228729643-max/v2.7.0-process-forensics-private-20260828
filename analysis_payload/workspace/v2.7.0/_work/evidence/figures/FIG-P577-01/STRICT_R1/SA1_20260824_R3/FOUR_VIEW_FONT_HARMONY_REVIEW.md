# R95 four-view font and hierarchy review

SA1 manually opened the full-page 200dpi, figure crop 300dpi, standalone 300dpi and grayscale 300dpi views. The following is a per-panel/role/script review, informed by the separately measured D/E table rather than a global boolean. The opaque-ground curve occlusion failures are visual geometry failures, not a font-harmony failure.

| Panel | Role | Glyphs | Script/style reviewed | Colour + grayscale + page integration |
|---|---|---:|---|---|
| PANEL_01 | ANNOTATION | 112 | CJK_FULLWIDTH/BASE_VISIBLE, DIGIT/BASE_VISIBLE, DIGIT/NATURAL_MATH_STYLE, MATH_OPERATOR_COMPONENT/BASE_VISIBLE, MATH_OPERATOR_COMPONENT/NATURAL_MATH_STYLE | PASS |
| PANEL_01 | AXIS_LABEL | 5 | CJK_FULLWIDTH/BASE_VISIBLE, MATH_OPERATOR_COMPONENT/BASE_VISIBLE | PASS |
| PANEL_01 | CAPTION | 50 | CJK_FULLWIDTH/BASE_VISIBLE, DIGIT/BASE_VISIBLE, MATH_OPERATOR_COMPONENT/BASE_VISIBLE | PASS |
| PANEL_01 | FORMULA_BLOCK | 129 | CJK_FULLWIDTH/BASE_VISIBLE, DIGIT/BASE_VISIBLE, DIGIT/NATURAL_MATH_STYLE, LOWERCASE_GREEK/BASE_VISIBLE, MATH_OPERATOR_COMPONENT/BASE_VISIBLE, MATH_OPERATOR_COMPONENT/NATURAL_MATH_STYLE | PASS |
| PANEL_01 | LEGEND | 16 | CJK_FULLWIDTH/BASE_VISIBLE, DIGIT/NATURAL_MATH_STYLE, MATH_OPERATOR_COMPONENT/BASE_VISIBLE | PASS |
| PANEL_01 | PANEL_TITLE | 11 | CJK_FULLWIDTH/BASE_VISIBLE | PASS |
| PANEL_01 | TICK | 22 | CJK_FULLWIDTH/BASE_VISIBLE, DIGIT/BASE_VISIBLE, DIGIT/NATURAL_TEX_SCRIPT, MATH_OPERATOR_COMPONENT/BASE_VISIBLE | PASS |

All visible source bases are 9.6pt or the 10.2pt title; natural TeX scripts have an actual eligible base and pass their 15px floor. No role is visually oversized, undersized, discordant, or dependent on colour alone.
