# After overlap and clearance adjudication

The foreground object universe is frozen at `N=122`: 108 visible glyphs plus 14 visible foreground drawing paths. The two visible fills are explicitly accounted as backgrounds and excluded; there are no math rules. The exhaustive unordered-pair ledger emits exactly `C(122,2)=7,381` unique rows.

Machine results:

- empty masks: 0
- unwhitelisted overlap candidate pixels: 0
- clip pixels: 0
- pair gates: 6,207 `MEETS_MACHINE_GATE`; 1,174 `DESIGN_WHITELIST`
- closest independent text/text bbox clearance: 9 px, against a 4 px gate
- closest text/line-arrow ink clearance: 12 px, against a 3 px gate
- closest own-node text/border ink clearance: 13 px, against a 5 px gate
- closest independent graphic/graphic ink clearance: 15 px, against a 0 px gate
- minimum text-to-frozen-crop-edge clearance: 25 px

All 11 frozen critical/closest relations were opened at raw 1× and 8× nearest-neighbor scale. The first six have empty intersections and clear their applicable gates. The remaining five intersections are the shaft/head joins of one inline arrow, three main arrows, and the feedback arrow. They are intentional same-parent design continuity; their canonical illegal-overlap count is 0. No glyph-border, glyph-arrow, independent-text, or independent-graphic collision was found.

Manual relation ledger: 11/11 rows opened, object-specific notes present, and decision `PASS` for every row. No manual field was generated or overwritten by a machine script.

Adjudication: `CLEAR`.
