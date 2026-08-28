# FIG-P634-01 R6 local visual coordination review

Result: **PASS for local SA2 review; not a formal independent acceptance.**

## Views inspected

- Whole local A4 page at direct 300 dpi: `renders/local_page_300dpi.png`.
- Whole local A4 page in reduced grayscale: `renders/local_page_gray_150dpi.png`.
- Figure at direct 300 dpi: `crops/figure_crop_300dpi_1x.png`.
- Figure at direct 300 dpi grayscale: `crops/figure_crop_grayscale_300dpi_1x.png`.
- Text/graphics mask-registration overlay: `overlays/text_graphics_measurement_overlay_300dpi_1x.png`.
- EL-035 raw 1:1, separated masks, intersection, and nearest-neighbour 8x packs in `critical_pairs/EL035_script_to_card1_border` and `critical_pairs/literal_j_to_card1_border`.

## Human findings

- The title, eight-slot coordinate band, status labels, two state cards, and caption preserve a clear top-to-bottom reading order.
- `前位 / 当前 / 后位 / 末位` is visually even and reads naturally as a positional axis; the eight centers and update arrow remain aligned.
- The hatched completed region, gold current cell, dotted future cells, and blue/gold/gray status labels remain immediately distinguishable in color and grayscale.
- The new two-line node labels are balanced within their unchanged boxes; no label appears crowded, isolated, or anomalously small.
- The first-card title has comfortable genuine whitespace above the text and does not appear artificially displaced.  Its body partitions remain visually balanced left/right.
- The two bottom arrows, formulas, annotations, and `轮末样本` form one coherent flow with no collision or optical ambiguity.
- The caption wraps to two balanced lines and stays clearly separated from the second card.  Its punctuation reads as prose rather than as detached formula fragments.
- Noto Sans title, Noto Serif instructional text, and STIX math glyphs remain coordinated with the surrounding page.
- No new white patch, occlusion, clipping, or result-directed mask is visible.  Existing white halos remain limited to the intended hatched node interiors.

## Measured coordination anchors

- Minimum independent text-to-text gap: 15px (gate 4px).
- Minimum cross-panel text gap: 36px (gate 8px).
- Minimum text-to-line/arrow gap: 13.036px (gate 3px).
- Minimum text-to-border gap: 8px (gate 5px).
- Minimum text-to-final-visible texture gap: 6px (gate 3px).
- EL-035 script element to first-card border: 16px; literal `j` to border: 18px (gate 5px, design target 8px).

All values come from separated final-visible 1:1 masks on the direct 300 dpi page; 8x images are visual corroboration only.
