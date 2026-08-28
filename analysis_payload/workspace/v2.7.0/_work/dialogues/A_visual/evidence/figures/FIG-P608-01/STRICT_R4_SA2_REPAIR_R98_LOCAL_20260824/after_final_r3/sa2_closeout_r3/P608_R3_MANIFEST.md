# FIG-P608-01 SA2 R3 local manifest

- Candidate: local one-page LuaLaTeX build from the Dialogue A worktree; this is not an official R99/full-book candidate.
- Native measurement raster: `../final_local_lua_official_stack_300dpi.png`, 2481 x 3508 px at direct 300 dpi.
- Page-fusion view: `../full_page_200dpi.png`; figure crop, standalone and grayscale are sibling native artifacts in `../`.
- Object denominator: 31 text parents + 58 visible PDF paths + 2 pattern-stroke objects = 91.
- Pair denominator: all unordered pairs = 4095, recorded by `P608_R3_ALL_4095_PAIRS.csv`.
- Ownership: `P608_R3_OBJECT_OWNERSHIP.csv` reports `foreign_pixel_px=0` and `missing_stroke_px=0` for every counted object.
- Rotated glyph inverse-axis dimensions: `P608_R3_ROTATED_GLYPH_LOCAL_METRICS.csv`.
- Low-profile same-codepoint/font/effective-size calibration: `P608_R3_LOW_PROFILE_CALIBRATION.csv` (11 records; all PASS).
- Hatch relationships: `P608_R3_HATCH_GLYPH_MATH_RULE_RELATIONS.csv` (140 records; all separate).
- Intentional graphic composites: `P608_R3_GRAPHIC_COMPOSITE_WHITELIST.csv` (45 documented line/marker, target-reference, or axis/arrow assemblies).
- Critical original/mask/overlay/8x cards: `critical_relation_cards/` (97 relations, three artifacts each).
- Glyph native 1x and 8x review sheets: `../glyph_opened_1x_sheets/` and `../glyph_opened_8x_sheets/` (13 sheets each, 74 glyph records).

Terminal consistency result: 91 objects, 4095 pairs, zero illegal text overlap, zero required-clearance failures, zero ownership foreign/missing pixels, zero low-profile failures, and zero hatch relation failures. The compact local PDF cannot substitute for the official full-book candidate or the later independent SA1/SA3 reviews.
