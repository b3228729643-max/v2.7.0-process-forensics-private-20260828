# Final crosscheck

- checks: 39
- failed checks: 0
- verdict: `PASS`
- route: `SA1_PASS_READY_FOR_FRESH_ISOLATED_SA3`

| Check | Result | Detail |
|---|---:|---|
| identity_handoff | PASS | "A-R107-P020-SA1-FRESH-ISOLATED-20260826" |
| identity_role_model_effort | PASS | ["SA1","gpt-5.6-sol","xhigh"] |
| identity_uid_round | PASS | ["FIG-P020-01","R107"] |
| independent_unique_locator | PASS | [1,17,16,"4"] |
| input_hashes_frozen | PASS | "official PDF and source hashes exact" |
| N_and_C_frozen | PASS | {"glyph_count":108,"foreground_graphic_path_count":14,"background_drawing_count_excluded":2,"math_rule_count":0,"N_total_foreground_objects":122,"C_N_2_expected_unordered_pairs":7381,"C_N_2_emitted_unordered_pairs":7381,"object_ids_unique":true,"safe_filenames_unique":true} |
| object_identity_unique | PASS | [true,true] |
| inventory_counts | PASS | {"glyphs":108,"graphics":14,"safe_map":122} |
| inventory_ids_unique | PASS | 122 |
| visible_drawing_accounting | PASS | {"page_drawing_count_total":29,"target_foreground_seqnos":[14,17,20,21,24,27,30,31,33,34,36,37,39,40],"target_foreground_count":14,"target_background_seqnos":[13,42],"target_background_count":2,"target_math_rule_count":0,"target_unaccounted_visible_drawing_seqnos":[],"scope_note":"Only drawing seqnos whose bboxes intersect the independently frozen figure region are target drawings; the two visible fills are explicitly background."} |
| pixel_row_count | PASS | 108 |
| machine_masks_nonempty_pure | PASS | "108/108 nonempty; foreign candidate 0" |
| raw_object_image_denominator | PASS | "366/366 valid PNGs" |
| source_font_elements | PASS | "10/10" |
| pair_exhaustiveness | PASS | {"rows":7381,"unique_pairs":7381} |
| pair_gate_partition | PASS | {"DESIGN_WHITELIST":1174,"MEETS_MACHINE_GATE":6207} |
| illegal_overlap_zero | PASS | 0 |
| machine_pair_failures_zero | PASS | "0 failure/unknown rows" |
| clip_gate | PASS | {"rows":122,"clip_pixels":0} |
| minimum_crop_edge | PASS | 25 |
| punctuation_calibration_partition | PASS | {"all":7,"comparable":5,"separate_actual_font":["G053","G068"]} |
| actual_font_punctuation_calibration | PASS | ["G053","G068"] |
| calibration_image_denominator | PASS | "8/8" |
| glyph_contact_sheet_denominator | PASS | "12/12" |
| graphic_contact_sheet_denominator | PASS | "4/4" |
| required_view_files | PASS | "7/7" |
| critical_relation_count | PASS | 11 |
| critical_relation_evidence_denominator | PASS | "77/77" |
| critical_machine_gates | PASS | "11/11" |
| manual_manual_glyph_review.csv_closed | PASS | "108/108; all fields nonblank; decisions PASS" |
| manual_manual_graphic_review.csv_closed | PASS | "14/14; all fields nonblank; decisions PASS" |
| manual_manual_relation_review.csv_closed | PASS | "11/11; all fields nonblank; decisions PASS" |
| manual_manual_view_review.csv_closed | PASS | "8/8; all fields nonblank; decisions PASS" |
| manual_manual_panel_role_review.csv_closed | PASS | "4/4; all fields nonblank; decisions PASS" |
| manual_manual_source_font_review.csv_closed | PASS | "10/10; all fields nonblank; decisions PASS" |
| manual_object_pixel_counts | PASS | "122/122" |
| manual_relation_open_denominator | PASS | "11/11 raw 1x and nearest 8x" |
| manual_view_open_denominator | PASS | "8/8" |
| hand_authored_reports_present | PASS | ["00_identity/semantic_context.md","07_reports/after_overlap_adjudication.md","07_reports/after_visual_acceptance.md","07_reports/after_model_route.md","07_reports/RESULT.txt"] |
