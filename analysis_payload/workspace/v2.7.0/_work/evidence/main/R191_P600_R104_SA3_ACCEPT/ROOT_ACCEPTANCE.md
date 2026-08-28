# FIG-P600-01 R104 fresh isolated SA3 中央接受

- Central revision: `191`
- UID: `FIG-P600-01`
- Role packet: `C-FIG-P600-01-R104-SA3-FRESH-ISOLATED-REPLACEMENT-V2`
- Evidence root: `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\C_visual\evidence\FIG-P600-01\sa3_r104_fresh_isolated_replacement_v2`
- Official candidate: R104 physical page 651 / printed page 638 / Figure 32.4
- Candidate identity: 817 A4 pages, 4,967,222 bytes, SHA-256 `E5C871642FBDDBEC6508BE1B61BD911FE281CA5ACFBD16B0449B13357770A641`
- Root verdict: `ACCEPT_C_LOCAL_PASS`

## 1. Sealed identity and mechanical closure

- Evidence ordinary files: `562 = 560 manifest entries + MANIFEST.csv + WRITE_STOPPED`.
- Main independently recomputed every listed path, byte count, SHA-256 and NTFS 100 ns FILETIME: mismatch `0`; missing `0`; extra `0`.
- All 560 payload files and `MANIFEST.csv` are read-only; read-only failures `0`.
- Non-default NTFS streams `0`; `__pycache__` / `.pyc` / `.tmp` `0`.
- `WRITE_STOPPED` is strictly newer than every preceding file by `563,245,321` ticks and declares no writes after the marker.
- Final validator reports 28/28 machine checks PASS and records `manual_files_modified_by_validator=0`, `manual_decisions_generated_by_validator=0`. Search of all evidence scripts finds no manual-ledger generator; the machine builder explicitly records `manual_decision_files_generated_by_script=0`.

## 2. Denominators and manual coverage

- Semantic objects: `N=23` = 11 text/formula parents + 12 graphic parents.
- Complete unordered parent pairs: `C(23,2)=253/253`; machine and manual pair ID sets are identical.
- Visible PDF drawing records: `18/18`, individually mapped to the 12 graphic parents and individually reviewed.
- Glyphs: `197/197`; all have safe IDs, non-empty masks, sheet/cell bindings and exact 8x evidence.
- Critical pairs: `15/15`; clip rows `23/23`; object rows `23/23`; view-role rows `32/32`; font rows `8/8`; math/content rows `12/12`; peer-role rows `8/8`.
- All appropriate primary IDs are complete and unique; view-role composite keys are `32/32` unique; blank IDs and blank notes are `0`; decisions contain no unresolved or hard failure.
- Repeated categorical notes such as `VISIBLE_COMPLETE_PURE` and `NO_ILLEGAL_CONTACT_OR_CLEARANCE_BREACH` are accepted as homogeneous observations, not as forbidden machine-generated defaults: every row remains bound to a distinct ID and evidence cell, scripts do not create or rewrite the manual ledgers, critical/design contacts have relation-specific notes, and the central visual checks below independently found no contradiction.

## 3. Object-granularity adjudication

The accepted R104 SA1 used `N=29`, treating all 18 low-level PDF drawing records as separate graphic objects alongside 11 semantic text/formula parents. This SA3 independently used 12 semantic graphic parents, so `N=23`, while retaining and reviewing all 18 low-level drawing records in `drawing_map_machine.csv` and `manual_drawing_review.csv`.

This is an explicit parent/primitive granularity difference, not an omitted visible element. All 18 primitives map exactly once; all 23 semantic parents have masks; all 253 parent pairs are covered; 15 tight or connected relations have dedicated 1x/8x evidence. The contraction therefore does not hide a semantic object, illegal overlap, crop or relation failure and is accepted for this UID.

## 4. Independent visual and semantic check

Main opened the 200 dpi whole page, native 300 dpi color crop, grayscale crop, measurement overlay, glyph contact sheets 01/09/17 and representative critical overlays `PAIR0001` and `PAIR0244`.

- The two states, proposal boxes, central `min(a,b)`, two accepted-flow arrows and four proposal connectors have a clear and unambiguous reading order.
- `a=π(x)q(x,y)`, `b=π(y)q(y,x)` and both accepted-flow formulas equal to `min(a,b)` are correct; the statement that detailed balance is sufficient but not necessary for stationarity matches the caption and neighboring text.
- No missing/tofu/wrong-codepoint glyph, actual unreadability, gross visible imbalance, real crop or illegal overlap was seen under Revision 168.
- Machine results are consistent with the images: illegal overlap `0 px`, clip `0 px`, minimum independent text clearance `8 px`, text/graphic clearance `23 px`, internal text/border clearance `9 px`.
- The grayscale rendering preserves all arrows, formulas and hierarchy.

## 5. Central decision

`FIG-P600-01` passes the independent R104 SA3 chain and is accepted into the shared local-pass bucket. It is the sixth accepted local pass. This is not the global 99/99 release verdict.

- Inventory transition: `39 SA1 / 53 SA2 / 2 SA3 / 5 A_LOCAL_PASS` → `39 SA1 / 53 SA2 / 1 SA3 / 6 A_LOCAL_PASS`.
- C-local completion becomes `3/46` (`FIG-P602-01`, `FIG-P637-01`, `FIG-P600-01`).
- Strict final remains `0/99`.
- TeX and business-source writers remain disabled.
