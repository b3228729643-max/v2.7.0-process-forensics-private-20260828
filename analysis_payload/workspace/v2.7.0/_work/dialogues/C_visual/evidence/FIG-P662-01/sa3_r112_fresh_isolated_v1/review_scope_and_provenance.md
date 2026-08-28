# Review scope and provenance

HANDOFF_ID: `C-FIG-P662-01-R112-SA3-FRESH-ISOLATED-V1`  
UID: `FIG-P662-01`  
Role: fresh isolated read-only SA3  
Model route: `gpt-5.6-sol`, reasoning `xhigh`

## Whitelisted inputs actually used

1. Frozen official R112 full-book PDF: `main_full.pdf`, 4,967,100 bytes, SHA-256 `D4B4DDF5F127D107FB66BF2805F4637D39CDB861F7CBB47BB2CDBB72E4E28FA2`.
2. Current main P662 source: `fig_v5_c05_gamma_normalization.tex`, 3,588 bytes, SHA-256 `B5232526402FEF6735DC3F9C07B418D7BF49E0D8C17EAEFB82A54B450B63113E`.
3. Root `GOAL.md` and its directly referenced current strict pixel/SA3 protocol.
4. Current V5-C05 chapter context around the figure's label plus its current `figure_sources.json` entry.

No SA1, reseal, SA2, prior P662 evidence/role/root/report/handoff/conclusion/metric/acceptance/path, other UID, Main state/history/acceptance/inventory, Git history, chat history, or agent/task status/history was read.

## Independent location and subject determination

The caption phrase and current label were searched directly in frozen R112 text extraction. The unique match was then rendered from the PDF itself and visually confirmed against the source. The independently located PDF page index is 710; the printed page number visible in the frozen page is 697. No prior-role locator was used.

The subject is the Gamma-normalization construction of a Dirichlet random vector: independent common-rate Gamma variables are summed, each is divided by the total, the resulting positive components sum to one, the total is independent of the normalized vector, and the two-component case is Beta.

## Execution boundary

- PDF and source remained read-only.
- No TeX engine, `latexmk`, compilation, build, source edit, Git write, central state edit, inventory edit, process-management action, or second UID/role/root was used.
- All generated evidence is derived from the frozen PDF page at native 300 dpi or from machine-only analysis of those native pixels.
- Manual decisions were authored only after their corresponding final views were opened.
- Active policy is R168: typography size, outline, pixel ratio, taxonomy, and tiny raster differences alone are advisory; hard failure requires a native defect in the enumerated hard-gate classes.
