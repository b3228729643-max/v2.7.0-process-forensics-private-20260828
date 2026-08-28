# R110 R168 SA2 read-only adjudication report

## assigned_scope

Fresh read-only R168 adjudication of `FIG-P632-01` in the official R110 full-book PDF, using only the current figure source, the necessary current V5-C04 adjacent text, the active goal's strict visual protocol, and evidence generated in this startup-absent role root.

## completed

- Confirmed the official R110 PDF identity: 817 pages, 4,967,063 bytes, SHA-256 `B49C5CA920DDEF6C0CD004B2581EAF710F4D1E1115BB459A324A84594B3831F3`.
- Confirmed the current main figure-source identity: 9,022 bytes, SHA-256 `1670F496E6CEBBF5636AC5BC97474A50FBA83811FFA2AAAAEF0CF8227BE8C8EB`.
- Independently located the current figure on physical page 682 / printed page 669 as Figure 33.2 from its current formulas and caption.
- Opened the complete page, native 300 dpi figure/caption, grayscale rendering, semantic/object/text overlays, candidate overlay, mask contact sheet and five nearest-neighbor 8x critical ROIs.
- Established 31 visible semantic objects and all 465 unordered pairs.
- Performed an explicit manual judgment for all 31 object IDs and all 465 pair IDs after opening the evidence.
- Independently verified numerical values, conditional-normal semantics, contour geometry, arrows/relationships, labels, caption, adjacent text, clipping, overlap, readability, font embedding and page integration.
- Adjudicated 8,196 pairwise candidate pixels as role-aware mask contamination or permitted topological contact; true illegal overlap pixels are 0 and unresolved candidates are 0.

## files_changed

No project/source/PDF/TeX file changed. All created files are evidence/report/seal material confined to the authorized role root. Source changes = 0; TeX/LuaLaTeX/latexmk = 0; Git = 0; central state/inventory = 0.

## decisions

- Hard defects under R168: none.
- Missing/tofu/wrong codepoint: none.
- Actually unreadable or obviously imbalanced text: none.
- True clipping or illegal overlap: none (`CLIP_PIXEL_COUNT=0`, `OVERLAP_PIXEL_COUNT=0`).
- Wrong numerical, probability-model or geometry semantics: none.
- Sealed decision: `P632_SA2_NO_SOURCE_CHANGE_READY_FOR_FRESH_SA1`.

## unresolved

None.

## validation

- Input identity and page count matched the dispatch exactly.
- Figure-source identity matched the dispatch exactly.
- Page text extraction, embedded-font inventory and native raster views agree.
- Manual object table: 31/31 unique IDs.
- Mechanical pair table: 465/465 unordered pairs.
- Manual pair table: 465/465 unique IDs.
- Machine nonzero-pair set and manual `MASK_CONTAMINATION_CONFIRMED` set: exact 19-ID match.
- Candidate-pixel closure: 8,196 classified, 0 true collision, 0 unresolved.
- Full page, crop, grayscale and page integration: no hard defect.

## next_action

Fresh SA1 may be dispatched by the parent coordinator using this sealed no-source-change result. This SA2 does not start SA1 or any other role.

## exact identities

- Report: `R110_R168_SA2_READONLY_ADJUDICATION_REPORT.md`
- Overlap adjudication: `after_overlap_adjudication.md`
- Visual acceptance: `after_visual_acceptance.md`
- Manual objects: `manual_object_judgments.csv`
- Manual pairs: `manual_pair_judgments.csv`
- Handoff: `HANDOFF_C-FIG-P632-01-R110-SA2-R168-READONLY-ADJUDICATION-V1.json`
- Manifest: `MANIFEST_R110_R168_SA2_READONLY_ADJUDICATION.json`
- Final write-stop marker: `WRITE_STOPPED`
