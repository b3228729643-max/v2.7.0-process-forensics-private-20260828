# FIG-P715-01 visual acceptance

- Reviewer: `gpt-5.6-sol / xhigh`, fresh isolated SA1.
- Candidate: frozen R107 PDF, physical page 765, printed page 752, Figure 36.2.
- Actual manual views: source plus all six rows in `review/manual_four_view_ledger.tsv`, all 18 glyph sheets, all 4 graphic sheets, and both critical-pair sheets.

The figure is readable at whole-page scale and at native crop scale. The two-panel hierarchy is balanced: blue panel titles lead, graph and matrices form the primary content, and notes/formulas remain subordinate but legible. No title, note, matrix entry, subscript, punctuation mark, or operator is actually unreadable; no tofu, wrong code point, clipping, crowding, or visually severe imbalance appears. Grayscale preserves the reading path and focus-cell distinctions.

Source declarations are 9.5 pt for general nodes/notes, 10.2 pt for node and matrix text, 10.4 pt for titles, and 12 pt for formulas. Extracted role medians are recorded in `review/manual_panel_role_script_ledger.tsv`. Small punctuation, natural scripts, PDF rounding near 9.5 pt, taxonomy/peer median differences, font metadata, `[0.92,1.08]` comparisons, and 1–2 px raster differences are treated as advisory under the controlling R168 instruction and are not used alone as hard failures. Each visible glyph nevertheless has a nonempty, complete, pure final mask and an individual manual PASS row.

`FONT_VISUAL_HARMONY_PASS = TRUE`

`FOUR_VIEW_PASS = TRUE`

`GLYPH_CONTACT_REVIEW_PASS = TRUE`

`GRAPHIC_CONTACT_REVIEW_PASS = TRUE`

`CRITICAL_PAIR_REVIEW_PASS = TRUE`

Decision: `PASS`.
