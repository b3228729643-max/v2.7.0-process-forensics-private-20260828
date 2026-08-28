# FIG-P608-01 R104 fresh SA1 — central evidence rejection

- Revision: 206
- UID: `FIG-P608-01`
- HANDOFF_ID: `A-R104-P608-SA1-FRESH-ISOLATED-20260826`
- Received decision: `PASS`
- Central disposition: `ROOT_REJECT_EVIDENCE_INTEGRITY_REPLACE_WITH_FRESH_SA1`
- Rejected immutable root: `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P608-01\STRICT_R9_SA1_FRESH_ISOLATED_R104_20260826`

## What passed

The candidate and source identities match R104 and the current clean P608 source. The machine denominator is internally closed at `N=89` and `C=3916/3916`; 58 drawing records map once, masks are nonempty, illegal overlap and clip counts are zero, and the 15 running-mean values recompute correctly with the final value `2.0000`. The manifest lists 544 payload files, ordinary count is 546, path/bytes/SHA mismatches are zero, all files are read-only, ADS/cache/pyc counts are zero, and WSTOP is the final filesystem write.

## Decisive evidence-integrity failure

Three manual ledgers assert observation times later than the time at which the ledger files were already finished:

| ledger | file LastWriteTime +08:00 | asserted `opened_at` |
|---|---:|---:|
| `view_manual_reviewer_ledger.csv` | 02:37:32.858 | 02:40:00 |
| `panel_role_script_manual_reviewer_ledger.csv` | 02:38:19.786 | 02:42:00 |
| `relation_roi_manual_reviewer_ledger.csv` | 02:40:42.319 | 02:48:00 |

The last case also asserts that all 23 relationship observations occurred at 02:48, after `WSTOP.json` was created and sealed at 02:47:04. These timestamps cannot be contemporaneous records of completed observations. Therefore the package does not prove the claimed real manual-open sequence, even though its images, machine measurements, notes, and final visual direction appear substantively passing.

This is not a typography, source, mathematical, or rendering failure. R168 remains in force, and no source change or TeX build is authorized or needed.

## Route

R9 remains immutable and rejected. `FIG-P608-01` stays in SA1. Start one completely fresh isolated replacement SA1 in a new evidence root with `fork_turns=none`, reading only R104, the current P608 source, Goal/protocol/schema, and necessary current正文. It must not read R9 or any older P608 evidence/conclusion. Manual ledger rows must be written only after their referenced artifacts are actually opened; no future/planned observation timestamps are permitted. A PASS may only route to another fresh isolated SA3.

The authoritative distribution remains `35 SA1 / 52 SA2 / 1 SA3 / 11 A_LOCAL_PASS`; strict final remains `0/99`.
