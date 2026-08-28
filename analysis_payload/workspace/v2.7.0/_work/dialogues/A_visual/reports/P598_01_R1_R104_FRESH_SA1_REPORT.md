# FIG-P598-01 R104 fresh isolated SA1 report

## Identity and isolation

- HANDOFF_ID: `A-R104-P598-01-SA1-FRESH-20260825`
- Assigned figure: `FIG-P598-01` (drawing-index B49)
- Instance: `/root/p598_01_r104_fresh_sa1`
- Reviewer UID: `SA1_FRESH_gpt-5.6-sol_xhigh`
- Actual configured model / effort: `gpt-5.6-sol / xhigh`
- Evidence root: `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P598-01\STRICT_R1_SA1_FRESH_R104_R168_20260825`

This review was rebuilt from zero under the stated read whitelist. It did not read prior P598-01/P598-02 evidence or verdicts, other figure evidence/conclusions, central state/history, task packets, route logs, Git history, or the inherited dialogue. No business source, PDF, central state, or inventory was modified. No TeX engine was invoked and no subagent was started.

## Frozen input

The reviewed input is the official frozen R104 `main_full.pdf`: 4,967,222 bytes, 817 A4 pages, SHA-256 `E5C871642FBDDBEC6508BE1B61BD911FE281CA5ACFBD16B0449B13357770A641`. The audited target is physical page 649. The page MediaBox is 595.276 x 841.890 pt.

The current single drawing source read-only reference is `fig_v5_c03_markov_chain_path.tex`. Its intended content agrees with the rendered target.

## Independent evidence result

Physical page 649 was rendered at 300 dpi (2481 x 3508 px), with a 200 dpi whole-page context view (1654 x 2339 px). The complete figure crop uses page-pixel box `(250,2054,2180,2760)`, `1930 x 706 px`; the tight standalone content box is `(408,2058,2010,2625)`, `1602 x 567 px`.

The complete visible denominator is:

- 142 non-space glyphs
- 22 visible foreground graphics
- `N=164` visible objects
- 4 additional auxiliary white occlusion paths for double-border separators, manually reviewed but excluded from visible `N`

All unordered pairs were measured: `C(164,2)=13,366`. Machine results: 0 empty glyph masks, 0 replacement/tofu code points, 0 below-gate pairs, 17 raw intersecting pairs, and minimum crop-edge clearance 9 px. The 17 raw pairs were each opened and observed: every one is an intentional structural connection. Thus illegal overlap count is 0 and clipping count is 0.

The 17 critical overlays all pass. State-glyph/border clearances are 20.4709-27.0179 px. Time-label/repeat-arc clearances are 8.4340-8.8489 px. The remaining semantic clearances span 12.6015-88.0000 px. All critical intersections are 0 and all clearances exceed their hard numeric gates.

All six directed transition endpoints were inspected at native scale and 8x. The last two show core-mask clearances 1.8284 and 2.6056 px, respectively, but their original pixels contain visible antialias bridges; there is no actual discontinuity. All transition lines join their source borders and arrowheads, and all arrowheads visually reach their targets.

## Content and semantic adjudication

The rendered path contains exactly seven states `a,b,b,c,c,b,a` at `t=0,1,2,3,4,5,T`, with six consecutive left-to-right transition arrows and a continuous time axis. The formula `K(x_t, d x_{t+1})` is correct. The caption's `K(x,dy)` wording correctly describes positive transition mass near `y` given current state `x`.

The consecutive repeated states `b,b` and `c,c` are explicit. The repeated-state nodes use clean double circles, and the relation arc/note correctly indicates adjacent correlation. The caption's state-space self-transition description is consistent with equal consecutive states in the temporal path. Exact vector centers give six increments of approximately 53.85898 pt with only 0.000435 pt range, so equal time spacing passes.

The complete crop, whole-page context, and grayscale version are clean. There is no caption truncation, circle/arrow/axis clipping, neighboring-body collision, or page-integration defect.

## R168 font adjudication

Under R168, font hard failure is limited to missing/tofu, wrong glyph/codepoint or math semantics, genuine unreadability, severe visible imbalance, or real clipping/overlap. None is present. The source sizes (9.2 pt top style, 9.4 pt states, 8.6 pt annotations/formula) and legacy pixel-height/ratio/taxonomy comparisons remain advisory. G0078, CJK `一`, is correctly rendered as a complete one-stroke glyph despite its 4 px ink height. Punctuation and natural subscripts are complete and readable. `FONT_VISUAL_HARMONY_PASS=true`.

## Human observation

The reviewer opened and visually inspected all 70 final views recorded in `manual_view_ledger.csv`: 4 base page/crop/grayscale views, 12 glyph contact sheets, 6 graphic contact sheets, 1 occlusion contact sheet, 17 critical overlays, 17 raw-relationship overlays, 6 endpoint overlays, and 7 global overlays/matrices. The human per-ID denominator ledger has 168 rows: 142 glyphs, 22 visible graphics, and 4 auxiliary occlusion paths. The separate human ledgers have 17 critical rows, 17 relationship rows, and 6 endpoint rows. Scripts did not generate or overwrite reviewer, boolean, decision, or note fields.

## Verdict

- `OVERLAP_PIXEL_COUNT=0` for illegal overlaps
- `RAW_STRUCTURAL_OVERLAP_PAIR_COUNT=17`, all human-whitelisted as intended joins
- `CLIP_PIXEL_COUNT=0`
- `FONT_VISUAL_HARMONY_PASS=true`
- Semantic/geometry hard gates: PASS
- Final SA1 verdict: `PASS`
- Required route: `SA1_PASS_AWAIT_FRESH_ISOLATED_SA3`

This report does not write or claim `A_LOCAL_PASS`; central acceptance remains outside this SA1 scope.

## Seal

The evidence package is sealed exactly once at final close. `SEALED_MANIFEST.sha256` and `SEALED_MANIFEST.json` provide complete dual manifests of all non-self-referential evidence artifacts plus this external report and the external handoff. `WRITE_STOPPED` is written after both manifests, has the strictly latest modification time, records the manifest hashes and route, and terminates all writes. Evidence files, this report, and the handoff are made read-only as part of the seal. Post-seal writes: 0.
