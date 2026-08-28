# Mathematical and textual semantic audit

The visible gray sample series represents

`U=(0.8,0.1,0.7,0.4)` and `h(U_i)=U_i^2=(0.64,0.01,0.49,0.16)`.

The blue running means are independently recomputed as

- `m_1=0.64`;
- `m_2=(0.64+0.01)/2=0.325`;
- `m_3=(0.64+0.01+0.49)/3=1.14/3=0.38`, displayed as `.380`;
- `m_4=(0.64+0.01+0.49+0.16)/4=1.30/4=0.325`.

Thus the curve genuinely decreases, increases, then decreases. The labels `↓ 下降`, `↑ 上升`, and `↓ 再下降` agree with the plotted regression. The dashed line `真值 1/3` is the correct value of `E[U^2]` for a uniform variable. The formula, all four sample squares, all four blue means, numeric annotations, axes, caption, and preceding chapter sentence agree. `.380` is numerically identical to `0.38` and is positioned with clear separation above the third blue mean. No wrong codepoint, missing symbol, semantic inversion, or caption/plot mismatch is present.

Manual semantic conclusion: `MATH_TEXT_SEMANTICS_PASS=true`.
