# FIG-P577-01 — strict SA1 R2 task specification

## Fixed identity

- Role: fresh per-figure SA1, `gpt-5.6-terra`, `reasoning_effort=max`, read-only for business source and central state.
- Official candidate: `src/build/strict_current_r94_fullbook/main_full.pdf`.
- Physical page: 625; printed page: 612; figure: 31.4; UID: `FIG-P577-01`.
- Figure source: `src/绘图源码/第05册_采样方法主题模型与图排序/V5-C02/fig_v5_c02_rejection_envelope.tex`.
- Adjacent chapter: `src/讲义源码/第05册_采样方法主题模型与图排序/chapters/V5-C02.tex`.
- New evidence only: `evidence/figures/FIG-P577-01/STRICT_R1/SA1_20260824_R2/`. Never overwrite or promote R1 evidence.
- Do not modify LaTeX, wrappers, manifests, inventory, state, official PDF, build files, public styles, or any other figure.

## Authority and semantic target

Use the actual source and adjacent chapter, not the stale Goal B42/old index cross-contamination. The figure is the accept--reject envelope with

`p(y)=6y(1-y)`, `q(y)=1`, `c=8/5`, and acceptance gate `Ucq(Y) <= p(Y)` including equality.

Independently recompute envelope validity, minimum gap, fixed candidate classification, acceptance rate, expected proposal count and rejection area. Unknown or inconsistent semantics are FAIL.

## Native rendering and inventory

1. Render physical page 625 directly from the frozen official R94 PDF at 300 dpi. The canonical grid is the unresampled 1:1 raster. Use 8× nearest-neighbour only for human inspection.
2. Recover every reader-visible text/formula/axis/tick/legend/annotation/panel/caption glyph and every final-visible graphic, line, arrow, marker, border, fill, texture and page edge in the figure scope.
3. Close `CHAR ↔ actual contour ↔ semantic parent ↔ bbox ↔ raw mask` for 100% of final-visible characters. Expected order is about 342 characters; derive the exact count from R94 rather than inheriting it.
4. Every mask ID and file must be an ordinary Windows file. Provide an explicit `ID ↔ SAFE_FILENAME` mapping; reject `:`, Windows-invalid characters, reserved device names and NTFS alternate data streams. Machine terminal must enumerate, open, dimension-check and reference-check every expected PNG/JSON/CSV.

## Per-glyph three-view manual gate

For every final-visible glyph, generate one cell with the same native bbox and pad in all three panels:

1. `ORIGINAL`: unmodified official R94 ROI at 8× nearest.
2. `TARGET OVERLAY`: the unique target raw mask painted red over that original ROI.
3. `MASK ONLY`: only the target glyph mask, no neighbour, hatch, curve, marker, border, background or shadow.

Maintain a reviewer-authored row for every glyph with `GLYPH_ID, REVIEWER, SHEET, CELL, ORIGINAL_MATCH, OVERLAY_COMPLETE, MASK_ONLY_PURE, MISSING_STROKE_PX, FOREIGN_PIXEL_PX, DECISION, NOTE`. Do not use a global boolean to bulk-promote rows. `pending`, blank, duplicate, extra, unknown, missing stroke or foreign pixel makes terminal PASS impossible.

The earlier R1 claim for `T022_G01` is rejected evidence: it labelled a tiny approximately 2×3 solid mask as U+FF08. R2 must independently show the actual fullwidth-left-parenthesis contour or mark the mapping FAIL. Review every other glyph with the same strictness; do not repair only this example.

## Mask completeness and contamination

- Target masks must include every final-visible target stroke pixel at effective contrast `>=20/255`; missing count must be exactly 0 for PASS.
- Target masks must contain 0 pixels from neighbouring glyphs, hatch/texture, curves, lines, arrows, markers, borders, fills, shadows or background.
- Do not use tight-character-bbox modal background estimation: high-ink glyphs can invert it and textured regions can contaminate it.
- Derive masks from traceable official PDF font/text operators or equivalent exact mapped path + actual fill/opacity + proved underlay. Preserve paint order and pre/halo/final-visible masks for occlusion.
- Border masks are stroke-only; never include opaque white interiors as border ink.

## Hard visual gates

- Source effective base text `>=9.5pt`. Natural TeX scripts may be smaller only when their base formula is `>=9.5pt` and the script passes its own pixel floor.
- Native 300 dpi pixel floors: CJK/fullwidth/near-fullheight `>=30px`; uppercase/digit `>=24px`; lowercase/Greek lowercase `>=17px`; base math/operator/fraction component `>=22px`; natural script `>=15px`.
- D gate: same panel + same semantic role + same script class only; no exact-glyph grouping and no cross-script comparison.
- E gate: comparable script against an actual eligible BASE in the same panel; otherwise explicit justified `N/A`, never a fabricated pass.
- Illegal overlap pixels must be 0. Independent text bbox clearance `>=4px`; text to line/arrow/marker `>=3px`; text to node border `>=5px`; figure edge `>=6px`; cross-panel `>=8px`; clip pixels 0.
- Glyphs inside one semantic formula do not use the independent-text 4 px rule, but true glyph overlap, occlusion or unreadable fusion still FAIL.
- Review font size, weight, baseline, line spacing, role hierarchy and cross-panel harmony. Fonts may be reduced only while remaining `>=9.5pt`, meeting the per-glyph pixel floor and preserving comfortable whole-figure viewing; any conspicuously oversized, undersized, crowded or inconsistent label is FAIL.
- Independently recompute all foreground pairs and all required relations. Revisit the prior relation identifiers TG304, TG317 and TG457 from raw masks without inheriting their old distance claims.

## Required output and terminal rule

Produce the five Goal files plus raw inventories, masks, mapping/contact/manual ledgers, D/E tables, all-pair table, required-relations table, pre/halo/final-visible evidence, failure/critical 1:1 and 8× packages, math/text review, grayscale/page-integration/font-harmony review and a machine-integrity JSON.

The machine terminal must cross-check unique/nonempty masks, safe ordinary files, 100% contact/manual coverage, completeness 0 missing pixels, contamination 0, expected pair count `n(n-1)/2`, all classified clearances, CSV/JSON/Markdown counts and verdict. A known hard failure does not permit early stopping: finish the complete audit, report `FAIL`, and provide a minimal source-level repair whitelist. Do not write a stop marker until all required evidence is complete and internally consistent.
