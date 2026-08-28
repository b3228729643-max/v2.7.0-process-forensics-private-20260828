# FIG-P639-01 R105 SA3 fresh isolated final report

## Outcome

`PASS` for `HANDOFF_ID=MAIN-R105-P639-SA3-FRESH-ISOLATED-20260826`.

The official R105 candidate matches the requested 817-page, 4,967,209-byte PDF with SHA-256 `F86E89047BA09FEA72FD8F79BF524A04DA367BFF3057806A879106A1032626A1`; review target is physical page 689 / printed page 676. No prior P639 result/evidence/handoff/state or any P640 conclusion was used.

## Evidence closure

- Native grid/crop: page `2481 x 3508` at 300 dpi; figure crop `[380,1350,1695,720]`.
- Denominator: `N=80` = 72 glyphs + 8 graphic/path objects.
- All unordered pairs: `3160/3160`, with unique ordinary pair IDs.
- Glyph package: 72 raw-mask PNGs, 72 per-glyph contact PNGs, 5 contact sheets covering 72/72 glyphs, and 72/72 manual contact-review rows.
- Drawing/path package: all 11 visible PDF drawing records map to 8 semantic graphic objects; no path-rendered math-rule object is present.
- Critical geometry: 5 designed intersections, each with 6 ROI files and an individual manual row.
- True geometry: illegal overlap 0, clip 0, empty masks 0. Minimum independent text-text / text-graphic / text-node-border / text-edge clearances are 13 / 16 / 19 / 23 px.

## Actual hard-gate findings

No missing/tofu/wrong glyph, mathematical semantic error, actual unreadability, visually gross imbalance, crop, or true illegal overlap was found. Page integration, grayscale differentiation, caption/text consistency, and mathematical semantics all pass. `FONT_VISUAL_HARMONY_PASS=true`.

## R168 advisory disclosure

The raw evidence retains the following non-blocking observations: source 8.5/9.2 pt values; two minus glyphs at 4 px; two equals glyphs at 13 px; low-stroke CJK `一` at 4 px; three same-color low-punctuation calibration gaps; and the resulting note-CJK ratio observation. Under current R168 these are advisory and cannot independently make the UID fail.

## Disposition

Return `PASS` to main and wait for `A_LOCAL_PASS` acceptance. This SA3 does not update central state or inventory.

