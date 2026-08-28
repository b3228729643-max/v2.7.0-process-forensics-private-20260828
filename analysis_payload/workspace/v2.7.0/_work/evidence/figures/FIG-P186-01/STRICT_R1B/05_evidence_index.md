# Five-class evidence index

1. **Scope and standalone build:** `01_scope_and_standalone_build.md`, `build/source_standalone.tex`, `build/source_standalone.pdf`, `build/source_standalone_300dpi.png`.
2. **Official native render:** `renders/official_p200_300dpi.png` (physical PDF page 200; 2481 x 3508 at 300 dpi).
3. **Four-view and native ROI evidence:** `02_native_raster_and_views.md`, the `renders/` view files, and all `roi/*_native_1x.png` files.
4. **Native measurement evidence:** `metrics/native_color_components.csv`, `metrics/text_element_audit.csv`, `metrics/text_glyph_spans_native.csv`, `metrics/geometry_ledger_native.csv`, and `metrics/view_inventory.csv`.
5. **Semantic/page-fusion evidence and decision:** `04_semantic_and_page_fusion.md`, `metrics/semantic_recompute.csv`, and `FIG-P186-01-SA1-STRICT-R1B.md`.

The executable evidence scripts in `tools/` are retained so the raster crops and measurement tables can be regenerated only from the R1B official-page image. They neither read nor modify project source files.
