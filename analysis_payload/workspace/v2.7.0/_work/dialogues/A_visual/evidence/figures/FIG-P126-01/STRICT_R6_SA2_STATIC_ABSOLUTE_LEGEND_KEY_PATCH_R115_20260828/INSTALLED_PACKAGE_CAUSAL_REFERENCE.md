# Installed pgfplots causal reference

Exact installed file: `D:\texlive\2026\texmf-dist\tex\generic\pgfplots\pgfplots.code.tex`, 486,348 bytes, SHA-256 `C4245419E40E5058320853728F6BB93521C153D89F1FBF185CE8793D067C1CA6`.

The installed implementation defines `/pgfplots/line legend` at lines 2007--2027. Its `/pgfplots/legend image code/.code` handler draws a continuous sample through `(0cm,0cm)`, `(0.3cm,0cm)`, `(0.6cm,0cm)` (lines 2021--2025).

At lines 5794--5797, `\pgfplots@addlegendimage@opt` calls:

`\pgfplots@rememberplotspec[#1]{/pgfplots/every axis plot,#2,/pgfplots/.cd,/pgfplots/every axis plot post}`

Thus the options supplied as `#2` are parsed before the later `/pgfplots/.cd`. The former relative key `legend image code/.code` was not anchored to the `/pgfplots/` family at that position, leaving the default continuous line-legend handler in effect. The new absolute key `/pgfplots/legend image code/.code` addresses the intended handler directly and is expected to replace the default with the already-frozen four-subpath drawing code.

This is a static causal prediction only. It is not rendered evidence and cannot establish PASS before an explicitly authorized fresh build.
