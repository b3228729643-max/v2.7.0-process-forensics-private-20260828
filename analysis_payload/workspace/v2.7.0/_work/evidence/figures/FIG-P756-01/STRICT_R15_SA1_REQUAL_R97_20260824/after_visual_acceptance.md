# FIG-P756-01 — SA1 visual acceptance record

Reviewer: SA1. Candidate: `main_full.pdf`, SHA-256
`062AD81020CB19A5C6688A45C73E00965F5060E0960A69AF820D7DC154DEE814`.
The figure is on physical PDF page 801 (printed page 788); the native grid is
2481 × 3508 at 300 dpi, with figure crop `[300,700,2150,1995]`.

The reviewer actually opened the following final-candidate renderings:

- `full_page_native_300dpi-801.png` and `full_page_200dpi-801.png`: caption,
  lead-in, figure, read-figure prose, and page flow were readable and mutually
  consistent. No figure/caption/body intrusion or clipping was seen.
- `figure_crop_300dpi.png` and `standalone_300dpi.png`: the five-station
  feedback loop, two task routes, shared engine pool, isolation validation and
  one-way report are legible with an unambiguous reading path.
- `grayscale_300dpi.png`: solid/dashed relationships, arrow direction, node
  hierarchy, and the double report frame remain distinguishable without hue.
- All 32 current critical-pair 5-up cards and the G030/G031 8× nearest card:
  named endpoint/component contacts remain limited to their stated source
  anchors; no unapproved crossing or mask pollution was observed.

## Typography and hierarchy

`reviewer_font_visual_harmony_by_element.csv` records each of the 25 text
objects after the actual page/crop/standalone/8× views. Normal visible text is
9.60 pt; panel titles are 10.20 pt. Thus the page-wide minimum is 9.60 pt and
the largest/smallest role ratio is 1.062500. Same-panel same-role source sizes
are all 1.000000 (zero absolute difference); cross-panel source ratios are
1.000000 for the only shared roles, `ANNOTATION` and `PANEL_TITLE`.

`font_harmony_by_element.csv` gives the per-element/per-script D/E medians:
all comparable rows meet the 0.92–1.08 element-to-role interval and the 1.08
same-panel extreme limit; 8 low-profile punctuation rows are separately
calibrated and manually signed. The two single-glyph lower-Latin panel labels
are explicitly `N/A_INSUFFICIENT_UNMATCHED_GLYPH_DISTRIBUTION` for a
cross-panel raw-height comparison (the visible letters are `a` and `b`, with
different x-height/ascender geometry); their declared 10.20 pt scale and
opened visual hierarchy are nevertheless identical and coherent.

FONT_VISUAL_HARMONY_PASS: true

This is a manual visual conclusion, not a script-produced PASS flag. Supporting
view, role/script, object-level, and low-profile reviewer ledgers have no
pending or blank rows.
