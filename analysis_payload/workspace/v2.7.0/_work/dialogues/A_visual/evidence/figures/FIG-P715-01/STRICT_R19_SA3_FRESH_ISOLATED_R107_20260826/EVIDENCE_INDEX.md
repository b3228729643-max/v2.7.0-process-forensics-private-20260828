# Evidence index

## Identity and primary views

- `candidate_identity.md`: frozen inputs, independently located page, crops, caption boundary, N/C construction, and 43-drawing ownership.
- `machine_summary.json`: machine-freeze summary.
- `full_page_200dpi.png`, `full_page_300dpi.png`: whole-page context.
- `figure_crop_300dpi.png`: two panels plus caption.
- `standalone_300dpi.png`: figure body only.
- `grayscale_300dpi.png`: grayscale visual check.
- `after_text_measurement_overlay_300dpi.png`: glyph/drawing coverage overlay.

## Machine evidence

- `after_pixel_measurements.csv`: 255-glyph native-pixel measurements and mask linkage.
- `drawing_path_inventory.csv`: all 43 visible drawing/path objects.
- `all_unordered_pairs.csv`: 44,253 frozen unordered pairs.
- `after_overlap_report.csv`: overlap/clearance classification.
- `critical_relationships.csv`: eight final hard/structural relation records.
- `four_side_clip_metrics.csv`: panel/matrix/focus border side metrics.
- `math_rule_inventory.csv`: explicit rule inventory.
- `after_font_audit.csv`, `element_pixel_role_metrics.csv`, `pdf_font_metadata.csv`: advisory typography metadata and role measurements.
- `masks/`, `glyph_views/`, `drawing_views/`: native object masks and per-object review tiles.
- `contact_sheets/glyphs/`: eight glyph sheets.
- `contact_sheets/drawings/`: two drawing sheets.
- `critical_relations/`: eight relationship images.

## Human evidence

- `manual_glyph_reviewer_ledger.csv`: 255 hand-authored per-glyph decisions.
- `manual_drawing_reviewer_ledger.csv`: 43 hand-authored per-drawing decisions.
- `manual_relation_reviewer_ledger.csv`: eight hand-authored relation decisions.
- `manual_view_role_ledger.csv`: actual-open ledger for four views, ten sheets, and eight relationships.
- `after_visual_acceptance.md`: R168-aware visual review and final booleans.
- `after_overlap_adjudication.md`: clearances and intended drawing relationships.
- `semantic_and_random_walk_audit.md`: graph, matrix, transpose, and Markov semantics.
- `SA3_INDEPENDENT_REVIEW.md`: consolidated independent adjudication.
- `preseal_validation.md`: final machine/manual reconciliation.
- `RESULT.txt`: final PASS decision consistent with all ledgers.

## Reproducibility

- `machine_build.py`: machine-only evidence builder. It does not generate or overwrite any manual reviewer field, manual boolean, manual note, or human decision.
- `id_safe_filename_map.csv`: stable object-to-file mapping.
- `physical_page_765_text_extract.txt`: local target-page text used for independent identification.

The two final manifests cover the same common payload and exclude only themselves and `WRITE_STOPPED` as the three seal controls.
