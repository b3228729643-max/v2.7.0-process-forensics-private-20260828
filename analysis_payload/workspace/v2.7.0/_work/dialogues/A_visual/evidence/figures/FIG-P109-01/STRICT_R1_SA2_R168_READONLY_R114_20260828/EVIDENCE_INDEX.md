# Evidence index

## Identity and current-location evidence

- `locator.json`: exact R114 identity, 817-page count, current unique match at physical page 116, and page vector/text geometry.
- `target_page_text.txt`: current page text extraction.
- `mechanical_metrics.json`: 14-object denominator, 91 unordered pairs, vector/PDF bounding boxes, pixel crops, and six ROI definitions; contains no manual reviewer decision fields.
- `denominator_freeze.json`: fixed manual-review denominator.

## Opened visual evidence

- `full_page_200dpi.png`
- `full_page_native300dpi.png`
- `figure_caption_native300dpi.png`
- `figure_caption_grayscale_native300dpi.png`
- `object_overlay_native300dpi.png`
- `text_overlay_native300dpi.png`
- `semantic_overlay_native300dpi.png`
- `R01_native1x.png` and `R01_nearest8x.png`: interpolation formula, segment, and middle marker.
- `R02_native1x.png` and `R02_nearest8x.png`: domain label, set boundary, y label, and endpoint.
- `R03_native1x.png` and `R03_nearest8x.png`: x marker and label.
- `R04_native1x.png` and `R04_nearest8x.png`: formal statement and frame.
- `R05_native1x.png` and `R05_nearest8x.png`: caption.
- `R06_native1x.png` and `R06_nearest8x.png`: tight native-pixel proof of boundary crossing the `C` glyph.

Every view listed above was opened by the reviewer. The 300 dpi images were rendered directly from the frozen R114 PDF without subsequent resize; `nearest8x` images magnify the corresponding native pixels with nearest-neighbor sampling.

## Genuine post-observation ledgers

- `object_ledger.csv`: O01-O14.
- `pair_ledger.csv`: every unordered object pair P001-P091.
- `glyph_codepoint_ledger.csv`: T01-T06.
- `font_advisory_ledger.csv`: R168 treatment of historic numeric font observations.
- `math_ledger.csv`: M01-M06.
- `semantic_ledger.csv`: S01-S08.
- `page_integration_ledger.csv`: I01-I06.
- `hard_gate_ledger.csv`: H01-H11.
- `findings.csv`: the one true hard defect.

## Reproducible read-only helpers

- `inspect_p109.py`
- `render_evidence.py`

These helpers read the allowlisted PDF and create evidence only inside this fixed root. They do not edit source, invoke TeX, build the book, or generate manual reviewer/decision/note/PASS fields.
