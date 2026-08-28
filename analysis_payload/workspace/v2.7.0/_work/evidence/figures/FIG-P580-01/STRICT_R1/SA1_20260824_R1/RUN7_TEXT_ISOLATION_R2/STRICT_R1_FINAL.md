# FIG-P580-01 — STRICT_R1_FINAL

- Frozen audited candidate: `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\build\strict_current_r94_fullbook\main_full.pdf`
- Anchor: physical PDF page 628; printed page 615.
- FINAL RESULT: **FAIL → SA2**.
- Machine evidence closure: **True**; candidate machine gate result: **FAIL**; pair 2145/2145, final-visible empty masks 0, mapping pending/unknown 0/0.
- Manual glyph contact review: 15/15 sheets, 234/234 records; documented negative shapes: G0061; unexpected mismatch: none.
- Manual visual review: 63/63 rows; font harmony=False, grayscale=False, page integration=False; reviewer source is `manual_visual_harmony_ledger.csv`, current metrics join `manual_visual_harmony_ledger_CURRENT_MACHINE_JOIN.csv`, reconciliation `manual_visual_harmony_metadata_reconciliation.csv`.
- Final-visible/source occlusion split: 228 visible glyphs and 6 visible necessary substrings; source-only glyphs G0095, G0096, G0106; source-only substrings S002; retained partial glyphs none.
- Active terminal evidence: 50 critical relation packages and 30 pixel-failure packages. Lifecycle index exact: True; all other retained package folders are explicitly SUPERSEDED in `evidence_lifecycle_index.csv` / `SUPERSEDED_EVIDENCE_INDEX.md`.

## Failed hard gates

- PIXEL_HEIGHT_PASS
- CHAR_SHAPE_PARENT_MAPPING_PASS
- TEXT_COMPLETENESS_PASS
- TEXT_HALO_GRAPHIC_COVERAGE_PASS
- TEXT_TRANSLUCENT_LABEL_GRAPHIC_COVERAGE_PASS
- SAME_CLASS_RATIO_PASS
- ROLE_RATIO_PASS
- FONT_VISUAL_HARMONY_PASS
- VISUAL_HARMONY_PASS
- GRAYSCALE_PASS
- PAGE_INTEGRATION_PASS
- CLEARANCE_FAILURE_COUNT = 17 (illegal text overlap pixels remain 0; clip failures 0).

## Principal disposition

- The B44 accept–reject language is a stale task-card conflict. The source/caption/body and recomputation correctly concern importance-sampling support coverage.
- The real rendered defect is E016: the later boundary-label opaque white fill covers required q_L '=2/5' text. This is TEXT_OCCLUSION/TEXT_COMPLETENESS hard FAIL, not a reason to fake a pre-text mask or to keep empty source glyphs in the final-visible inventory.
- No business source, frozen PDF, Goal, central state, inventory, or build entry was modified by SA1.

## Terminal evidence entry points

- `machine_final_check.json` / `machine_final_check.md`
- `after_visual_acceptance.md`
- `glyph_shape_contact_sheet_manual_review.md`
- `manual_visual_harmony_ledger.csv`, `manual_visual_harmony_ledger_CURRENT_MACHINE_JOIN.csv`, and `manual_visual_harmony_metadata_reconciliation.csv`
- `R2_TERMINAL_DOCUMENTATION_REISSUE.md` (documentation-only reissue provenance, if present)
- `source_occlusion_ledger.csv` and `text_occlusion_evidence/E016/`
- `active_terminal_critical_relations.csv`, `active_terminal_pixel_failures.csv`, and `evidence_lifecycle_index.csv`
- Retained `*_debug.txt` harness streams are non-active provenance only; each is nonempty and excluded from terminal evidence inventories/lifecycle lists.

WRITE STATE: this document is followed by the terminal write-stop marker; no further SA1 evidence writes are authorized after that marker.
