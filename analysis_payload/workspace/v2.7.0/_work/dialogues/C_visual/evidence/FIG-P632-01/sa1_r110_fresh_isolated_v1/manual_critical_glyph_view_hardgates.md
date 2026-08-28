# FIG-P632-01 manual critical, glyph, view, and hard-gate ledger

Reviewer identity: SA1, gpt-5.6-sol/xhigh. R168 is applied: minute raster antialiasing, font-outline, or taxonomy differences are advisory. Only missing/tofu/wrong-codepoint glyphs, mathematical or probability error, actual unreadability/obvious imbalance, clipping, illegal overlap, or substantive geometry error can hard-fail.

## Critical ROI decisions

- R01_joint_point_and_slices — Native 1x shows the filled point at the horizontal/vertical slice intersection; 8x shows exact intentional convergence of both slice strokes and the leader at the marker. The (a,b) glyph ink, nearby middle contour dashes, and outer contour dots remain separate. PASS.
- R02_horizontal_arrowhead — Native 1x shows the green map arrowhead left of the upper y-axis; 8x shows a large white gap, intact arrowhead polygon, and no arrowhead/text or arrowhead/axis collision. PASS.
- R03_vertical_arrowhead — Native 1x shows the blue routed arrowhead left of the lower y-axis; 8x confirms a large white gap and intact endpoints. PASS.
- R04_upper_peak_curve_guide — Native 1x shows a centered dashed guide; 8x shows the guide touching the solid curve only at the mathematical peak and touching the x-axis at its base. No accidental thickening or unreadable merge. PASS.
- R05_lower_peak_curve_guide — Native 1x shows a centered dotted guide; 8x shows the same two intended contacts with the dashed curve and x-axis, with dash/dot identities preserved. PASS.
- R06_note_border_text — Native 1x and 8x show the red rounded border, pale fill, and first two CJK lines with clean antialiasing and interior padding; no border/text overlap or clipping. PASS.
- R07_caption_number_glyphs — Native 1x and 8x show complete bold 图, digits 33.2 and the first caption-body glyph; counters/strokes are intact, without tofu or clipping. PASS.
- R08_upper_formula_fraction_radical — Native 1x and 8x show the peak formula’s numerator 5, fraction bars, 4, radical sign, 2 and pi; every codepoint has its expected outline and spacing. PASS.
- R09_upper_mean_vs_lower_formula — Native 1x and 8x show the green 12/25 mean fraction above-left of the black lower conditional identity. The closest ink regions have substantial whitespace; no fraction/formula overlap or misreading. PASS.

Critical ROI coverage: 9/9 at both 1x and 8x. Genuine hard FAIL: none.

## Glyph/codepoint integrity decisions

- G01 U+56FE 图 — Caption-number CJK glyph has a complete enclosure and internal strokes; not tofu. PASS.
- G02 U+8054 联 — Joint-conclusion CJK glyph is complete at 300 dpi and remains legible in grayscale. PASS.
- G03 U+0030 0 — Digit in “分母为0” and decimals is oval/zero-shaped, not substituted with letter O. PASS.
- G04 U+03C1 rho — The rho glyph is distinct from p in parameter, contour and formulas; correct codepoint/shape. PASS.
- G05 U+03C0 pi — Density symbol pi and denominator pi glyphs are complete, including subscripts when present. PASS.
- G06 U+03D5 phi — Standard-normal density phi in both marginal values has the expected loop/stem and is not empty-set/tofu. PASS.
- G07 U+1D4A9 mathematical calligraphic N — Both conditional normal-law symbols have a complete calligraphic outline. PASS.
- G08 U+222B integral — Both integral signs are tall, continuous and paired with the intended real-line lower limit. PASS.
- G09 U+211D blackboard-bold R — Both real-line limit glyphs have recognizable double-struck structure and are not substituted. PASS.
- G10 U+221A radical — Square-root signs in semiaxes and peak denominators cover the radicands and are not clipped. PASS.
- G11 fraction bars — Horizontal fraction rules for 3/5, 4/5, 12/25, 16/25 and peak formulas are continuous and correctly associated. PASS.
- G12 U+2223 conditioning bar — Conditional bars in pi1/pi2 and X1/X2 expressions are vertical and semantically distinct from numeral 1. PASS.
- G13 U+2248 approximately equal — Both numeric marginal approximations use an intact ≈, matching 0.29 and 0.242. PASS.
- G14 U+003E greater-than — Both positivity tests end in >0 with open, correctly directed inequality signs. PASS.
- G15 U+2212 minus — Exponential and quadratic minus signs use a true mathematical minus with correct direction/length. PASS.
- G16 superscript 2 — x1^2, x2^2 and sqrt-related math scripts are present, aligned and readable; none is dropped. PASS.
- G17 subscript 1 — x1, pi1 and m1 subscripts are positioned consistently and remain distinguishable at native 300 dpi. PASS.
- G18 subscript 2 — x2, pi2 and m2 subscripts are positioned consistently and remain distinguishable at native 300 dpi. PASS.
- G19 lowercase t — Both x-axis t labels and formula t variables retain complete ascender/crossbar shapes; the 25 px labels are readable. PASS.
- G20 lowercase m — Marginal symbols m1/m2 are italic, complete and not confused with n. PASS.
- G21 U+002C comma — Commas in (a,b), parameter lines and distribution parameters are visible at the baseline and not clipped. PASS.
- G22 U+FF1A fullwidth colon — Chinese annotation/note colons are present and aligned with CJK text. PASS.
- G23 parentheses — Parentheses around coordinates, function arguments and distribution parameters are paired and unbroken. PASS.
- G24 vector arrowheads — Although vector shapes rather than font glyphs, all four axis arrowheads and two mapping arrowheads are complete, correctly directed, and uncut. PASS.

Glyph/control coverage: 24/24. Missing glyph/tofu/wrong codepoint count: 0.

## View decisions

- V01 page_682_native_300dpi.png — Physical page 682/printed 669 is complete: header, Figure 33.2, caption, following prose/example, footer and margins are visible. Figure is centered and proportionate; no page-edge clipping or collision. PASS.
- V02 figure_crop_native_300dpi.png — The full figure from model formulas through the complete note border is present at native scale; all panels and routing arrows are readable without resampling. PASS.
- V03 caption_crop_native_300dpi.png — Caption number and both caption lines are complete; wrap and baseline alignment are natural, with no note-border intrusion. PASS.
- V04 figure_and_caption_native_300dpi.png — Figure/caption integration is coherent: note remains part of the figure, caption follows with visible separation, and the caption accurately describes the displayed conditionals. PASS.
- V05 figure_grayscale_native_300dpi.png — Solid/dashed/dotted encodings retain hierarchy without relying on color; outer contour is pale but still visible, both density curves remain distinct, and the note remains readable. PASS.
- V06 semantic_object_overlay_300dpi.png — All 23 frozen objects are covered exactly once; large bbox intersections are traceable to nested geometry or grouping and were individually resolved in the pair ledger. PASS.
- V07 text_measurement_overlay_300dpi.png — All 29 reader-visible text elements have labeled measurement regions; no visible figure/caption text is omitted from the denominator. PASS.
- V08 critical_rois_1x_contact.png — Native-pixel contacts, gaps, caption glyphs and formula glyphs are visible without interpolation; all nine source ROIs are indexed. PASS.
- V09 critical_rois_8x_contact.png — Nearest-neighbour enlargement exposes original pixel edges; no hidden collision, clipped stroke or tofu is revealed. PASS.

View coverage: 9/9. Hard-failing view count: 0.

## Mathematical, probability, numerical, and geometry checks

- M01 Joint normalization — With rho=3/5, sqrt(1-rho^2)=4/5, so the bivariate-normal constant is 1/(2*pi*4/5)=5/(8*pi), matching O01. PASS.
- M02 Quadratic exponent — 1/[2(1-rho^2)]=25/32 and 2*rho=6/5, so q=x1^2-(6/5)x1*x2+x2^2 and exponent -25q/32 are correct. PASS.
- M03 First conditional — E[X1|X2=4/5]=(3/5)(4/5)=12/25 and Var=1-(3/5)^2=16/25, matching O11/O13/O14. PASS.
- M04 Second conditional — E[X2|X1=1]=3/5 and Var=16/25, matching O16/O18/O19. PASS.
- M05 Marginal values — phi(4/5)=0.2896915528 rounds to displayed 0.29; phi(1)=0.2419707245 rounds to displayed 0.242. Both are strictly positive. PASS.
- M06 Conditional peak — 1/[sqrt(2*pi)*sqrt(16/25)]=5/[4*sqrt(2*pi)]=0.4986778505, matching both panels. PASS.
- M07 Integral semantics — Both displayed conditionals are normalized normal densities and the integrals over R equal 1. PASS.
- M08 Contour geometry — Positive rho gives covariance eigenvectors along +45 and -45 degrees with eigenvalues 1+rho and 1-rho; displayed semiaxes c*sqrt(1±rho) and +45 major direction are correct. PASS.
- M09 Slice mapping — Horizontal x2=b maps to pi1(t|b)=pi(t,b)/m2(b); vertical x1=a maps to pi2(t|a)=pi(a,t)/m1(a). Arrow routing preserves this correspondence and does not cross. PASS.
- M10 Zero-marginal qualification — The note correctly requires a preselected measurable regular-conditional version at zero marginal density and states marginal-a.e. uniqueness; the Gaussian example’s two denominators are positive. PASS.
- M11 Caption consistency — Caption’s variance 16/25, normalization over the real line, and zero-marginal qualification agree with formulas and chapter context. PASS.

## Hard-gate decisions

- HG01 IDENTITY — PDF SHA-256 B49C5CA920DDEF6C0CD004B2581EAF710F4D1E1115BB459A324A84594B3831F3, 4,967,063 bytes, 817 pages; source SHA-256 1670F496E6CEBBF5636AC5BC97474A50FBA83811FFA2AAAAEF0CF8227BE8C8EB, 9,022 bytes. Physical 682/printed 669/Figure 33.2/caption/label all match. PASS.
- HG02 SOURCE_FONT_PASS — Every figure node inherits declared 9.6 TeX pt from source line 66; graphics scale is 1.0, coordinate-only y=3.1cm scopes do not scale text, and no resizebox/scalebox/transform shape exists. PDF base spans are 9.5641 bp; natural math scripts are 6.6949 bp. PASS=true.
- HG03 PIXEL_HEIGHT_PASS — All CJK/full-height elements meet ≥30 px; base math elements meet ≥22 px (smallest audited base label t is 25 px); natural scripts were inspected at 8x and meet the ≥15 px semantic-script criterion. PASS=true.
- HG04 SAME_CLASS_RATIO_PASS — Matched top/bottom roles share identical 9.6 pt source and 9.5641 bp PDF base sizes; t labels are 25/25 px (ratio 1.000), and 水平截面/竖直截面 are 36/37 px (max/min 1.028). Fraction/line-envelope differences arise from intrinsic glyph composition and are advisory under R168, not scaling. PASS=true.
- HG05 ROLE_RATIO_PASS — Ordinary labels/formulas use one 9.6 pt base; the caption uses its separate document caption role. No ordinary label is enlarged/shrunk to dominate; top/bottom counterparts match. PASS=true.
- HG06 OVERLAP_DENOMINATOR — 23 objects and all 253 unordered pairs are frozen and manually adjudicated. PASS.
- HG07 OVERLAP_CANDIDATE_PIXEL_COUNT — Direct native-pixel semantic inspection finds 0 candidate illegal shared pixels. Separately, coarse bbox screening flags 46 candidate pairs; every one was manually resolved, and bbox intersection alone is not a pixel collision. Recorded values: OVERLAP_CANDIDATE_PIXEL_COUNT=0; BBOX_CANDIDATE_PAIR_COUNT=46. PASS.
- HG08 MASK_CONTAMINATION_PIXEL_COUNT — No pixel-mask algorithm was used to invent collision pixels; bbox-only candidates are geometry-screening candidates and were resolved manually. Pixel contamination count=0. PASS.
- HG09 OVERLAP_PIXEL_COUNT — No unintended independent semantic foregrounds share effective pixels. Intended axis/contour, slice/contour, slice/marker, curve/guide and guide/axis contacts are explicitly classified and do not obscure information. Canonical illegal overlap pixels=0. PASS.
- HG10 PIXEL_ADJUDICATION_STATUS — All candidates are resolved; status=CLEAR. No dispute or arbitration trigger. PASS.
- HG11 CLIP_PIXEL_COUNT — Page, figure, caption, arrows, markers, formulas, note border and all glyphs are intact at native 300 dpi. Canonical clipped foreground pixels=0. PASS.
- HG12 MIN_TEXT_CLEARANCE — Closest reviewed text-to-graphic clearance is the (a,b) label to its leader, about 2.21 PDF pt ≈9.2 px; node-note text to border bottom is about 11 px; note border to caption bbox is about 12.6 px. Applicable minima (3/5/8 px) are met. PASS.
- HG13 MATH_SEMANTICS_PASS — M01–M11 show correct bivariate-normal normalization, conditionals, contours and integral statements. PASS=true.
- HG14 PROBABILITY_SEMANTICS_PASS — Conditioning directions, marginal denominators, positivity, normalization and a.e. regular-condition qualification are correct. PASS=true.
- HG15 NUMERICAL_VALUES_PASS — 12/25, 3/5, 16/25, 0.29, 0.242 and peak 5/(4sqrt(2pi)) independently recompute correctly. PASS=true.
- HG16 TEXT_CONSISTENCY_PASS — Figure text, caption and necessary chapter context use the same a=1, b=4/5, rho=3/5, m1/m2 meanings and reading order. PASS=true.
- HG17 GRAYSCALE_PASS — Line type, weight and placement preserve all relationships without color. PASS=true.
- HG18 PAGE_INTEGRATION_PASS — Figure/caption placement on printed page 669 is balanced, no float/caption collision exists, and following text begins with adequate separation. PASS=true.
- HG19 VISUAL_HARMONY_PASS — Joint panel and two conditional panels have a clear left-to-right/top-to-bottom hierarchy; mapping arrows do not cross; formulas do not overpower curves; note is subordinate but readable. PASS=true.
- HG20 R168_ADVISORY_CHECK — Raster antialiasing and intrinsic glyph-outline differences observed at 8x do not change codepoints, meaning, readability, balance, clipping, overlap or geometry. No advisory observation escalates to hard FAIL. PASS.
- HG21 ISOLATION/WRITE_SCOPE — Reads were limited to the official R110 PDF, current P632 source, active Goal strict protocol section, and necessary V5-C04 context; all writes are inside the isolated evidence root; no TeX/source/Git/central write occurred. PASS.
- HG22 EVIDENCE_COMPLETENESS — Full page, figure/caption crops, grayscale, semantic/text overlays, 1x/8x ROIs, machine denominators, per-object/per-pair/per-text/per-glyph/per-view ledgers and this hard-gate ledger are present before sealing. PASS.

Hard-gate result: 22/22 PASS. `SOURCE_FONT_PASS=true`; `PIXEL_HEIGHT_PASS=true`; `SAME_CLASS_RATIO_PASS=true`; `ROLE_RATIO_PASS=true`; `OVERLAP_CANDIDATE_PIXEL_COUNT=0`; `BBOX_CANDIDATE_PAIR_COUNT=46`; `MASK_CONTAMINATION_PIXEL_COUNT=0`; `OVERLAP_PIXEL_COUNT=0`; `PIXEL_ADJUDICATION_STATUS=CLEAR`; `CLIP_PIXEL_COUNT=0`; `MIN_TEXT_CLEARANCE_PX=9`; `VISUAL_HARMONY_PASS=true`; `MATH_SEMANTICS_PASS=true`; `TEXT_CONSISTENCY_PASS=true`; `GRAYSCALE_PASS=true`; `PAGE_INTEGRATION_PASS=true`.
