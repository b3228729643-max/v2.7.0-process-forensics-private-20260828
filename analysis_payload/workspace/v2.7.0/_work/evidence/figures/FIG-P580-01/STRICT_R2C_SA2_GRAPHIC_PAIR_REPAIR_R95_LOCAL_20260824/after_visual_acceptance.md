# FIG-P580-01 R2C SA2 final visual acceptance

Reviewer: SA2. Basis: schema revision 111, the final page/standalone rebuild, and only current R2C evidence. Status scope: `SA2_LOCAL_PASS_AWAIT_ROOT_OFFICIAL_BUILD`; this is not root acceptance or final PASS.

## Evidence actually opened

- All 15 current contact sheets were opened at original detail. Their 234 distinct cells each show the native 1:1 source ROI, the unique target overlay, and the pure mask, physically enlarged by exact 8x nearest-neighbour sampling. All 234 per-glyph decisions are recorded individually in `manual_glyph_contact_ledger.csv`; totals are 234 PASS, 0 missing-stroke pixels, 0 foreign pixels, and 0 pending/unknown.
- The G0198 low-profile full-stop reference and candidate source/mask/overlay were separately opened at native 1x and 8x nearest. The candidate mask contains only the intended punctuation and matches the revision-111 same-codepoint calibration.
- `full_page_200dpi.png`, `figure_crop_300dpi.png`, `standalone_300dpi.png`, `grayscale_300dpi.png`, and `after_text_measurement_overlay_300dpi.png` were opened after the final rebuild. The 50 view/panel/role/script judgments are recorded in `manual_visual_harmony_ledger.csv`.
- All 53 current critical relation packages had `overlay_1x.png` and `overlay_8x_nearest.png` opened individually. For the three repaired pairs, raw ROI, object A, object B, intersection, and overlay were additionally opened at both 1x and 8x. Machine terminal validation decodes all 530 package PNGs and cross-checks every native intersection mask against its bottom-table overlap count.

## Repaired-pair visual and pixel gates

- `PAIR_GR004_GR025`: overlap 0; clearance 6.280110 px; required 3.000000 px; package `critical_relations/PAIR_GR004_GR025`.
- `PAIR_GR020_GR022`: overlap 0; clearance 5.000000 px; required 3.000000 px; package `critical_relations/PAIR_GR020_GR022`.
- `PAIR_GR020_GR024`: overlap 0; clearance 9.770330 px; required 3.000000 px; package `critical_relations/PAIR_GR020_GR024`.

The three repaired intersection masks are empty. The circle and triangle remain accurately centred on the p curve; no marker was shifted or semantically shrunk. The q_R height remains 1/5. The left hatch still represents exactly x in `[5/2,5]`. No semantic exemption is used for any repaired pair.

## Font size, weight, colour, and congestion

PASS. Minimum effective visible size is 9.60 pt, above 9.5 pt. Panel titles, annotations, tick labels, two-line axis decoding, formula-card text, and caption form a natural hierarchy with the lecture-page body. Nothing appears abruptly enlarged, undersized, unusually heavy/light, or colour-alien. The right weight card remains readable with comfortable line spacing and frame clearance; the user-highlighted card/text crowding does not recur.

## Whole-figure regression

- The composite q_R dash remains visually coordinated with the left dashed proposal line: dense 3/2 rhythm dominates and the two longer gaps read as natural marker clearances rather than broken data.
- The -2 mm axis extension is modest on both panels. It clears the left hatch, does not collide with right ticks or arrows, and stays clear of page edge and caption.
- In grayscale, curve, dashed proposal, dotted support boundary, hatch, card frame, and circle/square/triangle remain distinguishable.
- The full page preserves balanced whitespace, caption separation, page margins, and surrounding-body integration. The standalone view retains the full mathematical story without prose dependence.

## Bottom-table closure

All 300 graphic-graphic rows are `ASSESSED=true` with 300 unique pair-specific reasons: 48 intentional structural connections comprise exactly 25 native overlaps plus 23 disjoint sub-3 px adjacencies; the other 252 are nonintentional and pass. The full table contains 57 objects, 1,596 unique unordered pairs, and 445 required relations, all PASS. The manual relation ledger has 53 independently identified package rows and no blanket `intentional=true` justification.

SA2 local judgment: `SA2_LOCAL_PASS_AWAIT_ROOT_OFFICIAL_BUILD`.
