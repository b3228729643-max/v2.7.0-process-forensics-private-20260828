# FIG-P575-01 SA1 machine terminal check

RESULT: FAIL
MACHINE_EVIDENCE_INTEGRITY_PASS: true

| Check | Result | Detail |
|---|---|---|
| required_artifacts_exist | PASS | 17/17 |
| unique_nonempty_object_masks | PASS | objects=53, semantic_text=31 |
| semantic_font_elements_unique | PASS | semantic_font_elements=31, failed=28 |
| glyph_masks_nonempty_and_unique | PASS | glyph_trace=151, pixel_height_failed=26, all_gate_failed=141 |
| glyph_raw_masks_mutually_exclusive | PASS | duplicate_pixels=0 |
| all_unordered_pairs_covered | PASS | actual=1378, expected=1378 |
| all_failed_or_critical_pair_evidence | PASS | critical=4 |
| pixel_height_failure_glyph_evidence | PASS | pixel_height_failed=26, missing=0 |
| all_gate_failure_glyph_evidence | PASS | all_gate_failed=141, missing=0 |
| no_empty_graphic_mask | PASS | graphics=22 |
| csv_json_md_counts_consistent | PASS | semantic_font=31, glyph_trace=151, result=FAIL |
| final_result_consistent_with_underlying_fails | PASS | result=FAIL |
| node_border_relation_explicit_na | PASS | no NODE_BORDER source object; N/A explicitly reported |

The machine check validates evidence integrity only. It does not override underlying strict visual FAIL rows.
