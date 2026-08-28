# Revision 540 — P126 R17A acceptance and atomic commit authorization

- Goal authority SHA-256: `4FB8A2B615AC7EDA635D0F8DACACE9CF88692153A049D4A04BE06B56BCB53F1A`
- Inventory remains `30 SA1 / 30 SA2 / 0 SA3 / 40 local pass`; strict final `0/99`; B `66/66`.
- P689 remains permanently frozen as accepted `C_LOCAL_PASS`.
- P126 remains SA2 after this decision. Main accepts a local SA2 result, not a final local-pass inventory transition.

## R17A accepted root

Accepted root:

`D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P126-01\STRICT_R17A_SA2_FORGET_PLOT_PATCH_R115_EVIDENCE_ONLY_CONTROL_RESEAL_20260828`

Main independent root-external read-only recomputation:

- Files `150`; directories including root `11`; total file bytes `106,307,712`; non-ReadOnly files/directories `0/0`.
- COPY_IDENTITY rows `145`; old-to-copy missing/extra/five-field mismatch `0/0/0`.
- PAYLOAD_MANIFEST rows `147`; actual payload `147`; missing/extra/five-field mismatch `0/0/0`.
- Source snapshot entries/SHA-256: `158` / `BDE4D4BC9BD905C681EE7395852405B28F3786CB151380BBE5CD785912EC2943`.
- Destination snapshot entries/SHA-256: `161` / `5120FF1DC9204361E2487096B108C4AE666F2F4AAB76EBA97D4F5C3A69A4C04F`.
- WRITE_STOPPED: 1,546 bytes/SHA-256 `AD615D390F8A460A987B628A379DFAED0912856A863CC27919CE12FAA3CBAA3E`; 30 lines/30 unique keys; bad/duplicate/BOM `0/0/0`; ReadOnly; strict-latest margin `2,999,776,302` ticks; at-or-after excluding marker `0`.
- Source/destination nondefault ADS `0/0`; destination ADS items/streams `161/150`.
- CSV `6`/parse failure `0`; JSON `8`/parse failure `0`; pyc `0`; `__pycache__` `0`; designated texcache `1`; reparse `0`; staged marker absent.
- Controller and auditor result bindings to the live source/destination snapshots passed.

Root controls:

- COPY_IDENTITY.csv: 85,971/SHA `F99DBEBCC6F766EA71E992BFBDACF3DECD73C30284288A13365DB024B758348B`/ReadOnly.
- COPY_PROVENANCE.json: 1,446/SHA `D14A43F8A9CA6CEE2EAA25F95E52D0C44DAACA77CDA19AF1B017B3B774BF3D06`/ReadOnly.
- PAYLOAD_MANIFEST.csv: 24,509/SHA `26B7B9E377CC3F4D32FEBFB449CC5DF39A8F89A276AE7ABC9BF1AC0340702CC1`/ReadOnly.
- SEAL_AUDIT.json: 1,483/SHA `63146008C524F909D9D6DE82DAB41A8ED9234DB8149F034F751E576363B633A7`/ReadOnly.
- WRITE_STOPPED: 1,546/SHA `AD615D390F8A460A987B628A379DFAED0912856A863CC27919CE12FAA3CBAA3E`/ReadOnly.

Root-external run artifacts:

- Controller script: 18,655/SHA `96520D7AFC5056B3B7C1D3C5E6C4F7F9CDA11E9AEA6B4B974B6B65318A2F15D7`/ReadOnly; invocation1/retry0/natural exit0.
- Auditor script: 24,425/SHA `EB53C90FF836ED085F4ACD07D3F92011831E9910E95CAA04E24C996A28235F9A`/ReadOnly; invocation1/retry0/natural exit0.
- Controller result: 2,295/SHA `21C1126F87DAA619DF5E9F3C63AFE74D6F6FBB6BAF67BA05B5CD4A9862CB7AE2`; writable but root-external. Its current identity is bound by the independent auditor and Main, so this does not reject the sealed root.
- Auditor result: 2,333/SHA `625531584D8D33135DE9D6765CE15185B60E2C3D189E11BF67343823C0891AED`/ReadOnly.
- Report: 816/SHA `9C4BB6450A664CAA21B4E3CDD64FD1CBBBFDF894C1E3CD0D10B3BBA544B80C9E`/ReadOnly.
- Handoff: 346/SHA `23C6F09EE1FF9EE77D0937F587E992F7D6B45AD94B43F5B23237EDA09EE698D5`/ReadOnly.

Main's first audit command had a PowerShell parser-only whitespace error before any operation. The corrected read-only audit was rerun from the beginning and produced the accepted results above; neither attempt wrote the root.

## Source and Git boundary

- Worktree: `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\worktrees\dialogue_A_visual`.
- Branch: `v2.7.0/dialogue-a-visual`; current HEAD/authorized parent: `a19fe984d7bde5d982081899c599c635e9965bed`.
- Name-only: exactly `src/绘图源码/第01册_数学基础与统计学习基本理论/V1-C08/fig_v1_c08_coordinate.tex`.
- Index empty; numstat `38+/31-`; `git diff --check` clean.
- Source: 4,686 bytes/SHA-256 `2887758F5CC94987BE750E1EC53B555FB88CE8F71B7260CABBE0A17DDF237405`.
- Main read the complete diff. It contains the accepted rotated positive-definite contours, exact alternating coordinate updates, label protections/positions, distinct disconnected x2 legend handler, and `forget plot` exclusions validated by the R17 PDF and sealed N60/C1770 review.

## Atomic commit grant

Authorize exactly one commit:

- Stage only the exact source above.
- Exact subject: `fix(fig-p126): correct coordinate descent geometry and legend`.
- No amend, second commit, push, merge, cherry-pick, rebase, TeX/build, source edit, evidence mutation, central write, fresh role, or second UID.
- Return commit SHA, parent, subject, exact name-only/numstat, source identity, and postcommit clean worktree/index; then pause.
