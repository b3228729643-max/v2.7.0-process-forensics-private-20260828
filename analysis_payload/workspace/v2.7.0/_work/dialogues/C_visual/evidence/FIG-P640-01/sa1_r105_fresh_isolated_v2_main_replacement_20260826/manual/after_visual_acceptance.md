# FIG-P640-01 — R105 fresh isolated SA1 manual acceptance

- `HANDOFF_ID`: `MAIN-R105-P640-SA1-FRESH-ISOLATED-REPLACEMENT-20260826`
- `REVIEWER`: `R105-SA1-FRESH-ISOLATED-V2-MAIN-REPLACEMENT`
- `MANUAL_RECORD_UTC`: `2026-08-25T22:45:27.1834804Z`
- `RESULT`: `FAIL_TO_SA2`
- This file was written manually only after every item listed below had actually been opened. No machine script generated or overwrote these judgments.

## Candidate and views actually opened

| item | actual opened artifact | manual judgment |
|---|---|---|
| official page | `renders/full_page_200dpi.png` | Page 690 is the intended printed page 677. Figure placement, caption wrapping, surrounding paragraph and page balance are coherent. `PAGE_FUSION_PASS=true`. |
| color figure + caption | `renders/figure_crop_300dpi.png` | All plot text, curves, axes, legend and caption are readable. The right-panel curve visibly fuses with the first `N` in the lower limit-annotation line; geometry fails. |
| standalone | `renders/standalone_300dpi.png` | Panel balance and reading order are natural. No missing/tofu/wrong glyph was seen. Same curve/text fusion remains visible. |
| grayscale | `renders/grayscale_300dpi.png` | Curves remain distinguishable by solid/dash patterns and both panels remain readable. `GRAYSCALE_PASS=true`. The geometry defect is still visible. |
| marker/tick native | `roi/marker_tick_native1x.png` | Open marker and dedicated `.99` vertical tick do not share a foreground pixel. |
| marker/tick 8× | `roi/marker_tick_8x_nearest.png` | Red marker and blue tick masks have zero intersection. The continuous vector outlines retain a positive gap, even though it is narrower than one complete 300-dpi pixel row. |
| critical native | `roi/right_curve_vs_limit_N_native1x.png` | The gold ESS curve enters the first `N` glyph region of `N_eff/N→0`. |
| critical 8× | `roi/right_curve_vs_limit_N_8x_nearest.png` | The curve and the left-lower stroke/serif of the first `N` visibly fuse. Same-color paint prevents a trustworthy machine-only pure-glyph separation; visual contact is unambiguous and is conservatively `>=1` native pixel. |

## Complete glyph contact-sheet review

Every sheet and every cell was opened at native source resolution with the included native `ORIGINAL / TARGET OVERLAY / MASK ONLY` triplet and 8× nearest view. The sheet ranges below cover `GLYPH-0000` through `GLYPH-0241` exactly once.

| sheet | cells | IDs | original/codepoint match | missing/tofu/wrong glyph | manual note |
|---|---:|---|---|---|---|
| `contacts/glyph_contact_001.png` | 16 | 0000–0015 | yes | none | tick-label contours readable |
| `contacts/glyph_contact_002.png` | 16 | 0016–0031 | yes | none | left labels/formula readable |
| `contacts/glyph_contact_003.png` | 16 | 0032–0047 | yes | none | rotated formula components readable |
| `contacts/glyph_contact_004.png` | 16 | 0048–0063 | yes | none | title and legend readable |
| `contacts/glyph_contact_005.png` | 16 | 0064–0079 | yes | none | legend symbols and punctuation present |
| `contacts/glyph_contact_006.png` | 16 | 0080–0095 | yes | none | right tick labels and point annotation start present |
| `contacts/glyph_contact_007.png` | 16 | 0096–0111 | yes | none | `GLYPH-0109` visibly contaminated/fused by the ESS curve; hard geometry failure |
| `contacts/glyph_contact_008.png` | 16 | 0112–0127 | yes | none | remaining limit and axis labels readable |
| `contacts/glyph_contact_009.png` | 16 | 0128–0143 | yes | none | right title/fraction glyphs readable; fraction rule separately inventoried |
| `contacts/glyph_contact_010.png` | 16 | 0144–0159 | yes | none | caption start readable |
| `contacts/glyph_contact_011.png` | 16 | 0160–0175 | yes | none | caption glyphs readable |
| `contacts/glyph_contact_012.png` | 16 | 0176–0191 | yes | none | caption glyphs readable |
| `contacts/glyph_contact_013.png` | 16 | 0192–0207 | yes | none | caption glyphs readable |
| `contacts/glyph_contact_014.png` | 16 | 0208–0223 | yes | none | caption glyphs readable |
| `contacts/glyph_contact_015.png` | 16 | 0224–0239 | yes | none | caption glyphs readable |
| `contacts/glyph_contact_016.png` | 2 | 0240–0241 | yes | none | caption end readable |

The automatic padded candidate masks sometimes retain neighboring antialias context at a bbox edge. I do not promote those masks to a strict font-pixel PASS. Under R168, microscopic font-height/ratio details are advisory unless they cause missing/tofu/wrong codepoint, unreadability or gross visible imbalance; none of those true font defects was seen. The same-color curve/`N` fusion is different: it is a plainly visible illegal overlap and remains a hard failure.

## Manual hard-gate matrix

| gate | decision | basis |
|---|---|---|
| candidate identity | PASS | 817 pages, 4,967,209 bytes, SHA-256 `F86E89047BA09FEA72FD8F79BF524A04DA367BFF3057806A879106A1032626A1` |
| complete foreground denominator | PASS | 242 glyphs + 11 semantic foreground path groups = 253; two real white occluders are separately recorded and excluded from foreground denominator |
| all unordered pairs | PASS as coverage, FAIL as content | 31,878 expected and 31,878 present; 26,506 machine PASS, 5,371 design-whitelisted, 1 hard FAIL |
| `.99` marker—vertical tick | PASS | intersection `0`; positive continuous vector whitespace `0.2137756 pt = 0.8907317 native px`; no full intervening native pixel row, but also no contact |
| illegal overlap | FAIL | `GLYPH-0109` (first `N` in `N_eff/N→0`) visibly fuses with `PATH-RIGHT-ESS-CURVE`; candidate intersection report 103 px, manual hard lower bound `>=1 px` |
| crop | PASS | clip count 0; crop-edge minima L/T/R/B = 67/58/42/34 px |
| mathematical semantics | PASS | left panel shows `rho^(2k)` decay; right curve and `.99` point agree with `(1-rho^2)/(1+rho^2)` and the `|rho|→1^-` limit |
| caption/text consistency | PASS | title, axes, legend, point label and caption agree with the source and adjacent page explanation |
| grayscale | PASS | all three left curves remain distinguishable and right panel remains readable |
| page fusion | PASS | figure scale, caption, whitespace and surrounding text fit the page naturally |
| font visual harmony (R168) | PASS/advisory | no unreadable or grossly imbalanced font; small pixel/ratio variation is not treated as a hard defect |

## Final manual decision

`FAIL_TO_SA2`.

The failure is not the `.99` marker/tick relationship. It is the real curve/annotation collision in the right panel. SA2 should reposition the two-line limit annotation or introduce a genuine source-defined opaque background with auditable paint order, then rebuild and obtain a wholly new fresh SA1 package.
