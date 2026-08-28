# Manual glyph and codepoint review

The current R115 vector text and the native/nearest-8x images were compared after observation. No missing glyph, tofu, wrong codepoint, substitution, or broken math delimiter was found inside the frozen figure/caption denominator.

- `ℒ` is U+2112 SCRIPT CAPITAL L and is consistently used for the ELBO.
- Mathematical italic `𝑝`, `𝑞`, `ℎ`, and `𝑤` extract and render as the intended variables.
- `≥` is U+2265 and `≤` is U+2264; both faces and directions match the source statement.
- The KL separator is a double norm bar `‖` and the posterior condition uses the intended single conditioning bar.
- E10 uses fullwidth slash `／` U+FF0F between the two Chinese alternatives; it is intact and not a missing-glyph box.
- Tick glyphs `0` through `6` are all distinct; `0` is not confused with capital O and `6` is not malformed.
- Caption tokens `ELBO`, `KL`, numerals, Chinese punctuation, and Figure label `图 35.5` are complete.
- The hollow square visible above the figure in the full-page view is the intentional proof-end QED symbol outside the frozen denominator, not tofu.

Manual verdict: `GLYPH_CODEPOINT_PASS=true`.
