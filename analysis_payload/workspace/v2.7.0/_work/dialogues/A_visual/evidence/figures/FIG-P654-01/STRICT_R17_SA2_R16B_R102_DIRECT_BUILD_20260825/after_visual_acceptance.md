# FIG-P654-01 R17 visual acceptance

Status: **LOCAL_SA2_FAIL_NEEDS_SOURCE_R3**.

The one permitted direct LuaLaTeX invocation succeeded and produced a new one-page A4 PDF. The evidence was rebuilt from that PDF: 93 glyphs + 21 graphics = 114 objects, with all 6,441 unordered pairs and 173 critical pairs closed. All five required views, five glyph sheets, six graphic sheets, four all-pair matrices, ten critical-pair contact sheets, and the six raw failure bundles were actually opened.

R16B fixed the original trial `n`: G0005 is now 24px, meets the 22px absolute minimum, and has ratio 1.0000. Layout, semantics, clipping, masks, grayscale readability, and visible font harmony remain acceptable.

The round still fails hard gates:

- G0040/G0059/G0064 are true mathematical plus glyphs, each 26px against a frozen group median of 24px: 1.083333 > 1.08.
- G0065 is the authoritative literal `N`, 27px against 24px: 1.125 > 1.08.
- P06198 and P06219: external label glyphs `应`/`用` have 0px native clearance to the D0009 node border, below the 3px gate.
- The same frozen source formula role spans 11.6pt to 9.5pt: ratio 1.221053 and absolute difference 2.1pt, failing the 1.03 / 0.25pt source gates.

Four raw graphic-graphic contacts (P06240/P06261/P06285/P06347) were individually opened and adjudicated PASS because they are the intended line-to-node endpoints. No illegal overlap remains after that semantic adjudication.

No commit, fresh SA1, fresh SA3, LOCAL PASS, or A_LOCAL_PASS is authorized.
