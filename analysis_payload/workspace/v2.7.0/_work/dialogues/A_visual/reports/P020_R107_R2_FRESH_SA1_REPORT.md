# FIG-P020-01 R107 R2 fresh isolated SA1 report

## Verdict

`PASS — SA1_PASS_READY_FOR_FRESH_ISOLATED_SA3`

- Handoff ID: `A-R107-P020-SA1-FRESH-ISOLATED-20260826`
- Role: sole fresh isolated SA1
- Model / effort: `gpt-5.6-sol` / `xhigh`
- Canonical UID: `FIG-P020-01`
- Official round: `R107`
- Hard-fail count: 0
- Arbiter: not invoked
- SA2 / SA3: not run

## Isolation and immutable input identity

This audit started from zero and used only the strict whitelist. No prior/current P020 evidence, report, handoff, SA result, state, inventory, route log, task packet, chat conclusion, git history/diff/log, or other figure was read. The official PDF and current source remained read-only; no TeX engine, LuaLaTeX, latexmk, source edit, commit, second UID, second role, or additional agent was used.

Official R107 PDF:

- bytes: `4,967,249`
- SHA-256: `8811950621E2D64A3C2A8F0F7A52DD0FAC2BDB12018F3EA052C1F58C94EF8DF3`
- page count: 817

Current figure source:

- bytes: `2,627`
- SHA-256: `FF006894E35D1D3E79F1C1D85D212B79735F3D11937B17F23A49D68DC97547CE`

Independent exact-caption search for `数学语言从对象声明到任务陈述的依赖关系` produced exactly one PDF match: physical page 17, zero-based index 16, PDF/printed label 4. Page size is `595.276 × 841.890 pt`, rotation 0.

## Frozen render and crop identity

Both page views are direct native Poppler renders from the official PDF:

- 200 dpi full page: `1654 × 2339 px`
- 300 dpi full page: `2481 × 3508 px`
- frozen figure crop in 300 dpi page coordinates: `[240,1095,2200,1570]`, `1960 × 475 px`
- frozen standalone body crop: `[240,1095,2200,1490]`, `1960 × 395 px`

The required full-page, crop, standalone, grayscale, text-measurement overlay, and foreground-object overlay views were all actually opened after the final machine artifacts were fixed.

## Exhaustive foreground universe

Every visible foreground object was enumerated:

- visible glyphs: 108
- visible foreground drawing paths: 14
- visible math rules: 0
- total foreground objects: `N=122`
- exhaustive unordered pairs: `C(122,2)=7,381`; emitted rows: 7,381
- object IDs unique: true
- safe filenames unique: true
- empty masks: 0
- mask contamination candidates: 0

The 14 paths are the four node-border strokes, one inline arrow shaft/head pair, three main arrow shaft/head pairs, and the feedback route/head pair. Two visible fills were explicitly bidirectionally accounted as backgrounds and excluded: the outer background fill and the white feedback-label background. No target-visible drawing remained unaccounted.

## Machine overlap, clearance, clip, and typography gates

Exhaustive pair partition:

- `MEETS_MACHINE_GATE`: 6,207
- `DESIGN_WHITELIST`: 1,174
- failure/unknown rows: 0
- unwhitelisted overlap candidate pixels: 0
- canonical illegal overlap pixels after adjudication: 0
- clip pixels across all 122 foreground objects: 0

Critical category minima:

- independent text/text bbox clearance: 9 px, required 4 px
- text/line-arrow ink clearance: 12 px, required 3 px
- own-node text/border ink clearance: 13 px, required 5 px
- independent graphic/graphic ink clearance: 15 px, required 0 px
- text-to-frozen-crop-edge clearance: 25 px

Eleven critical/closest relations were frozen. All 11 raw 1× and all 11 nearest-neighbor 8× five-panel views were actually opened. Six independent relations have empty intersections. Five nonempty intersections are intentional same-parent shaft/head joins (inline, main arrows 1–3, feedback); each has canonical illegal overlap 0.

Source font audit covers 10/10 text elements. Every nominal effective size is at least 10.0 pt, every graphics scale is 1.0, and no resize/scalebox/transform/shape scaling was found. Ordinary CJK ink-height statistics are:

- node headings: count 19, min/median/max `38/41/42 px`
- node body: count 26, `35/36/37 px`
- annotation: count 16, `35/36/37 px`
- caption: count 37, `35/36/38 px`

The heading/body median ratio is `41/36=1.1389`, a deliberate 10.5 pt bold heading emphasis over 10 pt body text, visually controlled rather than severely imbalanced.

Punctuation calibration:

- `、` at G022/G035/G043: 10 px high; areas 42/42/41 px, same-candidate exact-font/size references
- `。` at G089/G108: 13 px high; areas 69/69 px, exact reference
- `：` at G053: actual embedded font glyph calibration, target/reference height `22/22 px`; complete, area difference advisory
- `.` at G068: actual embedded font glyph calibration, target/reference height `7/7 px`; complete, area difference advisory
- `一` at G091: complete single horizontal stroke, 5 px raster height; advisory by rule

R168 was applied exactly. Micro `[0.92,1.08]` ratios, PDF font-metadata differences, single-horizontal-stroke CJK pixel height, and 1–2 px raster differences were advisory and did not independently trigger FAIL or rebuild. No missing/tofu/wrong codepoint or meaning, unreadability, obvious severe imbalance, real clipping, illegal overlap, or geometric/semantic error was found.

## Manual review closure

Machine scripts never generated or overwrote manual reviewer, boolean, decision, or note fields. After the final artifacts were fixed, the reviewer actually opened the full denominators and then hand-authored object/relation-specific ledgers:

- glyph contact sheets: 12/12; glyph rows: 108/108
- graphic contact sheets: 4/4; graphic rows: 14/14
- required full/crop/standalone/grayscale/overlay views: 6/6
- critical relation raw/nearest views: 22/22
- actual-font punctuation calibration views: 2/2
- relation ledger rows: 11/11
- view ledger rows: 8/8
- panel-role rows: 4/4
- source-font rows: 10/10

Every manual row has all fields populated, an object- or relation-specific note, and `PASS`. Final crosscheck: 39/39 checks passed, 0 failed.

The figure is semantically consistent with the necessary neighboring current body text. The solid chain is 对象声明 → 关系/映射 → 逻辑断言 → 任务陈述. The dashed path returns from task to object and is labeled as a reverse sufficiency check; it records dependency/usage and does not claim reversible logical entailment. The inline `f:X→Y` is intact.

Grayscale and full-page review also pass: solid main arrows remain distinguishable from the dashed feedback path without relying on color alone, and the figure is balanced and integrated with the surrounding prose/caption.

## Seal

Evidence root:

`D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P020-01\STRICT_R2_SA1_FRESH_ISOLATED_R107_20260826`

One seal was performed:

- common-payload JSON rows: 536
- common-payload CSV rows: 536
- common-payload bytes: 11,118,569
- JSON/CSV common payload identity: true
- payload missing files: 0
- payload byte mismatches: 0
- payload SHA-256 mismatches: 0
- total sealed ordinary files including the two manifests and `WRITE_STOPPED`: 539
- read-only ordinary files: 539/539
- writable ordinary files: 0
- non-default ADS: 0
- cache/pyc/pyo artifacts: 0
- reparse points: 0
- `WRITE_STOPPED` is read-only and was the absolute final evidence-root content write
- post-seal evidence-root content writes: 0

Final verdict: `PASS`.

Final route: `SA1_PASS_READY_FOR_FRESH_ISOLATED_SA3`.
