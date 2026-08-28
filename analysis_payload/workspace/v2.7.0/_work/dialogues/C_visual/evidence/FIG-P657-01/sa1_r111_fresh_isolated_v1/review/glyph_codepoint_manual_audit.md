# Manual glyph and codepoint audit

Every item below was checked against the native 300 dpi crop, the relevant native1x/nearest8x ROI, and `glyph_codepoints_raw.tsv`.

- `T01 PASS` — “先验族” has three complete CJK glyphs; no tofu or substitution.
- `T02 PASS` — “Dirichlet分布” is spelled exactly; Latin letters and both CJK glyphs render cleanly.
- `T03 PASS` — “Beta分布” is spelled exactly and has intact mixed-script spacing.
- `T04 PASS` — the PDF maps mathematical italic K to U+1D43E and keeps ASCII equals/digit 2.
- `T05 PASS` — “似然族” has three intact CJK glyphs.
- `T06 PASS` — “多项分布” has four intact CJK glyphs.
- `T07 PASS` — “二项分布” has four intact CJK glyphs.
- `T08 PASS` — the second K=2 line again uses U+1D43E with the correct equals and digit.
- `T09 PASS` — “单次试验” has four intact CJK glyphs.
- `T10 PASS` — “类别分布” has four intact CJK glyphs.
- `T11 PASS` — the PDF maps mathematical italic N to U+1D441 and keeps the correct `=1` suffix.
- `T12 PASS` — “Bernoulli分布” is spelled exactly; neither Latin nor CJK glyphs are missing.
- `T13 PASS` — the full line is exactly `𝐾=2,𝑁=1`; comma, equals signs, and digits are all present.
- `T13A PASS` — the isolated `𝐾=2` substring contains U+1D43E, U+003D, U+0032.
- `T13B PASS` — the isolated `𝑁=1` substring contains U+1D441, U+003D, U+0031.
- `T14 PASS` — the upper “特殊情形” label has four correct CJK glyphs.
- `T15 PASS` — the middle “特殊情形” label has the same correct sequence.
- `T16 PASS` — left vertical-edge `𝑁=1` uses the expected mathematical N codepoint.
- `T17 PASS` — right vertical-edge `𝑁=1` uses the same expected codepoints.
- `T18 PASS` — bottom-edge `𝐾=2` uses the expected mathematical K codepoint.
- `T19 PASS` — legend “共轭” contains the correct U+5171/U+8F6D glyphs.
- `T20 PASS` — legend “特殊情形” is complete and readable at both native1x and nearest8x.
- `T21 PASS` — caption label is exactly “图34.3”; digits and punctuation are intact.
- `T22 PASS` — caption line 1 contains the exact distribution names Beta and Dirichlet with no wrong Latin letters.
- `T23 PASS` — caption line 2 contains Bernoulli and the complete concluding warning; no missing CJK glyph or punctuation.

Overall glyph/codepoint decision: `PASS`; missing-glyph, tofu, wrong-codepoint, and accidental-symbol counts are all zero.

