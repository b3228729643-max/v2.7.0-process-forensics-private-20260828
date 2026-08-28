# R243 P020 R168 SA2 no-source-change acceptance and fresh SA1 authorization

- Time: `2026-08-26T16:14:31+08:00`
- Official candidate: R107, 817 pages, 4,967,249 bytes, SHA-256 `8811950621E2D64A3C2A8F0F7A52DD0FAC2BDB12018F3EA052C1F58C94EF8DF3`.
- UID: `FIG-P020-01`; accepted handoff: `A-R107-P020-SA2-R168-READONLY-20260826`.
- Source: `src/绘图源码/第01册_数学基础与统计学习基本理论/V1-C01/fig_v1_c01_language_flow.tex`; SHA-256 `FF006894E35D1D3E79F1C1D85D212B79735F3D11937B17F23A49D68DC97547CE`; main/A equal; unchanged.

## Independent main checks

- Target independently reported as physical page 17 / printed page 4 / Figure 1.1; current caption and source semantics agree.
- Main opened the 300-dpi colour crop, grayscale crop and 8× caption context. Four nodes, three forward dependency arrows, dashed reverse audit, labels, caption and page integration are visibly complete and readable.
- U+4E00 `一` is a complete continuous low-profile stroke (native ink bbox 38×5 px). Per R168 this is advisory, not a hard defect.
- True hard failures are zero: missing/tofu, wrong codepoint or semantics, actual unreadability, obvious severe imbalance, real clipping, illegal overlap, geometry/relationship or page-integration error.
- Evidence root has 16 ordinary files: 13 payload + two manifests + `WRITE_STOPPED`. Both manifests contain 13 unique rows and are byte-identical. Manifest-to-filesystem path/bytes/SHA mismatch is zero; all 16 files are read-only; ADS count is zero; `WRITE_STOPPED` is strictly last by 2,598,245 ticks.

## Decision and routing

`ROOT_ACCEPT / SA2_NO_SOURCE_CHANGE_READY_FOR_FRESH_SA1`

No source edit, TeX build or commit is required. A is authorized to start exactly one new `gpt-5.6-sol/xhigh`, `fork_turns=none` fresh isolated SA1 in a previously nonexistent evidence root. It may read only R107, current P020 source, active Goal, strict protocol/schema and necessary current V1-C01 text. It must not read this SA2 root/report/handoff or any older P020 evidence, role conclusion, state, inventory, chat or git history. PDF/source/main remain read-only; TeX, commits, a second UID and a second role are forbidden. A PASS may only request a different fresh isolated SA3.

Until the actual SA1 identity is returned, P020 remains counted as SA2. Inventory remains `32 SA1 / 51 SA2 / 0 SA3 / 16 A_LOCAL_PASS`; strict final remains `0/99`.
