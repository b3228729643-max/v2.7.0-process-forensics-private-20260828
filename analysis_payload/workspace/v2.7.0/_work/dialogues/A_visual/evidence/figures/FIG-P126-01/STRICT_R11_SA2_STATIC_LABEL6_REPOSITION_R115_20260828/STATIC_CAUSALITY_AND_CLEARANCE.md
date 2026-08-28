# R11 static causality and clearance

No TeX engine was invoked. The projection uses the R9 native 300dpi render only as a frozen geometric reference.

The x2 legend mechanism remains unchanged from the accepted R10 direction. Installed `pgflibraryplotmarks.code.tex` lines 146--153 defines mark `-` as a 2×mark-size horizontal bar; installed `pgfplots.code.tex` lines 2007--2025 defines three default line-legend points at 0, 0.3, and 0.6cm and applies the plot specification after its defaults. Thus `only marks,mark repeat=1,mark phase=1,mark size=1.8pt` predicts three disconnected 3.6pt bars with 4.903937pt/20.433px internal blanks.

For the label, the new `anchor=south,yshift=4pt` uses the q6 axis point (293.136020pt,129.986990pt). Preserving the current glyph/background dimensions predicts:

- digit 4: minimum glyph/background bbox gap 6.969595pt (29.040px);
- q4 marker: 5.350495pt (22.294px);
- q6 marker: glyph gap 0.951941pt (3.966px), background gap 2.092126pt (8.717px);
- label 5: 13.072719pt (54.470px);
- label 7: 9.139944pt (38.083px);
- horizontal q5→q6 arrow: 3.103086pt (12.930px);
- vertical q6→q7 arrow: 2.844871pt (11.854px).

The opaque background intentionally erases 73 light-gray contour pixels and zero dark text/axis/arrow/marker pixels. After applying that authorized protection in the static projection, the nearest remaining foreign visible ink has center-distance 9.433981px and 8 complete blank pixels. The native1x and nearest8x projection were actually opened; no predicted label/marker/arrow/other-label contact remains. This is still static-only and requires a new PDF for PASS.
