# P654 R11 root test results

- R11 sealed package: PASS, 1060 ordinary files = 1057 payload + 3 controls.
- R11 manifest identity: PASS, CSV/JSON/current-filesystem counts 1057/1057/1057; missing/extra/duplicate/path/bytes/SHA-256/decimal-string-ticks differences 0.
- R10→R11 base-copy identity: PASS, 1052/1052 relative paths; missing source/destination, bytes, SHA-256 and NTFS tick mismatches all 0.
- New R11 payload inclusion: PASS, both manifests include `R11_copy_seal.ps1`, `R11_validator.ps1`, `R11_COPY_PROVENANCE.md` and both base-copy identity files.
- Independent validator identity/logic: PASS, SHA-256 `EED27FA5934B64CEFF18E26EB8DB5047A6DCC5FD5C9F78A47BFE576F13AD3909`; static audit confirms independent filesystem enumeration and no seal-script invocation.
- Parse/open: PASS, 24/24 CSV, 71/71 JSON, 856/856 PNG and 1/1 PDF; PDF is one A4 page, 43,385 bytes, SHA-256 `86712CDD9610F2136976064317F333B73D4A2FF8E22D5FEF904C915DD2787260`.
- ADS/PYC/cache: PASS, non-default ADS 0, `.pyc` 0 and named cache directories 0.
- Seal order: PASS, `WRITE_STOPPED.json` is uniquely latest; files written at or after it excluding itself 0.
- Content differential audit: PASS, N=116, glyph=95, graphic=21, C=6670, critical=50, taxonomy=95→10 groups with D/E=0, target `FRM_TRIAL_005` H=22/area=297, and 192 manual decisions; systematic representative/extreme counterexample sampling found no content contradiction.
- Provenance declaration: FAIL, `R11_COPY_PROVENANCE.md` contains literal `$src`/`$dst` instead of resolved roots.
- Terminal JSON denominator declaration: FAIL, `json_excluding_write_stopped=69` conflicts with the actual 70 JSON files after excluding only `WRITE_STOPPED.json`; its neighboring CSV field uses the all-files count.
- Root verdict: `ROOT_REJECT_R11`.
