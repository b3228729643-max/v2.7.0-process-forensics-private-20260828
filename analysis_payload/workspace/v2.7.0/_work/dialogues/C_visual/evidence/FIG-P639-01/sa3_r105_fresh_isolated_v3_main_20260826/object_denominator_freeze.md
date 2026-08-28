# Visible-object denominator freeze

- Freeze basis: final-visible foreground in `figure_crop_300dpi.png` at native 300 dpi and local-background contrast `>=20/255`, cross-checked against physical page 689 PDF character and drawing/path streams.
- Included visible objects: 72 non-space glyphs plus 8 explainable graphic/path objects = `N=80`.
- All unordered pairs: `C(80,2)=3160`; `after_overlap_report.csv` contains exactly 3160 unique rows.
- Spaces and pale blue density fill below the mandated 20/255 foreground contrast are backgrounds, not visible-ink objects.
- The 11 visible PDF drawing records are mapped without omission to the 8 semantic graphic objects in `math_rule_and_drawing_ledger.csv`; shaft/arrowhead and x/y tick-record joins are explicit semantic unions.
- No PDF path-rendered mathematical rule is present. The formula labels are glyph-only.
- Geometry quality uses separated final-visible raw masks. PDF font boxes are retained for mapping only; invisible font-box contact is not promoted to a hard collision when raw masks are separated.
- Five raw-mask intersections remain in the all-pairs ledger, all individually allowlisted and manually opened as designed graph geometry: axis-origin connection, density-to-axis endpoint connections, and each mean guide terminating on its own density curve. Illegal-overlap count is zero.

