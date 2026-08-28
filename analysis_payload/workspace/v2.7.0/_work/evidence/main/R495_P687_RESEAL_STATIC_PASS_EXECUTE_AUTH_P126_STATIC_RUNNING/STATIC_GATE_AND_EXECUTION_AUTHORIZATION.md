# R495 — P687 control reseal static acceptance and execute-once authorization

- Time: `2026-08-28T10:29:41+08:00`
- HANDOFF: `C-FIG-P687-01-R115-SA2-R168-READONLY-ADJUDICATION-CONTROL-RESEAL-V1`
- Operation: `P687_R115_SA2_EVIDENCE_ONLY_CONTROL_RESEAL_V1`
- P687 remains `SA2`; preserved verdict is only `SA2_NO_SOURCE_CHANGE_READY_FOR_FRESH_SA1`.

Main independently read the complete frozen controller and auditor and confirmed their identities: controller 23,208 bytes/SHA-256 `F4E859ECFF8AB8D57CF7E1BFCDA95EC13FA337F92AC1021E0B20B93C683F775F`; auditor 19,121 bytes/SHA-256 `BB5387B352FC0B68B05A540554FD6E93164F9BF9316E22ECFB2B363986D5654B`; both ReadOnly and PowerShell7 AST-clean. The controller has one `Move-Item`, solely for the externally staged ReadOnly future marker into the fixed destination as the final root operation; the auditor has none. No destructive, process-management, TeX, or retry-loop path exists.

The reviewed contract closes canonical relative-path rejection and containment, ordinal identity sets, source-root before/after state, exact copy of 37 material files with path/bytes/SHA-256/Creation+LastWrite FILETIME, identity plus resolved provenance, payload 39, controls 3, ordinary files 42, full-tree ReadOnly, an 18-line unique `KEY=VALUE` marker binding manifest and seal hashes, strict-latest ordering including directories/root, at-or-after zero, postmarker zero-change, and CSV/JSON/ADS/cache-pyc/reparse checks. Immediate Main pre-execution gate: destination Leaf/Container/Any=false, Parent=true; artifacts entry count zero; old root 40 files, no child directories, all files and root ReadOnly.

Authorization is narrow and one-shot: run the frozen controller exactly once with retry zero. Only on natural exit code 0 may the frozen auditor run exactly once with retry zero. Any first error ends the chain and preserves the scene. Script edits, second calls, repair, reseal, replacement, business-evidence rerun, source/TeX/build/Git/central/process actions, and fresh-role migration remain forbidden.

P126 continues only its previously authorized STATIC_ONLY line-65 legend-segment patch; no build is authorized by this checkpoint.
