# P608 R14A evidence-only control reseal root audit

Formal verdict: `ROOT_ACCEPT_R14A_CONTROL_RESEAL / SA3_PASS_READY_FOR_MAIN_A_LOCAL_PASS_ACCEPTANCE`

## Authorization and execution

- Source root: `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P608-01\STRICT_R14_SA3_FRESH_ISOLATED_R105_20260826` (permanently read-only).
- New root: `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P608-01\STRICT_R14A_SA3_EVIDENCE_ONLY_CONTROL_RESEAL_R105_20260826`.
- Root-external controller: `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\tools\P608_R14A_CONTROL_RESEAL_20260826.ps1`.
- Controller SHA-256: `30CE64C3ACF811616F023FFFB47F06FC46B068D632F6B5FB6A75955F6E98A7FB`.
- Static preflight: AST errors 0, compact command/operator hits 0, R14 ordinary 193, exclusions 5/5, material payload 188, new root absent, TeX processes 0.
- The single authorized execution completed once. No retry or second reseal was attempted.

## Lossless material copy

The old root-level control files `WRITE_STOPPED`, `seal_evidence.ps1`, `SEAL_AUDIT.json`, `POSTSEAL_WRITE_CHECKS.json`, and `SEALED_MANIFEST.csv` were excluded as old controls. The R14A root contains no copied `seal_evidence.ps1` or `POSTSEAL_WRITE_CHECKS.json`; its manifest, audit, and marker are newly generated controls.

- R14 material payload: 188 files.
- R14A material payload: 188 files.
- Relative path, bytes, SHA-256, and NTFS LastWriteTimeUtc ticks mismatches: 0.
- New manifest rows: 188; missing, extra, duplicate, or manifest-identity mismatches: 0/0/0/0.

## Final filesystem model

- Material payload: 188.
- Controls: 3 (`SEALED_MANIFEST.csv`, `SEAL_AUDIT.json`, `WRITE_STOPPED`).
- Ordinary files: 191 = 188 + 3.
- Read-only nonconforming files: 0.
- Non-default ADS, pyc/pyo, Python cache directories: 0/0/0.
- `WRITE_STOPPED` is strictly newest; it leads the next-newest file (`SEAL_AUDIT.json`) by 2,946,703 ticks.
- Files with mtime greater than or equal to `WRITE_STOPPED`: 0.
- Root-external post-seal audit performed read-only; no closure, postseal report, script, or self-check was written into R14A after the marker.
- TeX process count: 0.

## Immutable control identities

- `SEALED_MANIFEST.csv` SHA-256: `D543135F6FB6020649F66F9BE89529DB6735D568063A978D4641C97452F9E191`.
- `SEAL_AUDIT.json` SHA-256: `6671159BBAB4B83133DCFF83990C98303410B7BAFFA29C3A2C9D431CA7689147`.
- `WRITE_STOPPED` SHA-256: `CB4773E41522DE3FFAD771B0180F1AC7A6AE6154EF9D593D9F3DB4A35AC635DF`.

R14A repairs only the control-layer ordering defect. It does not rerun or change the accepted R14 SA3 content. Central A_LOCAL_PASS is not claimed here; main-thread acceptance remains required.
