# FIG-P580-01 R2C SA2 machine terminal check

Result: `SA2_LOCAL_PASS_AWAIT_ROOT_OFFICIAL_BUILD`

This is a local SA2 result awaiting root official-build review; it is not root acceptance or final PASS.

## Hard closure

- 234 glyph contact decisions, 50 visual/harmony decisions, and 53 critical relation decisions are individually closed with no pending/unknown.
- 57 objects produce exactly 1,596 unique unordered pairs; all 300 graphic-graphic rows are assessed with 300 unique reasons.
- Graphic-graphic semantics: 48 pair-specific intentional connections = 25 native overlaps + 23 disjoint sub-3 px adjacencies; the remaining 252 rows are nonintentional.
- 445 required relations PASS; font/pixel/D/E/pair/relation/clip/coverage/missing-stroke/foreign-pixel failures are all zero.
- Minimum effective visible size is 9.60 pt; font size, weight, colour, grayscale, page fusion, and card/text congestion are manually PASS.

## Three no-exemption repair gates

- `PAIR_GR004_GR025`: overlap `0`; clearance `6.280110` px; required `3.000000` px; evidence `critical_relations/PAIR_GR004_GR025`; exact raw/A/B/intersection/overlay 1x/8x package PASS.
- `PAIR_GR020_GR022`: overlap `0`; clearance `5.000000` px; required `3.000000` px; evidence `critical_relations/PAIR_GR020_GR022`; exact raw/A/B/intersection/overlay 1x/8x package PASS.
- `PAIR_GR020_GR024`: overlap `0`; clearance `9.770330` px; required `3.000000` px; evidence `critical_relations/PAIR_GR020_GR024`; exact raw/A/B/intersection/overlay 1x/8x package PASS.

## Check matrix

| Check | Result | Detail |
|---|---|---|
| `write_stop_absent_before_finalizer` | PASS | "D:\\Users\\ASUS\\Desktop\\机器学习\\v2.7.0\\_work\\evidence\\figures\\FIG-P580-01\\STRICT_R2C_SA2_GRAPHIC_PAIR_REPAIR_R95_LOCAL_20260824\\WRITE_STOPPED.md" |
| `external_inputs_exist` | PASS | ["D:\\Users\\ASUS\\Desktop\\机器学习\\v2.7.0\\_work\\source\\v2.7.0\\src\\绘图源码\\第05册_采样方法主题模型与图排序\\V5-C02\\fig_v5_c02_is_support.tex", "D:\\Users\\ASUS\\Desktop\\机器学习\\v2.7.0\\_work\\source\\v2.7.0\\src\\讲义源码\\合并总册\\v260_FIG-P580-01_page.tex", "D:\\Users\\ASUS\\Desktop\\机器学习\\v2.7.0\\_work\\source\\v2.7.0\\src\\讲义源码\\合并总册\\v260_FIG-P580-01_standalone.tex", "D:\\Users\\ASUS\\Desktop\\机器学习\\v2.7.0\\_work\\evidence\\audits\\STRICT-GOAL-20260823\\STRICT_FIGURE_EVIDENCE_SCHEMA.md", "D:\\Users\\ASUS\\Desktop\\机器学习\\v2.7.0\\GPT_Pro_统计学习方法讲义_v2.7.0_Codex_Goal主提示词.md"] |
| `source_semantic_freeze` | PASS | {"axis_extension": true, "hatch_domain_unchanged": true, "p4_coordinate_unchanged": true, "p4_marker_size_unchanged": true, "qR_composite_dash": true, "qR_height_unchanged": true, "qR_phase": true} |
| `final_local_build_files` | PASS | {"build/page/v260_FIG-P580-01_page.fls": 47798, "build/page/v260_FIG-P580-01_page.log": 146350, "build/page/v260_FIG-P580-01_page.pdf": 69568, "build/standalone/v260_FIG-P580-01_standalone.fls": 47882, "build/standalone/v260_FIG-P580-01_standalone.log": 144216, "build/standalone/v260_FIG-P580-01_standalone.pdf": 40556} |
| `final_build_identity` | PASS | {"fls_mentions_business_source": true, "logs_ok": true, "page_bytes": 69568, "pdfs_newer_than_source": true, "standalone_bytes": 40556} |
| `core_exact_counts` | PASS | {"D_failure_count": 0, "E_failure_count": 0, "actual_unordered_pair_count": 1596, "clip_failure_count": 0, "contact_manifest_count": 234, "contact_sheet_count": 15, "critical_relation_package_count": 53, "expected_unordered_pair_count": 1596, "font_failure_count": 0, "glyph_count": 234, "glyph_foreign_pixel_total": 0, "glyph_missing_stroke_total": 0, "graphic_count": 25, "graphic_graphic_assessed_count": 300, "graphic_graphic_disjoint_under_3px_count": 23, "graphic_graphic_intentional_count": 48, "graphic_graphic_overlap_pair_count": 25, "graphic_graphic_pair_count": 300, "necessary_substring_count": 18, "opaque_graphic_coverage_failure_count": 0, "pair_failure_count": 0, "pixel_failure_count": 0, "required_relation_count": 445, "required_relation_failure_count": 0, "semantic_object_count": 57, "source_duplicate_text_pixels": 0, "source_unassigned_text_pixels": 0, "strict_schema_revision": 111, "text_element_count": 32, "translucent_graphic_coverage_failure_count": 0, "uid": "FIG-P580-01", "visual_template_count": 50} |
| `core_boolean_gates` | PASS | {"anchor_checks_pass": true, "empty_mask_ids": [], "math_body_consistency_pass": true, "text_completeness_pass": true, "text_replay_exact": true} |
| `object_inventory` | PASS | {"rows": 57, "unique": 57} |
| `unordered_pair_closure` | PASS | {"expected": 1596, "rows": 1596, "unique": 1596} |
| `graphic_graphic_300_row_closure` | PASS | {"assessed": 300, "disjoint_under_3px": 23, "intentional": 48, "overlap": 25, "rows": 300, "unique_pair_specific_reasons": 300} |
| `graphic_graphic_nonintentional_gate` | PASS | {"rows": 252} |
| `critical_package_closure` | PASS | {"decoded_pngs": 530, "packages": 53, "problems": []} |
| `three_repair_pairs` | PASS | {"PAIR_GR004_GR025": {"clearance_px": 6.28011, "evidence_package": "critical_relations/PAIR_GR004_GR025", "exact_11_file_set": true, "overlap_pixel_count": 0, "pass": true, "required_clearance_px": 3.0}, "PAIR_GR020_GR022": {"clearance_px": 5.0, "evidence_package": "critical_relations/PAIR_GR020_GR022", "exact_11_file_set": true, "overlap_pixel_count": 0, "pass": true, "required_clearance_px": 3.0}, "PAIR_GR020_GR024": {"clearance_px": 9.77033, "evidence_package": "critical_relations/PAIR_GR020_GR024", "exact_11_file_set": true, "overlap_pixel_count": 0, "pass": true, "required_clearance_px": 3.0}} |
| `required_relations_445` | PASS | {"failures": 0, "rows": 445} |
| `overlap_report_union` | PASS | {"rows": 2041, "union": 2041} |
| `font_and_pixel_gates` | PASS | {"font_rows": 32, "minimum_effective_pt": 9.6, "pixel_rows": 252} |
| `D_and_E_gates` | PASS | {"D_rows": 79, "E_assessed": 10, "E_justified_NA": 28, "E_rows": 38} |
| `clip_coverage_completeness` | PASS | {"clip": 32, "completeness": 8, "opaque": 25, "translucent": 0} |
| `glyph_contact_inputs` | PASS | {"glyphs": 234, "sheets": 15} |
| `visual_template_inputs` | PASS | {"rows": 50, "unique": 50} |
| `final_views` | PASS | {"actual": {"after_text_measurement_overlay_300dpi.png": [2481, 3508], "figure_crop_300dpi.png": [1980, 942], "full_page_200dpi.png": [1654, 2339], "full_page_300dpi.png": [2481, 3508], "grayscale_300dpi.png": [1980, 942], "standalone_300dpi.png": [2481, 3508]}, "render_dpi": 300, "resize_after_render": false} |
| `revision111_low_profile_package` | PASS | {"files": 13, "rows": 1} |
| `manual_glyph_234_individual` | PASS | {"rows": 234, "unique_notes": 234} |
| `manual_visual_50_individual` | PASS | {"rows": 50, "unique_notes": 50} |
| `manual_critical_relation_53_individual` | PASS | {"rows": 53, "three_repair_full_sets_actually_opened": true, "unique_notes": 53} |
| `all_current_pngs_openable` | PASS | {"failures": [], "pngs": 1137} |
| `no_ordinary_zero_byte_file` | PASS | {"nonordinary_latex_placeholders": ["build/calibration/calibration_low_profile_punctuation.idx", "build/calibration/calibration_low_profile_punctuation.ind", "build/calibration/symbols.idx", "build/calibration/symbols.ind", "build/page/symbols.idx", "build/page/symbols.ind", "build/page/v260_FIG-P580-01_page.idx", "build/page/v260_FIG-P580-01_page.ind", "build/standalone/symbols.idx", "build/standalone/symbols.ind", "build/standalone/v260_FIG-P580-01_standalone.idx", "build/standalone/v260_FIG-P580-01_standalone.ind"], "ordinary_zero": []} |
| `safe_portable_filenames` | PASS | {"files": 1348} |
| `terminal_input_manifest` | PASS | {"dynamic_exclusions": ["WRITE_STOPPED.md", "final_file_integrity.csv", "machine_final_check.json", "machine_final_check.md", "machine_terminal_input_file_manifest.csv"], "entries": 1353, "external_inputs": 5, "local_inputs": 1348} |
| `terminal_references_exist` | PASS | ["manual_glyph_contact_ledger.csv", "manual_visual_harmony_ledger.csv", "manual_critical_relation_ledger.csv", "after_visual_acceptance.md", "source_diff_summary.md", "build_commands.md", "critical_relations/PAIR_GR004_GR025", "critical_relations/PAIR_GR020_GR022", "critical_relations/PAIR_GR020_GR024"] |
| `terminal_three_repair_packages_nonempty` | PASS | {"PAIR_GR004_GR025": {"clearance_px": 6.28011, "evidence_package": "critical_relations/PAIR_GR004_GR025", "exact_11_file_set": true, "overlap_pixel_count": 0, "pass": true, "required_clearance_px": 3.0}, "PAIR_GR020_GR022": {"clearance_px": 5.0, "evidence_package": "critical_relations/PAIR_GR020_GR022", "exact_11_file_set": true, "overlap_pixel_count": 0, "pass": true, "required_clearance_px": 3.0}, "PAIR_GR020_GR024": {"clearance_px": 9.77033, "evidence_package": "critical_relations/PAIR_GR020_GR024", "exact_11_file_set": true, "overlap_pixel_count": 0, "pass": true, "required_clearance_px": 3.0}} |

## Candidate freeze hashes

- `business_source_sha256`: `f0ecc9b28361a2ae73af085a4958ad09f8f94575d789b8f776c55631fd45e161`
- `page_pdf_sha256`: `46e28a030f2f11c3147423a02f4fe99913ffd985caf6807a9473a3fbb5bd3934`
- `standalone_pdf_sha256`: `7dda4690cbd2eadd1dd0ec6841d14a866733ac8fa64066b1717c5f4e60ec9276`

No official full-book build was run. Root must independently inspect and run the authorized official build before any final acceptance.
