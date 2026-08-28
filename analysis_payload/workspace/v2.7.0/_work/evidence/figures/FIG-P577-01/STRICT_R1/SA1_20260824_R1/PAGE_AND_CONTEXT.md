# FIG-P577-01 — official-page and context lock

- Frozen candidate: `main_full.pdf`, SHA-256 `CA76A41334ACA3587B9FE742C3D3B8BCBE598A505E58929C82B478FFF4F6A7A3`.
- Page localisation was redone from the frozen PDF: the unique caption anchor `图 31.4 包络满足 p≤cq（几乎处处）` and the in-figure title `合法包络与含边界接受门` occur on **physical PDF page 625**, printed page **612**. No historical page number was reused.
- Native page box: `595.276 × 841.890 pt` (A4); direct Poppler native 300-dpi rendering: `2481 × 3508 px`. Figure crop page coordinates: `[216,241]–[2272,1859]`; standalone plot `[216,241]–[2272,1767]`. No raster resize was used. `full_page_300dpi.png`, `figure_crop_300dpi.png`, and `standalone_300dpi.png` are direct evidence.
- Figure source read-only lock: `fig_v5_c02_rejection_envelope.tex`, SHA-256 `D33DFF3F8FB7E7E2830C9B2D6DD34CE4E87184EBF8BF0710DF240B4BB71D6B27`.

## Caption/body agreement checked

The adjacent page source `讲义源码/合并总册/v260_FIG-P577-01_page.tex` introduces exactly the same `p(y)=6y(1-y)`, `q(y)=1`, `c=1.6=8/5`, boundary-inclusive gate, acceptance rate `5/8`, average proposals `8/5`, accepted circle `(1/4,4/5)`, and ordinarily rejected triangle `(3/4,27/20)`. Chapter source `chapters/V5-C02.tex:351–354` additionally states that the triangle remains below the legal envelope. The printed caption agrees with that account.

## Source-font / source-order facts

- Base TikZ and axes text are declared `9.6pt`, title `10.2pt`, and no `resizebox`, `scalebox`, or graphics transform appears. Caption is rendered from the project `small` caption rule and recorded as `10.0pt` effective in the semantic audit.
- White label/callout fills are real source objects. Their pre-vector / final white halo / final-visible object evidence is preserved in `halos/H01_*` through `H06_*`; no hidden pixel beneath a white cover was synthesized.
- One PDF-extracted source candidate, the y=`0.4` tick, is fully covered by the later opaque accepted-callout fill. `occlusion_ledger.csv` records it as non-final-visible rather than borrowing the later `U=` pixels as its mask.
