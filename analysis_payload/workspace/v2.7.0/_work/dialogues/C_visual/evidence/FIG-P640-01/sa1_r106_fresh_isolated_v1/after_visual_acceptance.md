# FIG-P640-01 R106 fresh isolated SA1 visual acceptance

## Candidate identity

- HANDOFF_ID: `C-FIG-P640-01-R106-SA1-FRESH-ISOLATED-V1`
- reviewer: `/root/sa1_fig_p640_r106_fresh_isolated`
- fork_turns: `none`
- actual model/reasoning identity: `gpt-5.4` / `xhigh`
- official PDF: `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\build\strict_current_r106_fullbook\main_full.pdf`
- PDF identity: 817 pages; 4,967,249 bytes; SHA-256 `0FA4A5A0B35D2566D71B5472B49E9B4A8A60CBAE76B3FA744B92783AFC6BC31A`
- independently resolved location: physical page 690; printed page 677; Figure 33.7; `fig:V5-C04-mixing-rho-comparison`
- page size: 595.2760009765625 x 841.8900146484375 pt
- native full page: 2481 x 3508 px at 300 dpi; 1654 x 2339 px at 200 dpi
- figure crop: page pixels `[333,270,2188,1230]`; native 1855 x 960 px at 300 dpi
- standalone crop: page pixels `[333,270,2188,1084]`; native 1855 x 814 px at 300 dpi
- right panel: page pixels `[1520,270,2146,917]`; native 626 x 647 px at 300 dpi

## Independent semantic and visual decision

The left panel correctly renders the analytic autocorrelation curves `rho^(2k)` for absolute rho values .95, .70, and .20. The right panel correctly renders the ESS ratio `(1-rho^2)/(1+rho^2)`, the limit annotation, and the open endpoint near `(.99,.010)`. The current caption and adjacent explanation agree with those semantics. At native scale both panels are readable, balanced, unclipped, and integrated cleanly above the caption and following prose. In grayscale the three autocorrelation curves remain distinguishable by line style.

The strict drawing-sequence reconciliation found six live paths not separately returned by the high-level drawing grouping: three legend samples, two right-axis shafts, and one title fraction rule. They were added to the denominator and manually reviewed. The title fraction rule is nonempty, unbroken, pure, correctly attached to the ESS formula, five pixels below its numerator, and thirteen pixels above the denominator body.

The final reader-visible masks show no illegal overlap. The point note is 9.487 native pixels from the ESS curve. The endpoint marker is four pixels from the .99 tick, 8.944 pixels from the x-arrowhead, and one pixel above the x-axis shaft. Its white fill legitimately hides the continuing curve, leaving the visible marker and curve inks one pixel apart. The gray `.20` autocorrelation curve becomes pixel-coincident with the zero axis only after its mathematically valid convergence; this is a legitimate data/axis coincidence, not a semantic obstruction.

## Denominators and manual review

- semantic text objects: 74
- drawing/live-path objects: 20, including one `GRAPHIC_MATH_RULE`
- actual object denominator: 94
- unordered-pair denominator: `C(94,2) = 4,371`; machine ledger contains all 4,371 exactly once
- nonwhitespace glyph denominator: 242
- machine-critical relations: 71
- raw nonzero pair intersections before semantic adjudication: 33
- manual glyph rows: 242/242, individually noted, all PASS
- manual object rows: 94/94, individually noted, all PASS
- manual critical rows: 71/71 with native 1x and nearest-neighbor 8x review, all PASS
- manual role/peer rows: 49/49, all PASS
- manual view rows: 27, all PASS
- manual hard-gate rows: 20, all PASS
- empty glyph/object masks: 0/0
- missing/tofu/wrong glyph/codepoint: 0
- illegal overlap pixels: 0
- clip pixels: 0
- mask contamination pixels: 0

## R168 hard-font application

R168 is applied exactly. The 30 numeric glyph-box shortfalls are advisory natural scripts, punctuation, thin delimiters/operators, or raster extents; the contact sheets show them complete, pure, and readable. No advisory micro ratio, font taxonomy detail, metadata item, or 1-2 px raster difference is used as a hard failure. Hard font scope passes because there is no missing/tofu/wrong glyph or codepoint, wrong math semantics, actual unreadability, obvious severe size imbalance, real clipping, or illegal overlap.

## PASS matrix

- SA1_MODEL = `gpt-5.4` (actual inherited runtime identity; not rewritten to the goal-template model)
- SA1_REASONING = `xhigh`
- SA2_MODEL = `NOT_RUN_IN_THIS_SA1_ROOT`
- SA2_REASONING = `NOT_RUN_IN_THIS_SA1_ROOT`
- SA2_ESCALATED = `false`
- SA3_MODEL = `NOT_YET_ASSIGNED`
- SA3_REASONING = `NOT_YET_ASSIGNED`
- SOURCE_FONT_PASS = `true`
- PIXEL_HEIGHT_PASS = `true` under R168 hard scope; 30 numeric observations remain advisory
- SAME_CLASS_RATIO_PASS = `true` under R168 hard scope; micro-ratio minutiae are advisory
- ROLE_RATIO_PASS = `true` under R168 hard scope; no severe imbalance
- OVERLAP_CANDIDATE_PIXEL_COUNT = `33`
- MASK_CONTAMINATION_PIXEL_COUNT = `0`
- OVERLAP_PIXEL_COUNT = `0`
- PIXEL_ADJUDICATION_STATUS = `PASS`
- CLIP_PIXEL_COUNT = `0`
- MIN_INDEPENDENT_TEXT_TO_LINE_CLEARANCE_PX = `9.487`
- FONT_VISUAL_HARMONY_PASS = `true`
- VISUAL_HARMONY_PASS = `true`
- RESULT = `PASS`

## Disposition

SA1 returns `PASS`. No source change or central-state write is requested. The only next action is for the root coordinator to assign a different fresh isolated SA3 reviewer against the same official R106 PDF candidate.
