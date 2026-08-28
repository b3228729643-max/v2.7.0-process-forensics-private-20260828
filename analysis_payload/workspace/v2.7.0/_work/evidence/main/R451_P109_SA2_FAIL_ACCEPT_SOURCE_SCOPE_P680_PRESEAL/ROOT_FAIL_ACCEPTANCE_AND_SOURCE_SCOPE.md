# Revision 451 — P109 SA2 hard-fail acceptance and narrow source scope

Time: 2026-08-28T03:59:15+08:00  
Candidate: R114, 817 pages, 4,967,122 bytes, SHA-256 `C3BB9B1C7FC9D7AF9178CD33F227F24899AA505FAB81840DB6E3AD8BD6CE78A6`  
Main: branch `v2.7.0/integration`, HEAD `4eb592fba94241feb44e03337f027bbbc83b51e2`, clean before this state-only registration.

## Accepted P109 SA2 result

- UID: `FIG-P109-01`
- HANDOFF_ID: `A-R114-P109-SA2-R168-READONLY-20260828`
- Actual instance: `/root/p109_r114_r168_sa2`
- Model/effort/fork: `gpt-5.6-sol/xhigh/none`
- Route accepted by Main: `FAIL_TO_MAIN_SOURCE_SCOPE`
- Current source identity: 1,865 bytes, SHA-256 `E8B3303A3893491A69815F407423C68BC17663CC017DC3AB49953235E615FD98`
- Independent location: R114 physical 116/817, printed 103.
- Frozen denominator: N14; all unordered pairs C91; manual IDs close exactly.

The sole true hard defect is `F001 / P010 / O01-O11`: the convex-set boundary crosses the mathematical `C` glyph in the domain label `凸可行域 C`. Main independently opened the native-300 figure+caption crop, grayscale crop, and `R06_nearest8x.png`; the line visibly passes through the glyph. This is not a bbox-only candidate and is not relaxed by R168 advisory numeric font/pixel rules. All other pairs, codepoints, mathematics, caption, clipping, grayscale, readability, and page integration are clear.

## Main mechanical acceptance

- Manifest expected/actual files: 41/41; missing/extra 0; directories below root 0.
- Files/directories/root missing ReadOnly: 0.
- WSTOP strict-last margin including root: 5,767,715,328 ticks; excluding-marker at-or-after: 0.
- Object rows/unique IDs: 14/14; pair rows/unique IDs: 91/91; hard findings: exactly `F001`.
- Root-external audit reports postmarker content/attribute writes 0 and parse/ADS/cache-pyc/reparse failures 0.

The sealed P109 root, external handoff, and audit are permanently frozen. P109 remains in SA2 inventory until a corrected candidate is built and requalified.

## Exactly authorized narrow action

Dialogue A alone may make one static-only edit to:

`src/绘图源码/第01册_数学基础与统计学习基本理论/V1-C07/fig_v1_c07_convex_set.tex`

Only lines 29--30 are in scope: reposition the domain-label node, or add an opaque protective background to that label, so the set boundary no longer crosses the `C` or any other glyph. Preserve the set shape, segment, all points/markers, interpolation formula, statement box/formula, caption, chapter prose, labels, numbering, shared macros, and build entry. Produce a sealed static report and request one controlled standalone/direct build slot.

Not authorized: TeX/build, commit, source edits outside the one P109 file/scope, fresh role, second UID, directory fallback search, process management, or non-Main central-state changes.

## Concurrent P680 status

The same authorized P680 readonly SA2 has independently frozen N25/C300, opened 19 required views, completed all post-observation manuals, and reports no hard defect. It remains the sole P680 instance and may only finish exact-file consistency, manifest, ReadOnly/WSTOP-last sealing, and root-external audit before returning its sealed result.

Inventory remains `31 SA1 / 34 SA2 / 0 SA3 / 35 local pass`; strict final remains `0/99`; B remains `66/66`.
