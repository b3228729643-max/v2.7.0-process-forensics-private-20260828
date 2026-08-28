# <UID> 最终视觉验收

- CANDIDATE_ID: `<required>`
- SOURCE_FONT_PASS: `false`
- PIXEL_HEIGHT_PASS: `false`
- GLYPH_MAPPING_COVERAGE_PASS: `false`
- GLYPH_MASK_CONTAMINATION_PASS: `false`
- GLYPH_VISIBLE_CONTOUR_COMPLETENESS_PASS: `false`
- GLYPH_CONTACT_MANUAL_LEDGER_PASS: `false`
- SAME_CLASS_RATIO_PASS: `false`
- ROLE_RATIO_PASS: `false`
- OVERLAP_PIXEL_COUNT: `<required non-negative integer>`
- CLIP_PIXEL_COUNT: `<required non-negative integer>`
- MIN_TEXT_CLEARANCE_PX: `<required measured minimum>`
- TEXT_TEXT_CLEARANCE_PASS: `false`
- TEXT_GRAPHIC_CLEARANCE_PASS: `false`
- NODE_BORDER_CLEARANCE_PASS: `false`
- EDGE_CLEARANCE_PASS: `false`
- CROSS_PANEL_CLEARANCE_PASS: `false`
- FONT_VISUAL_HARMONY_PASS: `false`
- FONT_VISUAL_HARMONY_LEDGER_PASS: `false`
- VISUAL_HARMONY_PASS: `false`
- MATH_SEMANTICS_PASS: `false`
- TEXT_CONSISTENCY_PASS: `false`
- GRAYSCALE_PASS: `false`
- PAGE_INTEGRATION_PASS: `false`
- SA1_RESULT: `FAIL`
- SA3_RESULT: `NOT_RUN`
- ROOT_RESULT: `FAIL`

默认值故意为 FAIL。只有原始证据齐全并逐项验证后才可改为 true/PASS；不得以空值、未知或旧报告替换。

## 证据路径

- full_page_200dpi: `<required>`
- figure_crop_300dpi: `<required>`
- standalone_300dpi: `<required>`
- grayscale_300dpi: `<required>`
- font_audit: `after_font_audit.csv`
- pixel_measurements: `after_pixel_measurements.csv`
- overlap_report: `after_overlap_report.csv`
- measurement_overlay: `after_text_measurement_overlay_300dpi.png`
- glyph_mapping: `<required 100% CHAR-to-shape mapping CSV>`
- glyph_contact_sheets: `<required 100% native/8x-nearest contact-sheet set>`
- glyph_contact_manual_ledger: `<required one reviewer-authored row per glyph; no pending/blank/duplicate/extra row>`
- mask_contamination_report: `<required machine report; contamination intersection count must be 0>`
- visible_contour_completeness_report: `<required machine report; missing final-visible >=20/255 target stroke count must be 0>`
- font_visual_harmony_ledger: `<required native-view plus panel/role/script reviewer ledger; no hard-coded visual PASS>`

## 失败项或通过依据

`<逐 ELEMENT_ID 记录；不可写“基本可读/轻微重叠/肉眼可接受”>`
