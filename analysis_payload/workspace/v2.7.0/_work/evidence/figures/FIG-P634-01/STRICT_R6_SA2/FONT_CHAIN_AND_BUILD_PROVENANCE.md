# FIG-P634-01 R6 local build and font-chain provenance

## Candidate status

This directory contains an SA2-local candidate build only.  It is not the root-authorized whole-book PDF and cannot substitute for the next official rebuild or independent SA1/SA3 validation.

## Build inputs and isolation

- Business source: `fig_v5_c04_coordinate_sweep.tex` (the only edited business file).
- Evidence-only wrappers: `local_standalone.tex` and `local_page.tex`.
- Engine: `D:\texlive\2026\bin\windows\lualatex.exe`, two successful passes for each wrapper.
- Evidence-only build context uses junctions to the read-only project `common`, `styles`, `manifests`, and figure-source trees; all cache and build outputs remain under `STRICT_R6_SA2`.
- Final logs: `build/local_standalone.log` and `build/local_page.log` each say `Output written ... (1 page)`.  The second passes contain no fatal error, undefined reference, missing character, overfull box, or underfull box.  Remaining package/font-family redefinition warnings are project-stack initialization warnings and do not describe candidate layout failure.

## Direct render provenance

- `renders/local_page_300dpi.png`: direct Poppler render from `build/local_page.pdf`, `2481 x 3508`, A4 at 300 dpi, no resize; it is the sole raw-ink geometry source.
- `renders/local_page_200dpi.png`: direct Poppler render, `1654 x 2339`, used only as a whole-page cross-check.
- `renders/local_standalone_300dpi.png`: direct Poppler render of the figure-only wrapper.
- `crops/figure_crop_300dpi_1x.png`, its grayscale counterpart, overlays, masks, and all critical-pair `raw_1x.png` files are pixel slices of the direct 300 dpi whole page.
- Every `8x` file is nearest-neighbour human-review material only and never enters a measurement.

## Ordinary source font chain

The figure source declares four ordinary bases and no scaling transform:

| Role | Source base |
|---|---:|
| default nodes, indices, status, arrow annotations | 9.6pt |
| card partition/sample text | 9.8pt |
| state formulas/card title | 10.0pt |
| panel title | 10.6pt |

The minimum ordinary source size is therefore `9.6pt`, above the required `9.5pt`.  Legal TeX scripts under the 10pt formula base use the project math ladder `\DeclareMathSizes{10}{10}{9}{9}` from `statlearnbook.sty` line 295 and are audited by their dedicated `>=15px` raw-ink gate, not misreported as ordinary 9pt text.

## Caption chain

1. The evidence wrapper uses the same `ctexbook` 11pt project stack.
2. TeX Live `size11.clo` lines 58–60 define `\small` as a 10pt font with 12pt leading.
3. `statlearnbook.sty` line 305 selects `font={small,stretch=1.12}` for captions.  Stretch changes leading, not glyph size.
4. Figure-source line 60 changes caption width only; line 61 does not scale or override the font.
5. Caption ordinary base is therefore 10.0pt.

## Embedded output fonts

`pdffonts` confirms every local-page font is embedded, subsetted, and Unicode-mapped:

- Noto Sans SC Bold — panel title and bold caption label.
- Noto Serif SC ExtraLight — visible CJK labels, card text, and caption body.
- STIX Two Math Regular — mathematical states, indices, and legal scripts.
- STIX Two Text Regular/Bold — Latin prose/context and automatic caption number.

The CJK serif/sans and STIX math/text families match the project font system; the candidate introduces no substitute font.
