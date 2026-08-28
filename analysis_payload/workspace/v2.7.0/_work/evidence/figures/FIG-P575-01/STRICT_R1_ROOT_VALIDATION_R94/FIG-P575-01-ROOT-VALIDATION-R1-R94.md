# FIG-P575-01 root validation — R94 / strict R1

- Official candidate: `strict_current_r94_fullbook/main_full.pdf`
- Physical page / printed page / figure: 623 / 610 / 31.3
- Audit evidence: `STRICT_R1/SA1_20260824_R1`
- Root decision: **FAIL → SA2**

## Root-independent checks

- Read the figure source and adjacent generalized-inverse definition/theorem/proof; independently checked the continuous and discrete values. `Q(.65)=-ln(.35)/.65=1.615926`; the plotted 1.615 gives `F=0.650040`. The discrete masses `(0.25,0.45,0.25,0.05)` sum to one and give `Q(.70)=2`, `Q(.72)=3` under the first-attainment `>=` rule.
- Viewed the official R94 native figure crop, whole page, grayscale view, semantic-element overlay, all four failed-pair raw/1:1/8x packs, and representative colon, CJK `二`, equals-sign, and decimal-point glyph packs.
- Recomputed the machine ledger from the bottom CSVs: 31 unique semantic font elements, 151 unique glyph traces, 22 graphic objects, 53 total objects, and all `C(53,2)=1378` unordered pairs. Object, glyph, and pair IDs are unique; referenced raw masks exist.
- Source font: 28/31 semantic elements fail. Pixel height: 26/151 glyphs fail; this is deliberately separate from the 141/151 combined source/pixel/D/E glyph gate failures. D has 10 failed groups; E has 16 failed comparable-script rows.
- Geometry final result: illegal overlap 0px/0 pairs; clip 0. There are 32 explicitly intentional graphic--graphic relations, of which 24 have visible raw intersections totalling 1021px; all are legitimate axis/tick, curve/marker, or guide/marker connections and are excluded from illegal text-overlap counts.
- Four real text--text PDF/vector bbox-clearance failures remain: `PAIR_0171`, `PAIR_0406`, `PAIR_0533`, `PAIR_0977`. Their PDF bbox minimum is 0px and raw-ink minimum is 6.708px. Each required evidence pack has seven files and was viewed. They are clearance failures, not overlap failures.
- The initial intermediate audit incorrectly counted intentional graphic intersections as 204 illegal pixels. A later intermediate mask also admitted three gold antialias pixels into the black tick mask. Both intermediate results were rejected; the final mutually exclusive raw glyph masks report duplicate pixels 0 and overlap 0. The formal report, CSV, JSON, and Markdown terminal now agree.
- Mathematical semantics, caption/text consistency, reading order, grayscale distinction, and page integration pass; font and overall visual harmony fail because hard font/pixel/D/E/clearance gates fail.

## Routing

Route to a dedicated SA2 only when the current P634 business-source writer has stopped. Repair must raise all effective fonts to at least 9.5pt, preserve the generalized-inverse semantics, and move/reflow the four crowded text pairs rather than shrink the figure. A new official build and a brand-new per-figure SA1 are mandatory afterward.
