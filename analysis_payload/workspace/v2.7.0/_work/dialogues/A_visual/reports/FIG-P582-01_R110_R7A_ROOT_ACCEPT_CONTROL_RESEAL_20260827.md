# FIG-P582-01 R110 R7A evidence-only control reseal

## Verdict

`ROOT_ACCEPT_R7A_SA1_CONTENT_PASS_READY_FOR_FRESH_ISOLATED_SA3`

R7's content-PASS direction is preserved. The one authorized control reseal closed the read-only and strict-last-marker failure in a new root without rerunning or modifying PDF, visual, object, pair, manual, or semantic evidence.

## One-time execution identity

- Source R7 root: `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P582-01\STRICT_R7_SA1_FRESH_ISOLATED_R110_20260827`
- New R7A root: `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P582-01\STRICT_R7A_SA1_R110_EVIDENCE_ONLY_CONTROL_RESEAL_20260827`
- The new root did not exist at the static gate or invocation boundary.
- Host: `D:\PowerShell7\pwsh.exe -NoProfile`
- Controller: `P582_R7A_CONTROL_RESEAL_CONTROLLER_20260827.ps1`, 18,932 bytes, SHA-256 `EF2884D0E547775AE9B0F230E681FD8F339F64FC2CB07000865F11C728F149A1`, read-only.
- External auditor: `P582_R7A_CONTROL_RESEAL_EXTERNAL_AUDITOR_20260827.ps1`, 13,754 bytes, SHA-256 `A97C3C899B9A9B3345EEF9366112846444D517650FC9C2C6F868C618AA5E9528`, read-only.
- PowerShell 7 AST errors: controller 0; auditor 0.
- Controller invocation count: 1; retry count: 0; start `2026-08-26T18:23:34.1956154Z`; end `2026-08-26T18:23:38.8936607Z`; duration 4,698.045 ms; exit 0.
- Auditor invocation count: 1; start `2026-08-26T18:23:58.0612416Z`; end `2026-08-26T18:24:00.5922676Z`; duration 2,531.026 ms; exit 0.

## Lossless copy identity

- R7 manifest-bound material copied: 140 / 140.
- Old controls copied: 0 / 3 (`payload_manifest.json`, `payload_manifest.sha256`, `WRITE_STOPPED`).
- `COPY_IDENTITY.csv` rows: 140; duplicate path: 0.
- Source-to-destination relative path / bytes / SHA-256 / NTFS mtime ticks mismatch: 0.
- `COPY_PROVENANCE.json` contains the resolved absolute source and destination roots and no unresolved placeholder.

## Final count and seal model

- Payload: 142 = 140 material + `COPY_IDENTITY.csv` + `COPY_PROVENANCE.json`.
- Controls: 3 = `PAYLOAD_MANIFEST.json` + `SEAL_AUDIT.json` + `WRITE_STOPPED`.
- Ordinary files: 145.
- Payload manifest rows / unique paths: 142 / 142; duplicate/missing/extra/path/bytes/SHA/ticks mismatch: 0.
- Payload-manifest SHA-256: `C51709AE19EBFEB7AE9EBC4680302DCB27F3BEFFD9B85512F18A305826156CE4`.
- Seal-audit SHA-256: `44A51EEDD5E61CEFF6A192ACA3FB43F7C970A22CECC904600D68E1554D604148`.
- Ordinary files read-only: 145 / 145.
- Directories read-only: 5 / 5, including the new root.
- JSON/CSV/PNG parse failures: 0 / 0 / 0; PNG denominator: 116.
- ADS, pyc, cache-directory, and reparse-point findings: 0 / 0 / 0 / 0.
- `WRITE_STOPPED` count: 1; strict-latest margin: 2,184,335 ticks; files at/after marker excluding marker: 0; post-marker root content writes: 0.

## Independent root-external audit

- Audit JSON: `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\reports\FIG-P582-01_R110_R7A_EXTERNAL_ROOT_AUDIT_20260827.json`
- Audit JSON identity: 1,143 bytes; SHA-256 `A2D150B9B9E1D21412EA09CA030A119A134D7A8E3E44EEBB6827630B9A38357B`; read-only.
- Auditor verdict: `ROOT_ACCEPT_R7A_SA1_CONTENT_PASS_READY_FOR_FRESH_ISOLATED_SA3`; errors: 0.

## Route

Freeze R7 and R7A. Keep the accepted SA1 content PASS and request one different completely fresh isolated R110 SA3 with a new root. This reseal did not start SA3 or write source, Git, TeX, central state, or inventory.
