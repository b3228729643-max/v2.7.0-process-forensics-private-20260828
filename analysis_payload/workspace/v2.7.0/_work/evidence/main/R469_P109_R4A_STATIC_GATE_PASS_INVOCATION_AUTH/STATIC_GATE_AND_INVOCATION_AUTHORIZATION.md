# R469 P109 R4A static gate and invocation authorization

Timestamp: `2026-08-28T06:08:46+08:00`

Main independently verified the frozen root-external scripts:

- Controller: 18,592 bytes, SHA-256 `C04BBB5581B9A933B5EA621F835E53C2649949B0138806F3D58D8AACD210A11B`, ReadOnly, PowerShell AST errors 0.
- Auditor: 14,530 bytes, SHA-256 `D5A9F2DAEC0E6399ECCC52790F5835EE4D0492E285B203878A8EFEDC9860FF90`, ReadOnly, PowerShell AST errors 0.
- Remove/process-management/TeX/loop sites: 0.
- Controller marker Move-Item sites: 1; auditor Move-Item sites: 0.
- Fixed R4A root, controller result and external staged marker were absent at Main's immediate gate.

Main inspected the actual sequence: 37 copied materials plus identity/provenance make payload39; manifest and seal audit complete premarker contents; all 41 premarker files plus root are made and verified ReadOnly; the marker is created outside R4A, validated as 26 nonempty KEY=VALUE lines, future-dated and ReadOnly; its one external-to-root move is the final root operation; postmarker and source-root snapshots are then read-only checked. The separate auditor recomputes copy, manifest, provenance, readonly, marker order, postmarker/source stability and hygiene.

Authorization: exactly one controller invocation, retry0/first-error stop. Only on controller natural success may exactly one auditor invocation run. No script edits, business rerun, rejected-R4 write, TeX/source/Git/process/role action is authorized.

Inventory remains `32 SA1 / 32 SA2 / 0 SA3 / 36 local pass`; strict final remains `0/99`.
