# FIG-P580-01 SA3 blind R96 — identity and scope

## Isolation

This is a fresh SA3 review. Its evidence was created in this new directory only. The review used the authority Goal, `AGENTS.md`, the current candidate PDF, the current figure source, and the candidate's direct FLS identity. No prior FIG-P580-01 review, repair, root-acceptance evidence, inventory, or state file was read or used.

## Candidate identity

| Item | Verified value |
|---|---|
| Figure | `FIG-P580-01` / Fig. 31.6 |
| Candidate PDF | `v2.7.0/_work/source/v2.7.0/src/build/strict_current_r96_fullbook/main_full.pdf` |
| PDF SHA-256 | `8EED8765A4856C4C197262DEA06E283790FBA8DA906C70C26FC7BD56F6F7E5E8` |
| Physical PDF page / printed page | `628 / 615` |
| PDF pages | `813` |
| Current figure source | `v2.7.0/_work/source/v2.7.0/src/绘图源码/第05册_采样方法主题模型与图排序/V5-C02/fig_v5_c02_is_support.tex` |
| Source SHA-256 | `F0ECC9B28361A2AE73AF085A4958AD09F8F94575D789B8F776C55631FD45E161` |

The candidate's `main_full.fls` directly establishes the build linkage:

```text
3: INPUT ./main_full.tex
478: OUTPUT D:/Users/ASUS/Desktop/机器学习/v2.7.0/_work/source/v2.7.0/src/build/strict_current_r96_fullbook/main_full.pdf
657: INPUT d:/Users/ASUS/Desktop/机器学习/v2.7.0/_work/source/v2.7.0/src/build/strict_current_r96_fullbook/../../绘图源码/第05册_采样方法主题模型与图排序/V5-C02/fig_v5_c02_is_support.tex
```

## Native raster scope

The final candidate PDF itself was rasterized with `pdftoppm -r 300 -f 628 -l 628 -png -singlefile`; no post-render resize was used. The resulting full page is `2481 × 3508 px` (`02_native_render/page_628_full_300dpi.png`). The independently rendered 200 dpi full page is `02_native_render/page_628_full_200dpi.png`.

The audited figure-with-caption scope is `[100.0, 266.0, 505.0, 480.0]` PDF pt, mapping directly to native pixels `[416, 1108, 2105, 2001]`. The directly cropped current-PDF artifacts are:

- `02_native_render/figure_scope_with_caption_native_300dpi.png`
- `02_native_render/figure_body_isolated_native_300dpi.png`
- `02_native_render/figure_scope_grayscale_300dpi.png`

All coordinate and pixel assertions in the CSV ledgers refer to that 300 dpi native raster. 8× evidence is nearest-neighbour enlargement for human inspection only, never a measurement source.
