# FIG-P634-01 machine terminal check — revision103

- Machine-terminal integrity: **PASS**
- Underlying audit result (not rewritten by this integrity check): **FAIL → SA2**
- Method: independent re-read of emitted manifest, compressed masks, all pair/glyph packs, CSV/JSON/Markdown ledgers and retained views.

| Check | Expected | Actual | Status |
|---|---|---|---|
| `manifest_row_count` | 452 | 452 | **PASS** |
| `manifest_unique_object_ids` | 452 | 452 | **PASS** |
| `manifest_nonempty_masks` | 0 zero masks | 0 | **PASS** |
| `raw_mask_registry_matches_manifest` | 452 unique non-empty masks | 452 ids; ids=452, coordinate_count=855967, zero_spans=0, manifest_span_mismatches=0 | **PASS** |
| `semantic_plus_pair_graphic_objects` | 106 + 39 = 145 | 106 + 39 = 145 | **PASS** |
| `foreground_graphic_empty_masks` | 0 | 0 | **PASS** |
| `unordered_pair_count` | 10440 | 10440 | **PASS** |
| `unordered_pair_unique_coverage` | 10440 | 10440 | **PASS** |
| `after_overlap_copy_identity` | f93d50af8e1660d290a433ee447ea7a7e2dfaa1564acd1948bcfe3fd844ff12d | f93d50af8e1660d290a433ee447ea7a7e2dfaa1564acd1948bcfe3fd844ff12d | **PASS** |
| `pair_relation_classification_complete` | 0 blank classifications | 0 | **PASS** |
| `pair_failure_status_count` | 1 | 1 | **PASS** |
| `overlap_failure_count` | 0 | 0 | **PASS** |
| `clearance_failure_count` | 1 | 1 | **PASS** |
| `failed_pair_identity` | EL-035-CARD1_STATE-MATH_SCRIPT + G-CARD1-BORDER | EL-035-CARD1_STATE-MATH_SCRIPT + G-CARD1-BORDER | **PASS** |
| `literal_glyph_row_count` | 307 | 307 | **PASS** |
| `literal_glyph_failure_count` | 11 | 11 | **PASS** |
| `glyph_failure_evidence_packs` | 11 complete | dirs=11, incomplete=0, empty_masks=0 | **PASS** |
| `same_class_ratio_failure_count` | 23 | 23 | **PASS** |
| `role_ratio_failure_count` | 3 | 3 | **PASS** |
| `clip_failure_count` | 0 | 0 | **PASS** |
| `critical_failed_pair_evidence_packs` | 35 dirs; 7 core + 2 overlays each | dirs=35, missing=0, unreadable_images=0, empty_A_or_B=0, bad_json=0 | **PASS** |
| `four_view_and_overlay_files` | 5 readable files | 5 | **PASS** |
| `result_consistency` | FAIL → SA2 | json=FAIL → SA2; after=FAIL → SA2; report=FAIL → SA2 | **PASS** |
| `all_gate_values_consistent_across_json_after_report` | all derived gates match | mismatches=0; min_gap_recomputed=2.162 | **PASS** |
| `audit_summary_counts_match_disk` | all count fields match | mismatches=0 | **PASS** |

## Recomputed counts

```json
{
  "manifest_rows": 452,
  "manifest_unique_ids": 452,
  "registry_mask_ids": 452,
  "registry_zero_spans": 0,
  "semantic_objects": 106,
  "pair_graphic_objects": 39,
  "pair_objects": 145,
  "unordered_pairs": 10440,
  "status_fail_pairs": 1,
  "overlap_fail_pairs": 0,
  "clearance_fail_pairs": 1,
  "glyph_failures": 11,
  "glyph_failure_dirs": 11,
  "critical_failed_pack_dirs": 35,
  "D_failures": 23,
  "E_failures": 3,
  "clip_failures": 0,
  "empty_foreground_graphics": 0,
  "minimum_text_clearance_px_recomputed": 2.162
}
```
