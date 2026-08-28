# FIG-P556-02｜SA1 machine consistency check

`CHECK_STATUS: PASS` verifies 21/21 required artifacts, 343/343 all-pair rows and 12 complete critical sets. It does not override `FIGURE_RESULT: FAIL`.

Canonical grid: full physical PDF page direct 300dpi, then pixel-slice crop/standalone; no resize. Missing required artifacts: `[]`. For every critical pair, native original/A-mask/B-mask/overlap/overlay and raw/overlay/overlap nearest-neighbour 8x files all exist; missing paths: `[]`.

Read-only revalidation also confirms source-font failures=10, pixel-height failures=17, same-class raw-H failures=36 (34 glyph rows + 2 cross-panel role/script rows), role-ratio failures=3, all-pair overlap sum=0 and clip sum=0.
