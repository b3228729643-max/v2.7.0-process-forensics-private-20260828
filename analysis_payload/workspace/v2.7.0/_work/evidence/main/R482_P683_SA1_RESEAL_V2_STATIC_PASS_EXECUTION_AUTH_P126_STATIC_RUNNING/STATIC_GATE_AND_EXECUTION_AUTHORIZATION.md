# R482 — P683 SA1 control-reseal V2 static gate and one-shot execution authorization

Timestamp: `2026-08-28T08:13:05+08:00`

## Decision

Main accepts the frozen P683 V2 controller/auditor package at the static gate and authorizes exactly one controller invocation with the exact token:

`MAIN_R481_P683_SA1_CONTROL_RESEAL_V2_EXECUTE_ONCE_GRANTED`

Retry is 0. The separate frozen auditor may be invoked exactly once and only after the controller returns natural success. At the first controller or auditor error, C must stop without editing either script, retrying, repairing the target root, or creating a replacement.

## Frozen scripts reviewed in full

- controller: `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\C_visual\control\P683_R115_SA1_CONTROL_RESEAL_V2\P683_CONTROL_RESEAL_V2_CONTROLLER.ps1`, 22,726 bytes, SHA-256 `B14AD45E31670A8BFB79EEF8BB1C689976C7BA4A4911C43D8BC31815ACF28CD6`, ReadOnly, PowerShell 7 AST errors 0;
- auditor: `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\C_visual\control\P683_R115_SA1_CONTROL_RESEAL_V2\P683_CONTROL_RESEAL_V2_AUDITOR.ps1`, 19,145 bytes, SHA-256 `E6577AF3AA949C96C782EA5DF5955BC55196D14CE357E493D1EA18E0E9E6ECA7`, ReadOnly, PowerShell 7 AST errors 0.

Main's independent AST inventory found controller Move-Item 1, New-Item 2, Remove-Item 0, process-management commands 0, While/Do loops 0, and TeX commands 0; auditor Move-Item/New-Item/Remove-Item/process/While-Do/TeX all 0. The single controller Move-Item is the staged ReadOnly WSTOP final insertion.

## Canonical-path gate

Main extracted and executed only the frozen canonicalization/self-test/row-comparison function definitions, without invoking either script. Results:

- canonical self-test case-sensitive diff 0;
- all 8 invalid path representatives rejected;
- equal state-row comparison mismatch 0;
- old manifest rows 35 and pre-canonical leading-dot rows 35;
- canonical duplicate groups 0;
- canonical expected-versus-actual case-sensitive set diff 0;
- first raw `.\INPUT_IDENTITY.txt`, first canonical/actual `INPUT_IDENTITY.txt`.

The canonical value is used through old manifest import, safe source and destination joins, COPY_IDENTITY, COPY_PROVENANCE, PAYLOAD_MANIFEST, and controller/auditor expected/actual case-sensitive sets. Empty, rooted/absolute, empty-segment, dot-segment, and parent-segment paths are rejected.

## Control contract reviewed

The controller verifies the old MANIFEST and WSTOP identities, snapshots the old source root externally, canonicalizes and binds 35 old material files, copies zero old controls, and checks bytes/SHA-256/Creation+LastWrite FILETIME. It adds COPY_IDENTITY and resolved COPY_PROVENANCE, yielding payload 37; creates PAYLOAD_MANIFEST and SEAL_AUDIT; validates parse/hygiene; freezes 39 premarker files and all directories/root ReadOnly; builds a 13-line no-BOM one-key-per-line WSTOP externally with manifest/audit/root/count/verdict bindings and a future FILETIME; performs the sole final Move-Item; and only then writes external snapshots/results. Final ordinary count is 40.

The independent auditor recomputes old-root before/after identity, copy identities, provenance canonical set, manifest set and full identity, seal and marker bindings, full-tree ReadOnly, marker strict-latest over files/directories/root, at-or-after 0, parse/ADS/cache/reparse, and postmarker state equality.

## Immediate preinvoke gate

- rejected old root: 37 files and 4 directories including root; all ReadOnly;
- old MANIFEST SHA-256 `0A96A24F0ED097B6C1B2CBCE2B14860980A95A910E53C9A0FAEF14CCE3792521`;
- old WSTOP SHA-256 `2E15CF2BA14232CCCD1A91CC1A88664122EFCA46B4FCB6CE6C544CBD7A861C55`;
- required new root: Leaf false, Container false, Any false, Parent true;
- V2 artifact directory entry count 0;
- controller invocation 0 and auditor invocation 0 before this authorization.

V1 remains permanently frozen and must not be invoked. This authorization does not permit PDF/render/business/manual/math/semantic reruns, SA3, a second UID/role, TeX/build, source/PDF/Git/central writes, or process management. P683 remains SA1 until Main independently accepts a successful reseal. A/P126 continues only its already-authorized STATIC_ONLY single-source patch.
