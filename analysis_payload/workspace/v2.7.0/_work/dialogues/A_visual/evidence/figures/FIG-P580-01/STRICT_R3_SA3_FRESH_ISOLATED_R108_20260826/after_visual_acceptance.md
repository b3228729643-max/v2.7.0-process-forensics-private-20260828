# FIG-P580-01 — R108 fresh isolated SA3 visual acceptance

- Handoff: `A-R108-P580-SA3-FRESH-ISOLATED-20260826`
- Reviewer: `SA3_FRESH_ISOLATED_R108`
- Official candidate: R108 `main_full.pdf`, physical page 630, printed page 617, Figure 31.6
- Official PDF: 817 pages; 4,967,161 bytes; SHA256 `C2EC93425486A57DE4C6670E16FC7DA729649A183230C28E8A0652467D3B5B78`
- Single current source: 5,580 bytes; SHA256 `F0ECC9B28361A2AE73AF085A4958AD09F8F94575D789B8F776C55631FD45E161`
- Manual decision timestamp: `2026-08-26T12:32:15.1404754Z`

## Independent route and frozen denominator

The reviewer independently scanned the official full PDF by current figure text anchors and located the unique target on physical page 630. No prior P580 page, object ID, count, pair classification, result, report, or conclusion was read or inherited.

The complete visible foreground denominator is frozen at `N=219`: 194 visible text glyph clusters representing 195 visible codepoints, plus 25 visible graphic objects. The U+0338/U+226A sequence is one shaped visible contour and remains mapped to both source codepoints. Every unordered object pair is present exactly once: `C(219,2)=23,871`.

## Native views and visual harmony

The reviewer actually opened `full_page_200dpi`, `figure_crop_300dpi`, `standalone_300dpi`, `grayscale_300dpi`, and the critical U+0338/U+226A native/8× view. The reviewer also opened all 25 glyph contact sheets, all five graphic contact sheets, all 23 final relation sheets, and the final corrected card-border contact.

`FONT_VISUAL_HARMONY_PASS=true`. The 9.6 pt base text and 10.2 pt panel titles form a natural hierarchy. Titles do not dominate; tick labels and formula text are readable; neither panel is crowded; the ratio card is balanced; cross-panel role sizing is consistent; grayscale retains all required distinctions; and the figure integrates naturally with the surrounding page. There is no actual clipping, unreadability, or obvious imbalance.

The reviewer-owned ledgers close exactly:

- glyph rows: 194/194, unique, no missing/extra rows, `missing_stroke_px=0`, `foreign_pixel_px=0`;
- graphic rows: 25/25, unique, no missing/extra rows;
- critical relation rows: 114/114, unique, no missing/extra rows, `actual_hard_failure=false` for every row;
- opened-evidence inventory: five required views, one correction contact, 25 glyph sheets, five graphic sheets, and 23 relation sheets.

## R168 hard-gate adjudication

The raw automated report preserves 74 conservative detections. After native/8× observation, none is an R168 hard failure:

- four fraction/tick-label detections arise from a geometric panel-seam taxonomy split; the actual glyph contours are separate and readable;
- card-text detections arose because the initial path support included the card’s opaque filled interior; a preserved correction layer isolates only the actual rounded-rectangle stroke and recomputes all 44 card-text pairs with zero intersections;
- graph-graph detections are intended topology: axes with ticks/arrowheads, axes at origins, density curves at zero endpoints, proposal-line crossings, support boundary crossings, and markers placed on their defining lines/curves;
- three same-formula contacts are two/four antialias pixels at ordinary typography kerning; R168 treats these tiny contour differences as advisory because codepoints, contours, semantics, and readability are intact.

The final corrected card-border mask contains 2,936 pixels, is border-only, and has zero intersections with all 44 formula-block glyph objects. The original raw support and raw detections remain preserved for auditability.

## Semantic and numerical recomputation

Independent recomputation confirms:

- `p(x)=6x(5-x)/125` integrates to 1 on `[0,5]`;
- `q_L=2/5` on `[0,5/2]` and zero afterwards integrates to 1 but fails support coverage for positive `p` on `(5/2,5)`;
- `q_R=1/5` on `[0,5]` integrates to 1 and covers the support of `p`;
- `w(1)=24/25`, `w(5/2)=3/2`, and `w(4)=24/25`.

The rendered U+0338/U+226A relation is the correct slashed much-less-than contour with no missing glyph, tofu, replacement character, or wrong codepoint.

## Cross-check and decision

The final machine cross-check passes 34/34 controls: identities, zero forbidden operations, denominator/pair closure, masks, sheets, evidence paths, manual-ledger exactness, corrected border support, critical codepoint, semantic recomputation, and visual-harmony record.

Manual SA3 decision: `A_LOCAL_PASS` for return to main acceptance only. This role does not update central state and does not start another role.

## Operation counters

- TeX/latexmk/lualatex/luatex/luahbtex invocations: 0
- source edits: 0
- commit/git writes: 0
- central state writes: 0
- second UID/role: 0

