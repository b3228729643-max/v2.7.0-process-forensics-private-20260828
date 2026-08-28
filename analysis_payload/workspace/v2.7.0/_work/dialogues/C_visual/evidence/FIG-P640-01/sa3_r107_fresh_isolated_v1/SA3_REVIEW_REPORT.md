# FIG-P640-01 SA3 R107 fresh isolated review report

## Assigned scope

Independently inspect only FIG-P640-01 in official R107 using the authorized PDF, current main figure source, necessary adjacent chapter context, goal and strict evidence specifications. Write only this fresh isolated evidence root. Do not read any earlier P640/P639 evidence, central state, inventories, task packets, histories or other UIDs; do not run TeX, build, edit source, modify main state, delegate or claim acceptance authority.

## Completed

- Exact R107 identity and page mapping confirmed: 817 pages, 4,967,249 bytes, required SHA256, physical 690 / printed 677 / Figure 33.7.
- Source/PDF/chapter semantics independently checked for ACF `rho^(2k)`, ESS ratio `(1-rho^2)/(1+rho^2)` and the strict boundary approach `|rho|→1−`.
- Native PDF render set produced without TeX or resize-based measurement: 200dpi full page, native 300dpi full page, figure, standalone, panels, grayscale, page integration and all-element measurement overlay.
- Machine denominator frozen: 145 glyphs; 20 visible PDF drawing records; 28 semantic leaves (`15 TEXT + 10 GRAPHIC + 1 GRAPHIC_MATH_RULE + 2 BACKGROUND`); 378 unordered pairs; 42 critical relations; 12 overlap candidates totaling 5843 native pixels.
- Manual per-ID ledgers completed: 145 glyphs, 28 objects, 20 drawing records, 42 critical relations, 12 overlap candidates, 24 peer/role/script groups, 9 views and 16 hard gates.
- All 29 glyph contact sheets and all 42 critical relations at native-1x and 8x were actually opened. All referenced raw masks and evidence paths are inside this root.
- Candidate overlap count reconciled transparently; current machine/manual/report denominators agree at 5843 candidate pixels, 0 true illegal pixels and 0 unresolved pixels.

## Files changed

Only the isolated evidence root was created and populated. No authority source, chapter, PDF, build artifact, central state, inventory or other UID was modified. The complete immutable inventory and SHA256 values are recorded in `ARTIFACT_MANIFEST.sha256`; the final seal records its hash.

## Decisions

`SA3_REVIEW_OUTCOME=CANDIDATE_PASS_PENDING_MAIN_ACCEPTANCE`  
`LOCAL_PASS_COUNTED=false`  
`GLOBAL_PASS_COUNTED=false`

R168 hard-font review finds no tofu/missing glyph, wrong glyph/codepoint/math semantics, actual unreadability, visibly severe imbalance, real clipping or illegal overlap. Nominal pixel/category/peer differences remain preserved as advisories and do not independently fail this review. All 12 automated overlap candidates are manually classified `MASK_CONTAMINATION` false positives from actual opaque backgrounds or intended chart geometry; canonical illegal overlap is zero.

## Unresolved

NONE within the assigned UID and evidence scope. Main-thread acceptance remains deliberately pending because SA3 has no authority to count or publish a pass.

## Validation

The seal workflow parses every CSV, checks expected row counts and unique IDs, verifies all referenced evidence paths are ordinary openable files, checks N/C(N,2), glyph/contact/drawing/math-rule/critical denominators, validates candidate-pixel arithmetic and report/result consistency, enumerates ADS and cache/pyc absence, writes and reparses a SHA256 manifest, and creates `WRITE_STOPPED` strictly last. The machine verification result is recorded in `SEAL.json`.

## Next action

The main thread should review this candidate package and either accept it explicitly or return FIG-P640-01 to SA2. It must not infer a counted local/global pass merely from this SA3 candidate label.
