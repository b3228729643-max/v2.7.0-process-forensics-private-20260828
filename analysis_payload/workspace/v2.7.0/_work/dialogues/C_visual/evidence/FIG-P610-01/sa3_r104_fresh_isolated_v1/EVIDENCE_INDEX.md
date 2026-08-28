# FIG-P610-01 / R104 / fresh isolated SA3 evidence index

- Handoff: `C-FIG-P610-01-R104-SA3-FRESH-ISOLATED-V1`
- Reviewer instance: `/root/sa3_fig_p610_r104_fresh_isolated`
- Reviewer transparency: `reviewer_type=AI_SA3_VISUAL_REVIEW`, `human_certification=false`
- Local result: `C_LOCAL_PASS_ONLY`; main-thread/root acceptance remains pending.
- Independent page mapping: source label `fig:V5-C03-rejection-vs-mh` and caption uniquely map to official R104 physical page 662, printed page 649, Figure 32.10.
- Fresh denominators: 77 non-whitespace glyph IDs, 17 text/formula element IDs, 21 non-text semantic object IDs, 38 total actual objects, 703/703 unordered object pairs, 26 individually adjudicated closest pairs, 17 reader-element clip rows, 13 manually viewed render variants.

## Principal manual records

- `SA3_RESULT.md`: SA3 template result, R168 hard-gate matrix, advisories, and local-only routing.
- `manual_object_review.csv`: 38/38 actual objects, individually reviewed.
- `manual_glyph_review.csv`: 77/77 non-whitespace glyph IDs, individually reviewed for code point, shape, and actual legibility.
- `manual_critical_pair_review.csv`: all 26 pairs with raw blank clearance <=20 px, individually adjudicated.
- `manual_clip_review.csv`: 17/17 reader text/formula elements.
- `manual_peer_role_review.csv`: peer-role and cross-panel comparisons.
- `manual_multiview_review.csv`: full page, figure, standalone, grayscale, overlays, and focused 1x/8x views actually examined.
- `manual_semantics_geometry_relations_review.md`: formula, geometry, relationship, object-content, caption, and adjacent-text hard gates.
- `after_overlap_adjudication.md`, `after_visual_acceptance.md`, `after_model_route.md`: canonical local records.

## Raw mechanical records

- `mechanical_measurement_metadata_raw.json`: page/raster identity and exact denominators.
- `glyph_inventory_raw.csv`, `text_element_measurements_raw.csv`, `graphic_object_inventory_raw.csv`, `actual_object_inventory_raw.csv`.
- `all_unordered_object_pairs_raw.csv`: exactly 703 unique `n choose 2` pair rows.
- `critical_and_required_pairs_raw.csv`, `peer_role_aggregates_raw.csv`, `clip_and_boundary_measurements_raw.csv`, `render_crop_inventory_raw.csv`.
- `masks/`: one isolated semantic foreground mask per each of the 38 actual objects.
- Canonical schema copies: `after_font_audit.csv`, `after_pixel_measurements.csv`, `after_overlap_report.csv`, and canonical render names.

## Render evidence

- Native whole page: `full_page_native_300dpi.png` (Poppler) and `full_page_fitz_reference_300dpi.png` (mask-aligned reference), plus `full_page_200dpi.png`.
- Figure/caption: `figure_crop_with_caption_native_300dpi.png`.
- Standalone-equivalent: `standalone_equivalent_native_300dpi.png`, grayscale counterpart, `standalone_1x_native_300dpi.png`, and nearest-neighbour 8x inspection view.
- Focused closest-region 1x/8x crops: right rejection connector, horizontal state arrows, and right note glyphs.
- Measurement overlays: object and glyph overlays plus text/graphic union masks.

`SEALED_MANIFEST.json` is generated only after all payload files are frozen. It explicitly excludes itself and `WRITE_STOPPED`. `WRITE_STOPPED` is created strictly last; after it is created, no file in this evidence root is written again.
