# R481 — P683 SA1 control-reseal V1 static rejection and V2 correction authorization

Timestamp: `2026-08-28T08:02:30+08:00`

## Decision

Main rejects the frozen P683 V1 control-reseal scripts at the static gate. No controller or auditor invocation is authorized or consumed, the required sibling root remains absent, and the accepted P683 fresh-SA1 business result remains unchanged. P683 stays at SA1 and may not start SA3.

The frozen V1 scripts remain immutable and ReadOnly:

- controller: `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\C_visual\control\P683_R115_SA1_CONTROL_RESEAL_V1\P683_CONTROL_RESEAL_CONTROLLER.ps1`, 20,452 bytes, SHA-256 `867DACB351C91C36E6882337FA096C086FAAE7B021C3E6887B3E06418623F10B`;
- auditor: `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\C_visual\control\P683_R115_SA1_CONTROL_RESEAL_V1\P683_CONTROL_RESEAL_AUDITOR.ps1`, 15,544 bytes, SHA-256 `7ABF727DED70C8CB6CAB9B8CD3CE992356635E2331616F4EC7773BD4C6447743`.

## Deterministic V1 failure

All 35 rows in the rejected source root's `MANIFEST.csv` use a leading `.\` path. V1 line 180 only replaces backslashes with forward slashes, so for example `.\INPUT_IDENTITY.txt` becomes `./INPUT_IDENTITY.txt`. The actual recursive file set uses `INPUT_IDENTITY.txt` without the leading `./`.

Main's exact read-only test produced:

- manifest rows: 35;
- rows normalized to a leading `./`: 35;
- first manifest value: `./INPUT_IDENTITY.txt`;
- first actual value: `INPUT_IDENTITY.txt`;
- case-sensitive set difference: 70.

V1 therefore deterministically throws `OLD_MANIFEST_SET_MISMATCH` at line 204. This happens before the new root creation at line 206, although the script would already have written `SOURCE_ROOT_BEFORE.csv` outside the root at line 170. Sending the frozen execution token would consume the single attempt without producing a compliant reseal, so Main expressly withholds it.

One preliminary Main read-only probe used a `Split-Path -LiteralPath ... -Parent` combination that this PowerShell build rejected as an incompatible parameter set. It wrote nothing. Main repeated the test with `System.IO.Path.GetDirectoryName`; the values above are the definitive result.

## V2 static-only correction authorization

C may create new root-external V2 controller and auditor files under the same HANDOFF, operation, destination root, and count model, while keeping V1 frozen. This authorization is for static preparation only; V2 controller/auditor invocation counts must remain `0/0` and the new evidence root must remain absent until a later explicit Main ACK.

Required canonical relative-path function:

1. replace every `\` with `/`;
2. repeatedly remove every leading `./`;
3. reject an empty value, rooted/absolute value, empty segment, `.` segment, or `..` segment;
4. preserve case and compare expected/actual sets case-sensitively;
5. use the canonical value throughout imported material rows, safe source/destination joins, `COPY_IDENTITY`, resolved `COPY_PROVENANCE`, `PAYLOAD_MANIFEST`, expected sets, and actual sets in both controller and auditor.

V2 must include a StrictMode-safe static microtest showing that manifest representatives `.\top.txt` and `.\nested\child.txt` compare with actual representatives `top.txt` and `nested/child.txt` with case-sensitive set difference 0. It must also run the same canonicalization against the real rejected manifest and report rows 35, leading-dot rows 35 before canonicalization, canonical duplicate groups 0, and canonical expected-versus-actual set difference 0.

All other frozen contract requirements remain unchanged:

- copy only the 35 old manifest-bound material files and copy zero old controls;
- add `COPY_IDENTITY` and resolved `COPY_PROVENANCE`, yielding payload 37;
- controls exactly `PAYLOAD_MANIFEST`, `SEAL_AUDIT`, and multiline one-key-per-line no-BOM `WRITE_STOPPED`, yielding ordinary 40;
- bind relative/resolved paths, bytes, SHA-256, Creation/LastWrite FILETIME, manifest SHA, roots, counts, and preserved verdict;
- set all files/directories/root ReadOnly before the single final staged-marker move;
- require WSTOP strict-latest over files, directories, and root with at-or-after excluding marker 0;
- perform no post-marker root content or attribute write;
- independently recompute source-root before/after identity, destination post-marker state, JSON/CSV parse, ADS, cache/pyc, and reparse gates;
- destructive actions, retry loops, TeX/build, process management, PDF/render/business/manual/math/semantic reruns, source/Git/central writes, SA3, second UID, and second role remain forbidden.

V2 must return its new paths, bytes, SHA-256, ReadOnly status, PowerShell 7 AST result, move/delete/retry/TeX/process sites, real-manifest canonicalization test, exact-root/stage/result absence gates, and invocation counts `0/0`, then pause for Main review.

## Concurrent authorized work

A/P126 continues only its already-authorized single-source STATIC_ONLY patch to `fig_v1_c08_coordinate.tex`; no P126 TeX/build/commit/fresh role has been authorized. Inventory remains `32 SA1 / 31 SA2 / 0 SA3 / 37 local pass`; strict-final remains `0/99`.
