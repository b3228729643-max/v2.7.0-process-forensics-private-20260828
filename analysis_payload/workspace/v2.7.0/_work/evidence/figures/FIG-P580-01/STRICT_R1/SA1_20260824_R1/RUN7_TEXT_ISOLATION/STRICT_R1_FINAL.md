# FIG-P580-01 — STRICT_R1_FINAL (05:30 ATTEMPT SUPERSEDED)

> **WITHDRAWN.** This document is internally inconsistent with its own
> `glyph_shape_contact_sheet_manual_review.json` (`PENDING_ALL_SHEETS`,
> 0/15, 0/236). No conclusion, count, lifecycle index, or write-stop claim
> in this attempt is terminal evidence. See `RUN7_ATTEMPT_0530_SUPERSEDED.md`.

- Frozen audited candidate: `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\build\strict_current_r94_fullbook\main_full.pdf`
- Anchor: physical PDF page 628; printed page 615.
- FINAL RESULT: **FAIL → SA2**.
- Machine structural closure: **FAIL**; pair 2145/2145, final-visible empty masks 2, mapping pending/unknown 234/0.
- Manual glyph contact review: 15/15 sheets, 236/236 records; documented negative shapes: G0106, S002; unexpected mismatch: none.
- Final-visible/source occlusion split: 229 visible glyphs; source-only fully hidden G0095, G0096; retained fragment G0106 plus S002.
- Active terminal evidence: 28 critical relation packages and 39 pixel-failure packages. Lifecycle index exact: True; all other retained package folders are explicitly SUPERSEDED in `evidence_lifecycle_index.csv` / `SUPERSEDED_EVIDENCE_INDEX.md`.

## Failed hard gates

- PIXEL_HEIGHT_PASS
- FINAL_VISIBLE_MASK_CLOSURE_PASS
- CHAR_SHAPE_MAPPING_RESOLUTION_PASS
- CHAR_SHAPE_PARENT_MAPPING_PASS
- TEXT_COMPLETENESS_PASS
- EVIDENCE_COMPLETE
- CLEARANCE_FAILURE_COUNT = 22 (illegal text overlap pixels remain 0; clip failures 0).

## Principal disposition

- The B44 accept–reject language is a stale task-card conflict. The source/caption/body and recomputation correctly concern importance-sampling support coverage.
- The real rendered defect is E016: the later boundary-label opaque white fill covers required q_L '=2/5' text. This is TEXT_OCCLUSION/TEXT_COMPLETENESS hard FAIL, not a reason to fake a pre-text mask or to keep empty source glyphs in the final-visible inventory.
- No business source, frozen PDF, Goal, central state, inventory, or build entry was modified by SA1.

## Terminal evidence entry points

- `machine_final_check.json` / `machine_final_check.md`
- `after_visual_acceptance.md`
- `glyph_shape_contact_sheet_manual_review.md`
- `source_occlusion_ledger.csv` and `text_occlusion_evidence/E016/`
- `active_terminal_critical_relations.csv`, `active_terminal_pixel_failures.csv`, and `evidence_lifecycle_index.csv`

WRITE STATE: this document is followed by the terminal write-stop marker; no further SA1 evidence writes are authorized after that marker.
