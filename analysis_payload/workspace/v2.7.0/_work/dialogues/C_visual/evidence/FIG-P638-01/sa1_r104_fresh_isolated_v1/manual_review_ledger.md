# Manual review ledger and denominators

This is a fresh, per-ID review; no old verdict or bulk/default PASS was imported.

- Text objects: E001–E010, each separately ruled in `manual_object_rulings.csv`.
- Graphic objects: G001–G006, each separately ruled in `manual_object_rulings.csv`.
- Total objects: 16.
- All unordered object pairs: C(16,2) = 120; every OP0001–OP0120 has an explicit manual ruling in `manual_all_object_pair_rulings.csv`.
- Mechanically selected close/overlap pairs: 21; each has an expanded independent ruling in `manual_critical_pair_rulings.csv`.
- Visible non-whitespace glyphs: 202; every GL0001–GL0202 has an explicit glyph/codepoint/height/ruling row in `manual_glyph_rulings.csv`.
- All unordered glyph pairs: C(202,2) = 20,301 in `all_unordered_glyph_pairs.csv`; the glyph inventory and pair table were reviewed by owning element, same-run typographic relation, cross-element bbox contact, and the critical object-pair ledger. No cross-element glyph collision survives native-pixel adjudication.
- Peer/role rows: 10. The machine file reports raw object-height ratios, which are not font-size proxies for stacked formulas or mixed scripts. Source effective sizes are equal within the diagram, dominant same-script glyphs remain visually balanced, and no severe size imbalance exists. R168 treats micro ratio/taxonomy differences as advisory.
- Clip rows: 16. Every object has positive reserve within the evidence crop; the smallest is 25 px. Original-page inspection shows no clipped text, formula, arrowhead, border, or caption, so canonical clip count is zero.

Views personally checked at native or inspection scale:

- R104 full page at 300 dpi and 200 dpi;
- 300 dpi figure crop and standalone-equivalent local crop;
- grayscale 300 dpi crop;
- 8x nearest-neighbor top-flow, exception, and caption inspection views (inspection only, never used as measurement input);
- object-box overlay, combined class mask, each object mask, and the raw MC001 masks;
- current figure source lines 1–27 and R104 extracted page text/font inventory.

R168 hard-failure audit found no tofu, missing/wrong glyph or codepoint, mathematical-semantic error, actual unreadability, obvious severe size imbalance, true clipping, or illegal overlap. Geometry, relations, formulas, object content, and neighboring-text consistency also pass.
