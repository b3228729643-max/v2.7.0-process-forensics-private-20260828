# Sealed evidence root plan

This root belongs only to `C-FIG-P670-01-R114-SA3-FRESH-ISOLATED-V1` for `FIG-P670-01`.

The reviewed input is the official R114 full-book PDF and the fixed current single source named in `input_identity.csv`. No LaTeX source, build tree, Git state, central inventory, other UID, other role, or historical P670 evidence was changed or used.

The visible denominator is frozen in `denominator_freeze.json`; the 63 rows are in `visible_object_inventory.csv`, and all 1,953 unordered pairs are in `all_unordered_pairs.csv`.

Objective extraction and rendering are separate from manual judgment. `generate_mechanical_evidence.py` produced only machine evidence. Manual judgments were written after the images were actually opened and are recorded in `manual_object_review.csv`, `manual_pair_candidate_review.csv`, `manual_semantic_review.md`, `after_overlap_adjudication.md`, and `after_visual_acceptance.md`.

`WRITE_STOPPED` is the final root content operation. Its manifest hash authenticates `MANIFEST.csv`.
