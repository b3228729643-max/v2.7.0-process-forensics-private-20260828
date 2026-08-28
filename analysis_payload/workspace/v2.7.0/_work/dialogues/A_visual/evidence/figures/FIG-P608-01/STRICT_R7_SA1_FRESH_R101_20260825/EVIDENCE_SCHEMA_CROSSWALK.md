# Evidence schema crosswalk

| Requirement | Evidence |
|---|---|
| Frozen candidate identity | `candidate_identity.json` |
| Page mapping and crop geometry | `page_mapping_locator.json`, `render_geometry.json`, locator overlay |
| Raw glyph and drawing conservation | `denominator_conservation.json`, page rawdict/drawing exports |
| Stable object IDs and denominator | `object_inventory.csv/json`, `safe_filename_map.csv` |
| Native and 8× final-visible masks | four complete mask trees under `masks/` |
| Complete unordered pair coverage | `all_unordered_pairs.csv`, `denominator_and_pair_summary.json` |
| Critical-pair evidence and adjudication | `critical_pairs_with_evidence.csv`, `critical_pairs/`, manual critical-pair ledger |
| Caption natural paragraph closure | caption glyphs `TXT-069`–`TXT-112`, role/object ledgers |
| Math-rule floor | `math_assembly_measurements.csv` |
| Declared/effective typography | `after_font_audit.csv`, `after_pixel_measurements.csv` |
| Low-profile peer policy and candidates | `FULLBOOK_PEER_SELECTION_POLICY.json`, full-book candidate/calibration files |
| Preliminary failure retention | `preliminary_algorithm_v1_replay.py`, `preliminary_run/`, preliminary manual ledger |
| Manual object/pair/view/role decisions | `manual_*_ledger.csv`, `MANUAL_REVIEW_EVENT_LOG.json` |
| Hard failure and outcome | `hard_failures.json`, `SA1_REVIEW.md`, `RESULT.txt` |
| Parse, ADS, manifest, stop and seal | terminal control JSON files created last |

All ledgers use unique decision IDs. The terminal checker validates counts, identifiers, image decodability, mask dimensions, pair completeness, and outcome consistency before sealing.
