# FIG-P756-01 R115 SA1 Figure Hard Gates

**Final figure decision: FAIL_TO_SA2.** Evidence integrity is PASS, but two independent non-waivable hard failures remain.

## Hard failure 1: P1408 merges two independent route objects

- Pair: `P1408`, `O-G016` supervised-route border versus `O-G017` unsupervised-route border.
- Raw final-visible measurement: **792 common pixels; minimum clearance 0 px** on the official p801 native 300-dpi grid.
- Object evidence: `object_masks/O-G016_final_visible_mask_only_1x.png` and `object_masks/O-G017_final_visible_mask_only_1x.png`; corresponding independent pre-occlusion masks are in `draw_masks/`.
- Source locator: `full_course_synthesis_map.tex` l57-58 defines the supervised route and l59-60 defines the unsupervised route. They are separate semantic route objects; the source contains no declaration that they share one boundary object. Draw-order distinction is retained in `object_inventory.csv` (`O-G016` order 60; `O-G017` order 63).
- Semantic ruling: this is **not** intentional shared geometry. The later shared-engine-pool semantics do not authorize the two route panels to co-own a border; their raw final-visible overlap is therefore an illegal route-boundary merge.
- Full human-inspected package, with no peer deletion/dilation/resampling: `roi_packages/P1408_O-G016_O-G017/`:
  - 1x: `original_raw_1x.png`, `mask_A_1x.png`, `mask_B_1x.png`, `intersection_1x.png`, `overlay_1x.png`
  - 8x nearest: `original_raw_8x_nearest.png`, `mask_A_8x_nearest.png`, `mask_B_8x_nearest.png`, `intersection_8x_nearest.png`, `overlay_8x_nearest.png`

## Hard failure 2: three non-low-profile CJK glyphs below the strict raw-pixel floor

All three are `口`, are classified `LOW_PROFILE=false`, use actual effective type size 9.5641 pt, and nevertheless have raw native 300-dpi ink height **29 px < 30 px**. A valid low-profile calibration cannot exempt these full-contour glyphs.

| Glyph | Element / role | Result |
|---|---|---|
| `G0208` | `E024`, BOTTOM `EXIT_NOTE` | FAIL: H=29 px |
| `G0212` | `E025`, BOTTOM `LEGEND` | FAIL: H=29 px |
| `G0222` | `E025`, BOTTOM `LEGEND` | FAIL: H=29 px |

Authoritative records: `R115_PIXEL_FINAL_ADJUDICATION.csv` and `R115_CALIBRATION_AND_DE_SUMMARY.json` (375 pass, 3 fail, 0 invalid calibration method).

## Closed gates that do not cure the failures

- All 1,485 unordered pairs were measured; P1408 is the sole pair failure. All 1,107 mandatory relationships are present in the ledger.
- Clip/edge test passes for all 55 foreground objects; D/E same-class and role checks pass for 378 glyphs.
- All actual effective font sizes are at least 9.5 pt. The typography is visually coordinated: 10.1619-pt bold panel hierarchy, 9.5641/9.9626-pt internal labels, and blue/teal/orange roles are legible, balanced with page text, and retain structure in grayscale. This visual pass does not waive the separate raw-pixel failures.
- Arrow/badge overlaps other than P1408 are expressly visible attachments and are individually adjudicated in `R115_HUMAN_RELATION_ROI_LEDGER.csv`; they do not repair P1408.

**Disposition: send to SA2 with both failures preserved as independent fixes.**
