# R164｜FIG-P602-01 v3C full-evidence root acceptance

- Main verdict: `ROOT_ACCEPTED_STRICT_FAIL_G032_H06_TO_SA2_SOURCE_R3_STATIC`.
- This accepts the sealed evidence identity and the strict FAIL route; it is not `C_LOCAL_PASS` or global PASS.
- Candidate identity: one A4 page, 41,240 bytes, SHA-256 `203977543DB0F41686A955D33D83A55BA272A7AAE07599AED58227914019EE2C`.
- Fresh denominator: 30 objects, 154 glyphs, 435 unordered pairs, 16 critical pairs, 28 peers, 3 roles, 30 clips, 4 views and 12 hard gates.
- Sole failure: `G032` (`一`) is visually complete but measures 36 x 4 px under the unchanged `CJK_FULL` minimum-height gate of 30 px; hard gate `H06` fails.
- Sealed source root: 900 ordinary files, 898 manifest rows, payload/control/self/seal `882/16/1/1`; path/bytes/SHA/exact NTFS mtime, parse/open, ADS/cache, read-only and strictly-latest marker checks pass.
- Fresh acceptance root: `ROOT_ACCEPTED_STRICT_FAIL_G032_H06`, acceptance-check failures `0`.
- Manual-ledger audit: the evidence builder does not emit `manual_*`; the validator reads those ledgers without generating or overwriting reviewer/decision/note fields. All expected manual IDs occur exactly once and all 435 pair observations are nonblank and unique.
- Source remains uncommitted. Central inventory remains `43 SA1 / 55 SA2 / 0 SA3 / 1 A_LOCAL_PASS` because P602 was already in SA2.
- Authorized next scope: the same P602 source only, `STATIC_ONLY`, to remove the G032 low-profile wording exposure without changing semantics, thresholds or taxonomy. No TeX, commit or fresh role is authorized.

Accepted evidence:

- `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\C_visual\evidence\FIG-P602-01\sa2_r2_controlled_build_v3c\02_native_evidence_r1\HANDOFF.md`
- `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\C_visual\evidence\FIG-P602-01\sa2_r2_controlled_build_v3c\03_root_acceptance_r1\ROOT_ACCEPTANCE.json`
- `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\C_visual\evidence\FIG-P602-01\sa2_r2_controlled_build_v3c\03_root_acceptance_r1\HANDOFF.md`
