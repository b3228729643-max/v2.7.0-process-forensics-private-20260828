# FIG-P634-01 R6 SA2 evidence index

## Primary reports

- `FIG-P634-01-SA2-STRICT-R6.md` — local repair disposition and gate summary.
- `SOURCE_DIFF_AND_SEMANTIC_PRESERVATION.md` and `source_diff.patch` — exact change set and semantic mapping.
- `FONT_CHAIN_AND_BUILD_PROVENANCE.md` — engine, render, font, and caption-chain proof.
- `VISUAL_COORDINATION_REVIEW.md` — whole-page/figure/grayscale/font-coordination review.
- `MATH_TEXT_CONSISTENCY.md` — formula, alt, node, card, and caption agreement.

## Machine evidence

- `audit_summary.json`, `machine_end_check.json`.
- `machine_terminal_check.csv`, `.json`, and `.md`.
- `complete_object_manifest.csv`.
- `raw_char_measurements.csv`, `after_pixel_measurements.csv`, `after_font_audit.csv`.
- `same_class_ratio_audit.csv`, `role_ratio_audit.csv`, `cross_panel_role_audit.csv`.
- `all_pairs_overlap_clearance.csv`, `after_overlap_report.csv`, `edge_clip_audit.csv`.
- `targeted_EL035_clearance.csv`.
- `masks/independent_raw_masks_registry_v2.npz`.

## Visual evidence

- `renders/local_page_300dpi.png`, `renders/local_page_200dpi.png`, `renders/local_standalone_300dpi.png`.
- `crops/figure_crop_300dpi_1x.png`, `crops/figure_crop_grayscale_300dpi_1x.png`, `crops/figure_crop_8x_nearest_review.png`.
- `overlays/text_graphics_measurement_overlay_300dpi_1x.png`.
- `critical_pairs/EL035_script_to_card1_border/*` and `critical_pairs/literal_j_to_card1_border/*`.
- `critical_pairs/auto_*/*` for all near-gate separated-mask witnesses.

## Reproducibility assets

- `scripts/audit_fig_p634_r6_local.py`.
- `local_page.tex`, `local_standalone.tex`, and final build logs/PDFs under `build/`.

Every result in this index is a local SA2 candidate artifact.  None is an official whole-book acceptance artifact.
