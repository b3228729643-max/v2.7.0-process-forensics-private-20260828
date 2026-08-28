# Low-profile punctuation calibration audit

Twenty low-profile targets were calibrated only against independent official-PDF
instances matching codepoint, font, observed size, and RGB; the target page
(801) was excluded. Calibration used native 300 dpi H_INK and ink-area ratios,
with allowed interval [0.92, 1.08]. All reference contact sheets were opened.

| Result | Target count |
| --- | ---: |
| PASS | 19 |
| FAIL | 1 |

The sole failure is GLY0215 (U+FF1A, NotoSerifSC-ExtraLight, observed
9.5641 pt, RGB [77,83,88]), glyph-contact-sheet 11 cell 13. I opened its
original, target overlay, mask-only, and nearest-neighbor 8x cards plus both
same-codepoint references CAL02_01 and CAL02_02. It has a clean two-dot mask
and no foreign/neighbor pixels. Nevertheless the integer measurements are
target H_INK/area = 10/34; both references = 10/37; median = 10/37.
Thus H ratio = 1.0000 and area ratio = 0.918918..., not 0.92. Because
0.918918... < 0.92, this is a hard failure without rounding or visual-offset
exception.

Calibration table: 'calibration/official_pdf_same_codepoint/low_profile_punctuation_calibration.csv'.

LOW_PROFILE_CALIBRATION_GATE: FAIL_TO_SA2
