# FIG-P634-01 final visual acceptance — R8 CID-knockout authority

- Review identity: `3e8d102b15d1d40e9d08d8426b0cd7e849eb0cdb81625385c4e591a25f5cd4dd`.
- Official anchor: `main_full.pdf`, physical page 682 / printed page 669 / Figure 33.3; native render is 2481×3508 at 300 dpi.
- The reviewer actually opened `full_page_200dpi.png`, `figure_crop_300dpi.png`, `standalone_300dpi.png`, and `grayscale_300dpi.png`. The completed reviewer ledger has 192 unique view×panel×role×script rows (48 per view), no empty or unresolved row, 168 visual PASS rows and 24 explicit visual FAIL rows.
- The reviewer actually opened all 14 `glyph_mapping_*_8x_nearest.png` contact sheets. `glyph_manual_review.csv` and `glyph_contact_sheet_coverage.csv` each contain 193 unique completed glyph records. For every glyph, the original crop matches its uniquely red target overlay, the mask-only cell is pure, and manual missing/foreign stroke pixels are both zero. This is a mask/identity conclusion, not a waiver of a native-height gate.

## Visual findings

- Colour, grayscale, local, standalone, and full-page reading all retain the state-card hierarchy, update-order arrows, caption association, page integration, baseline stability, and panel separation. No reviewed visual row found crowding, clipping, an illegal text/graphic contact, or a cross-panel intrusion.
- `FONT_VISUAL_HARMONY_PASS: FAIL`. The same six semantic groups fail in every view: formula bases `T030`, `T037`, and `T039` have complete visible `x` at native H=21<22 px; the period in `T045` has H=7<22 px; `T046` contains the complete fullwidth `；`/`，` at H=16/13<30 px; and `T047` contains the complete fullwidth `，`/`。` at H=13<30 px. The formula scripts are separately reviewed as natural TeX script and do not create an independent base/script clearance relation.
- These nine hard native-pixel failures are visually traceable but are not missing-stroke or foreign-mask findings. Their individual IDs are `T030:G01`, `T037:G01`, `T039:G01`, `T045:G03`, `T046:G14`, `T046:G28`, `T046:G37`, `T047:G06`, and `T047:G28`.

## Decision

Machine identity/mapping, raw-mask purity, final-visible CID support, relation/clearance, clipping, and manual-review closure pass; the figure does not pass the required typography/pixel and font-visual-harmony gates. **Final SA1 result: FAIL → SA2.**
