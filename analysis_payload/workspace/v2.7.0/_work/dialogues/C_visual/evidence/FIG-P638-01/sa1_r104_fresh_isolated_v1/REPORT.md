# FIG-P638-01 R104 fresh isolated SA1 report

## Outcome

`SA1_PASS_REQUEST_FRESH_SA3`

The official R104 candidate independently maps to physical page 688, printed page 675, Figure 33.5. The current diagram passes the R168 hard gates for mathematical semantics, relationships, formula content, object completeness, native readability, real overlap, clipping, grayscale behavior, caption/body consistency, and page integration. No SA2 repair is requested by this SA1.

## Evidence coverage

- Native renders: full page 300 dpi, full page 200 dpi, figure crop 300 dpi, standalone-equivalent 300 dpi, grayscale 300 dpi.
- Inspection views: 1x and three 8x critical regions.
- Inventories: 16 objects, 202 glyphs, page text, page fonts.
- Pair denominators: 120/120 unordered object pairs and 20,301/20,301 unordered glyph pairs present; 21 critical object pairs separately adjudicated.
- Manual ledgers: 16 object rulings, 202 glyph rulings, 120 all-pair rulings, 21 expanded critical-pair rulings.
- Clip, peer/role, source font, pixel height, formula/content, caption/body, grayscale, and full-page integration were all reviewed.

## Pixel adjudication

MC001 is the only independent-semantic candidate: vector text bboxes for E003/E004 overlap by 0.16 pt, producing 17 duplicated pixels when a composited raster is reselected by those bboxes. Native ink ends/starts at rows 1085/1092 with six blank rows; isolated masks share zero pixels and have 8 px clearance. It is therefore `MASK_CONTAMINATION_CONFIRMED`.

The decorative divider shares two pixels with each warning branch. Those four pixels are intended line-line structural crossings, not illegal semantic overlaps, and do not enter the canonical candidate count.

Canonical values: candidate 17; mask contamination 17; illegal overlap 0; clip 0; minimum text clearance 7 px.

## R168 advisory notes

The source diagram uses 9.2 pt, and natural script glyphs extract at 6.4159 pt. Several naturally short glyphs have small ink heights (equals, punctuation, assignment arrow); pi/alpha show a one-pixel legacy-threshold deviation. All are visually clear at native 300 dpi with correct codepoints. Raw object-height peer ratios are distorted by stacked formulas and mixed scripts. These are advisory under R168 and do not constitute tofu, actual unreadability, severe imbalance, clipping, or overlap.

## Required next action

Dispatch a completely fresh, isolated, read-only SA3 instance against the same official R104 PDF and current single source, without giving it this SA1's verdict or summary. It must independently rebuild its evidence and apply R168.
