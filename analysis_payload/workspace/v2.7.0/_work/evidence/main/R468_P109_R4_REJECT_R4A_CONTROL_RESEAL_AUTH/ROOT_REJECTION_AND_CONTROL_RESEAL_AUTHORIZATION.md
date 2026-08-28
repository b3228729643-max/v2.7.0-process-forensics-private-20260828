# R468 P109 R4 rejection and R4A control reseal authorization

Timestamp: `2026-08-28T06:01:32+08:00`

## R4 disposition

The original R4 root is formally rejected as `ROOT_REJECT_PREMATURE_MARKER_BEFORE_READONLY_FREEZE`. A disclosed that the intended final WSTOP was created externally and moved into R4 once while the other 38 files and the root directory were still writable. It was not a temporary in-root stage. Although no writes followed the move, the required pre-move readonly-tree gate was not met. In-place repair is forbidden.

Main's read-only checks:

- 39 files = 37 manifest-listed material + old manifest + old WSTOP;
- old manifest 37 rows, duplicate/set/name/bytes/lastwrite mismatch 0;
- old WSTOP 26 physical KEY=VALUE lines, bad/duplicate keys 0;
- only old WSTOP is ReadOnly; the other 38 files and root are writable;
- two canonical full-root snapshots both equal `161ECBDB2153C7497971F3AD2C58A88AB33F12C59B1498EFCE75F204FBE847A0`;
- old manifest SHA-256 `13F530C3BE817C6C50CB64420EB7CB8268E1B83025D9D460F227BC09659F0E5C`;
- old WSTOP SHA-256 `2C48561B31FD652CAA78BD460DE890D8484B458CCFC74AADD6B7D9DB29259614`.

The business/manual PASS direction is preserved but not counted. P109 remains SA1.

## One-time R4A authorization

- HANDOFF_ID: `A-R115-P109-SA1-FRESH-ISOLATED-CONTROL-RESEAL-V1-20260828`
- Operation: `P109_R115_SA1_EVIDENCE_ONLY_CONTROL_RESEAL_V1`
- New root: `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P109-01\STRICT_R4A_SA1_R115_EVIDENCE_ONLY_CONTROL_RESEAL_20260828`
- Immediate gate: Leaf=false, Container=false, Any=false, Parent=true.

Only the 37 old manifest-listed materials may be copied. Old manifest/WSTOP copy count must be 0. Resolved copy identity and provenance make payload39; exactly three controls make ordinary42. No business evidence may be rerun. A must report static controller/auditor identities and pause for explicit Main ACK before the single invocation.

Inventory remains `32 SA1 / 32 SA2 / 0 SA3 / 36 local pass`; strict final remains `0/99`.
