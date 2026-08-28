# Opened-view ledger

All entries below record actual post-generation visual openings by the fresh SA1 reviewer. `native1x` means unresized pixels from the direct 300 dpi page raster. `nearest8x` means exactly 8x nearest-neighbour enlargement of that native ROI.

| View ID | File | Opened | Manual observation |
|---|---|---|---|
| V01 | `visual/full_page_native300dpi.png` | yes | Page integration, caption, neighboring proof/paragraph/next heading all balanced; no page-level clipping or overflow. |
| V02 | `visual/full_page_200dpi.png` | yes | At normal full-page scale the figure remains readable, proportionate, and neither dominates nor disappears. |
| V03 | `visual/figure_crop_native300dpi.png` | yes | Both curves, fills, labels, brace, axes, ticks and caption are complete and semantically coherent. |
| V04 | `visual/figure_crop_grayscale_native300dpi.png` | yes | Solid versus dashed curves remain unambiguous; reference line remains subordinate; fills do not erase hierarchy. |
| V05 | `visual/text_measurement_overlay_native300dpi.png` | yes | T01-T13 boxes cover every logical text/formula/caption construct with no missing visible text object. |
| V06 | `visual/visible_object_denominator_overlay_native300dpi.png` | yes | T01-T13 and G01-G17 are all locatable; broad fill bboxes explain mechanical bbox intersections without implying visible-ink collision. |
| V07 | `visual/critical_narrow_label_native1x.png` | yes | T09 is sharp and isolated from curve ink. |
| V08 | `visual/critical_narrow_label_nearest8x.png` | yes | No tofu, wrong radical/codepoint, broken stroke, or shared visible foreground pixel. |
| V09 | `visual/critical_wide_label_native1x.png` | yes | T10 and its natural superscript are readable; the dashed curve stays below the carrier. |
| V10 | `visual/critical_wide_label_nearest8x.png` | yes | Superscript, parentheses, radical bar and denominator are intact; no text/curve collision. |
| V11 | `visual/critical_area_brace_label_native1x.png` | yes | Brace, carrier, area statement and visible x-axis portions are cleanly separated. |
| V12 | `visual/critical_area_brace_label_nearest8x.png` | yes | Brace-to-text and text-to-visible-axis gaps are genuine, not antialias artifacts. |
| V13 | `visual/critical_caption_native1x.png` | yes | Figure number and complete one-line conclusion are legible. |
| V14 | `visual/critical_caption_nearest8x.png` | yes | No missing/tofu/wrong glyph, clipping, or character collision. |
| V15 | `visual/critical_axis_ticks_titles_native1x.png` | yes | Axis/tick/title relationships and curve geometry are correct at native pixels. |
| V16 | `visual/critical_axis_ticks_titles_nearest8x.png` | yes | Arrowheads, tick joints, curve dashes and reference line are intact; all intended intersections are geometrically coherent. |
| V17 | `visual/critical_area_center_tick_native1x.png` | yes | Tight center region shows label carrier and the small residual center tick below the label. |
| V18 | `visual/critical_area_center_tick_nearest8x.png` | yes | The 2-pixel machine hit is a duplicated tick-mask fragment below text ink, not a text/tick collision. |

Opened coverage: 18/18 required or critical views opened; 0 inferred only from filenames/logs.
