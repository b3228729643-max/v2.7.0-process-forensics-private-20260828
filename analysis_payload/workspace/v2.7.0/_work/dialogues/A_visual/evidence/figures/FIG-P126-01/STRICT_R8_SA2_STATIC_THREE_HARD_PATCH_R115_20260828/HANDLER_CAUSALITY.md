# Legend handler causality

Main R514 binds the installed pgfplots behavior: `/pgfplots/line legend` draws the normal 0--0.6 cm sample and the earlier custom key-definition supplied through `\addlegendimage` did not replace the rendered handler.

This patch therefore does not redefine `legend image code`. It deliberately uses the actual default line-legend path and gives that path a robust dash pattern with butt caps. Over 0.6 cm, the `.06cm on / .09cm off` period yields visible runs at approximately `[0,.06]`, `[.15,.21]`, `[.30,.36]`, and `[.45,.51]` cm, with full 0.09 cm gaps. At 300 dpi, each designed gap projects to about 10.63 pixels, materially above antialiasing closure.

The x1 legend declaration and all four teal trajectory dash declarations are unchanged.
