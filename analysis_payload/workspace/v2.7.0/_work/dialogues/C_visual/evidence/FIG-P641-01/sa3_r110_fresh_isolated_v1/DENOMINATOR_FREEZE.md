# FIG-P641-01 R110 SA3 Fresh-Isolated Visible-Object Freeze

- Handoff: `C-FIG-P641-01-R110-SA3-FRESH-ISOLATED-V1`
- Reviewer: `/root/sa3_fig_p641_r110_fresh_isolated_v1`
- Located artifact: physical PDF page 691, printed page 678, Figure 33.8.
- Freeze point: after opening the full page, complete figure plus caption, standalone figure body, grayscale view, semantic/object overlay, text overlay, all glyph and graphic contact sheets, all critical contact sheets, and all 41 nearest-neighbor 8× ROIs.

The complete visible foreground denominator is frozen at `N = 180`:

- `C001`–`C162`: 162 visible glyph objects. Each row in `after_pixel_measurements.csv` contains its semantic parent, text, Unicode codepoint/name, font, vector size, native-300-dpi ink box and mask path. Every ID has a genuine manual judgment in `manual_glyph_ledger.csv`.
- `G01`–`G18`: 18 foreground graphical objects, consisting of three factor borders, four node borders, three dashed Markov-blanket borders, six factor-graph edges, one annotation-arrow shaft and one annotation-arrowhead. Every PDF drawing object intersecting the figure body is assigned exactly once in `graphics_inventory.csv`, and every ID has a genuine manual judgment in `manual_graphic_ledger.csv`.

The union of these two inventories contains no background, page furniture or caption container as a foreground object. The exhaustive unordered-pair universe is therefore `180 × 179 / 2 = 16,110`, recorded one row per pair in `all_unordered_pairs.csv`. The critical-relation subset is frozen at 41 rows in `critical_relations_machine.csv` and manually adjudicated in `manual_critical_relation_ledger.csv`.

No object was added to or removed from the denominator after the pair table was generated.
