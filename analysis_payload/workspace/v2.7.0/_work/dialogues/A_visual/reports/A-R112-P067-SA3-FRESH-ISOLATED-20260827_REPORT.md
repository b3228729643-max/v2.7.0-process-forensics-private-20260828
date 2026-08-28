# FIG-P067-01 — fresh isolated R112 SA3 report

`HANDOFF_ID=A-R112-P067-SA3-FRESH-ISOLATED-20260827`

## assigned_scope

Fresh isolated SA3 review of `FIG-P067-01` against only the official R112 full-book PDF, the current single figure source, `GOAL.md`, the direct strict pixel/typography protocol, and the strict evidence schema. No SA1 material, old P067 evidence, central state, inventory, history, Git history, other UID conclusion, or second role was accessed.

## completed

- Confirmed before startup that the exact evidence root did not exist as either file or directory.
- Independently located the caption in the official R112 PDF at `page_index0=68`, `physical_page1=69` (printed page 56).
- Rendered and actually opened the native/original final evidence: full page 200dpi, full page 300dpi, figure crop 300dpi, standalone 300dpi, grayscale 300dpi, element overlay, eight text contact sheets, and nine graphic contact sheets.
- Froze `130` visible elements (`95` text glyphs + `35` foreground graphic paths) and all `8,385` unordered pairs.
- Completed a post-open manual ledger for all `130/130` IDs and a complete four-class pair reconciliation whose counts sum to `8,385/8,385`.
- Independently checked PMF mass, cumulative levels, monotonicity, right continuity, open/closed endpoints, axes, cross-panel relation, caption, grayscale, and page fusion.
- Ran the final evidence-integrity cross-check: all checks passed and all `413` expected PNGs opened successfully.

## files_changed

- Evidence only under `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P067-01\STRICT_R5_SA3_FRESH_ISOLATED_R112_20260827`.
- This report under `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\reports`.
- Matching handoff under `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\handoff\A`.
- No PDF, TeX source, build output, Git, central state, inventory, or process-management file was modified.

## decisions

`SA3_FAIL_RETURN_TO_SA2`

The lower PMF is correct: `0.15 + 0.30 + 0.35 + 0.20 = 1.00`. The closed CDF markers `0.15, 0.45, 0.80, 1.00` and open markers `0, 0.15, 0.45, 0.80` are also correct. However, the visible connecting path `GFX-007` places each plateau one support interval too early. For example, it draws `0.15` before `t=1`, then draws `0.45` immediately to the right of `t=1` even though the closed marker at `t=1` is `0.15`. The same contradiction occurs at `t=2` and `t=3`.

This is a hard mathematical-semantic and geometric failure under R168: the curve contradicts its own endpoint markers, the annotation “右连续：实心点取跳后值”, the PMF/CDF cumulative relation, and the caption. The current source’s `const plot mark right` setting diagnostically explains the one-interval left shift; SA3 made no source change.

No tofu, wrong code, actual unreadability, obvious imbalance, real clipping, or final-visible illegal overlap was observed. Font sizes and micro-grid differences are advisory under R168 and do not form the hard failure.

## unresolved

- `GFX-007` must be repaired in the authorized source so the plateau on each interval equals the cumulative value at its left support point and the graph is right-continuous.
- The repaired source must receive a new official build and entirely new SA1 evidence; only after SA1 passes should a new isolated SA3 run occur.

## validation

- Official page: `595.276 x 841.890 pt`; native 300dpi: `2481 x 3508 px`.
- Figure crop: `[100,64,485,220] pt` -> `1605 x 651 px`.
- Standalone crop: `[100,64,485,200] pt` -> `1605 x 568 px`.
- Manual objects: `129 PASS`, `1 FAIL_SEMANTIC (GFX-007)`.
- Final-visible illegal overlap: `0`; real clip: `0`.
- Pair inventory: `8,385 = 130*129/2`; class reconciliation totals `8,385`.
- Final cross-check: `all_checks_pass=true`; `413/413` expected PNGs openable.

## next_action

Return this SA3 hard FAIL to the authorized SA2 source-repair path. Do not count `A_LOCAL_PASS`, global PASS, or final completion, and do not start the next UID from this role.
