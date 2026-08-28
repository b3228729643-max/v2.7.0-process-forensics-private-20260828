# Pixel adjudication

## MC001 — E003 heading vs E004 formula

- Automatic/raw bbox-derived candidate: 17 duplicated pixels.
- Native source coordinates: E003 is the first line of the `r` node on source line 15; E004 is the second-line stacked formula in the same node. The extracted PDF text boxes end/start at y=262.59 pt / y=262.43 pt, a 0.16 pt bbox-only overlap.
- Native 300 dpi pixels: E003's last actual ink row is 1085; E004's first actual ink row is 1092. Rows 1086–1091 are blank, giving six blank raster rows. The separated semantic masks have 0 shared pixels and an 8 px center-to-center clearance.
- Views checked: `full_page_300dpi.png`, `figure_crop_300dpi.png`, `critical_top_flow_8x.png`, raw E003/E004 bbox masks, raw overlap mask, separated object masks, source line 15, and the object overlay.
- Classification: `MASK_CONTAMINATION`. The candidate is caused by using overlapping vector glyph bboxes to select ink from the already composited raster; it is not an overlap of the two actual glyph runs.

## LC001 / LC002 — decorative divider vs warning branches

The red dashed warning arrows each share two final raster pixels with G002. These are real, intentional line-line crossings: the arrows must pass from the main flow across the pale structural divider to the exception box. G002 carries no reader text or independent relation, and the crossings obscure neither arrow direction nor any label. They are recorded in the all-pair ledger as `LEGAL_STRUCTURAL_CROSSING` and excluded from the illegal semantic-overlap candidate denominator.

## Canonical counts

- `OVERLAP_CANDIDATE_PIXEL_COUNT = 17` (independent semantic foreground only)
- `MASK_CONTAMINATION_PIXEL_COUNT = 17`
- `OVERLAP_PIXEL_COUNT = 0`
- `PIXEL_ADJUDICATION_STATUS = MASK_CONTAMINATION_CONFIRMED`
- `CLIP_PIXEL_COUNT = 0`

All mandatory text/text, text-or-formula/line-arrow, text-or-formula/marker, text-or-formula/node-border, text-or-formula/panel-edge, annotation/data, legend/data, and arrowhead/text combinations applicable to this concept diagram are covered by the 120-row all-object-pair ledger. There is no marker, curve, legend, axis, tick, or panel border in this figure.
