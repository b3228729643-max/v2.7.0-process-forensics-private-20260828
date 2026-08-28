# Font, mathematics, and semantic-contact audit

## Source and final-PDF typography

The source establishes the normal reader-facing base at 9.6 pt (`fig_v5_c02_is_support.tex:18,24,25,60,63,66`) and panel titles at 10.2 pt (`:26`). A targeted source scan found no `resizebox`, `scalebox`, `transform shape`, or other whole-figure text shrink. Final-PDF effective sizes in `text_element_audit.csv` are:

| Reader-facing role | Final effective pt | Ratio to tick base | Result |
|---|---:|---:|---|
| ticks / ordinary annotations / both axis titles | 9.5641 | 1.0000 | pass, >= 9.5 pt |
| caption | 9.9626 | 1.0417 | pass |
| formula-card base | 9.9626 | 1.0417 | pass |
| panel titles | 10.1619 | 1.0625 | pass |

The only smaller final glyphs are TeX-derived math descendants (6.6949, 7.1133, and 8.9664 pt) of reader-facing >=9.5 pt bases; they are not independently shrunken labels. `role_ratio_audit.csv` and `same_class_ratio_audit.csv` both pass every row. The left rotated title is correctly a single semantic `ylabel` object (source line 38), not two independent labels.

Page-628 embedded fonts, read from the current candidate, are subset-embedded and include `NotoSerifSC-ExtraLight`, `STIXTwoText-Regular`, `STIXTwoMath-Regular`, `STIXTwoText-Bold`, and `NotoSansSC-Bold`. CJK prose, STIX mathematical notation, and the bold figure number form a coordinated hierarchy: panel titles are only 6.25% above the tick base, normal labels remain at the base, and the formula card/caption are only 4.17% above it. Native page, crop, and grayscale inspection found no abrupt CJK/mathematics mismatch or a normal label visually overtaking the curves.

## Every-glyph coverage

`glyph_ledger.csv` has a non-whitespace denominator of **234 / 234** visible glyphs, with **0** pixel-gate failures and **0** manual-review failures. For every glyph it records its PDF/vector boundary, native pixel boundary, source-line role, final font, effective size, ink height, and these three review artifacts:

- `03_glyph_evidence/original_1x/Gxxxx.png`
- `03_glyph_evidence/target_overlay_1x/Gxxxx.png`
- `03_glyph_evidence/mask_only_1x/Gxxxx.png`

The matching native 1× tri-view sheets are `03_glyph_evidence/atlases/glyph_triview_1x_native_atlas_01.png` through `_07.png`; 8× nearest-neighbour sheets are `glyph_triview_8x_atlas_01.png` through `_07.png`. Each was visually inspected. There were no omitted strokes, mixed-in foreground, or cut glyphs.

| Script class | Glyphs | Native ink-height range (px) | Result |
|---|---:|---:|---|
| CJK full | 93 | 33–38 | pass |
| Latin lower / Greek | 30 | 20–31 | pass |
| Latin upper / digit | 60 | 26–31 | pass |
| TeX math script | 6 | 21–27 | pass |
| low-contour calibrated glyphs | 45 | control-calibrated | pass |

The low-contour denominator is independently calibrated in `low_contour_calibration.csv`: 9 groups cover `/`, `(`, `)`, `≪`, and `.` with the same code point, embedded font, final size, and weight from the current PDF. All 9/9 controls pass; punctuation is not incorrectly rejected merely for having a shallow contour.

## Mathematics and figure-text consistency

The current source's analytic contract is correct:

- `p(x)=6x(5-x)/125` on `[0,5]` integrates to 1.
- `q_L(x)=(2/5)1_[0,5/2](x)` integrates to 1 but is zero while `p(x)>0` on `(5/2,5)`, so `p` is not absolutely continuous with respect to `q_L`.
- `q_R(x)=1/5` on `[0,5]` integrates to 1 and covers the target support.
- With `w=p/q_R`, the card values are correct: `w(1)=24/25`, `w(5/2)=3/2`, and `w(4)=24/25`.

These facts agree with source lines 1–17, 37–40, 47–58, 69–99, and the caption at line 102. The caption correctly limits the conclusion to the support condition `p << q`; it does not infer low variance or estimator reliability. The left-to-right reading path is unambiguous: find the support gap on the left, then verify full support and recompute the ratio on the right.

## Complete named semantic-contact whitelist

All 24 actual foreground contacts are named in `pair_universe.csv` and are source-semantic. They are excluded from the illegal-overlap count only for the stated reason below; no other contact is white-listed.

| ID | Pair | Source-semantic reason |
|---|---|---|
| WC01 | `P0902 G002/G005` | target curve crosses the support boundary at `x=5/2` (42,47,57) |
| WC02 | `P0905 G002/G008` | hatch is bounded by target curve (45–47) |
| WC03 | `P0886 G001/G002` | target curve has named axis endpoints (47) |
| WC04 | `P0915 G003/G006` | filled `q_L` endpoint marks its upper support value (49–54) |
| WC05 | `P0888 G001/G004` | displayed `q_L=0` lies on the x-axis (51–52) |
| WC06 | `P0927 G004/G007` | open `q_L=0` endpoint at the support boundary (51–56) |
| WC07 | `P0925 G004/G005` | zero baseline meets the boundary (51–58) |
| WC08 | `P0936 G005/G006` | boundary passes through the filled endpoint (53–58) |
| WC09 | `P0937 G005/G007` | boundary starts at the open endpoint (55–58) |
| WC10 | `P0892 G001/G008` | hatch is closed by the x-axis (45–46) |
| WC11 | `P0970 G009/G010` | right target curve has named axis endpoints (73) |
| WC12 | `P0976 G010/G011` | analytic `p=q_R` crossings (73,75–82) |
| WC13 | `P0978 G010/G013` | circle is placed on `p(1)` (83–84) |
| WC14 | `P0979 G010/G014` | square is placed on `p(5/2)` (85–86) |
| WC15 | `P0980 G010/G015` | triangle is placed on `p(4)` (87–88) |
| WC16 | `P0887 G001/G003` | `q_L=2/5` starts on the y-axis (49–50) |
| WC17 | `P0889 G001/G005` | dotted boundary begins on the x-axis (57–58) |
| WC18 | `P0891 G001/G007` | open endpoint is deliberately on the x-axis (55–56) |
| WC19 | `P0901 G002/G004` | `p(5)=0` meets the displayed zero baseline (47,51–52) |
| WC20 | `P0914 G003/G005` | top support segment meets boundary at `x=5/2` (49–50,57–58) |
| WC21 | `P0928 G004/G008` | zero baseline is hatch lower boundary (45–46,51–52) |
| WC22 | `P0938 G005/G008` | boundary is hatch left edge (45–46,57–58) |
| WC23 | `P0955 G007/G008` | open endpoint marks hatch/baseline start (45–46,55–56) |
| WC24 | `P0971 G009/G011` | `q_R=1/5` begins on right y-axis (75–82) |

The right dashed-line phase is deliberately controlled in source lines 75–82. Native 1×/8× inspection confirms a gap at the circle and triangle markers: those marker/dash envelope intersections are not physical ink contacts, hence remain unwhitelisted and pass manual review.
