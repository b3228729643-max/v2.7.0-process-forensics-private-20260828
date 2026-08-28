# FIG-P756-01 R115 SA1 Evidence Integrity

**Status: PASS.** This is an independent SA1 requalification record for FIG-P756-01 (图37.8). Evidence integrity is assessed separately from the figure hard-gate outcome.

## Authoritative input and locator

- Official candidate only: `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\build\strict_current_r95_fullbook\main_full.pdf`
- SHA-256: `24CC8BE127D00435CC544E4E9142D45272675DA0D9967C89ADAC294D08910496`
- Figure page: physical PDF page 801; printed page 788; native grid `2481 x 3508` at 300 dpi.
- Read-only source locator: `src/绘图源码/第05册_采样方法主题模型与图排序/V5-C08/full_course_synthesis_map.tex`; source facts and draw-order locators are recorded in `object_inventory.csv`.

## Independent measurement provenance

- There are 56 inventory objects: 55 foreground relation objects and one opaque halo/background (`O-H001`). The 55 foreground objects yield all `C(55,2)=1485` unordered pairs; `1107` are mandatory relationships.
- Each final-visible object mask is independently replayed on the same official native 300-dpi grid. No mask was made by deleting a peer, by dilation/erosion, by resampling, or by reclassifying an overlap away. Pre-occlusion masks and source draw order are retained separately.
- The ledger covers 378 visible glyphs. `R115_HUMAN_GLYPH_LEDGER.csv` has one row per glyph; `R115_CONTACT_VIEW_OPEN_LOG.csv` records the SA1 opening all 48 native 1x sheets and all 95 8x nearest-neighbour sheets (143 contact views total).
- `R115_HUMAN_RELATION_ROI_LEDGER.csv` covers all 24 critical/failure ROI packages. For every package, SA1 opened original, A mask, B mask, intersection, and overlay at native 1x and 8x nearest-neighbour scales.

## Low-profile calibration validity

- The superseded Unicode-insertion experiment, `low_profile_calibration/calibration_source_from_official_embedded_fonts.pdf`, is retained only as an invalid historical intermediate and is not used for adjudication.
- The adjudicative calibration is `low_profile_calibration/calibration_source_raw_cid_replay_from_official_v2.pdf`: an official embedded-font raw-CID replay with ToUnicode confirmation. It preserves source F93/F94 font, weight, RGB, effective size, 300-dpi grid, and exact crop/mask bounds.
- All 10 calibration groups and 20 calibration targets validate (`invalid_targets=0`); SA1 also opened raw, overlay, and mask at 1x and 8x for every group. See `R115_LOW_PROFILE_CALIBRATION_MANIFEST.csv`, `R115_LOW_PROFILE_CALIBRATION_VALIDATION.csv`, and `R115_LOW_PROFILE_CALIBRATION_HUMAN_LEDGER.csv`.

## Integrity closure

`R115_MACHINE_FINAL_CHECK.json` verifies the identity, raw-mask availability, complete pair universe, all 10 files in each of 24 relation packages, human-review ledger coverage, calibration validity, clipping ledger, and D/E records. The evidence is complete and internally consistent. It deliberately preserves, rather than suppresses, the two figure-quality hard failures stated in `FIGURE_HARD_GATES.md`.
