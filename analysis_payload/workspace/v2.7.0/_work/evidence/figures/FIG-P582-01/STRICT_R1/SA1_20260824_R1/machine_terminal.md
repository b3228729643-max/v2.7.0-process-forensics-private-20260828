# FIG-P582-01 SA1 machine terminal check

The active evidence package is machine-consistent only if `TERMINAL_MACHINE_CONSISTENCY_PASS=true`. This field is distinct from the figure verdict.

- `TERMINAL_MACHINE_CONSISTENCY_PASS=true`
- `EVIDENCE_INTEGRITY_PASS=true`
- `FIGURE_HARD_GATES_PASS=false`
- `FIGURE_RESULT=FAIL→SA2`

## Recomputed bottom-level counts

- Objects: 62 = 45 semantic/text + 17 graphic; pairs: 62 choose 2 = 1891.
- Mandatory relationships: 1686; source-font failures: 29; glyph pixel/calibration failures: 6; combined glyph source-or-pixel failures: 68.
- Low-profile: 21 targets, 2 calibration failures, 11 source-floor failures, 13 total `LOW_PROFILE_TOTAL_GATE_PASS=false` rows.
- Actual native final-mask H_INK: D failures 3; applicable E failures 2.
- Pair failures: 1; P0717 arrow/value relation: 3px overlap and 0px clearance; clip failures: 0.

## File hygiene

- Pre-terminal ordinary files: 1539; PNG files opened: 1329; zero-byte files: 0; unsafe/ADS-style names: 0; non-ordinary files: 0; unopenable PNGs: 0.
- `machine_terminal_input_file_manifest.csv` records the 1536 post-deletion input artifacts; only dynamic terminal products and the future stop marker are excluded to avoid self-reference.
- The initial raw `glyph_reviewer_ledger.csv` and `glyph_machine_integrity.csv` are parseable `SUPERSEDED_INITIAL_RAW` diagnostics and are excluded from final integrity counts.

## Checks

- PASS — `all_existing_csv_parseable`: `{'count': 28, 'errors': []}`
- PASS — `all_existing_json_parseable`: `{'count': 68, 'errors': []}`
- PASS — `json::measurement_summary.json`: `parsed`
- PASS — `json::role_actual_hink_summary.json`: `parsed`
- PASS — `json::low_profile_calibration/low_profile_calibration_summary.json`: `parsed`
- PASS — `csv::after_font_audit.csv`: `{'rows': 45, 'columns': 13}`
- PASS — `csv::after_pixel_measurements.csv`: `{'rows': 184, 'columns': 40}`
- PASS — `csv::object_inventory.csv`: `{'rows': 62, 'columns': 18}`
- PASS — `csv::graphic_object_inventory.csv`: `{'rows': 17, 'columns': 10}`
- PASS — `csv::semantic_text_inventory_machine.csv`: `{'rows': 45, 'columns': 7}`
- PASS — `csv::all_unordered_pairs.csv`: `{'rows': 1891, 'columns': 17}`
- PASS — `csv::after_overlap_report.csv`: `{'rows': 1891, 'columns': 17}`
- PASS — `csv::mandatory_relationships.csv`: `{'rows': 1686, 'columns': 17}`
- PASS — `csv::clip_report.csv`: `{'rows': 62, 'columns': 7}`
- PASS — `csv::glyph_file_manifest.csv`: `{'rows': 139, 'columns': 13}`
- PASS — `csv::glyph_final_mask_manifest.csv`: `{'rows': 139, 'columns': 5}`
- PASS — `csv::glyph_final_mask_integrity.csv`: `{'rows': 139, 'columns': 11}`
- PASS — `csv::glyph_final_reviewer_ledger.csv`: `{'rows': 139, 'columns': 18}`
- PASS — `csv::glyph_isolation_ledger.csv`: `{'rows': 11, 'columns': 16}`
- PASS — `csv::low_profile_punctuation_calibration.csv`: `{'rows': 21, 'columns': 22}`
- PASS — `csv::low_profile_reviewer_ledger.csv`: `{'rows': 21, 'columns': 15}`
- PASS — `csv::four_view_reviewer_ledger.csv`: `{'rows': 5, 'columns': 16}`
- PASS — `csv::panel_role_script_visual_ledger.csv`: `{'rows': 23, 'columns': 17}`
- PASS — `csv::semantic_reviewer_ledger.csv`: `{'rows': 45, 'columns': 10}`
- PASS — `csv::role_hierarchy_audit.csv`: `{'rows': 46, 'columns': 20}`
- PASS — `csv::role_e_actual_hink_audit.csv`: `{'rows': 25, 'columns': 12}`
- PASS — `object_inventory_unique`: `{'count': 62, 'unique': 62}`
- PASS — `semantic_inventory_unique`: `{'count': 45, 'unique': 45}`
- PASS — `graphic_inventory_unique`: `{'count': 17, 'unique': 17, 'matches_authoritative_object_inventory': True}`
- PASS — `object_composition`: `{'all_objects': 62, 'semantic': 45, 'graphics': 17}`
- PASS — `object_safe_names`: `{'unsafe': []}`
- PASS — `all_unordered_pair_formula`: `{'objects': 62, 'expected_n_choose_2': 1891, 'pair_rows': 1891, 'unique_pair_ids': 1891}`
- PASS — `after_overlap_complete_pair_coverage`: `{'after_overlap_rows': 1891, 'all_pair_rows': 1891}`
- PASS — `mandatory_relationship_coverage`: `{'mandatory_rows': 1686, 'required_pair_count': 1686}`
- PASS — `critical_failure_package_paths`: `{'critical_or_failure_count': 1, 'missing': []}`
- PASS — `P0717_real_relation_failure`: `{'PAIR_ID': 'P0717', 'OBJECT_A': 'E014', 'OBJECT_B': 'E016', 'KIND_A': 'TEXT', 'KIND_B': 'TEXT', 'RELATION': 'TEXT_TEXT', 'REQUIRED_BY_921': 'true', 'EXCEPTION_OR_DRAWING_ORDER_NOTE': 'none', 'MASK_A': 'object_masks/E014_final_visible_mask.png', 'MASK_B': 'object_masks/E016_final_visible_mask.png', 'OVERLAP_PIXEL_COUNT': '3', 'MIN_CLEARANCE_PX': '0.0', 'REQUIRED_CLEARANCE_PX': '4', 'MEASUREMENT_COORDINATE': 'native final-PDF 300dpi; raw masks', 'CRITICAL_OR_FAILURE': 'true', 'ROI_PACKAGE': 'roi_packages_r2_geometry_isolated/P0717_E014_E016', 'PASS_FAIL': 'FAIL'}`
- PASS — `P0717_native_and_8x_package_complete`: `{'package': 'roi_packages_r2_geometry_isolated\\P0717_E014_E016', 'missing': []}`
- PASS — `font_and_pixel_row_coverage`: `{'font_elements': 45, 'semantic_elements': 45, 'after_pixel_total_rows': 184, 'pixel_glyphs': 139, 'manifest_glyphs': 139}`
- PASS — `revision111_low_profile_coverage`: `{'calibration_rows': 21, 'pixel_low_profile_rows': 21, 'manual_rows': 21}`
- PASS — `revision111_low_profile_gate_field`: `counted from LOW_PROFILE_TOTAL_GATE_PASS; no STATUS column is used`
- PASS — `revision111_low_profile_counts`: `{'calibration_fail': 2, 'source_font_floor_fail': 11, 'total_gate_fail': 13}`
- PASS — `low_profile_manual_ledger_closed`: `{'rows': 21, 'manual_decision_counts': {'CALIBRATION_PASS_FONT_FAIL': 11, 'CALIBRATION_FAIL': 2, 'PASS_LOCAL': 8}}`
- PASS — `final_glyph_id_coverage`: `{'expected': 139, 'final_ledger_rows': 139, 'final_ledger_unique': 139, 'final_mask_manifest_rows': 139, 'final_integrity_rows': 139}`
- PASS — `final_manual_glyph_ledger_closed`: `{'rows': 139, 'blank_cells': [], 'bad_decisions': [], 'broken_paths': []}`
- PASS — `final_contact_sheet_coverage`: `{'count': 12, 'paths': ['glyph_final_contact_sheets/contact_sheet_01_final_visible.png', 'glyph_final_contact_sheets/contact_sheet_02_final_visible.png', 'glyph_final_contact_sheets/contact_sheet_03_final_visible.png', 'glyph_final_contact_sheets/contact_sheet_04_final_visible.png', 'glyph_final_contact_sheets/contact_sheet_05_final_visible.png', 'glyph_final_contact_sheets/contact_sheet_06_final_visible.png', 'glyph_final_contact_sheets/contact_sheet_07_final_visible.png', 'glyph_final_contact_sheets/contact_sheet_08_final_visible.png', 'glyph_final_contact_sheets/contact_sheet_09_final_visible.png', 'glyph_final_contact_sheets/contact_sheet_10_final_visible.png', 'glyph_final_contact_sheets/contact_sheet_11_final_visible.png', 'glyph_final_contact_sheets/contact_sheet_12_final_visible.png']}`
- PASS — `final_mask_and_overlay_files`: `{'rows': 139, 'broken': []}`
- PASS — `final_mask_purity_completeness`: `{'rows': 139, 'bad': []}`
- PASS — `initial_candidate_isolation_closure`: `{'rows': 11, 'bad_decisions': [], 'package_missing': []}`
- PASS — `P0717_mask_integrity_vs_real_collision_separated`: `{'G0029': {'GLYPH_ID': 'G0029', 'ELEMENT_ID': 'E014', 'CHAR': '↓', 'FINAL_MASK_STATUS': 'INDEPENDENT_OBJECT_REPLAY_REAL_COLLISION', 'RAW_SHARED_GLYPH_PIXEL_PX': '3', 'FINAL_SHARED_GLYPH_PIXEL_PX': '3', 'REAL_SHARED_COLLISION_PX': '3', 'FINAL_FOREIGN_GLYPH_PIXEL_PX': '0', 'MASK_PURITY_COMPLETENESS_PASS': 'true', 'RAW_DISCARDED_PIXEL_PX': '0', 'COORDINATE': 'native candidate PDF 300dpi 1:1 final-mask ROI'}, 'G0036': {'GLYPH_ID': 'G0036', 'ELEMENT_ID': 'E016', 'CHAR': '0', 'FINAL_MASK_STATUS': 'INDEPENDENT_OBJECT_REPLAY_REAL_COLLISION', 'RAW_SHARED_GLYPH_PIXEL_PX': '3', 'FINAL_SHARED_GLYPH_PIXEL_PX': '3', 'REAL_SHARED_COLLISION_PX': '3', 'FINAL_FOREIGN_GLYPH_PIXEL_PX': '0', 'MASK_PURITY_COMPLETENESS_PASS': 'true', 'RAW_DISCARDED_PIXEL_PX': '0', 'COORDINATE': 'native candidate PDF 300dpi 1:1 final-mask ROI'}}`
- PASS — `initial_raw_ledgers_declared_superseded`: `{'raw_files_exist': True, 'declared': True}`
- PASS — `four_view_manual_ledger_closed`: `{'rows': 5, 'view_ids': ['FULL_PAGE_NATIVE_300DPI', 'FULL_PAGE_200DPI', 'FIGURE_CROP_300DPI', 'STANDALONE_300DPI', 'GRAYSCALE_300DPI']}`
- PASS — `panel_role_script_manual_ledger_closed`: `{'rows': 23}`
- PASS — `semantic_manual_ledger_closed`: `{'rows': 45}`
- PASS — `actual_final_mask_H_INK_D`: `{'panel_role_script_rows': 23, 'D_fail': 3}`
- PASS — `actual_final_mask_H_INK_E`: `{'E_fail': 2, 'annotation_operator_is_NA_with_empty_base': True}`
- PASS — `actual_H_INK_summary_consistency`: `{'coordinate': 'native final-PDF 300dpi 1:1 final glyph masks', 'pdf_span_proxy_used_for_pass': False, 'panel_role_script_group_count': 23, 'element_script_row_count': 65, 'd_applicable_fail_count': 3, 'same_role_applicable_fail_count': 0, 'e_applicable_fail_count': 2, 'e_na_with_basis_count': 15, 'd_hink_pass': False, 'same_role_hink_pass': True, 'e_hink_applicable_pass': False, 'e_coverage_closed_with_basis': True}`
- PASS — `post_deletion_input_manifest`: `{'file': 'machine_terminal_input_file_manifest.csv', 'input_file_count': 1536, 'excluded_dynamic_products': ['WRITE_STOPPED.md', 'machine_terminal.json', 'machine_terminal.md', 'machine_terminal_input_file_manifest.csv']}`
- PASS — `ordinary_files_nonzero_safe_names`: `{'file_count': 1539, 'zero_byte': [], 'unsafe_name_or_ads': [], 'non_ordinary': []}`
- PASS — `all_png_openable`: `{'png_count': 1329, 'bad_png': []}`
- PASS — `measurement_summary_recomputed_from_csv`: `{'text_element_count': 45, 'glyph_count': 139, 'graphic_object_count': 17, 'all_object_count': 62, 'all_unordered_pair_count': 1891, 'mandatory_relationship_count': 1686, 'source_font_fail_element_count': 29, 'pixel_fail_glyph_count': 6, 'low_profile_target_count': 21, 'low_profile_calibration_fail_count': 2, 'low_profile_font_floor_fail_count': 11, 'low_profile_total_gate_fail_count': 13, 'pair_failure_count': 1, 'clip_failure_count': 0, 'real_shared_collision_px': 3}`
- PASS — `low_profile_summary_recomputed_from_csv`: `{'revision': '111', 'low_profile_target_count': 21, 'calibration_fail_count': 2, 'font_floor_fail_count': 11, 'total_low_profile_gate_fail_count': 13, 'all_packages_have_1x_and_8x': True}`
- PASS — `markdown_conclusion_consistency`: `{'visual_tokens_present': ['SOURCE_FONT_PASS=false', 'PIXEL_HEIGHT_PASS=false', 'LOW_PROFILE_CALIBRATION_PASS=false', 'FONT_VISUAL_HARMONY_PASS=false', 'H_INK_D_PASS=false', 'H_INK_E_PASS=false', 'REQUIRED_OVERLAP_CLEARANCE_PASS=false', 'CLIP_PASS=true', 'EVIDENCE_INTEGRITY_PASS=true', 'RESULT: FAIL→SA2']}`
- PASS — `evidence_integrity_expected_true`: `active final evidence only; initial raw ledgers excluded from final counts`
