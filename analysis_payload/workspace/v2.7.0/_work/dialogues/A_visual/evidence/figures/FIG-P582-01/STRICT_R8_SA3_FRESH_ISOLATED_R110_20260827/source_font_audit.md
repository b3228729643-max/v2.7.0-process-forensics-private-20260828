# FIG-P582-01 R110 SA3 source font audit

- Source identity: `fig_v5_c02_running_mean.tex`, SHA-256 `989E12DFD1B7A7F58A7953F36A8E8F24427A56154EED33325262045C17583A57`.
- Global TikZ style: `font=\fontsize{9.5pt}{11.4pt}\selectfont`; no `scale`, `transform shape`, `resizebox`, `scalebox`, `tiny`, `scriptsize`, `footnotesize`, or `small` override occurs in the audited source.
- Tick labels: explicit `9.5pt / 11.4pt`; effective reader size `9.5pt`.
- Axis labels: explicit `9.6pt / 11.5pt`; effective reader size `9.6pt`.
- All five annotation/value node styles: explicit `9.5pt / 11.4pt`; effective reader size `9.5pt`.
- Formula `h(U_i)=U_i^2`: base formula inherits `9.5pt`; only TeX-natural subscript/superscript glyphs use the smaller derivative outlines and all remain at least 15 native pixels.
- Caption: the figure source does not locally override caption typography. The official-PDF trace records a `9.963pt` base caption, with `8.966pt` TeX-natural script traces for `U_i^2`; the base reader size therefore remains above `9.5pt`.
- Same-role source sizing: tick/value/annotation/formula base `max/min=1.000`; axis-title `max/min=1.000`; body cross-role maximum/minimum is `9.6/9.5=1.0105`; no source-size hard gate fails.

Manual source conclusion: `SOURCE_FONT_GATE=PASS`.
