# FIG-P756-01 independent blind SA3 terminal report

## Identity and denominator

- Official candidate: main_full.pdf, SHA-256
  062AD81020CB19A5C6688A45C73E00965F5060E0960A69AF820D7DC154DEE814,
  813 pages; independently located Figure 37.8 at physical page 801 / printed
  page 788.
- Source: full_course_synthesis_map.tex, SHA-256
  00213AE30379E4337830B1C4957BE4CB7B1E99BE88144E2D7D262998E1B6CAAA.
- Objects: 113 = 55 text + 58 graphics; pairs: C(113,2) = 6,328
  (TT 1,485, TG 3,190, GG 1,653).
- Rawdict characters: 380 = 378 visible glyphs + 2 U+0020 nonvisible spaces.
- In-scope PDF drawing paths: 39 mapped / 39; math-rule objects: 0 / 0.
- Critical manual cards: 129. All opened native 1x, mask-A, mask-B, overlay,
  and nearest-neighbor 8x.

## Hard-gate results

| Gate | Result |
| --- | --- |
| candidate/source identity | PASS |
| native 300 dpi render and crop | PASS |
| rawdict two-way glyph reconciliation | PASS; 7 duplicate boundary pixels resolved, 0 remain |
| glyph visual mask completeness/purity | PASS |
| foreground object/path completeness | PASS |
| full unordered pair denominator | PASS |
| illegal foreground overlap | PASS; 0 |
| ordinary clearance failure | PASS; 0 |
| clipping | PASS; 0 |
| declared/effective font-size floor | PASS; minimum 9.6 pt |
| manual font visual harmony | PASS; true |
| semantic/caption/body consistency | PASS |
| color/grayscale readability | PASS |
| low-profile same-codepoint calibration | FAIL; GLY0215 |

## Blocking failure

GLY0215 is a U+FF1A colon at glyph-contact-sheet 11, cell 13. It is visibly
complete and clean, but the mandated same-codepoint/font/size/RGB calibration
uses two independent official-PDF references with H_INK/area 10/37 and target
H_INK/area 10/34. Exact area ratio is 34/37 = 0.918918..., below 0.92.
No rounding, ancestor-line substitute, or visual exception is permitted.

## Terminal

TERMINAL_STATUS: FAIL_TO_SA2

This independent evidence set is complete enough to identify a concrete
corrective target; the failure is substantive, not an evidence-coverage
failure. It is not a final project close.
