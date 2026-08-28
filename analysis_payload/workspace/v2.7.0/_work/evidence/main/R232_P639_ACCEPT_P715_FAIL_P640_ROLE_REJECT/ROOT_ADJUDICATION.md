# Revision 232 root adjudication

Timestamp: `2026-08-26T09:38:40+08:00`

Official candidate remains R106: `src/build/strict_current_r106_fullbook/main_full.pdf`, 817 A4 pages, 4,967,249 bytes, SHA-256 `0FA4A5A0B35D2566D71B5472B49E9B4A8A60CBAE76B3FA744B92783AFC6BC31A`.

## FIG-P639-01

- Accepted result: `MAIN-R105-P639-SA3-FRESH-ISOLATED-20260826` = `PASS`.
- Evidence root: `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\C_visual\evidence\FIG-P639-01\sa3_r105_fresh_isolated_v3_main_20260826`.
- Denominator: `N=80`; all unordered pairs `3160/3160`; illegal overlap, clipping, and empty masks all 0.
- R168 hard review found no missing/tofu/wrong glyph, mathematical-semantic error, unreadability, gross imbalance, real crop, or illegal overlap. The disclosed small-font and fine raster observations remain advisory.
- Mechanical closure: manifest 218 rows, ordinary files 220, path/bytes/SHA mismatch 0, ADS/cache/pyc 0, WSTOP strictly last and later writes 0.
- Root decision: `A_LOCAL_PASS`. Freeze source/evidence/handoff; do not rerun this role.

## FIG-P715-01

- Accepted result: `A-R106-P715-SA1-FRESH-ISOLATED-20260826` = `FAIL_TO_SA2`.
- Evidence root: `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P715-01\STRICT_R15_SA1_FRESH_ISOLATED_R106_20260826`.
- Denominator: `N=259`; all unordered pairs `33411/33411`; clip count 0.
- Primary clean hard failure: `PAIR_08396`, the node-`j` border intersects the visible glyph `矩` by 37 native pixels. Root independently opened the native 1x and nearest-neighbour 8x ROI and confirmed the border cuts into the glyph. This is a real geometry collision and is not relaxed by R168.
- The sealed report also records other independent formula/formula, formula/matrix-border, text/panel-clearance and text/text-clearance failures; confirmed illegal intersection sum is 888 native pixels after excluding the two contaminated-comma relations.
- Mechanical closure: payload manifest 502 rows, ordinary files 507, identity mismatch 0, all 507 read-only, ADS/cache/pyc 0, WSTOP strictly last and later writes 0.
- Root decision: return `SA1 -> SA2`; do not start SA3 and do not count local pass.
- Authorized next scope: Dialogue A may use exactly one business-source writer on `src/绘图源码/第05册_采样方法主题模型与图排序/V5-C07/web_random_walk.tex`, static-only, to remove the confirmed real collisions and clearance failures while preserving graph edges, matrices, transition semantics, labels, caption, and R168 typography policy. It must freeze a source patch and request a build slot; no TeX or commit is authorized yet.

## FIG-P640-01

- The sealed R106 SA1 evidence reports a clean graphical `PASS`, but `RESULT.json` and `SA1_FRESH_HANDOFF.md` disclose actual model/reasoning `gpt-5.4 / xhigh`.
- The active Goal requires the core independent SA1 role to use `gpt-5.6-sol / xhigh`; a silent or inherited substitute cannot satisfy the role identity.
- Root decision: `ROLE_REJECT_WRONG_MODEL`. The evidence root remains immutable historical evidence but cannot migrate P640 or authorize SA3. P640 remains centrally at SA2/local-SA2-awaiting-valid-fresh-SA1.
- Authorized next scope: Dialogue C must launch one replacement fresh isolated R106 SA1 with explicit `gpt-5.6-sol / xhigh`, a new evidence root, and absolute prohibition on reading this rejected root or any older P640 conclusions. Source/PDF/main remain read-only and TeX remains disabled.

## Central result

- Inventory moves from `33 SA1 / 52 SA2 / 1 SA3 / 13 A_LOCAL_PASS` to `32 SA1 / 53 SA2 / 0 SA3 / 14 A_LOCAL_PASS`.
- Strict final completion remains `0/99`.
- The TeX build lock remains free and unassigned.
