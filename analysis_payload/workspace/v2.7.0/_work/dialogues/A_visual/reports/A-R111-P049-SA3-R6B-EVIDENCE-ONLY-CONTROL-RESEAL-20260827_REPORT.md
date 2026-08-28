# P049 R6B evidence-only control reseal report

## Identity and scope

- Handoff/operation identity: `A-R111-P049-SA3-R6B-EVIDENCE-ONLY-CONTROL-RESEAL-20260827` / `R6B_EVIDENCE_ONLY_CONTROL_RESEAL`.
- Figure UID: `FIG-P049-01`.
- Source material root: `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P049-01\STRICT_R6_SA3_FRESH_ISOLATED_R111_20260827`.
- Sealed destination root: `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P049-01\STRICT_R6B_SA3_R111_EVIDENCE_ONLY_CONTROL_RESEAL_20260827`.
- The failed R6A root remained permanently untouched and was not used as a copy source.
- This operation copied evidence and rebuilt only the control layer. It did not rerun or modify PDF rendering, visual review, object denominators, unordered pairs, manual ledgers, semantics, TeX, source, Git, central state, roles, or any second UID.

## R6A failure disclosure and R6B correction

R6A remains `UNSEALED_CONTROLLER_FAILURE_AFTER_PAYLOAD_COPY`: it stopped after 34 copied materials plus two new payload files because StrictMode applied `.Count` directly to an empty `Where-Object` result. It has no manifest, seal audit, or WSTOP and is not a valid sealed root.

R6B was created as a new startup-absent sibling. Its controller and auditor use the new R6B identity and explicitly arrayize every potentially empty pipeline/filter result before reading `.Count`. Before the sole invocation, PowerShell 7.6.4 StrictMode executed an empty-filter probe with result count 0. Static source and AST lint found zero unsafe pipeline-to-`.Count` sites.

## Frozen scripts and invocation

- Controller: `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\controllers\P049_R6B_control_reseal_20260827.ps1`; 15,314 bytes; SHA-256 `FBB208CB4F79549A33F964CAC01BABF27B42271AA098A16994F65EAB6C37C61A`; AST errors 0; read-only before execution.
- Auditor: `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\controllers\P049_R6B_control_reseal_auditor_20260827.ps1`; 15,409 bytes; SHA-256 `CBFADE96450D7C42ACDF962FBDB8A5C31F71C27A309B6DE7476BFDAD94936AB0`; AST errors 0; read-only before execution.
- Controller host: `D:\PowerShell7\pwsh.exe -NoProfile`, version 7.6.4.
- Controller invocation count: 1; retry count: 0; child/TeX invocation count: 0; exit code: 0.
- Independent root-external auditor invocation count: 1; exit code: 0.

## Source and copy identity

- Original R6 material: 34 files / 4,333,519 bytes.
- Canonical row bytes: 4,071, using actual TAB separators, ordinal forward-slash relative paths, decimal bytes, uppercase SHA-256, decimal NTFS LastWriteTimeUtc ticks, LF, UTF-8 without BOM, and one final LF.
- Canonical SHA-256: `B77ADA737922FFA781C84AC7101F707E70C79C60EF33BA031729E8324D2830A9`.
- `COPY_IDENTITY.csv`: 34 rows.
- Source-to-destination relative path, bytes, SHA-256, and NTFS tick mismatches: 0.
- Old controls copied: 0.
- Original R6 zero-write identity check: PASS.

## Final R6B count and seal model

- Material files copied: 34.
- New payload files: `COPY_IDENTITY.csv` and resolved `COPY_PROVENANCE.json`.
- Final payload: 36.
- Controls: exactly `PAYLOAD_MANIFEST.json`, `SEAL_AUDIT.json`, `WRITE_STOPPED.json`.
- Final controls: 3.
- Final ordinary files: 39, totaling 4,350,902 bytes.
- `PAYLOAD_MANIFEST.json`: 36 rows; duplicate, missing, extra, path, bytes, SHA-256, and NTFS tick mismatches all 0.
- Manifest SHA-256: `86685010773B60DD9998AED88FDA1AF66A9341DA7B7264256B320D7DB6BC0CDE`.
- Seal-audit SHA-256: `4D30323753C822A2901F271186898FA61180C6D80F375F77CA9B5C92EB046A0F`.
- WSTOP SHA-256: `9EA74FA26D1E97E50668EE8899410FAC2D49682C60E4D14AA906196E1CF81D78`.

## Independent read-only audit

- Files read-only: 39/39.
- Directories including root read-only: 1/1.
- Unique `WRITE_STOPPED.json`: PASS.
- WSTOP strict-latest margin: 10,310,932 ticks in the independent auditor; a separate parent readback also found a positive approximately 10.31-million-tick margin.
- Files at or after marker excluding marker: 0.
- Post-marker content or attribute writes: 0.
- JSON/CSV parse failures: 0.
- ADS/cache/pyc/reparse counts: 0.
- PDF identity: unchanged and PASS.
- P049 TeX source identity: unchanged and PASS.
- A worktree Git identity: branch `v2.7.0/dialogue-a-visual`, HEAD `d8f1e5fb15abdf09ce5ead5245c270b43abd5741`, worktree/index clean.
- `latexmk`/`lualatex`/`luatex`/`luahbtex` processes: 0.

## Preserved SA3 content direction

R6B preserves without rerun the prior fresh SA3 content direction: N=152, C=11,476, genuine manual ledgers for 135 glyphs, 17 paths, and 122 relation candidates, with preseal hard-gate direction CLEAR. This evidence-only reseal does not independently recreate or revise those business conclusions.

## Decision and route

`ROOT_ACCEPT_R6B_EVIDENCE_ONLY_CONTROL_RESEAL`.

The only requested route is `MAIN_A_LOCAL_PASS_REVIEW`. This report does not self-grant `A_LOCAL_PASS`, does not change central inventory, and does not authorize any further UID, role, TeX run, source edit, Git operation, or reseal.
