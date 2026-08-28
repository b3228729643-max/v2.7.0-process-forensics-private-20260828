# FIG-P580-01 R108 SA1 R2A evidence-only control reseal audit

## Verdict

`ROOT_ACCEPT_R2A_SA1_CONTENT_PASS_READY_FOR_FRESH_ISOLATED_SA3`

This audit accepts only the lossless R2-to-R2A evidence control reseal. It does not rerun or replace the fresh SA1 business review. R2 remains permanently read-only and historically rejected for the WSTOP/manifest timestamp tie.

## Authorized execution

- New root: `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P580-01\STRICT_R2A_SA1_FRESH_ISOLATED_R108_EVIDENCE_ONLY_CONTROL_RESEAL_20260826`
- Root existence before invocation: false.
- Controller: `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\tools\P580_R2A_ONE_TIME_CONTROL_RESEAL.ps1`
- Controller identity: 12,514 bytes; SHA-256 `937184AFC204EA0AA9EB1068BC4566D53B6BAFA25D8F80AD2B96F5BB997FB801`; AST errors 0; read-only.
- Host: `D:\PowerShell7\pwsh.exe -NoProfile`.
- Unique execution grant: `P580_R2A_EVIDENCE_ONLY_CONTROL_RESEAL_EXPLICITLY_GRANTED`.
- Invocation count: 1; exit code: 0; output: `P580_R2A_CONTROLLER_COMPLETE`.
- Retry count: 0.

## Copy identity and count model

- R2 manifest intersection material payload: 45.
- Copied R2 controls: 0.
- `COPY_IDENTITY.csv`: 45 rows, 7,719 bytes, SHA-256 `219A8615FD318A38F972EC43C7F1C109DC901346B143C24FB5429A5E13CD9F53`.
- R2 source to R2A destination path/bytes/SHA/NTFS mtime-ticks mismatches: 0.
- New provenance payloads: `COPY_IDENTITY.csv` and `COPY_PROVENANCE.md`.
- Final payload: 47 = 45 material + 2 provenance.
- Controls: 3 = CSV manifest + SHA manifest + WSTOP.
- Ordinary files: 50 = 47 + 3.

## Manifest and filesystem closure

- `PAYLOAD_MANIFEST.csv`: 47 rows, 6,291 bytes, SHA-256 `640DF1A75C3EAD9DBD6F9173D3C3142A0408EA1119F41D3F9344D1B40D0D824F`.
- `PAYLOAD_MANIFEST.sha256`: 47 rows, 4,726 bytes, SHA-256 `6EEA24C956489F0A51A996506993FE10D0DA727A648C688C10C6B6AA608B9503`.
- CSV↔SHA↔filesystem path/bytes/SHA/mtime-ticks missing, extra, or mismatch: 0.
- Provenance source and target roots resolve to the authorized absolute R2/R2A paths.
- Read-only ordinary files: 50/50.
- ADS/cache/pyc/reparse: 0/0/0/0.
- No new postseal audit, closure, or script file exists inside R2A. The filename `machine/after_font_audit.csv` is one of the 45 byte-identical material payloads and is not a new control.

## Final marker

- `WRITE_STOPPED`: 411 bytes; ticks `639233411386066849`.
- Maximum non-WSTOP ticks: `639233411365640212` (`PAYLOAD_MANIFEST.sha256`).
- Strict margin: `20,426,637 ticks` (2.0426637 seconds).
- Files at or after WSTOP other than WSTOP: 0.
- Writes inside the root after WSTOP: 0.

The current P580 source remains SHA-256 `F0ECC9B28361A2AE73AF085A4958AD09F8F94575D789B8F776C55631FD45E161`; worktree is clean; TeX processes and invocations for this reseal are zero. The preserved SA1 content result is PASS-direction (`N=32`, `C=496`, R168 hard failures 0). SA3 was not started.
