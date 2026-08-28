# P049 R6A evidence-only control reseal failure report

## Scope and authority

- UID: `FIG-P049-01`
- Preserved role identity: `A-R111-P049-SA3-FRESH-ISOLATED-20260827`
- Operation: one-time root-external PowerShell 7 evidence-only control reseal authorized by `MAIN_R336`, with the canonical source-set identity corrected by `MAIN_R337`.
- Original material root: `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P049-01\STRICT_R6_SA3_FRESH_ISOLATED_R111_20260827`
- Failed destination root: `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P049-01\STRICT_R6A_SA3_R111_EVIDENCE_ONLY_CONTROL_RESEAL_20260827`

No PDF, TeX, business evidence, object denominator, pair table, manual ledger, semantics, role, Git state, central state, second UID, or TeX process was created or rerun by this operation.

## Static preflight

- Host: `D:\PowerShell7\pwsh.exe -NoProfile`, version `7.6.4`.
- Controller: 15,000 bytes, SHA-256 `EE87B73AABFC37B07D6CD1C0548A717ECF01C16BC0DB3E27956390D1B3E927EB`, AST errors 0, read-only before invocation.
- Auditor: 15,046 bytes, SHA-256 `12A33840A31E15A21EE257BCC35CE10245463067E8F524ABA61EAF0734B3AFA8`, AST errors 0, read-only before invocation.
- Destination file absent and destination directory absent immediately before invocation.
- Corrected original-root identity: 34 files, 4,333,519 bytes; canonical row byte length 4,071; actual TAB/LF UTF-8-no-BOM SHA-256 `B77ADA737922FFA781C84AC7101F707E70C79C60EF33BA031729E8324D2830A9`.
- Controller invocation count before execution: 0.

## Sole invocation and first failure

- Controller invocation count: 1.
- Retry count: 0.
- Exit code: 1.
- First error: `The property 'Count' cannot be found on this object.`
- Static location consistent with the observed write boundary: controller line 168 applies `.Count` directly to an empty `Where-Object` result while `Set-StrictMode -Version Latest` is active. The failure occurred after the 34 material files and the two permitted new payload files were created, and before any manifest or seal control was written.
- Per the authorization, execution stopped immediately. The controller was not modified or rerun, and the read-only auditor was not run against an unsealed root.

## Failed-root filesystem facts

- Destination root exists.
- Ordinary files: 36.
- Total bytes: 4,340,097.
- Files present: exactly the copied 34 materials plus `COPY_IDENTITY.csv` and `COPY_PROVENANCE.json`.
- `PAYLOAD_MANIFEST.json`: absent.
- `SEAL_AUDIT.json`: absent.
- `WRITE_STOPPED.json`: absent.
- External marker-preparation file: absent.
- Writable files: 36/36.
- Writable directories including root: 1/1.
- Root classification: `UNSEALED_CONTROLLER_FAILURE_AFTER_PAYLOAD_COPY`.

## Identity preservation

- `COPY_IDENTITY.csv` rows: 34.
- Source-to-destination relative path, bytes, SHA-256, and NTFS LastWriteTimeUtc ticks mismatches: 0.
- Resolved provenance source and destination roots are exact.
- Provenance records the corrected source set SHA-256 `B77ADA737922FFA781C84AC7101F707E70C79C60EF33BA031729E8324D2830A9` and canonical byte length 4,071.
- The original R6 root remained read-only input and retained its 34-file canonical identity.

## Decision

`R6A_CONTROL_RESEAL_FAILED_NO_RETRY`.

The prior SA3 content direction remains historical evidence only: N=152, C=11,476, manual 135 glyph / 17 path / 122 relation candidates, preseal CLEAR. Neither R6 nor R6A is a sealed root, so this report does not claim `A_LOCAL_PASS`, integrated pass, or final pass.

## Next action

Main must decide whether to authorize a new sibling evidence-only control reseal. The failed R6A root must not be modified, retimestamped, sealed in place, or used as a completed root. No further invocation is authorized by this report.
