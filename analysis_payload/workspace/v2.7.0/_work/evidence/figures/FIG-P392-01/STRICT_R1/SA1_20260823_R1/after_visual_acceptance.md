# FIG-P392-01 SA1 strict visual acceptance R1

RESULT: FAIL

Identity: caption and label search uniquely found frozen-R93 physical PDF page 428, printed page 415, figure 图 22.1.

| Gate | Value | Status |
|---|---:|---|
| SOURCE_FONT_PASS | false | FAIL |
| PIXEL_HEIGHT_PASS | false | FAIL |
| SAME_CLASS_RATIO_PASS | true | PASS |
| ROLE_RATIO_PASS | true | PASS |
| OVERLAP_PIXEL_COUNT | 39 | FAIL |
| CLIP_PIXEL_COUNT | 0 | PASS |
| MIN_TEXT_CLEARANCE_PX | 0.000 | FAIL |
| VISUAL_HARMONY_PASS | false | FAIL |
| MATH_SEMANTICS_PASS | true | PASS |
| TEXT_CONSISTENCY_PASS | true | PASS |
| GRAYSCALE_PASS | true | PASS |
| PAGE_INTEGRATION_PASS | true | PASS |

Methods: full_page_200dpi.png, figure_crop_300dpi.png, standalone_300dpi.png and grayscale_300dpi.png are direct native PDF views without resize. The direct Poppler page render full_page_300dpi_native.png feeds all 300 dpi coordinates. Glyph foreground is taken from a local text-only derivative that preserves original PDF text operators, transforms and fonts while removing vector paint operations; this avoids same-colour node-border contamination. Raw ROI remains the original page. Each visible glyph is separate in after_pixel_measurements.csv. Natural script fragments and all basic mathematics and punctuation are independently measured, never replaced by a formula-level bbox. Vector masks are independently reconstructed from final-PDF path operators and stroke width at 8x supersample. All object masks are under masks; after_overlap_report.csv records span and vector masks, bbox clearance, ink clearance, nearest local and page coordinates, and closest or failed raw ROI/overlay/overlap-mask evidence.

Findings:

- Source-font FAIL: 85 glyph rows have an under-9.5 pt final base, a script whose base is under 9.5 pt, or unknown caption declaration under the permitted read scope.
- Pixel-height FAIL: 12 glyph rows fail their own threshold. Worst independent glyph is ⋯ (TXT011), H_ink 6 px against 22 px.
- Visual-harmony FAIL: in native 300 dpi views the terminal y_(n+1) label runs into both rings of its double boundary, so the endpoint is visibly crowded and no longer balanced with the other node labels.
- Semantics PASS: white y labels form the label chain, gold M factors represent adjacent-label factors, and the teal fixed-input strip makes complete observed x explicit. The note correctly says undirected edges do not imply generation. This agrees with adjacent source lines 234 to 241.
- Reading order PASS: left-to-right chain, then downward fixed input and note. No arrowhead exists because the graph is undirected.
- Grayscale PASS: shape, white/gray fill, rectangle/circle distinction, dashed links and brace preserve the structural encoding. No axes, legend, data curve, marker, or panel label exist; those ratio rows are explicit N/A.
- Page integration PASS: the caption, explanatory sentence and next section are separated without clipping, abnormal whitespace or an intrusive figure footprint.

Any hard failure means this candidate cannot proceed to SA3. The only next actor is subagent2, which must repair and rebuild a new candidate before a fresh full SA1 audit.
