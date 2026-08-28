# FIG-P580-01 SA2 machine final check

Result: `SA2_LOCAL_PASS_AWAIT_ROOT_R96`

Schema revision: `111`

## Check matrix

| Check | Result | Detail |
|---|---|---|
| `json_parse::core_audit_summary.json` | PASS | "object parsed" |
| `json_parse::render_manifest.json` | PASS | "object parsed" |
| `json_parse::math_and_body_consistency.json` | PASS | "object parsed" |
| `json_parse::source_text_anchor.json` | PASS | "object parsed" |
| `json_parse::text_only_replay_probe.json` | PASS | "object parsed" |
| `json_parse::glyph_ownership_report.json` | PASS | "object parsed" |
| `csv_parse::after_font_audit.csv` | PASS | "rows=32" |
| `csv_parse::after_pixel_measurements.csv` | PASS | "rows=252" |
| `csv_parse::all_unordered_pairs.csv` | PASS | "rows=1596" |
| `csv_parse::required_relations.csv` | PASS | "rows=445" |
| `csv_parse::after_overlap_report.csv` | PASS | "rows=2041" |
| `csv_parse::after_D_same_class.csv` | PASS | "rows=79" |
| `csv_parse::after_E_role_ratios.csv` | PASS | "rows=38" |
| `csv_parse::object_inventory.csv` | PASS | "rows=57" |
| `csv_parse::mask_manifest.csv` | PASS | "rows=313" |
| `csv_parse::glyph_contact_manifest.csv` | PASS | "rows=234" |
| `csv_parse::manual_glyph_contact_ledger.csv` | PASS | "rows=234" |
| `csv_parse::manual_visual_harmony_ledger.csv` | PASS | "rows=50" |
| `csv_parse::opaque_label_graphic_coverage.csv` | PASS | "rows=25" |
| `csv_parse::translucent_label_graphic_coverage.csv` | PASS | "rows=0" |
| `csv_parse::clip_and_edge_clearance.csv` | PASS | "rows=32" |
| `csv_parse::text_completeness_ledger.csv` | PASS | "rows=8" |
| `csv_parse::role_assignment_ledger.csv` | PASS | "rows=32" |
| `csv_parse::low_profile_punctuation_calibration.csv` | PASS | "rows=1" |
| `core_exact_counts` | PASS | {"D_failure_count": 0, "E_failure_count": 0, "actual_unordered_pair_count": 1596, "clip_failure_count": 0, "contact_manifest_count": 234, "contact_sheet_count": 15, "critical_relation_package_count": 0, "expected_unordered_pair_count": 1596, "font_failure_count": 0, "glyph_count": 234, "glyph_foreign_pixel_total": 0, "glyph_missing_stroke_total": 0, "graphic_count": 25, "low_profile_calibration_failure_count": 0, "low_profile_punctuation_count": 1, "necessary_substring_count": 18, "opaque_graphic_coverage_failure_count": 0, "opaque_label_ground_count": 1, "pair_failure_count": 0, "pixel_failure_count": 0, "required_relation_count": 445, "required_relation_failure_count": 0, "semantic_object_count": 57, "source_duplicate_text_pixels": 0, "source_unassigned_text_pixels": 0, "strict_schema_revision": 111, "text_element_count": 32, "translucent_graphic_coverage_failure_count": 0, "translucent_label_ground_count": 0, "uid": "FIG-P580-01", "visual_template_count": 50} |
| `core_boolean_gates` | PASS | {"anchor_checks_pass": true, "math_body_consistency_pass": true, "text_completeness_pass": true, "text_replay_exact": true} |
| `core_empty_mask_ids` | PASS | [] |
| `font_rows` | PASS | "rows=32 min_effective_pt=9.60" |
| `pixel_rows` | PASS | "rows=252 unique=252" |
| `object_inventory` | PASS | "rows=57 text=32 graphic=25" |
| `unordered_pair_formula` | PASS | "expected=1596 actual=1596 unique=1596" |
| `all_pair_results` | PASS | "failures=0" |
| `required_relations` | PASS | "rows=445 failures=0" |
| `overlap_report_union` | PASS | "rows=2041 union=2041" |
| `D_gate` | PASS | "rows=79 failures=0" |
| `E_gate` | PASS | {"NA_reason_counts": {"no eligible all-C-pass sample for role": 2, "no same-panel same-script tick base": 26}, "assessed": 10, "assessed_failures": 0, "justified_NA": 28, "rows": 38} |
| `opaque_coverage` | PASS | {"failures": 0, "rows": 25, "same_node_border_fill_stroke_overlap": [{"FINAL_VISIBLE_MASK": "masks/graphics/GR021_raw.png", "GRAPHIC_ID": "GR021", "GRAPHIC_ROLE": "NODE_BORDER", "HALO_ID": "HALO01", "HALO_MASK": "masks/opaque_halos/HALO01_weight_card_opaque_fill.png", "OVERLAP_PIXEL_COUNT": "2943", "PASS_FAIL": "PASS", "PRE_MASK": "masks/pre_occlusion/GR021_pre_occlusion.png", "REASON": "associated card border; intentional same-node fill/stroke"}], "zero_overlap_graphics": 24} |
| `translucent_coverage` | PASS | "rows=0" |
| `clip_gate` | PASS | "rows=32" |
| `text_completeness` | PASS | "rows=8" |
| `role_assignment` | PASS | {"E004": "ANNOTATION", "E028": "AXIS_TITLE", "E029": "AXIS_TITLE", "E030": "LEGEND", "E031": "LEGEND"} |
| `rev111_low_profile_punctuation` | PASS | {"AREA_RATIO_TO_CALIBRATION": "1.000000", "CALIBRATION_COLOUR_MATCH": "true", "CALIBRATION_FONT_MATCH": "true", "CALIBRATION_H_INK_PX": "7", "CALIBRATION_INK_AREA_PX": "41", "CALIBRATION_PASS": "true", "CALIBRATION_REFERENCE": "low_profile_punctuation/reference_measurement.json", "CALIBRATION_SIZE_DELTA_PT": "0.000000", "EFFECTIVE_PT": "10.00", "FINAL_PIXELS": "41", "H_INK_PX": "7", "H_RATIO_TO_CALIBRATION": "1.000000", "LOW_PROFILE_EVIDENCE": "low_profile_punctuation/G0198", "MEASURE_ID": "G0198", "PANEL_ID": "GLOBAL", "PARENT_ELEMENT_ID": "E032", "PASS_FAIL": "PASS", "PDF_FONT_PT": "9.963", "REASON": "PASS_REV111_LOW_PROFILE_CALIBRATION", "ROLE": "CAPTION", "SAME_ROLE_CROSS_PANEL_RATIO": "1.000000_SINGLE_GLOBAL_INSTANCE", "TEXT_SAMPLE": ".", "THRESHOLD_RULE": "REV111_LOW_PROFILE_CALIBRATION", "UNICODE": "U+002E"} |
| `low_profile_evidence_package` | PASS | "expected=13 actual=13" |
| `manual_glyph_ledger` | PASS | "manifest=234 manual=234 unique=234" |
| `contact_sheet_set` | PASS | "count=15" |
| `manual_visual_ledger` | PASS | "rows=50 unique=50" |
| `mask_manifest_logical_rows` | PASS | {"kind_counts": {"GLYPH": 234, "GRAPHIC": 25, "NODE_BORDER_EDGE": 4, "TEXT": 32, "TEXT_SUBSTRING": 18}, "rows": 313, "unique_ids": 313, "unique_raw_paths": 313} |
| `mask_physical_file_formula` | PASS | {"actual_files": 580, "declared_deprecated_auxiliary": 6, "formula": "313 + 234 + 25 + 2 + 6 = 580", "global_current_derivatives": 2, "glyph_source_shape_derivatives": 234, "graphic_pre_occlusion_derivatives": 25, "logical_raw": 313, "missing": [], "unexpected": []} |
| `deprecated_mask_auxiliary_isolation` | PASS | {"paths": ["masks/glyphs/S_FRACTION_01_raw.png", "masks/glyphs/S_FRACTION_02_raw.png", "masks/glyphs/S_FRACTION_03_raw.png", "masks/glyphs/VBAR01_raw.png", "masks/glyphs/VBAR02_raw.png", "masks/glyphs/VBAR03_raw.png"], "status": "six pre-final fraction/vbar composites retained as explicitly nonauthoritative; none is a manifest row or current measurement input"} |
| `ownership_pollution` | PASS | {"rule": "BT/ET replay candidate, rawdict/texttrace ROI, nearest unpadded rawdict character box owns shared replay pixel", "source_duplicate_text_pixels": 0, "source_text_pixels_in_scope": 66307, "source_unassigned_text_pixels": 0} |
| `render_identity` | PASS | {"build_exit_codes": {"page": 0, "standalone": 0}, "build_logs": ["build/page/v260_FIG-P580-01_page.log", "build/standalone/v260_FIG-P580-01_standalone.log"], "candidate_page_pdf": "D:\\Users\\ASUS\\Desktop\\机器学习\\v2.7.0\\_work\\evidence\\figures\\FIG-P580-01\\STRICT_R2_SA2_R95_LOCAL_20260824\\build\\page\\v260_FIG-P580-01_page.pdf", "candidate_standalone_pdf": "D:\\Users\\ASUS\\Desktop\\机器学习\\v2.7.0\\_work\\evidence\\figures\\FIG-P580-01\\STRICT_R2_SA2_R95_LOCAL_20260824\\build\\standalone\\v260_FIG-P580-01_standalone.pdf", "figure_crop_full_page_px": [250, 583, 2230, 1525], "full_page_200dpi_grid": [1654, 2339], "full_page_300dpi_grid": [2481, 3508], "measurement_basis": "page wrapper direct Poppler 300dpi; integer crop only", "measurement_dpi": 300, "page_size_pt": [595.276, 841.89], "physical_page": 1, "resize_after_render": false, "standalone_300dpi_grid": [2481, 3508]} |
| `math_body_consistency` | PASS | {"checks": {"body_consistency": true, "left_support_gap": true, "no_accept_reject_semantics": true, "right_support_full": true, "w1_24_over_25": true, "w4_24_over_25": true, "wmid_3_over_2": true}, "result": "PASS"} |
| `source_anchor` | PASS | {"checks": {"caption": true, "figure_uid": true, "general_font_9_6": true, "left_hatch_decode": true, "left_title": true, "no_resize_or_scale_y": true, "right_line_decode": true, "right_title": true}, "result": "PASS"} |
| `text_replay` | PASS | {"character_count": 617, "character_stream_exact": true, "output_pdf": "page_text_only_replay.pdf", "parser": {"dropped_operators": {"B": 7, "S": 18, "f": 5, "n": 2}, "preserved_clipping_paths": 0, "text_blocks": 31, "unclosed_path_buffer_entries": 0}, "source_pdf": "D:\\Users\\ASUS\\Desktop\\机器学习\\v2.7.0\\_work\\evidence\\figures\\FIG-P580-01\\STRICT_R2_SA2_R95_LOCAL_20260824\\build\\page\\v260_FIG-P580-01_page.pdf", "text_trace_visual_properties_exact": true, "texttrace_count": 578} |
| `required_view_openability` | PASS | {"after_text_measurement_overlay_300dpi.png": [2481, 3508], "figure_crop_300dpi.png": [1980, 942], "full_page_200dpi.png": [1654, 2339], "full_page_300dpi.png": [2481, 3508], "grayscale_300dpi.png": [1980, 942], "standalone_300dpi.png": [2481, 3508]} |
| `manual_markdown_closure` | PASS | "required visual statements present" |
| `build_markdown_closure` | PASS | "commands and exit codes recorded" |
| `stale_evidence_declaration` | PASS | "stale packages, six deprecated masks, and exact cleaned auxiliary residue declared" |
| `external_input_exists::fig_v5_c02_is_support.tex` | PASS | "D:\\Users\\ASUS\\Desktop\\机器学习\\v2.7.0\\_work\\source\\v2.7.0\\src\\绘图源码\\第05册_采样方法主题模型与图排序\\V5-C02\\fig_v5_c02_is_support.tex" |
| `external_input_exists::v260_FIG-P580-01_page.tex` | PASS | "D:\\Users\\ASUS\\Desktop\\机器学习\\v2.7.0\\_work\\source\\v2.7.0\\src\\讲义源码\\合并总册\\v260_FIG-P580-01_page.tex" |
| `external_input_exists::v260_FIG-P580-01_standalone.tex` | PASS | "D:\\Users\\ASUS\\Desktop\\机器学习\\v2.7.0\\_work\\source\\v2.7.0\\src\\讲义源码\\合并总册\\v260_FIG-P580-01_standalone.tex" |
| `external_input_exists::STRICT_FIGURE_EVIDENCE_SCHEMA.md` | PASS | "D:\\Users\\ASUS\\Desktop\\机器学习\\v2.7.0\\_work\\evidence\\audits\\STRICT-GOAL-20260823\\STRICT_FIGURE_EVIDENCE_SCHEMA.md" |
| `external_input_exists::GPT_Pro_统计学习方法讲义_v2.7.0_Codex_Goal主提示词.md` | PASS | "D:\\Users\\ASUS\\Desktop\\机器学习\\v2.7.0\\GPT_Pro_统计学习方法讲义_v2.7.0_Codex_Goal主提示词.md" |
| `final_build_uses_source` | PASS | {"fls_mentions_source": true, "page_bytes": 69542, "pdf_after_source": true, "standalone_bytes": 40522} |
| `current_round_auxiliary_residue_cleanup` | PASS | {"post_cleanup": [{"bytes": 0, "extensions": [], "files": 0, "path": "D:\\Users\\ASUS\\Desktop\\机器学习\\v2.7.0\\_work\\source\\v2.7.0\\src\\讲义源码\\合并总册\\$page", "resolved": null}, {"bytes": 0, "extensions": [], "files": 0, "path": "D:\\Users\\ASUS\\Desktop\\机器学习\\v2.7.0\\_work\\source\\v2.7.0\\src\\讲义源码\\合并总册\\$stand", "resolved": null}], "removed_before_counts": {"bytes": 11205, "files": 8}} |
| `ordinary_zero_byte_files` | PASS | {"known_nonordinary_empty_latex_placeholders": ["build/calibration/calibration_low_profile_punctuation.idx", "build/calibration/calibration_low_profile_punctuation.ind", "build/calibration/symbols.idx", "build/calibration/symbols.ind", "build/page/symbols.idx", "build/page/symbols.ind", "build/page/v260_FIG-P580-01_page.idx", "build/page/v260_FIG-P580-01_page.ind", "build/standalone/symbols.idx", "build/standalone/symbols.ind", "build/standalone/v260_FIG-P580-01_standalone.idx", "build/standalone/v260_FIG-P580-01_standalone.ind"], "ordinary_zero": []} |
| `all_png_openable` | PASS | {"failures": [], "png_count": 1227} |
| `safe_portable_filenames` | PASS | "checked=1456" |
| `preterminal_input_manifest` | PASS | {"entries": 1461, "excluded_dynamic_products": ["WRITE_STOPPED.md", "final_file_integrity.csv", "machine_final_check.json", "machine_final_check.md", "machine_terminal_input_file_manifest.csv"], "external_inputs": 5, "local_input_entries": 1456, "missing_required": [], "unexpected_local_entries": [], "unlisted_local_inputs": []} |

## Final numeric closure

- Objects/pairs: 57 objects; 1596/1596 unordered pairs; 445 required relations.
- Native text: 234 glyphs plus 18 necessary substrings = 252 measurements; minimum effective size 9.60 pt.
- Failures: pixel 0; font 0; D 0; E 0; pair 0; required relation 0; clip 0; opaque coverage 0; translucent coverage 0.
- Clearances: minimum assessed pair 10.045361 px; minimum text-text 14.033296 px.
- Formula card minima: border 22/5 px; y-axis 70/3 px; y-tick text 89/4 px.
- E gate: 10 assessed PASS plus 28 explicitly justified N/A rows; opaque coverage: 24 zero-overlap graphic rows plus the permitted GR021/HALO01 same-node border-fill/stroke row.
- Mask closure: 313 logical raw-mask rows + 234 glyph source shapes + 25 graphic pre-occlusion masks + 2 global current derivatives + 6 explicitly nonauthoritative pre-final composites = 580 physical files; no missing or unexpected path.
- Manual evidence: 234 glyph ledger rows and 50 visual/harmony rows; all PASS with no pending/unknown.
- File integrity: 1227 PNG files machine-opened; 0 ordinary zero-byte files; 12 known empty LaTeX `.idx/.ind` placeholders classified nonordinary.
- Pre-terminal input manifest: 1461 entries; exact dynamic exclusions: WRITE_STOPPED.md, final_file_integrity.csv, machine_final_check.json, machine_final_check.md, machine_terminal_input_file_manifest.csv.

## Freeze hashes

- `business_source_sha256`: `74a21ea35bdb09d5c01858e027b96aec844233f6850f6e7a8a9da03524466ef0`
- `page_pdf_sha256`: `81273bfd2784cc6b1c7f06ba19bd891e80c049c49011cddf82a50a7e8f35af05`
- `standalone_pdf_sha256`: `37dd8457043cd8738111923bd8dcf67d506517ba0596d2ff5c863ddaaa51973c`
- `figure_crop_sha256`: `af2c3a98c74872678f9148084e46ebb5e7011029e69d434d0214bb65ab71b7e0`

Retained stale packages are explicitly classified nonauthoritative in the pre-terminal input manifest. The two verified current-round literal auxiliary directories were precisely removed (8 files, 11,205 bytes; both paths now absent). No official full-book build was run. This local result awaits root R96 review and is not a strict final PASS declaration.
