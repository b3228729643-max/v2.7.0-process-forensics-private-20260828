# R168 manual visual adjudication

## Native findings

- Figure and caption are crisp and readable at native 300 dpi; no element is clipped.
- The 20-object denominator is complete and all 190 unordered pairs have a manual disposition.
- Eight machine bbox contact candidates are all intended connector-to-card-border contacts. Additional near-endpoint pairs are separated by native white pixels or intentionally terminate at a border. No connector, marker, border, or caption ink touches reader text illegally.
- Main-chain arrows stop at the relevant borders and never cross formula ink. Auxiliary dashed paths stay below the main cards and above the independence result.
- The simplex icon/label, lower result cards, and caption have visible clearances in native and nearest8× evidence.
- Color is not required to recover meaning: card positions, borders, arrow direction, dashed auxiliary paths, triangle/point, numbered badges, and explicit text survive grayscale.
- The figure occupies the normal text width, is balanced on printed page 697, and leaves a clean transition to the following bold subheading. There is no visibly obvious imbalance or anomalous whitespace.
- The current caption and nearby V5-C05 theorem say the same thing as the figure. The reading order is unique and left-to-right.

## R168 hard-defect matrix

| Hard-defect category | Manual result |
|---|---|
| Missing glyph / tofu / wrong codepoint | NONE |
| Wrong mathematics or semantic statement | NONE |
| Actual unreadability at native evidence | NONE |
| Visibly obvious imbalance | NONE |
| True clipping | NONE; `CLIP_PIXEL_COUNT=0` |
| Illegal visible-ink overlap | NONE; `OVERLAP_PIXEL_COUNT=0` |
| Semantic/geometric error | NONE |
| Grayscale collapse | NONE |
| Page-integration defect | NONE |
| Unresolved candidate | NONE |

The source's 9.2 pt main declarations and 8.5 pt note/badge declarations, and the older numeric typography thresholds, were considered advisory exactly as required by R168. Native pixels show no actual unreadability or wrong glyph and therefore provide no hard source-return basis.

## Verdict

`SA2_NO_SOURCE_CHANGE_READY_FOR_FRESH_SA1`

No source or PDF was modified. This adjudicator does not start fresh SA1 or any other UID/role.
