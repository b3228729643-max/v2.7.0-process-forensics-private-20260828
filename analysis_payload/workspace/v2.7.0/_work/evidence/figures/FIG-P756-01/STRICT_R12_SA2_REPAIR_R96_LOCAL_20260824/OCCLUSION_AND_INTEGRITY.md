# Occlusion, clipping, and mask integrity — local R12

- Inventory: 56 objects total; 55 final-visible foreground relation objects plus one real source-declared opaque halo `O-H001`.
- `O-H001` final/background mask foreground pixels: 35650.
- Feedback path `O-G015` pre-occlusion pixels: 4343; final-visible pixels after applying only the real halo mask: 4343; removed pixels: 0. A zero removal count is preserved honestly because the routed path does not enter the current opaque-label interior.
- All object final/pre masks exist, decode as ordinary image files, are nonempty, and preserve unique safe names.
- Clip report: 55/55 PASS; crop-edge foreground count 0 and page-edge foreground count 0 for every object.
- Glyph integrity: 378/378 masks report foreign pixels 0, missing-stroke pixels 0, nonempty, purity/completeness true; six 1×/8× files per glyph machine-opened.
- Relation masks use independent final-visible objects; no peer deletion, dilation, resized counting, or shared-boundary reclassification.
