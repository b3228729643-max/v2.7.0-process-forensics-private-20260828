# FIG-P067-01 manual view ledger

- Reviewer: `/root/p067_r113_fresh_sa1`
- Handoff ID: `A-R113-P067-SA1-FRESH-ISOLATED-20260827`
- Official candidate: frozen R113 `main_full.pdf`
- Located independently from the current caption/source at physical page 69, printed page 56, Figure 4.1.
- Native page: 595.276 x 841.890 pt; 300 dpi grid 2481 x 3508 px.
- Frozen figure crop: global `[420,260,1600,670]` px; standalone body crop: `[420,260,1600,575]` px.

## Actually opened evidence

| Evidence | Opened | Manual observation | R168 hard result |
|---|---:|---|---|
| `page_300dpi.png` | 1/1 | Complete native page; figure, caption, following prose, header/footer all visible. | PASS |
| `full_page_200dpi.png` | 1/1 | Figure is balanced in the page, caption and following prose have natural separation, no page-edge collision. | PASS |
| `figure_crop_300dpi.png` | 1/1 | Both panels, axes, all labels, endpoint markers, note and caption are sharp and readable. | PASS |
| `standalone_300dpi.png` | 1/1 | Complete two-panel plot body; no object cut at the crop boundary. | PASS |
| `grayscale_300dpi.png` | 1/1 | Steps, stems, guides, open/filled markers and text remain legible without color. | PASS |
| `after_text_measurement_overlay_300dpi.png` | 1/1 | G001-G095 cover every non-space visible glyph exactly once in the frozen denominator. | PASS |
| `machine_drawing_overlay_300dpi.png` | 1/1 | D001-D035 cover all foreground drawing records; five later white text backgrounds are separately inventoried. | PASS |
| `critical_rois/*_native_300dpi_8x_nearest.png` | 4/4 | CDF continuity, all jump endpoints, PMF stems/note and caption inspected at nearest-neighbour 8x. | PASS |
| `contact_sheets/glyph_sheet_*.png` | 16/16 | All 95 glyph cells opened; original, target overlay and mask-only views inspected at 1x/8x. | PASS under R168; extraction fringe noted separately |
| `pair_contact_sheets/pair_overview_*.png` | 5/5 | All 99 independently near/overlap-candidate pair IDs opened. | PASS after manual adjudication |
| R00229/R00230/R01219 individual original + 8x overlays | 3/3 | The only machine relationships below text/graphic reference clearance were inspected individually. None is a real text-line collision. | PASS |

No tofu, replacement glyph, wrong codepoint, missing label, clipping, illegal overlap, actual unreadability, obvious imbalance, semantic error or geometric error was observed.

## Pre-manual correction disclosure

Before any reviewer field existed, the first drawing-color mask admitted pale gray text into long colored drawing bboxes. Those machine artifacts were discarded, hue isolation was tightened, and the machine evidence was regenerated. A second pre-manual correction constrained drawing masks to vector-path support and subtracted the five real later-painted opaque text backgrounds; those intermediate machine artifacts were likewise discarded and regenerated. A later proposed glyph-purification regeneration was not authorized by the execution gate and therefore was not run; its code change was reverted so the retained builder matches the retained evidence. The surviving one-pixel/bbox-context glyph-mask fringes are recorded as R168 advisory extraction artifacts and were checked against the unmodified native originals.

