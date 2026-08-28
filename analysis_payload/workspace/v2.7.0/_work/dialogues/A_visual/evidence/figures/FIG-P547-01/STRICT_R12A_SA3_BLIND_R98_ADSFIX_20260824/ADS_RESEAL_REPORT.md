# FIG-P547-01 ADS mechanical reseal report

- Result: `SA3_INDEPENDENT_PASS_RESEALED_NOT_FINAL`
- Operation: `MECHANICAL_ADS_RESEAL_ONLY_NO_SEMANTIC_REAUDIT`
- Source package: `STRICT_R12_SA3_BLIND_R98_20260824` (read-only and untouched)
- Target package: `STRICT_R12A_SA3_BLIND_R98_ADSFIX_20260824`

## Mechanical failure and exact repair

The source package failed the added mechanical check because `_tmp/texmf-cache/luatexja/extra_notoserifsc-extralight` carried two non-default NTFS data streams: `1.lua.gz` (72,949 bytes) and `1.luc` (422,176 bytes). Windows ordinary recursive copy retained both streams. Only these two explicitly named streams were removed, and only from the target copy. The target file's ordinary `:$DATA` stream remains present at 0 bytes.

A recursive stream enumeration over every target ordinary file after removal found:

- files scanned before terminal metadata regeneration: 1,861
- non-default stream count: 0
- non-default stream bytes: 0

No broad or recursive stream deletion was used.

## Ordinary-file reconciliation

The initial ordinary copy and the source package both contained 1,862 files totaling 137,637,490 bytes. The deterministic tree digest is SHA-256 `42bc2f4cf1833800335ad58d07f637b50038707cfc92570276cdd48374ccd256`; its record format is relative path, NUL, byte length, NUL, ordinary-stream SHA-256, LF, sorted by relative path.

After removing the copied stop marker to begin the authorized reseal, all 1,861 remaining shared paths were compared by ordinary-stream length and SHA-256; mismatch count was 0. Reconstructing the pre-reseal tree with the copied marker record produced the same 1,862-file count, 137,637,490-byte total, and tree digest above.

Six pre-existing seal-metadata files were authorized for regeneration: `WRITE_STOPPED`, `09_manifest/terminal_crosscheck.json`, `09_manifest/manifest.json`, `08_reports/SA3_RESULT.txt`, `08_reports/sa3_final_summary.json`, and `08_reports/SA3_INDEPENDENT_BLIND_REVIEW.md`. Excluding those files, the reused ordinary evidence reconciliation is:

- preserved ordinary evidence files: 1,856
- preserved ordinary evidence bytes: 137,288,966
- source tree SHA-256: `4be1180bfed14b94b761c39c13615a3ac21986f8f7b4ea3ed48aa078c30cb224`
- target tree SHA-256: `4be1180bfed14b94b761c39c13615a3ac21986f8f7b4ea3ed48aa078c30cb224`
- missing, extra, size-mismatched, or hash-mismatched preserved evidence files: 0

This report and `08_reports/sa3_reseal_summary.json` are new reseal metadata. No semantic evidence was regenerated or re-adjudicated.

## Reused closed semantic ledger

The already closed isolated SA3 ledger is reused without semantic re-audit: 23 text parents + 34 vector parents = 57 objects; 1,596 object pairs; 193 glyphs; 71 path records; 2,485 path pairs; 143 commands; and 186 within-record command pairs. G139 remains governed by its recorded multi-owner/20:1 ownership correction and has `missing_stroke_px=0` in the preserved evidence.

The only valid conclusion of this resealed package is `SA3_INDEPENDENT_PASS_RESEALED_NOT_FINAL`.
