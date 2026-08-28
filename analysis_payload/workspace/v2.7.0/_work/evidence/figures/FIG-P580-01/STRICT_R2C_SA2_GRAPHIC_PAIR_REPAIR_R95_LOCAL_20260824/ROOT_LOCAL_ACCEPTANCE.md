# ROOT local acceptance — FIG-P580-01 R2C

- Root review completed: `2026-08-24T11:33:05.6166020+08:00`
- Scope: sealed SA2 local candidate against revision-116 Goal/schema; this is **not** final figure closure and does not replace a fresh independent SA1 review on an official full-book build.
- Agent stop invariant: `WRITE_STOPPED.md` remained the agent's last write. This file is a later, explicitly identified root-only acceptance record and is intentionally outside the agent terminal manifest.

## Root-independent checks

- Evidence integrity: 1,353 terminal-manifest entries unique; 1,137 PNG files decoded; 22 CSV and 62 JSON files parsed; 344/344 safe/openability rows passed; 1,348/1,348 final-integrity rows passed; no ADS; only the 12 expected zero-byte LaTeX index placeholders.
- Text/font gates: 32/32 text elements have unique source locations and `EFFECTIVE_PT >= 9.5` (minimum 9.6 pt). All 234 glyph rows plus 18 necessary-substring rows passed; missing-stroke and foreign-pixel totals are zero.
- Pixel evidence: all 15 triple contact sheets were opened by root at 8x nearest-neighbour inspection scale. Target overlays and pure masks match the intended glyphs without capturing neighbouring glyphs or graphic objects. Native 300 dpi remains the measurement grid.
- Low-profile punctuation: G0198 (`.`) is 10 pt / STIXTwoText-Bold with native ink height 7 px and area 41 px; the independently rendered same-font/same-size reference is also 7 px / 41 px. Candidate/reference height and area ratios are both 1.000000; 1x and 8x raw, overlay and pure-mask evidence were opened.
- Pair/occlusion gates: all 1,596 unordered pairs have unique assessments; all 300 graphic–graphic pairs are covered; all 252 non-intentional graphic pairs pass. All 445 required relations and all 53 critical relation packages pass.
- Mandatory repaired pairs were opened at native 1x and 8x nearest-neighbour scale, including raw ROI, pair overlay, both object masks and intersection mask:
  - GR004–GR025: overlap 0 px; clearance 6.280110 px (required 3 px).
  - GR020–GR022: overlap 0 px; clearance 5.000000 px (required 3 px).
  - GR020–GR024: overlap 0 px; clearance 9.770330 px (required 3 px).
  - Each intersection mask is empty; both object masks are distinct and visually correspond to the intended objects.
- Visual views: full-page, crop, standalone, grayscale and post-text-measurement overlay were opened. The previous title/card/axis collisions are absent; the qR dashed line has deliberate visible gaps at the circle and triangle; panel typography is proportionate to the book body; the figure remains legible in grayscale and integrates naturally on the page.
- Mathematics/source scope: `p(x)=6x(5-x)/125`, `q_L=2/5` on `[0,5/2]`, `q_R=1/5`, and the displayed ratios `24/25`, `3/2`, `24/25` are consistent. The repair is confined to the figure source and preserves the teaching point.
- Local builds: page and standalone PDFs each have one A4 page, PDF 1.7 metadata for v2.7.0, no hard log-pattern match, and recorder provenance to the current figure source.

## Decision

`EVIDENCE_INTEGRITY=PASS`  
`SA2_LOCAL_CANDIDATE=ACCEPTED_FOR_OFFICIAL_R96_BUILD`  
`FINAL_FIGURE_STATUS=NOT_CLOSED`

The source is frozen for the R96 official full-book build. A fresh independent SA1 must audit the R96 physical page without reading this evidence package or any prior local conclusion.
