# FIG-P582-01 R110 fresh isolated SA1 visual acceptance

## Identity

- `HANDOFF_ID=A-R110-P582-SA1-FRESH-ISOLATED-20260827`
- Instance: `/root/p582_r110_fresh_sa1`
- Model / effort: `gpt-5.6-sol / xhigh`
- Fork boundary: `fork_turns=none`
- Candidate: `main_full.pdf`, physical page 632, printed page 619, Fig. 31.7
- Official PDF: 817 pages, 4,967,063 bytes, SHA-256 `B49C5CA920DDEF6C0CD004B2581EAF710F4D1E1115BB459A324A84594B3831F3`
- Frozen source: `fig_v5_c02_running_mean.tex`, 2,627 bytes, SHA-256 `989E12DFD1B7A7F58A7953F36A8E8F24427A56154EED33325262045C17583A57`
- Active Goal entry read: `D:\Users\ASUS\Desktop\机器学习\GOAL.md`; no other Goal/state/acceptance route was read.

The candidate and source identities exactly match the R110 dispatch. The evidence root did not exist before this role created it. No old P582 evidence, report, handoff, state, inventory, chat, Git-history conclusion, or central acceptance route was read.

## Native views and crop geometry

The official A4 page is `595.276 × 841.890 pt`. The direct 300 dpi page grid is `2481 × 3508 px`.

| View | Native dimensions | Page-space crop |
|---|---:|---:|
| `full_page_200dpi.png` | 1654 × 2339 px | full physical page 632 |
| `page_300dpi.png` | 2481 × 3508 px | full physical page 632 |
| `figure_crop_300dpi.png` | 1943 × 788 px | `[291,1354,2234,2142]`, includes body and the complete two-line caption |
| `standalone_300dpi.png` | 1201 × 651 px | `[666,1354,1867,2005]`, plot body only |
| `grayscale_300dpi.png` | 1201 × 651 px | same native body crop, no resize |

All 300 dpi evidence is directly rendered from the same official PDF with PyMuPDF 1.28.0; no TeX engine and no standalone build was used. The body crop has at least 14 px to all visible graphics and at least 18 px to text. The body-plus-caption crop has at least 15 px to all visible objects. `CLIP_PIXEL_COUNT=0`.

## Frozen denominators

- Visible glyph denominator: `139/139`, with unique `GLY-*` IDs and unique portable safe filenames.
- Text semantic-object denominator: `27/27`, including all tick labels, both axis titles, the complete equation, six separately auditable trend components, truth label, four numeric labels, and the entire caption natural paragraph.
- PDF foreground drawing/path denominator: `17/17`, exactly draw numbers 1-17 on the figure body.
- Math-rule/path denominator: `0`; the equation contains glyph-rendered parentheses, equality sign, slash, and natural scripts, but no visible `GRAPHIC/MATH_RULE` path. All 17 drawing/path records are assigned to axes, ticks, stems, polyline, guide, or markers.
- Total visible-object denominator: `N=44`.
- Complete unordered-pair denominator: `C(44,2)=946`; `946/946` machine rows are present.

All 14 final glyph contact sheets were actually opened. Every cell contains the native-context ORIGINAL, TARGET OVERLAY, MASK ONLY, and complete 8× nearest-neighbour views. The 139 manual rows record `original_match`, `overlay_complete`, `mask_only_pure`, missing strokes, foreign pixels, decision, and a per-glyph note. Empty glyph masks, duplicated IDs, duplicated safe names, missing contact cells, missing strokes, and foreign pixels are all zero.

## Source and typography

The frozen source declares 9.5 pt ordinary/tick/annotation text and 9.6 pt axis labels. It contains no `tiny`, `scriptsize`, `footnotesize`, `small`, `large`, `resizebox`, `scalebox`, `scale=`, or `transform shape` override. PDF-reported base sizes are 9.46451 pt and 9.56414 pt respectively, a declared/effective ratio of about 1.00375. Under the explicit R168 rule, the 0.03549 pt renderer delta is advisory and not a hard defect.

Every CJK glyph is at least 33 px in plot annotations, 35-38 px in axis titles/caption, and all tick/value digits are 26-28 px. Natural scripts are 19-23 px in the plot equation and 28-33 px in the caption. Same-role medians remain within the required role bands: tick/value extreme ratio is `27/26=1.0385`; CJK trend-label extreme ratio is `35/34=1.0294`.

One old-grid exception is retained transparently: the equality sign's two complete rules have a 12 px own-ink height versus the old 22 px micro-glyph threshold. It is correctly coded, complete, visually balanced, and immediately readable in color, grayscale, and full-page context. This is `PASS_R168_ADVISORY`, not a hard failure under the task's explicit R168 scope.

Low-profile punctuation peer groups pass height and area ratios. Three unique no-peer caption punctuation cases were opened and recorded as R168 advisories; all are complete and readable. Details are in `low_profile_punctuation_audit.md`.

`FONT_VISUAL_HARMONY_PASS=true`: labels are neither oversized nor undersized, line spacing is natural, the equation remains subordinate, and the caption matches the page's text hierarchy.

## Pixel geometry and pair review

- `OVERLAP_PIXEL_COUNT=0` across all final-visible object masks.
- Text-text minimum blank clearance: `13.142 px` (`PAIR-0887`), versus the 4 px gate.
- Text-graphic minimum blank clearance: `13.036 px` (`PAIR-0025`), versus the 3 px gate.
- Node-border and panel-border classes: `N/A`; the plot has neither text-bearing nodes nor panel borders.
- Text-to-crop-edge minimum: 15 px in the figure-plus-caption crop and 18 px in the body crop, versus the 6 px gate.
- Final-visible pair overlap failures: `0/946`.
- Text-related clearance failures: `0/946`.

The 29 pairs with pre-occlusion contact are intentional plot construction: axis/tick/arrowhead joins, stem-marker endpoints, marker-polyline endpoints, guide/data crossings, or the i=1 raw/mean coincidence. All 29 plus six explicit regression relations were individually opened in the final relation evidence and individually signed in `manual_critical_pair_reviewer_ledger.csv`. Their final-visible separated masks have zero intersection.

The highlighted regression relations pass:

- `↓` to `再下降`: 13.866 px blank clearance.
- `↓` to `.380`: 27.018 px.
- `再下降` to `.380`: 38.115 px.
- `.380` to running-mean polyline: 30.064 px.
- `.380` to i=3 mean marker: 44.277 px.
- upper-right equation to running-mean polyline: 195.726 px.

## Mathematical semantics and text consistency

For the fixed sample sequence `0.8, 0.1, 0.7, 0.4`, the plotted raw squared values are `.64, .01, .49, .16`. The running means are:

- `i=1`: `.640`;
- `i=2`: `(.64+.01)/2=.325`;
- `i=3`: `(.64+.01+.49)/3=.380`;
- `i=4`: `(.64+.01+.49+.16)/4=.325`.

These values match the blue curve and labels. The trend is down, up, down, matching `↓ 下降`, `↑ 上升`, `↓ 再下降` and the caption. The dashed line at `1/3` matches `E[U^2]=1/3` for a uniform variable. The equation `h(U_i)=U_i^2`, axis labels, printed Fig. 31.7 number, and caption are mutually consistent. There is no missing glyph, tofu, wrong codepoint, wrong mathematical operator, or semantic mismatch.

## Opened-view conclusions

- Full page 200 dpi: PASS. The upper plot integrates naturally above Fig. 31.8, with intact margins and a natural two-line caption.
- Figure crop 300 dpi: PASS. Body and caption are complete and balanced.
- Standalone 300 dpi: PASS. Curves, stems, markers, labels, and reading path are clear.
- Grayscale 300 dpi: PASS. The curve, markers, stems, and dashed guide remain distinguishable.
- Text overlay 300 dpi: PASS. All 27 text parents and all 139 glyphs are covered.

## SA1 decision

`RESULT=PASS`

Under the expressly supplied R168 hard-failure scope, FIG-P582-01 has no missing/tofu/wrong-coded glyph, mathematical semantic error, actual unreadability, obvious visual imbalance, clipping, or illegal overlap. The single equality-sign micro-height item and three unique punctuation calibration gaps remain non-blocking advisories. This fresh isolated SA1 requests that the mainline assign a separate fresh isolated SA3; this role does not start SA3.
