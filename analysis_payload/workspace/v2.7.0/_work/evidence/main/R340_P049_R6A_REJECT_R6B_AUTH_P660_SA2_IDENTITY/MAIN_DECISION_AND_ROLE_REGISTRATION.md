# R340 — P049 R6A rejection / R6B authorization and P660 SA2 registration

- Decision time: `2026-08-27T13:26:19+08:00`.
- Main repository HEAD: `b819e9f4810a2afc04d24a2f0b8bdaa2a3ccb079`; worktree clean.
- Official R111 remains the sole candidate: 4,967,076 bytes, SHA-256 `DAB1062500E39DD2C34C6B4A9FF51CAC2BE0A4C84B2F45F5FB8E645C4BC012D6`.
- TeX-family process count by read-only `Get-Process`: 0.

## P660 R111 R168 read-only SA2 actual identity

The R339 authorization has been consumed by exactly one role:

- HANDOFF_ID: `C-FIG-P660-01-R111-SA2-R168-READONLY-ADJUDICATION-V1`.
- Actual instance: `/root/sa2_fig_p660_r111_r168_readonly_adjudication_v1`.
- Model / effort / fork: `gpt-5.6-sol / xhigh / fork_turns=none`.
- New root: `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\C_visual\evidence\FIG-P660-01\sa2_r111_r168_readonly_adjudication_v1`.
- Dispatch-time root file/dir and UID parent were absent. R111 and current P660 source identities match R339 exactly; TeX0.

The same instance may continue once to a sealed `SA2_NO_SOURCE_CHANGE_READY_FOR_FRESH_SA1` or `FAIL_TO_MAIN_SOURCE_SCOPE`. All R339 whitelist, stale-Goal-card clarification, R168 advisory boundary, old-evidence/status-tool denylist, and PDF/source/Git/central/TeX/second-role prohibitions remain unchanged. No duplicate or restart is authorized.

## P049 R6A independent failure audit

R6A is rejected as `UNSEALED_CONTROLLER_FAILURE_AFTER_PAYLOAD_COPY` and cannot support `A_LOCAL_PASS`.

Main independently verified:

- Controller SHA-256 `EE87B73AABFC37B07D6CD1C0548A717ECF01C16BC0DB3E27956390D1B3E927EB`; AST0; sole invocation exit1, retry0.
- First deterministic error is controller line 168 under `Set-StrictMode -Version Latest`: an empty `Where-Object` result is dereferenced with `.Count` without first being array-normalized.
- Original R6 remains exactly 34 files / 4,333,519 bytes, with canonical UTF-8-no-BOM TAB/LF bytes=4,071 and SHA-256 `B77ADA737922FFA781C84AC7101F707E70C79C60EF33BA031729E8324D2830A9`.
- Failed R6A contains exactly 36 writable files / 4,340,097 bytes: the 34 copied materials plus `COPY_IDENTITY.csv` and `COPY_PROVENANCE.json`.
- R6A copy identity rows=34; source-to-destination path, bytes, SHA-256, and NTFS LastWriteTimeUtc ticks mismatch all 0.
- `PAYLOAD_MANIFEST.json`, `SEAL_AUDIT.json`, and `WRITE_STOPPED.json` are all absent. Root and all 36 files remain writable. The root-external auditor was correctly not run.
- Immutable failure report and handoff identities match the returned bytes/SHA values and are read-only.

The failed R6A root is permanently frozen as an unusable partial copy. It must not be modified, retimestamped, sealed in place, deleted, used as a copy source, or cited as a completed root.

## Exactly-once R6B evidence-only control reseal authorization

Authorize exactly one new root-external PowerShell 7 controller invocation, retry0, to create the startup-absent sibling:

`D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P049-01\STRICT_R6B_SA3_R111_EVIDENCE_ONLY_CONTROL_RESEAL_20260827`

Authorization-time gate: destination file=false, destination directory=false, parent=true.

Required contract:

1. Use `D:\PowerShell7\pwsh.exe -NoProfile`. Controller and auditor remain root-external, UTF-8-safe for Chinese paths, read-only before invocation, and AST errors0. Invocation count1, retry0, no child process, TeX, role, PDF/render, visual, object/pair, manual, semantic, source, Git, central, or second-UID action.
2. Use only the original R6 root as material source. R6A is denylisted even as a copy source. Before mutation, assert R6 exact identity: 34 files, 4,333,519 bytes, canonical bytes4,071, SHA-256 `B77ADA737922FFA781C84AC7101F707E70C79C60EF33BA031729E8324D2830A9`; also assert R6B absent and record the immutable R6A failure identity without touching it.
3. Correct the R6A line-168 defect structurally: every pipeline/filter result that may be empty and whose `.Count` is inspected must be wrapped as an array (for example `@(...).Count`) or counted with an equivalent empty-safe method. Static preflight must explicitly exercise an empty result and prove count0 under StrictMode before the sole invocation.
4. Copy exactly the original 34 material files, preserving relative path, bytes, SHA-256, and NTFS LastWriteTimeUtc ticks. Copy zero controls and zero files from R6A. Add exactly `COPY_IDENTITY.csv` and fully resolved `COPY_PROVENANCE.json`; final payload36.
5. Create exactly three controls: `PAYLOAD_MANIFEST.json`, `SEAL_AUDIT.json`, and one `WRITE_STOPPED.json`; final ordinary39. Manifest must bind all 36 payload files by relative path, bytes, SHA-256, and NTFS ticks, with duplicate/missing/extra/mismatch all 0.
6. Before WSTOP enters the root, set Windows ReadOnly on all 38 existing files and all directories including root. Prepare a fully resolved, ReadOnly WSTOP outside the root with mtime strictly later than every destination item, then move it into the root as the sole and final root-content operation.
7. After WSTOP placement, perform no root content or attribute mutation. A separate root-external read-only auditor must verify ordinary39, payload36, controls3, files39/39 and all directories ReadOnly, one strict-latest WSTOP, at-or-after excluding marker0, postmarker content+attribute writes0, JSON/CSV parse0, ADS/cache/pyc/reparse0, and unchanged source/PDF/Git/TeX identities.
8. Root-external report/handoff must disclose R6A's failure and R6B's corrected empty-safe control path, preserve the already-reviewed SA3 business direction without rerun, and request Main `A_LOCAL_PASS`; they must not self-claim central acceptance.

P049 remains counted as SA3 until Main independently accepts a valid R6B. No build slot is granted.
