# FIG-P605-01 / R104 / SA3 fresh isolated report

## 1. Scope and independence

This report is the self-contained output of HANDOFF_ID `C-FIG-P605-01-R104-SA3-FRESH-ISOLATED-V1`. The only evidence root is this directory. I did not read, list, or hash the forbidden SA1 root; I did not read central FIG-P605 evidence, old P605 evidence, other UID evidence, central reports/state/inventory/routing, task packets, chat/git history, or other-agent output. TeX execution was disabled throughout, the figure/body/PDF were read-only, and `source-writer=NONE`. No source, central state, or central inventory file was modified.

The `codex-lean-execution` process discipline was used only to avoid repeated global scans and redundant gates. The explicit instruction not to create `.codex/continuity` was followed.

## 2. Official-candidate identity and independent location

- PDF: `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\build\strict_current_r104_fullbook\main_full.pdf`
- Pages: 817
- Page size: 595.276 × 841.890 pt (A4)
- Bytes: 4,967,222
- SHA-256: `E5C871642FBDDBEC6508BE1B61BD911FE281CA5ACFBD16B0449B13357770A641`
- Physical page: 658
- Printed page: 645
- Figure: 32.7, label `fig:V5-C03-componentwise-sweep`

The page was located from the R104 PDF itself by searching for both current panel titles and the current caption. No page, denominator, result, or hash was inherited.

## 3. Native renders and mapping

The full page is 2481×3508 px at native 300 dpi and 1654×2339 px at direct 200 dpi. The 300 dpi color/caption crop is 1980×803 px, and the direct standalone body crop is 1819×673 px. These were direct clips of the official PDF, not resized screenshots. Grayscale was rendered directly at the same 300 dpi clip. `IDENTITY.json` records page points, native grids, and integer crop coordinates.

PDF target blocks 1–11 yielded 150 visible glyph objects; seven whitespace characters were explicitly excluded as having no visible ink. Target drawings 1–23 yielded 23 graphic foreground objects: two panel borders, eight node/note borders (including the diamond), six line segments, and six arrowheads, plus the remaining mapped border. Formula `∑` is a font glyph. There is no visible overline, underline, root rule, fraction rule, hat, cancel line, or other formula path in target drawings 1–23. Every atomic object has a safe ordinary filename, native mask, 1× triptych, 8× nearest triptych, semantic parent, role, panel, and bounding box.

## 4. Manual glyph and graphic review

I opened all 13 glyph sheets and completed 150 distinct rows in `manual_glyph_review.csv`. Every row records its own character, codepoint, contact files, sheet/cell, ink height, original match, overlay completeness, mask-only purity, missing-stroke pixels, foreign pixels, tofu/codepoint status, actual readability, imbalance status, decision, and a glyph-specific note. All 150 glyphs are complete and readable; no replacement character or wrong mathematical codepoint is present.

I separately opened each of the 23 graphic contact pairs and completed `manual_graphic_review.csv`. Panel fills and node fills are explicitly treated as backgrounds; border masks contain only visible strokes. Segment tubes were isolated from adjacent gold/blue borders. At own-arrow seams, the shared pixels are intended same-structure connections and are adjudicated at pair level.

## 5. Complete relations, overlap, clearance, and clip

For 173 atomic foreground objects, `machine_pair_inventory.csv` contains exactly 14,878 rows, equal to C(173,2). It covers text–text, text/formula–line/arrow, text/formula–node border, text/formula–panel border, and graphic–graphic relations. There are no hard-geometry candidate pairs.

Thirteen raw-mask intersection candidates total 224 pixels. I opened each candidate's native A/B/intersection/overlay and 8× nearest quint. Four are same-formula natural-subscript seams (`sys`/`rand`), six are a segment joining its own arrowhead, two are node-to-outgoing-line anchors, and one is the choice diamond-to-branch anchor. `manual_candidate_pair_review.csv` records every pair-specific decision. Thus `MASK_CONTAMINATION_PIXEL_COUNT=0` and confirmed `OVERLAP_PIXEL_COUNT=0`.

Measured hard-class minima are 41 px for independent text–text, 20.1 px for text/formula–line/arrow, 16 px for text–node border, and 27 px for text–panel border. These exceed the 4/3/5/6 px thresholds. No target object touches the official page or padded crop edge, so `CLIP_PIXEL_COUNT=0`.

## 6. Font hierarchy and R168 adjudication

Source declarations are 9.2 pt ordinary / 9.8 pt bold panel titles with graphics scale 1.0 and no size-transform mechanism. The old 9.5 pt source rule would flag 9.2 pt, and the legacy pixel taxonomy yields 17 non-PASS measurements: nine low-profile calibration requirements and eight 1–9 px threshold differences involving natural scripts or low-profile math signs.

R168 makes these micro-proportion, taxonomy, peer, and 1–2 px issues advisory unless they cause tofu/wrong codepoint or math semantics, actual unreadability, obvious severe size imbalance, real clipping, or illegal overlap. Every affected ID was personally reviewed: the `sys`/`rand` subscripts, both equals signs, the lower-limit equals, `∼`, ellipses, colons, semicolon, full stops, and period are all intact and legible. No hard trigger exists. The title CJK median is 39 px on both panels, annotation CJK median is 34 px on both, node/formula K bases are 27 px, and caption CJK median is 36 px. The hierarchy is balanced in color, grayscale, standalone, and full-page views. `FONT_VISUAL_HARMONY_PASS=true`.

## 7. Mathematical semantics and body consistency

The left panel correctly displays `K_sys=K_1K_2\cdots K_d` and states that a fixed-order composite generally is not reversible. The right panel samples `J\sim\omega`, points to `K_1,K_j,K_d`, displays `K_rand=\sum_{j=1}^d\omega_jK_j`, and states the correct condition/conclusion: if every `K_j` is reversible with respect to `\pi`, the fixed-weight mixture remains reversible. The caption states the same distinction.

The optional current body was read only where necessary. Its proposition, proof, and figure-introduction lines say that each coordinate kernel preserves `\pi`, the fixed product preserves `\pi` but is generally not reversible, and the fixed-weight mixture is reversible. The figure and body therefore agree without missing premises or reversed arrows.

## 8. Result and advisories

All R168 hard gates pass: identity, object completeness, C(n,2) coverage, nonempty/pure masks, codepoints, actual readability, visual hierarchy, math semantics, body consistency, zero illegal overlap, zero clip, required clearances, grayscale, and page integration.

Advisories retained transparently:

1. the ordinary source declaration is 9.2 pt versus the legacy 9.5 pt threshold;
2. 17 glyph measurements are legacy calibration/threshold advisories;
3. four same-formula seams contain 1–4 shared native pixels but are readable same-parent typography, not illegal overlap.

SA3 conclusion: `C_LOCAL_PASS_ONLY`.

This conclusion is local to the isolated SA3 role. It does not claim global PASS, does not update central inventory/state, and awaits mainline acceptance.

