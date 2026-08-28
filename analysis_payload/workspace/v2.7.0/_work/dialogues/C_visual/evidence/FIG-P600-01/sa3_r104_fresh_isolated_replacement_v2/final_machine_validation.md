# Final machine validation

- MACHINE_VALIDATION_PASS: `true`
- CHECK_COUNT: `28`
- FAILED_CHECKS: `NONE`

| Check | Pass | Detail |
|---|---|---|
| object_count_unique | true | `{"count":23,"unique":23}` |
| object_masks_nonempty | true | `{"empty":0}` |
| object_mask_files | true | `{"expected":23}` |
| all_pairs_coverage | true | `{"actual":253,"expected":253}` |
| machine_pair_fail_zero | true | `{"fail_count":0}` |
| manual_pair_coverage | true | `{"actual":253,"expected":253}` |
| manual_pair_fail_zero | true | `{"nonpass":[]}` |
| critical_coverage_assets | true | `{"machine":15,"manual":15}` |
| critical_manual_complete | true | `{"rows":15}` |
| glyph_count_unique_nonempty | true | `{"count":197,"unique":197}` |
| glyph_assets | true | `{"glyph_masks":197,"glyph_8x":197,"sheets":17}` |
| manual_glyph_coverage | true | `{"actual":197,"expected":197}` |
| manual_glyph_complete | true | `{"rows":197}` |
| legacy_advisory_counts | true | `{"legacy_fail":30,"punct_calibration":16}` |
| drawing_coverage | true | `{"machine":18,"manual":18,"math_rules":0}` |
| drawing_manual_pass | true | `{"rows":18}` |
| clip_coverage_zero | true | `{"machine":23,"manual":23}` |
| view_role_coverage | true | `{"rows":32}` |
| r168_font_hard_gate | true | `{"rows":8}` |
| math_content_semantics | true | `{"rows":12}` |
| native_view_dimensions | true | `{"full_page_300dpi.png":[2481,3508],"full_page_200dpi.png":[1654,2339],"figure_crop_300dpi.png":[2000,888],"standalone_300dpi.png":[1435,740],"grayscale_300dpi.png":[2000,888],"machine_native_full_page_300dpi.png":[2481,3508]}` |
| required_FINAL_REPORT.md | true | `{"bytes":6931}` |
| required_SA3_CARD.md | true | `{"bytes":991}` |
| required_SA3_CARD.json | true | `{"bytes":682}` |
| required_RESULT.txt | true | `{"bytes":469}` |
| required_after_text_measurement_overlay_300dpi.png | true | `{"bytes":195850}` |
| portable_names_no_colon | true | `[]` |
| cache_pyc_zero | true | `[]` |
