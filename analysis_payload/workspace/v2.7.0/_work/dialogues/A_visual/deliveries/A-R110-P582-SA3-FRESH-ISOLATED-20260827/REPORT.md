# FIG-P582-01 R110 fresh isolated SA3 formal report

## Identity and candidate

- HANDOFF_ID: `A-R110-P582-SA3-FRESH-ISOLATED-20260827`
- Instance: `/root/p582_r110_fresh_sa3`
- Model/effort: `gpt-5.6-sol/xhigh`; fork: `none`
- Official candidate: `main_full.pdf`, 817 pages, 4,967,063 bytes, SHA-256 `B49C5CA920DDEF6C0CD004B2581EAF710F4D1E1115BB459A324A84594B3831F3`
- Independently located target: physical page 632, printed page 619, Figure 31.7
- Current source: `fig_v5_c02_running_mean.tex`, SHA-256 `989E12DFD1B7A7F58A7953F36A8E8F24427A56154EED33325262045C17583A57`

## Frozen evidence denominator

- Complete Figure 31.7 body and caption: 156 visible non-empty objects = 139 glyphs + 17 drawing/path objects.
- Visible mathematical drawing rules: 0; all visible formula marks are accounted for as glyphs.
- Complete unordered-pair ledger: `C(156,2)=12,090` unique pairs.
- Native evidence: full page 200dpi `1654x2339`; full page 300dpi `2481x3508`; figure crop `1958x794` at `[284,1354,2242,2148]`; body-only crop `1207x657` at `[670,1354,1877,2011]`.
- Individual masks: 156 ordinary PNGs; contact sheets: 12 glyph + 2 drawing; critical relations: 89 rows on 15 sheets.

## Machine and manual closure

- Machine crosscheck: PASS; empty masks 0; illegal overlap pixels 0; clip pixels 0; pair hard failures 0; pixel hard failures 0.
- Manual review completed: 139/139 glyphs, 17/17 drawing paths, 89/89 critical relations, 5/5 views, and 18/18 panel/role/script groups.
- Every glyph mask was checked in ORIGINAL / TARGET OVERLAY / MASK ONLY / 8x nearest views. Every critical relation was checked at 1x and 8x.
- Minimum independent text-text vector-bbox gap is 8px; minimum independent text/drawing ink clearance is 21px; crop-edge clearance is at least 24px.
- Nonzero drawing intersections are intentional axis construction or plot encoding and are individually hand-ledgered; none is an illegal overlap.

## Key R168 findings

- `↓ 再下降`: four complete glyph masks; no wrong codepoint or missing stroke; nearest relevant sample marker clearance 81px and running-mean curve clearance 91.35px.
- `.380`: four complete glyph masks; clearances are 32.06px to the running-mean curve, 40.25px to the third mean marker, 45px to stems, and 58px to the truth line.
- The formula equals sign has a 12px low-profile outline, and three singleton punctuation glyphs have no second same-style in-candidate comparator. All four contours are complete, pure, crisp, and readable; under R168 they are advisory only.
- No tofu, missing glyph, wrong encoding, mathematical semantic error, actual unreadability, obvious imbalance, real clipping, or illegal overlap exists.

## Semantic verification

`U=(0.8,0.1,0.7,0.4)` gives `U_i^2=(0.64,0.01,0.49,0.16)` and running means `(0.64,0.325,0.38,0.325)`. The displayed `.640,.325,.380,.325`, down/up/down curve, `真值 1/3`, preceding prose, and caption are mutually consistent.

## Seal and verdict

Evidence root: `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P582-01\STRICT_R8_SA3_FRESH_ISOLATED_R110_20260827`

The root is sealed with 217 files in 5 directories; every file and directory has the Windows read-only attribute, `WRITE_STOPPED` is read-only and was the final root file, and root writes after it are zero.

**SA3 verdict: PASS.** Await parent/root `A_LOCAL_PASS` acceptance. No central state was written and no next UID was started.
