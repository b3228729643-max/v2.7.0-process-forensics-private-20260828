# R336 — P049 R111 SA3 root rejection and evidence-only control reseal authorization

> R337 correction: every expected canonical set hash `72FF48C1...F1D3B` below is superseded by `B77ADA737922FFA781C84AC7101F707E70C79C60EF33BA031729E8324D2830A9`. The prose algorithm always intended actual TAB bytes; the earlier diagnostic accidentally hashed literal backtick-plus-`t` characters. See `_work/evidence/main/R337_P049_R6_CANONICAL_HASH_CORRECTION_P657_SA3_PASS_AUDIT/P049_CANONICAL_IDENTITY_CORRECTION.md`.

- Decision time: `2026-08-27T13:05:07+08:00`
- SA3 HANDOFF_ID: `A-R111-P049-SA3-FRESH-ISOLATED-20260827`
- Actual instance: `/root/p049_r111_fresh_sa3`; the instance stopped and will not retry.
- Original R6 root: `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P049-01\STRICT_R6_SA3_FRESH_ISOLATED_R111_20260827`

## Content direction retained

- Fresh business denominator `N=152` (`135` glyph + `17` foreground path), complete unordered pairs `C=11,476`.
- Genuine manual ledgers: glyph `135/135`, path `17/17`, relation candidates `122/122`.
- `preseal_audit.json` is `CLEAR`; all 22 asserted checks are true.
- Manual summary reports true illegal overlap, clipping, missing/tofu/wrong-codepoint, unreadability, material geometry/semantic error, and obvious imbalance all 0; `sa3_result=PASS`, explicitly pending central assessment.
- This content direction is preserved but is not yet `A_LOCAL_PASS` because the evidence root is not sealed.

## Decisive root rejection

The sole seal helper stopped on its first error before any root write because Windows PowerShell misread the no-BOM script's Chinese root path and returned `Directory.Exists=false`. Main independently confirmed:

- Original root exists and has exactly 34 ordinary files / one directory including root.
- `PAYLOAD_MANIFEST.json` absent; every `WRITE_STOPPED*` absent; postseal auditor not run.
- Writable files `34/34`; writable directories `1/1`.
- No completed seal/control set exists. The original R6 root is permanently classified `UNSEALED_CONTROL_FAILURE` and must remain zero-write.
- The 34 files total 4,333,519 bytes. Canonical identity hash is `72FF48C16BBAC7D4DA57E9555480230BDB493FE0E23F9FBC01E9BA1C126F1D3B`, over ordinal relative-path rows encoded UTF-8 without BOM as `relative_path_forward_slash<TAB>bytes<TAB>SHA256<TAB>LastWriteTimeUtcTicks<LF>`.
- Root-external preseal report: 3,818 bytes / SHA-256 `ECD8A41DE1480613B55A53613E3DD92042A2FE545BDE1AB5D0700CFFF85D936E`.
- Root-external preseal handoff: 2,649 bytes / SHA-256 `AEF86C33D59F2440ACDEF900B572CFA45757593885F0B5576C2AD114DD7D36F1`.
- Those two external files describe expected sealing and cannot substitute for the actual failure state.

## One-time evidence-only reseal authorization

Authorize exactly one root-external PowerShell 7 controller invocation, no retry, to create this startup-absent sibling root:

`D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P049-01\STRICT_R6A_SA3_R111_EVIDENCE_ONLY_CONTROL_RESEAL_20260827`

Authorization-time gate: new root file absent, directory absent, parent present.

Required controller contract:

1. Use `D:\PowerShell7\pwsh.exe -NoProfile`; save the controller with an encoding that preserves Chinese paths. Static AST errors must be 0. Invocation limit 1, retry 0, no child process, TeX, visual/business rerun, or role launch.
2. Treat the original R6 root as read-only input. Recompute and assert exactly the 34 files and the canonical identity above before copying; do not read the misleading external preseal report/handoff as authority for a sealed state.
3. Copy exactly those 34 files to the new root, preserving relative path, bytes, SHA-256, and NTFS LastWriteTimeUtc ticks. Copy zero old controls.
4. Add exactly `COPY_IDENTITY.csv` and resolved `COPY_PROVENANCE.json` as two new payload files. Final payload count must be 36.
5. Add exactly three controls: `PAYLOAD_MANIFEST.json`, `SEAL_AUDIT.json`, and one `WRITE_STOPPED.json`; final ordinary count must be 39. The manifest must bind all 36 payload files by relative path, bytes, SHA-256, and NTFS ticks with duplicate/missing/extra/mismatch all 0.
6. All payload and pre-marker control files plus all directories including root must have Windows ReadOnly set before the marker enters the root. Prepare the fully resolved marker outside the root, make it ReadOnly, guarantee its NTFS mtime is strictly later than every destination item, then move it into the root as the sole and final root-content operation.
7. After marker placement, perform no root content or attribute write. A separate root-external read-only auditor must verify ordinary39, payload36, controls3, all files/directories ReadOnly, unique strict-latest WSTOP, at-or-after excluding marker0, postmarker content/attribute writes0, JSON/CSV parse0, ADS/cache/pyc/reparse0, and source/PDF/Git/TeX identities unchanged.
8. Root-external final report/handoff must honestly state this is an evidence-only control reseal preserving SA3 content direction and requesting Main `A_LOCAL_PASS`; they must not claim central acceptance themselves.

P657 R111 fresh isolated SA3 continues independently. No TeX or build slot is granted.
