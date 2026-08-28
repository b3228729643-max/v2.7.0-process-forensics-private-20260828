# P608 R3 mechanical verification

- `OWNER_DIALOGUE`: `DIALOGUE_A_VISUAL`
- `HANDOFF_ID`: `A-R130-P608-MECH-VERIFY-20260824`
- `FIGURE_ID`: `FIG-P608-01`
- `WORKTREE`: `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\worktrees\dialogue_A_visual`
- `ARCHIVE`: `...\STRICT_R4_SA2_REPAIR_R98_LOCAL_20260824\after_final_r3\sa2_closeout_r3`
- Scope: mechanical verification only; this report does not declare `A_LOCAL_PASS` or final PASS.

## Result

**MECHANICAL PASS, with release-chain gaps recorded below.** The sealed local evidence package is mechanically internally consistent for the requested R3 gates. It remains explicitly `NON_OFFICIAL_LOCAL_CANDIDATE` / `TERMINAL_READY_NOT_A_VISUAL_PASS`.

## Checks

1. **Write stop:** `WRITE_STOPPED.md` exists. File timestamps show it is the absolute last file written (`2026-08-24 21:58:29 +08:00`); the preceding manifest/report writes are at `21:58:08`, and no archive file has a later timestamp. Its text states writing stopped after terminal check, manifest and SA2 report.
2. **Manifest/package integrity:** `P608_R3_MANIFEST.md`, terminal JSON, and all referenced raster/CSV/JSON/Markdown artifacts exist. The package contains 399 ordinary files; all opened successfully. ADS scan found none; case-insensitive duplicate filename scan found none. The manifest's declared counts agree with the package inventory. No independent hash declaration is present in the manifest, so consistency was checked by counts, paths, file readability, and cross-file values.
3. **Denominators:**
   - 91 objects = 31 text parents + 58 visible PDF paths + 2 pattern strokes;
   - 4095 all unordered pairs (`P608_R3_ALL_4095_PAIRS.csv`: 4095 data rows);
   - 74 glyph rows;
   - 11 low-profile calibration rows;
   - 140 hatch→glyph/math-rule relation rows.
   These values match the terminal JSON, manifest, report, and underlying CSVs. The vector inventory independently reports 31 text spans and 60 drawing records, consistent with 58 visible paths plus 2 pattern strokes.
4. **Failure counters:** ownership `foreign_pixel_px != 0`: 0; `missing_stroke_px != 0`: 0; illegal overlap: 0; required-clearance failures: 0; low-profile calibration failures: 0/11; hatch relation failures: 0/140. Pair CSV has 45 raw intersections, all represented by documented graphic composites with illegal overlap 0; 4050 pairs are `SEPARATE`.
5. **Build/raster evidence:** native direct 300 dpi raster exists at 2481×3508 px; 200 dpi page-fusion raster exists at 1654×2339 px. The referenced local LuaLaTeX PDF exists, and `local_wrapper_r3_worktree.log` contains a successful PDF-output marker. Crop/standalone/grayscale artifacts also exist.
6. **Git scope:** worktree has exactly one unstaged path changed: the authorized P608 figure source `src/绘图源码/第05册_采样方法主题模型与图排序/V5-C03/fig_v5_c03_trace_running_mean.tex`. No staged changes and no other source paths are present.

## Gaps / boundary

- This is a compact local R98 replay, not the official full-book candidate; the package itself says the official full-book build and fresh independent SA1/SA3 review remain mandatory.
- The manifest does not contain a standalone file-by-file hash list; no hash claim was available to recompute. This is not a mechanical inconsistency, but root should retain the existing path/count/readability evidence when routing the next review.
- Mechanical PASS must not be promoted to `A_LOCAL_PASS` or final PASS by this report.

## Handoff

- `assigned_scope`: verify WRITE_STOPPED ordering, manifest references/readability/ADS/name integrity, denominators and zero-failure counters, build/raster evidence, and Git scope for FIG-P608-01.
- `completed`: all requested mechanical checks; result is mechanical PASS with boundary gaps above.
- `files_changed`: only this report outside the sealed package; no package, source, mainline, B, or FINAL_ROOT files changed.
- `decisions`: preserve non-official-local status; do not declare A_LOCAL_PASS/final PASS.
- `unresolved`: official full-book candidate and independent SA1 then isolated SA3 remain; no file-level hash list in manifest.
- `validation`: see Checks 1–6.
- `next_action`: root builds the next official full-book candidate and routes FIG-P608-01 through fresh independent SA1, then isolated SA3.
