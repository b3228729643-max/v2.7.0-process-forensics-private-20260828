# Fresh SA1 input — FIG-P602-01 / R101

You are a completely fresh, read-only SA1 reviewer.  Do not read `SA1_REVIEW.md`, any prior reviewer output, or any older PASS/FAIL conclusion.  Do not write files.  Do not run TeX, LuaLaTeX, latexmk, or any build.  Do not request a source writer merely to improve evidence.

## Identity and scope

- UID: `FIG-P602-01`; scope row `B52`; branch denominator `46`.
- Candidate: `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\build\strict_current_r101_fullbook\main_full.pdf`.
- Target: PDF page `651`, printed book page `638`, figure `32.5`.
- Source, read only: `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\worktrees\dialogue_C_visual\src\绘图源码\第05册_采样方法主题模型与图排序\V5-C03\fig_v5_c03_mh_accept_reject.tex`.
- Context, read only: `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\worktrees\dialogue_C_visual\src\讲义源码\第05册_采样方法主题模型与图排序\chapters\V5-C03.tex`.
- Evidence root: this directory.
- Machine denominator: 26 semantic objects and 325 unordered object pairs.

Start with `MACHINE_EVIDENCE.md`, `00_identity/identity.json`, and `00_identity/WRITE_STOPPED.json`.  Treat every machine result as evidence, not as a manual conclusion.

## Required independent inspection

1. Inspect the frozen full-page/crop/grayscale/overlay views and the read-only source/context for semantic truth, text consistency, reading order, caption match, page fit, font declarations, and grayscale legibility.
2. Inspect every one of the 26 object cards and both masks recorded in `03_objects/object_manifest_26.csv`; explicitly decide every object ID.
3. Inspect all 15 glyph contact sheets and the 175 measurement rows; explicitly decide every glyph ID.  Low-profile symbols require actual same-character/font/size peer or visual/source-metric reasoning, not a global default.
4. Inspect every one of the 325 rows in `05_pairs/object_pair_ledger.csv`; explicitly decide every pair ID.  For the eight raw intersections, inspect each pair's native 1x and 8x critical cards and decide whether it is the intended arrow-to-border endpoint or illegal overlap.
5. Inspect and explicitly decide each of the 27 low-profile peer IDs, 50 role/script rows, and 26 clipping rows.  Do not convert them to PASS by a loop, template note, default, or one global Boolean.
6. Check source SHA, R101 PDF/page identity, denominators, and `WRITE_STOPPED` seal.

## Required response

Return a self-contained review suitable for verbatim persistence.  Include:

- reviewer role/model and freshness statement;
- exact identity values and denominator checks;
- `OBJECT_LEDGER` with 26 explicit ID rows;
- `GLYPH_LEDGER` with 175 explicit ID rows;
- `PAIR_LEDGER` with 325 explicit ID rows;
- `CRITICAL_LEDGER` with the eight intersection IDs and individual 1x/8x reasons;
- `PEER_LEDGER` with 27 explicit glyph IDs;
- `ROLE_LEDGER` with all 50 explicit `(parent, script class)` IDs;
- `CLIPPING_LEDGER` with 26 explicit object IDs;
- a short `VIEW_AND_HARD_GATES` ledger with individually reasoned decisions;
- final `RESULT: PASS|FAIL`, `NEEDS_SOURCE_WRITER: yes|no`, `NEEDS_TEX_SLOT: yes|no`, and one exact next action.

Every row must be genuinely reviewed.  Never use phrases such as “all others PASS”, ranges, inherited/default PASS, or a script-generated manual result.  A missing denominator or unreviewed ID is a strict FAIL.
