# FIG-P657-01 fresh isolated SA1 evidence index

## Authoritative inputs

- Official R111 full book: identity and hash recorded in `review/source_and_identity_audit.md`.
- Current main P657 source: identity, hash, line-level font/route audit, and R168 application recorded in the same report.
- Independently located target: physical PDF page 706, printed page 693, figure 34.3.

## Visual evidence actually opened

- `raw/page706_full_page_200dpi.png` — full-page integration at 200 dpi.
- `raw/page706_native300dpi.png` — authoritative unscaled 300 dpi page.
- `raw/figure_with_caption_native300dpi.png` — local figure plus complete two-line caption.
- `raw/standalone_figure_native300dpi.png` — local figure-only crop from the authoritative page, without resampling.
- `raw/standalone_figure_grayscale300dpi.png` — grayscale structure/hierarchy audit.
- `review/visible_object_denominator_overlay.png` — 18 internal object IDs over the local figure.
- `review/text_element_bbox_overlay_native300dpi.png` — all 25 measured text/substring IDs, including caption integration.
- `masks/text_foreground_mask_native300dpi.png`, `graphics_foreground_mask_native300dpi.png`, and `text_graphics_overlap_overlay_native300dpi.png` — separated native-pixel masks and zero-overlap overlay.
- Six critical native1x ROIs and their six nearest-neighbor 8x counterparts: top relations, bottom relations, legend, caption, Dirichlet/Beta glyphs, and categorical/Bernoulli glyphs.

## Numeric and manual ledgers

- `review/pixel_measurements_raw.csv` — automated measurements only; no manual verdict fields.
- `review/after_pixel_measurements.csv` — 25 individually authored manual decisions.
- `review/visible_object_denominator_raw.csv` and `visible_object_denominator.md` — 20-object frozen page-scoped denominator.
- `review/object_pair_geometry_raw.csv` — automated geometry for all 190 unordered pairs.
- `review/object_pair_manual_ledger.csv` — 190 individually authored manual pair decisions.
- `review/text_pair_pixel_overlap_raw.csv` — pairwise actual-ink intersections for independent text measurements; maximum 0 px.
- `review/glyph_codepoints_raw.tsv` and `glyph_codepoint_manual_audit.md` — extracted Unicode evidence and per-ID manual glyph/codepoint decisions.
- `review/after_overlap_adjudication.md` — manual zero-collision/zero-clip adjudication.
- `review/math_semantics_manual_audit.md` — six-node, seven-relation, legend, caption, and alt-text semantics.
- `review/geometry_and_readability_manual_audit.md` — clearances, line hierarchy, R168 readability judgment.
- `review/grayscale_and_page_integration_manual_audit.md` — grayscale and page integration.
- `review/after_visual_acceptance.md` — sealed local SA1 result.

## Result

`PASS — SA1_PASS_READY_FOR_FRESH_ISOLATED_SA3`

