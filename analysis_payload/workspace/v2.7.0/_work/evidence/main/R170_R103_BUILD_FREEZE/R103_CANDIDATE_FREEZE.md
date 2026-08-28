# R103 official candidate freeze

- Status: `OFFICIAL_R103_FROZEN`
- Frozen at: 2026-08-25 (Asia/Shanghai)
- Main branch: `v2.7.0/integration`
- Main commit: `f5971bdca5f25628d077594cdd8fd35dc9b895f5`
- Build invocation: exactly one `build_v2.7.0.ps1 -Engine lualatex -OutputDir src\build\strict_current_r103_fullbook -NoPublish`
- Build result: wrapper/build exit `0`; latexmk completed naturally; no retry or concurrent TeX invocation.
- Post-build TeX processes: `NONE` for latexmk/lualatex/luatex/luahbtex.

## Official PDF identity

- PDF: `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\build\strict_current_r103_fullbook\main_full.pdf`
- Pages: `817`
- Page size: `595.276 x 841.89 pt (A4)`
- Rotation: `0`
- PDF version: `1.7`
- Encrypted: `no`
- Suspects: `no`
- Bytes: `4,967,184`
- SHA-256: `9379A489E0C2A57A7DA670C98029BB27B3F1A385BF8E4C3BD14FE9B606AA0F23`
- Log bytes: `258,877`

## Mechanical gates

- TeX hard errors: `0`
- Undefined references/citations/control sequences: `0`
- Duplicate definitions/destinations: `0`
- Missing characters: `0`
- Memory/capacity failures: `0`
- Overfull hbox/vbox: `0`
- Underfull hbox/vbox: `0`
- Main index: `731 accepted / 0 rejected / 0 warnings`
- Symbols index: `355 accepted / 0 rejected / 0 warnings`
- Embedded math fonts confirmed by `pdffonts`: IBM Plex Math, Libertinus Math, Mezenets Unicode (`emb=yes`, `sub=yes`, `uni=yes`).

The build log's luaotfload database-reload message about initially not finding an IBM Plex Math filename is not a final missing-font condition: the build completed successfully and the resulting PDF contains the embedded IBM Plex Math font shown above.

## Incremental visual gate

Because R103 differs from the last full-book baseline only by the integrated P602 and P654 figure-source changes, the lean incremental visual gate covered both target pages and their immediate neighbors. All six rendered pages passed for legibility, real clipping/overlap, glyph correctness, relation/formula semantics, and visibly gross imbalance:

- P602: physical pages `652, 653, 654`; target page `653` PASS.
- P654: physical pages `702, 703, 704`; target page `704` PASS.
- Render evidence: `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\evidence\main\R170_R103_BUILD_FREEZE\visual`

Per Revision 168, micro typography ratios, peer-taxonomy minutiae, font metadata microdifferences, and 1--2 px raster differences are advisory only. None of the hard font, semantic, geometry, clipping, or overlap gates failed.

## Routing

R103 is the sole official candidate for the next fresh isolated role chain:

- `FIG-P602-01`: fresh isolated SA1 on R103; PASS routes only to a different fresh isolated SA3.
- `FIG-P654-01`: fresh isolated SA1 on R103; PASS routes only to a different fresh isolated SA3.

No source edit, new TeX build, central inventory transition, or final-book PASS may be inferred from this freeze alone.
