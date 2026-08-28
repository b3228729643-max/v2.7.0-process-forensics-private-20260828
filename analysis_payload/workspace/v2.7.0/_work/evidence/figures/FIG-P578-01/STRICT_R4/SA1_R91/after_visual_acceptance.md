RESULT: FAIL

# FIG-P578-01 — SA1 R91 strict visual acceptance

Scope: physical PDF page 626 of `main_full.pdf`, figure 31.5, and the assigned live source `fig_v5_c02_rejection_flow.tex` only. The native Poppler raster is 2481×3508 at 300 dpi; every geometry value below comes from that unchanged raster or an unscaled 1:1 crop. The 200 dpi fit view is visual-only and was never used for a geometry measurement.

## Required decision matrix

| Gate | Result | Evidence / finding |
|---|---:|---|
| SOURCE_FONT_PASS | true | 227 visible PDF spans have source-effective provenance. Normal node/edge text is 9.6pt, compact formula blocks 10.7pt, and natural scripts are derived from a qualifying base. No scale/`transform shape`/`resizebox`/`scalebox` occurs in the assigned source. |
| PIXEL_HEIGHT_PASS | false | 17 individually identified base mathematical operators are below the 22px floor: `=` is 12–13px, `∼` is 11px, and `∞` is 18px. See every `OPERATOR` FAIL row in `after_pixel_measurements.csv`; each gives a unique element ID, parent formula, source line, 300dpi bbox, and H_ink. |
| SAME_CLASS_RATIO_PASS | true | Same declared role/font cohorts are uniform; no per-role source-size drift or page/panel scaling was found. The page contains one state-machine panel, so no cross-panel comparison applies. |
| ROLE_RATIO_PASS | true | The formula-block 10.7pt base relative to 9.6pt normal node text is 1.115, inside the formula-block [1.00, 1.18] role band; no unsupported emphasis is present. |
| OVERLAP_PIXEL_COUNT | 0 | Formal high-confidence foreground masks for 21 node borders, 23 arrows/return loop, 16 branch labels, loop label, and adjacent text lines produced no illegal foreground-pixel intersection. |
| CLIP_PIXEL_COUNT | 0 | Figure foreground is 283px from the closest page edge (required >=6px); no text, arrowhead, border, or marker reaches an image boundary. |
| MIN_TEXT_CLEARANCE_PX | **2** | `TEXT_precheck_valid` to `EDGE_precheck_to_valid` has 2 blank pixels (3.000px ink-centre distance, pixel-edge gap = floor(distance)-1), below the text/arrow >=3px floor. |
| VISUAL_HARMONY_PASS | false | `countproposal` breaks the lexical word “立即” as “立 / 即令” at source line 56. It is an abnormal wrap in a central state label even though its formal border/arrow clearance passes. |
| MATH_SEMANTICS_PASS | true | Inputs are verified before randomness; `a=N` precedes `m=B`; a successful proposal alone increments `m`; only acceptance appends/increments `a`; ordinary rejection preserves prefix; random/numerical failures retain the legal prefix; an envelope violation routes to `invalid_input` with envelope diagnostic. |
| TEXT_CONSISTENCY_PASS | true | The source, caption, and page read-guide consistently name the zero-target/zero-budget priority, ordinary rejection, failure exits, and envelope certificate failure. |
| GRAYSCALE_PASS | true | In the gray view, shape, dashed style, arrow direction, status text, and spatial position retain the state distinctions; color is not the sole carrier. |
| PAGE_INTEGRATION_PASS | true | The full-page and fit views retain caption and read-guide association without clipping or isolated figure placement. |

## High-risk formal-mask results

`SA1_R91_precheck_formal_masks_300dpi.png`, `SA1_R91_init_formal_masks_300dpi.png`, `SA1_R91_evaluate_formal_masks_300dpi.png`, and `SA1_R91_countproposal_formal_masks_300dpi.png` are direct, unscaled native-pixel crops. Cyan=TEXT/FORMULA, magenta=NODE_BORDER, yellow=LINE_ARROW.

| Relationship | Clearance | Required | Result |
|---|---:|---:|---:|
| precheck formula → outgoing arrow | 2px | 3px | FAIL |
| init: top/bottom/left/right text → border | 8 / 17 / 56 / 56px | 5px | PASS |
| init incoming/outgoing text → arrow | 27 / 13px | 3px | PASS |
| init line-to-line | 19px | 4px | PASS |
| init natural subscript `X_{1:a}` | min glyph 17px | 15px | PASS |
| evaluate: top/bottom/left/right text → border | 9 / 17 / 113 / 117px | 5px | PASS |
| evaluate incoming/outgoing text → arrow | 23 / 7px | 3px | PASS |
| evaluate line-to-line | 12px | 4px | PASS |
| countproposal text → border / outgoing arrow / next line | 8 / 9 / 29px | 5 / 3 / 4px | PASS |

## Independent visible-object enumeration

- 227 nonempty visible PDF text spans (full inventory in `SA1_R91_pdf_span_inventory.csv`).
- 21 state nodes, 23 directed arrow/return paths, 16 branch labels, the two-line return condition, all borders, caption, and page read-guide (`SA1_R91_object_inventory.csv`).
- The standard pixel ledger has 552 rows: 227 parent spans plus individually measured figure characters for math, status code, Latin/Greek, digits/capitals, scripts, and all operators.

## Required correction before a new candidate

1. At source lines 35, 36, 40, 44–46, 48–49, 51, 53, 57, 62, and 100, make every base mathematical operator satisfy H_ink >=22px at native 300dpi. This likely requires a readable formula-style/size change plus structural reflow; shrinking cannot repair it.
2. Increase the precheck bottom formula-to-arrow separation by at least one more blank native pixel (source lines 37 and 77), then remeasure at 300dpi.
3. Reflow source line 56 so “立即” remains intact, while preserving all node-clearance minima.
4. Rebuild a fresh continuous full-book PDF and repeat the isolated SA1/SA3/root process. This is only an SA1 FAIL finding, not a root issuance.

## Evidence set

- `SA1_R91_page626_300dpi.png` — original 2481×3508 page used for all metrics.
- `SA1_R91_figure_100pct_roi.png`, the four native high-risk ROIs, and the four formal-mask overlays — 1:1 local checks.
- `SA1_R91_page626_fitview_200dpi.png` — fit-page visual-only check.
- `SA1_R91_page626_grayscale_300dpi.png` — gray visual check.
- `after_font_audit.csv`, `after_pixel_measurements.csv`, `after_overlap_report.csv`, and `after_text_measurement_overlay_300dpi.png` — standard strict-audit outputs.
