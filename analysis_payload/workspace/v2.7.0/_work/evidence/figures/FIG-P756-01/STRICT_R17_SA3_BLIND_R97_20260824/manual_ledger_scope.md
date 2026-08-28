# Manual-ledger scope

The final ledgers were written after direct visual opening, not script-generated
pass filling.

- 'glyph_manual_ledger.csv': 380 rawdict characters: 378 individually visible
  contact-sheet cells and two explicit nonvisible U+0020 records. Every visible
  row records original/overlay/mask/8x review, missing-stroke pixels,
  same-color-neighbor contamination, foreign pixels, calibration status, and
  conclusion.
- 'graphic_manual_ledger.csv': 58 semantic graphics, including opaque fills,
  white feedback label, report separator, paths, borders, and arrowheads.
- 'critical_relation_manual_ledger.csv': all 129 critical cards. Each row
  records native 1x, both masks, overlay, and nearest-neighbor 8x opening. Its
  pair IDs join directly to 'after_overlap_report.csv', which contains exact
  source anchors, final-visible contact pixels, z-order, and clearance.

The only non-pass conclusion is GLY0215 in glyph-contact-sheet 11, cell 13.
