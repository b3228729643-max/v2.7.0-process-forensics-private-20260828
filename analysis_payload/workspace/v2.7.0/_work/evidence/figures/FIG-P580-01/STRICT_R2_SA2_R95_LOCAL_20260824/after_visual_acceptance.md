# FIG-P580-01 SA2 final visual acceptance

Schema basis: STRICT_FIGURE_EVIDENCE_SCHEMA revision 111. Reviewer: SA2. Review basis: final source and the final page/standalone rebuild represented by `render_manifest.json` and `core_audit_summary.json`.

## Files actually opened

- All 15 final `glyph_shape_contact_sheets/contact_sheet_01...15_triple_8x_nearest.png` files were opened at original detail. Every one of the 234 cells was examined in its ORIGINAL / TARGET OVERLAY / MASK ONLY triplet. The independent decisions are recorded one row per glyph in `manual_glyph_contact_ledger.csv`.
- The revision-111 low-profile punctuation reference source/mask at native 1:1 and 8x nearest, and candidate G0198 source/overlay/mask at native 1:1 and 8x nearest, were separately opened. The candidate mask contains only the automatic figure-number period and no pixels from the adjacent digit.
- `full_page_200dpi.png`, `figure_crop_300dpi.png`, `standalone_300dpi.png`, `grayscale_300dpi.png`, and `after_text_measurement_overlay_300dpi.png` were each opened after the final rebuild. The 50 view/role decisions are recorded in `manual_visual_harmony_ledger.csv`.
- The current audit has zero pixel-failure packages and zero failed/critical relation packages. Therefore there is no current failure/critical 1:1 or 8x package to open. Old packages left by superseded iterations are explicitly excluded in `NONAUTHORITATIVE_STALE_INTERMEDIATE_EVIDENCE.md`.

## Hard visual gates

- **Glyph completeness:** PASS. Each target overlay covers the intended glyph; each pure raw mask contains the intended glyph only. Manual totals are 234 PASS, 0 missing-stroke pixels, 0 foreign pixels, 0 pending/unknown.
- **Font size and harmony:** PASS. No visible text is too small, abruptly enlarged, unusually compressed, vertically scaled, or stylistically alien to the page. Minimum declared/effective visible size is 9.60 pt. The 9.6 pt ticks, labels, axis decoding, and formula card form a natural hierarchy below the 10.2 pt panel titles and alongside the 10 pt caption.
- **Native readability:** PASS. Inline `1/2`, `2/5`, `3/10`, `5/2`, `24/25`, and `3/2` are readable at native 300 dpi; no numerator or denominator is hidden in a smaller TeX fraction style.
- **Clearance:** PASS. The minimum assessed nonintentional pair clearance is 10.045361 px against 3 px required. The minimum text-to-text clearance is 14.033296 px against 4 px required. In particular the final two-row xlabel gaps are 15.155494 px on the left and 14.033296 px on the right.
- **Formula card:** PASS. Every one of the 44 card glyphs was checked against all four stroke-only border edges, the right y-axis, and all five right y-tick text objects. The minima are 22 px versus 5 px for border edges, 70 px versus 3 px for the y-axis, and 89 px versus 4 px for y-tick text. No card glyph crosses or crowds the frame.
- **Graphic preservation:** PASS. The single white formula-card fill is the only opaque label ground and covers zero pixels of every nonbackground graphic. There are no translucent label grounds. The border is modeled as stroke-only; the white interior is background rather than a data-erasing halo.
- **Colour and grayscale:** PASS. Blue solid target curves and teal dashed proposal lines remain distinguishable in colour; dash pattern, markers, curve geometry, and hatch remain distinguishable in grayscale.
- **Page integration:** PASS. At 200 dpi the figure scale, caption, whitespace, colour weight, and typographic density match the surrounding lecture page. No label appears disproportionately small or oversized.

## Standalone semantic gate

PASS. A reader using the figure alone can identify all required mappings without the alt text or surrounding prose:

- left dashed teal line is `q_L(x)` and takes value `2/5`;
- left dotted vertical line is the support boundary at x-coordinate `5/2`;
- left hatched region is explicitly decoded below the axis as `q_L(x)=0` while `p(x)>0`;
- solid blue line is `p(x)`;
- right dashed teal line is `q_R(x)=1/5` and the panel title states that it covers the target;
- the formula card uses `w(x)=p(x)/q_R(x)` and shows the values `24/25`, `3/2`, `24/25` at `1`, `5/2`, `4`.

The figure still teaches support insufficiency on the left and support coverage on the right; it has not been converted into an acceptance-rejection process.

## Manual conclusion

All manual glyph, font-harmony, grayscale, page-integration, clearance, card-boundary, and standalone-semantic gates are PASS for this final local candidate. This is an SA2 local judgment only and does not claim the root strict final decision.
