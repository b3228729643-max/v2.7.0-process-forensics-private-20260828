# FIG-P602-01 — SA2 R2 v3C native evidence review

## Outcome

`STRICT_FAIL_G032_H06`

This is a complete current-candidate evidence review and a strict FAIL. It is not `C_LOCAL_PASS`, `A_LOCAL_PASS`, or global PASS, and it does not authorize a central state/inventory write.

## Frozen identities

- Candidate PDF: 41,240 bytes; SHA256 `203977543DB0F41686A955D33D83A55BA272A7AAE07599AED58227914019EE2C`.
- Current P602 source: SHA256 `2B15B4BEEA7A922FEE24259678DBAE2A54915955915E6714A350122A6251E349`.
- Standalone wrapper: SHA256 `AFE3464AEA950331908CD3C56DD0392A6D5010138C4EE9341B78F7FD3E9F7279`.
- Direct-build START: SHA256 `DC0A69FD5BF9E3B09E76388F9CB896D5F7F72FE72DA26B0B8344B33AC3D1F5DE`.
- Direct-build RESULT: SHA256 `307A6AFDDDF67D2AD4B80009D8CD067FFF4FE760C24A6227F8E17722906F5F3E`.

No TeX command was run while constructing or reviewing this native evidence root.

## Fresh current denominator

- 30 objects: 17 text/formula and 13 graphics.
- 154 glyphs.
- 435 unordered object pairs: exactly `C(30,2)`.
- 16 critical pairs.
- 28 peer rows.
- 3 role rows.
- 30 clip rows.
- 4 required view rows.
- 12 hard gates.

The denominator was enumerated from the current one-page v3C standalone PDF. The standalone output contains no caption; the earlier 32-object/496-pair denominator was not imported.

## Manual review coverage

The reviewer opened the native color and grayscale figure; five nearest-neighbor 8x landmarks; all 13 glyph contact sheets; all four object contact sheets; all 18 pair contact sheets; and all 16 critical pair cards. The manual ledgers contain explicit current-ID rows with nonblank unique observations:

- objects 30/30;
- glyphs 154/154;
- unordered pairs 435/435;
- critical pairs 16/16;
- peers 28/28;
- roles 3/3;
- clips 30/30;
- views 4/4;
- hard gates 12/12.

No manual ledger was populated by a loop, default/global boolean, machine-to-manual copy rule, or repeated template note.

## Strict failure

`G032` is U+4E00 `一` in O-T07. Its native glyph mask is nonempty and visually shows the complete intended horizontal stroke at 36×4px and 78 ink pixels. Its frozen class is `CJK_FULL`, whose unchanged height threshold is 30px. The native ink height is 4px, so:

- manual visual decision: PASS;
- machine threshold: FAIL;
- hard-gate decision H06: FAIL;
- overall evidence outcome: FAIL.

The glyph was not reclassified as a natural/low-profile form, and its visual completeness was not used to override the hard gate.

## Other results

- empty glyph masks: 0;
- empty object masks: 0;
- machine pair failures: 0;
- manual pair failures: 0;
- critical-pair failures: 0;
- peer failures: 0;
- role failures: 0;
- clip failures: 0;
- view failures: 0.

All twelve intended connector/border intersections stay inside their explicit design whitelist. The four critical text-line pairs preserve their required separation. The acceptance/rejection semantics, dashed rejection self-loop, borders, formula, labels, arrow tips, 1x views, grayscale view, and 8x landmarks remain complete.

## Preserved control-history facts

- `qa/BUILDER_ATTEMPT_01_FAIL.md` records a pre-evidence builder sorting-assertion defect; no manual result was produced by that failed attempt.
- `qa/validation_report.json` and `qa/VALIDATOR_ATTEMPT_01_FAIL.md` preserve the first validator assertion defect involving peer compound keys.
- `qa/validation_report_r2.json` is the corrected mechanical validation result and has zero failed checks.

Both corrections were confined to evidence tooling/validation. Candidate PDF, business source, machine measurements, and manual decisions were not modified by them.
