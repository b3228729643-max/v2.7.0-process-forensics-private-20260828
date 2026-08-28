# FIG-P429-01 — SA1 STRICT_R1 report

RESULT: **FAIL**

Current candidate location was independently established as PDF physical page **466** (printed page **453**), not the historical task-card page. The figure is 图 24.1 in chapter 24; its current caption and the adjacent explanatory paragraph are text-consistent with the three branches (clustering, dimension reduction, probabilistic modelling), and the directed reading path is semantically intelligible.

## Coverage and native evidence

- 21 visible text/formula ELEMENT_IDs, including all body labels, four variable labels, the inline `→`, the evidence node, and both caption lines.
- 47 individual PDF/vector graphic objects; 1,197 pair checks: 210 text-text plus 987 text/vector. Parent-label and parent-border/arrow pairs were included rather than exempted.
- The corrected geometry disposition has 8 applicable failures and 117 explicit `N/A` external-text-to-node-border pairs. `N/A` does not suppress a same-parent text/arrow check: all arrows and markers remain subject to the 3px gate.
- Direct final-PDF views: full page at 200 dpi, figure crop at 300 dpi, grayscale crop at 300 dpi, and 300-dpi text-measurement overlay. No PNG was resized or screenshot-derived.
- A genuine independent standalone build was not possible under this read-only task because the source is an in-document fragment that depends on shared styles and this role may not create a wrapper. `standalone_300dpi.png` is deliberately absent and documented as a hard evidence gap.

## Source-font and pixel results

`SOURCE_FONT_PASS = false`.

- 14 visible items are below the 9.5pt floor: `E01–E02` at 9.4pt; `E06–E09` and `E15–E17` at 9.2pt; `E10–E14` at 9.0pt. `graphics_scale = 1.0000`; no global scale rescues these values.
- The 300-dpi class floor also fails for `E12_DIM_ARROW`: `→` has `H_ink_px=16`, below the 22px base-math-symbol threshold. Other measured minima: CJK 31px (>=30), uppercase/digit 25px (>=24), Latin/Greek lowercase 19px (>=17), and slash 29px (>=22).
- `SAME_CLASS_RATIO_PASS = true`; element ratios span 0.9500–1.0141. `ROLE_RATIO_PASS = true`: panel label 1.1935, annotation 1.0000, node label 1.0968, evidence note 1.0323 relative to the annotation base. Axis/tick/legend/formula-block roles are absent.

## Overlap, clearance, and clip results

`OVERLAP_PIXEL_COUNT = 466` is the unique union of confirmed native-300-dpi foreground pixels. It is not the arithmetic sum of pair counts (the 8 pair counts sum to 494 because geometries can share pixels).

For each applicable pair, the disposition first intersects an independently reconstructed current-PDF glyph silhouette with the separately enumerated PDF vector path/stroke; it then requires the matching final raw 300dpi foreground pixel. This separates the geometry verdict from paint order. No dilation, closing, broad-bbox proxy, or same-parent exemption is used. Every failure has 1:1 `raw_roi`, independent `text_mask` and `vector_mask`, `separated_masks`, `overlay`, and `overlap_mask` files named by `PAIR_ID`.

| Pair | Confirmed illegal relation | PDF glyph/vector px | Native raw foreground px | Clearance / gate |
|---|---|---:|---:|---:|
| TG0339 | `E03_CLUSTER_TITLE` × `G35_SOURCE_TO_CLUSTER` | 86 | 86 | 0.00 / 3px |
| TG0340 | `E03_CLUSTER_TITLE` × `G36_SOURCE_TO_CLUSTER_HEAD` | 79 | 79 | 0.00 / 3px |
| TG0388 | `E04_DIM_TITLE` × `G37_SOURCE_TO_DIM` | 19 | 17 | 0.00 / 3px |
| TG0389 | `E04_DIM_TITLE` × `G38_SOURCE_TO_DIM_HEAD` | 45 | 45 | 0.00 / 3px |
| TG0437 | `E05_PROB_TITLE` × `G39_SOURCE_TO_PROB` | 204 | 204 | 0.00 / 3px |
| TG0438 | `E05_PROB_TITLE` × `G40_SOURCE_TO_PROB_HEAD` | 38 | 38 | 0.00 / 3px |
| TG0675 | `E10_CLUSTER_NOTE` × `G42_CLUSTER_TO_EVIDENCE` | 7 | 7 | 0.00 / 3px |
| TG0867 | `E14_PROB_NOTE` × `G46_PROB_TO_EVIDENCE` | 19 | 18 | 0.00 / 3px |

The prior-looking proximity of `E14_PROB_NOTE` to the neighbouring middle/right `x` circles is retained in the CSV as `N/A` (4.15px and 4.14px), not a failure: it is an external annotation, not text inside either node. The applicable node-text-to-own-border minimum is **12.25px**, so the required 5px node-border gate passes.

- `CLIP_PIXEL_COUNT = 0`; `after_edge_clip_report.csv` covers all 68 text/vector objects, with 0 failed rows.
- Minimum text-text clearance: 8.00px; applicable text/graphic 0.00px; applicable node-border 12.25px; line/arrow 0.00px; marker 15.57px; page edge 258.00px; crop edge 27.00px; cross-panel text 212.00px.

## Four-view and semantic review

- `MATH_SEMANTICS_PASS = true` and `TEXT_CONSISTENCY_PASS = true`.
- `GRAYSCALE_PASS = true` and `PAGE_INTEGRATION_PASS = true` for the available direct-PDF views.
- `VISUAL_HARMONY_PASS = false`: the eight actual arrow-through-text collisions are visible at 1:1, and the required independent standalone view is missing. Thus a four-view PASS is impossible.

## Blocking repairs for SA2

1. Raise every reader-visible body item to effective >=9.5pt without global shrinkage; re-balance the layout instead of compressing it.
2. Replace the inline mathematical `\to` in `高维点 $\to$ 低维坐标` with wording such as `高维点映射为低维坐标`, or otherwise redesign it so that every retained base math symbol reaches 22px while preserving role ratios.
3. Terminate/reroute the three source arrows outside the three panel-title glyph areas; preserve >=3px text-to-line/arrow clearance.
4. Move the cluster/probability evidence-arrow start points or their notes so they no longer pass through glyphs; retain the already-passing 5px own-node text clearance.
5. After repair, generate a real independent standalone build at 300 dpi (not a crop), then regenerate all native evidence and return to a new SA1 review.

Next role: **SA2 only**. Do not route this failed object directly to SA3.

## Evidence paths

- `after_font_audit.csv`
- `after_pixel_measurements.csv`
- `after_overlap_report.csv`
- `after_edge_clip_report.csv`
- `after_visual_acceptance.md`
- `full_page_200dpi.png`, `figure_crop_300dpi.png`, `grayscale_300dpi.png`, `text_measurement_overlay_300dpi.png`
- `standalone_300dpi_UNAVAILABLE.md`
