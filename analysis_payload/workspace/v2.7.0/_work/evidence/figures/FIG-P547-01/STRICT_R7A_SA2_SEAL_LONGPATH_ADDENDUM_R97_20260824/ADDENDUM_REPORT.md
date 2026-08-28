# FIG-P547-01 R7A long-path seal addendum

## Corrected seal statement

R7's statement that all superseded files were hash-covered is incorrect. Its Python `Path.rglob()/is_file()` payload enumeration omitted 60 pre-existing long-path files. The sealed R7 directory remains read-only; this independent R7A package records and binds the omitted set without editing R7.

The correction is limited to seal coverage. It does not change the local figure evidence result or expand it into an official PASS. The recommendation remains `LOCAL_PASS_TO_ROOT_BUILD`, subject to the already-required root full-book build and fresh independent SA1 audit.

## Bound identities

| Bound item | SHA256 |
|---|---|
| R7 `evidence_manifest.json` | `9CDE425189C7149504C95DF4658B5572ED06EA2379CC6897178EC4E04AEE032E` |
| R7 `MANIFEST.sha256` | `E09227E2B66CE15F76891ADF7F943AB90402F27DF0CEADC37DECA2A2232A2C0F` |
| R7 `WRITE_STOPPED.md` | `01871051A57F9A64F0EE6D6935A41198D7350D74414EDB1B0A677643B8C4F80A` |
| Authorized figure source | `DF3D4415EDC56D02E056CAE0F3E38830DF28E781BC67ECDFB69863C5038F1600` |

No business source or R7 file was written during R7A.

## Exact path-set reconciliation

PowerShell/.NET enumerated R7 with the Win32 extended path prefix and `System.IO.Directory.EnumerateFiles`:

- actual files: 6,732;
- actual unique relative paths: 6,732;
- R7 evidence-manifest payload entries: 6,669;
- R7 MANIFEST rows and unique listed paths: 6,670;
- listed paths plus `MANIFEST.sha256` and `WRITE_STOPPED.md` metadata: 6,672;
- omitted paths: 60;
- stale listed paths: 0.

The closure is exactly `6672 covered + 60 omitted = 6732 actual`. Path-set digests are:

- actual: `211C829C37B566A79B79535CF8887F36972AB394DA56DBF33D39E56D32D86677`;
- covered: `E03FC3C47604EAF835CFE494D6EB21767CB4373FBAFCAFF7796E782EF5CE2218`;
- omitted: `9A4E9C231BCC7E9220702C331E5430F71233CBB97F478A4F5779003DE726C9E6`.

All 6,670 declared R7 MANIFEST entries were rehashed through long-path-safe file streams: parse failures 0, duplicate paths 0, missing references 0, SHA256 mismatches 0. The 6,669 evidence-manifest entries also have duplicate paths 0 and evidence-to-MANIFEST hash mismatches 0.

## Exact omitted set

`R7_OMITTED_LONGPATH_60.csv` contains one row per omitted file with relative path, byte count, SHA256, local and UTC CreationTime, local and UTC LastWriteTime, generation, classification, R7 coverage flag, and post-WSTOP flag.

- GEN2 superseded `final_audit/low_profile_calibration/texmfvar/`: 30 files;
- GEN3 superseded `final_audit/low_profile_calibration/texmfvar/`: 30 files;
- all superseded: 60;
- active omissions: 0;
- omissions outside the two exact prefixes: 0;
- zero-byte omitted files: 0;
- omitted bytes: 139,079,066.

Omitted CreationTime UTC ranges from `2026-08-24T08:19:13.6811759Z` to `2026-08-24T08:33:10.5251156Z`. Omitted LastWriteTime UTC ranges from `2026-08-24T08:12:43.0630669Z` to `2026-08-24T08:31:05.8893264Z`. R7 `WRITE_STOPPED.md` has LastWriteTime UTC `2026-08-24T09:29:49.4822348Z`. Therefore:

- R7 files last-written after WSTOP: 0;
- R7 files created after WSTOP: 0;
- omitted files last-written after WSTOP: 0.

The omitted files are LuaTeX/font-loader cache artifacts in already superseded GEN2/GEN3 audit generations. They are not active glyph, graphic, relation, pair, PDF, source, report, or signed-ledger evidence. This is why the coverage correction does not alter the local repair recommendation.

## R7A seal contract

Before sealing, this addendum has exactly six nonzero payload files: two scripts, the 60-row CSV, the reconciliation JSON, this report, and the terminal. `evidence_manifest.json` lists all six; `MANIFEST.sha256` covers those six plus the evidence manifest and rehashes every entry; `WRITE_STOPPED.md` is written last. Final closure is `6 payload + 1 evidence manifest + 1 MANIFEST + 1 WRITE_STOPPED = 9 actual files`.
