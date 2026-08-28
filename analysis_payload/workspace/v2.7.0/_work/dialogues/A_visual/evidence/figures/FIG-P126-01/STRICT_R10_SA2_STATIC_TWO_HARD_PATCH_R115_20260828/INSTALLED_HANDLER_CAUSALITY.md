# Installed handler causality

This is a static-only analysis; no TeX engine was invoked.

- `D:\texlive\2026\texmf-dist\tex\generic\pgf\libraries\pgflibraryplotmarks.code.tex`, 14,526 bytes, SHA256 `C65E39FFD0C7FAC8FABF7A51A47ACD9E11BAC5B70DCE14347B1C78887C81151F`, lines 146--153 declares plot mark `-` as a horizontal path from `+\pgfplotmarksize` to `-\pgfplotmarksize`, hence a total bar length of `2*mark size=3.6pt`.
- `D:\texlive\2026\texmf-dist\tex\generic\pgfplots\pgfplots.code.tex`, 486,348 bytes, SHA256 `C4245419E40E5058320853728F6BB93521C153D89F1FBF185CE8793D067C1CA6`, lines 2007--2025 defines the default line legend and its fixed coordinates 0, 0.3, and 0.6cm. The plot specification is applied after the handler defaults, so `only marks,mark repeat=1,mark phase=1` statically selects all three points and suppresses the continuous connector.
- Center spacing is `0.3cm=8.503937pt`. With 1.8pt half-length, adjacent bars leave a predicted blank of `8.503937-3.6=4.903937pt`, about `20.433px` at 300dpi.

The legend part therefore has a positive static causal direction and must still be verified from a new PDF.

The digit-6 part does not pass static geometry. Moving the existing node and its opaque background upward by 5pt predicts 8.200px bbox clearance from q4 marker C016, but the translated background overlaps digit-4 object T009 by 25.619449pt^2 and covers 88 currently dark digit-4 pixels. The current exact coordinate scope therefore trades one hard defect for a predicted new occlusion.
