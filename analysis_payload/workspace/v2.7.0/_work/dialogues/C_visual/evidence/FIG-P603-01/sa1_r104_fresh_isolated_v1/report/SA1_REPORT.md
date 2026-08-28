# FIG-P603-01 / R104 — fresh isolated SA1 report

## Result and limits

`SA1_RESULT=PASS` for this sealed evidence package. The result authorizes only a request for another completely fresh isolated SA3. It does not claim `C_LOCAL_PASS`, global PASS, or permission to modify source. `source-writer=NONE`; TeX remained disabled.

HANDOFF_ID: `C-FIG-P603-01-R104-SA1-FRESH-ISOLATED-V1`  
Instance: `/root/sa1_fig_p603_r104_fresh_isolated`  
Evidence root: `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\C_visual\evidence\FIG-P603-01\sa1_r104_fresh_isolated_v1`

## Independence and input identity

The sole reviewed PDF is `main_full.pdf`: 4,967,222 bytes, SHA256 `E5C871642FBDDBEC6508BE1B61BD911FE281CA5ACFBD16B0449B13357770A641`, 817 A4 pages. The figure was independently located from that PDF at physical page 655 (1-based; PDF index 654), printed page 642, figure `图32.6`.

Localization anchors were the caption opening “MH 接受概率是比值 r 的截断函数”, the displayed graph/formulas `α=min{1,r}`, `r=π(y)q(y,x)/[π(x)q(x,y)]`, `r=w(y)/w(x)`, and the following page sentence “图32.6 同时画出比值小于与大于1的两段；‘截到1’来自概率上界，而不是数值补丁。” No page number, denominator, or conclusion was inherited from an older audit.

Only the six dispatched input paths recorded in `identity/INSTANCE_SCOPE.json` were read. No old P603 evidence/SA1/SA2/SA3/root/handoff/conclusion was read, including the explicitly forbidden `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\evidence\figures\FIG-P603-01\R1`. No central reports/state/inventory/routing/C current state/task packet/scope/model-route/chat/git history, other UID evidence, or other agent output was read. No subagent was started. Source, PDF, and main body were read-only. LuaLaTeX, latexmk, texlua, and all TeX executables were not invoked.

## Native render and crop identity

Poppler rendered the original PDF page directly at 300dpi. The page grid is 2481×3508px for 595.276×841.890pt. Crops are integer-coordinate extractions with no resizing:

- standalone figure: page pt `[108,507,479,657]`, page px `[450,2112,1997,2738]`;
- figure plus caption: page pt `[57,507,527,691]`, page px `[237,2112,2197,2880]`;
- complete page: native 300dpi plus a direct 200dpi overview;
- grayscale: conversion only, no resampling;
- overlay: native raster with audited object boundaries.

The full page, figure crop, standalone, grayscale, overlay, all 15 glyph sheets, all five critical-pair sheets, and both fraction-rule cards were actually opened. `manual/view_reviewer_ledger.jsonl` contains 28/28 view records.

## Complete object universe

The foreground universe contains 24 objects: eleven text objects (`T01`-`T11`) and thirteen graphic objects (`G01`-`G13`). Text covers both tick-label groups, both graph annotations, fold label, both axis labels, both boxed mathematical lines, caption label, and caption body. Graphics cover both tick groups, axis lines and arrowheads, both curve segments, threshold guide, fold marker, formula frame, and both fraction rules.

The PDF page exposes 22 drawing records. Drawing indices 8-13 and 15-21 map one-to-one to the thirteen graphic foreground objects. Indices 0-7 are preceding page content and are explicitly excluded. Index 14 is the pale acceptance-region background field, retained in all color/grayscale views but excluded from reader-foreground pair geometry. Included and adjacent excluded PDF text blocks are enumerated in `machine/drawing_coverage_machine.json`; there are zero uncovered drawing indices.

All 24 object masks are nonempty. Manual object review is 24/24, with each object checked for content, mask completeness/purity, readability, and clip status.

## Glyph audit

There are 150 visible glyphs and 13 explicitly excluded whitespace characters. Each glyph has a machine inventory row, a native/8x inspection card, a mask, a position on one of 15 contact sheets, and one independently authored manual record. All 15 sheets were opened. Manual results:

- 141 `PASS`;
- 5 `ADVISORY_R168_LEGACY_OPERATOR_HEIGHT` for equality signs C037, C064, C094, C107, and C141;
- 4 `ADVISORY_R168_PEER` for unique punctuation C007, C076, C103, and C131.

For every glyph, `original_match=true`, `overlay_complete=true`, `mask_only_pure=true`, `missing_stroke_px=0`, and `foreign_pixel_px=0`. No tofu, wrong codepoint, wrong mathematical glyph, unreadable mark, or obvious serious size imbalance is present.

The five equality signs are ordinary crisp equality glyphs with 12-13px ink height at native 300dpi. That triggers a legacy operator-height metric but is not a font hard failure under R168. The four unique punctuation marks lack an exact same-font peer inside this single figure; each was manually inspected and is complete and correct. Comparable colon and comma peers have exact 1.0 height/area ratios.

## Typography, roles, and harmony

The figure source declares 8.5pt/10pt tick labels and 9.2pt/11pt figure text/formulas at graphics scale 1.0. It contains no resizebox, scalebox, transform-shape, or scale token; its two clip settings are false. The PDF renders tick text at 8.9664pt, body/formula text at 9.1656pt, and caption text at approximately 9.963-10.062pt.

The 8.5pt and 9.2pt declarations are below a legacy 9.5pt test and are recorded as advisories. At native page and crop scale the text is crisp, readable, balanced with neighboring page text, and free of severe role imbalance. Same-class role ratios are tight: tick digits 1.04, annotation CJK at most 1.0303, caption-label digits 1.037, and caption-body CJK 1.0882. Larger cross-glyph ranges reflect normal differences among parentheses, equality signs, CJK squares, and lowercase math glyphs rather than a font defect. `manual/role_reviewer_ledger.jsonl` gives separate D (declared/source) and E (actual rendered) decisions for all eleven text objects.

## Pair, overlap, clearance, and clip audit

All unordered pairs are covered: `C(24,2)=276`, with 276 machine rows and 276 unique manual per-pair records. Twenty-three pairs are critical because the measured separation is at most 12px or an overlap is detected; each has 1x/8x isolated evidence and appears on one of five opened contact sheets.

Eleven pairs have detected geometric overlap. All are intentional graph construction contacts: x/y ticks at axes, ticks at origin/curve/guide, arrowheads on axes, axes at the origin, curve at the origin, plateau at the y=1 tick/guide, and rising curve at the fold marker. Manual `illegal_overlap_px` is zero for all 276 pairs.

No pair violates its category clearance requirement. The minimum text-text clearance is 18px between caption label and body. Minimum text-to-line clearance is 6px where each formula meets its own fraction rule; the opened 8x rule cards show separate numerator/denominator ink and an intact rule. Minimum text-to-frame clearance is 26px. The close curve-to-guide separation is 6.0711px and remains visibly distinct.

All 24 objects lie fully inside their relevant crop; total clipped pixels are zero. Minimum crop-edge clearance is 18px. Full-page review confirms no collision with adjacent prose, display material, caption, or footer.

## Mathematics, relations, and page consistency

The graph exactly represents the MH acceptance function: `α=r` for `0≤r<1`, a fold at `(1,1)`, and `α=1` for `r≥1`. The dashed guides and annotations support rather than contradict the curve.

The boxed general ratio preserves numerator/denominator order and proposal arguments: `r=π(y)q(y,x)/[π(x)q(x,y)]`. The independent-proposal specialization `r=w(y)/w(x)` is correct. The caption repeats the same function and ratios. Necessary surrounding body context gives `α(x,y)=min{1,b/a}` and the equivalent target/proposal ratio. The body's use of unnormalized tilde-π versus normalized π in the figure is mathematically consistent because the normalizing constant cancels. Grayscale review shows that line style and geometry preserve all essential distinctions without relying only on color.

## Hard-gate decision

All thirteen manually authored hard gates pass: identity, independent localization, content, object completeness, glyph completeness, all-pairs completeness, illegal-overlap, clearance, clip, R168 typography, actual rendered views, page fusion, and operational scope. Machine denominators are 150 glyphs, 24 foreground objects, 276 pairs, 23 critical pairs, zero empty masks, zero machine below-clearance pairs, and zero clip pixels. Manual ledgers contain no hard failure.

Advisories are limited to legacy point/operator metrics and exact-peer metadata. Under R168, those are not hard failures because the affected content is visibly crisp, semantically correct, and harmonious. Geometry, relation, mathematical semantics, visible-object content, body consistency, true clipping, and illegal overlap all pass their hard gates.

## Disposition

`SA1_RESULT=PASS`  
`NEXT_REQUEST=REQUEST_FRESH_ISOLATED_SA3`  
`C_LOCAL_PASS=NOT_CLAIMED`  
`GLOBAL_PASS=NOT_CLAIMED`  
`SOURCE_WRITE=NONE`  
`TEX=DISABLED`

The next reviewer must be a completely fresh isolated SA3 and must independently locate and evaluate the figure rather than inheriting this report's physical page, denominator, or conclusion.
