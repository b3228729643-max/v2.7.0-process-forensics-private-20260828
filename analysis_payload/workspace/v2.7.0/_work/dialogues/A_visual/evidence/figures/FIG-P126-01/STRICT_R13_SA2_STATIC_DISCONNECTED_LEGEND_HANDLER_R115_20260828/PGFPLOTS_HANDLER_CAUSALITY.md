# Installed pgfplots handler causality

Installed primary source:

- path: `D:\texlive\2026\texmf-dist\tex\generic\pgfplots\pgfplots.code.tex`
- bytes: 486,348
- SHA-256: `C4245419E40E5058320853728F6BB93521C153D89F1FBF185CE8793D067C1CA6`

Relevant installed-source chain:

1. Lines 2007--2030 define and install the default `/pgfplots/line legend`; its handler draws one plot path through `(0cm,0cm)`, `(0.3cm,0cm)`, and `(0.6cm,0cm)`.
2. Lines 5794--5796 show that `\addlegendimage{...}` stores its argument `#2` in the remembered plot specification.
3. Lines 5843--5848 define the current plot style from that stored specification, enter the `current plot style` scope, and only then invoke `/pgfplots/legend image code/.@cmd`. The installed comment on line 5847 explicitly states that this scope allows plot styles to change `legend image code`.
4. Line 11488 applies the stored plot specification with `\pgfplotsset{/tikz/draw,#1}` when the current plot style is activated.

The new adjacent style `p126 x2 disconnected legend` therefore installs `/pgfplots/legend image code/.code` at legend-image generation time before line 5848 invokes it. Its body contains four independent `\draw` commands and no default continuous plot path. The x1 legend and global/default line-legend handler are unchanged.

This is a static installed-package causality proof only; the rendered pixels must be verified from a separately authorized new PDF.
