# FIG-P639-01 R104 SA1 formula, geometry, relation, content, and context review

- HANDOFF_ID: `C-FIG-P639-01-R104-SA1-FRESH-ISOLATED-V1`
- reviewer_type: `AI_SA1_VISUAL_REVIEW`
- human_certification: `false`
- official PDF mapping: physical page `689`, printed page `676`, figure `33.6`
- source label: `fig:V5-C04-bivariate-normal-conditionals`
- source: `fig_v5_c04_bivariate_normal_conditionals.tex`
- necessary context: `V5-C04.tex` lines 365--409

## Formula semantics

For the current-context model

\[
(X_1,X_2)^\mathsf T\sim N\!\left(0,\begin{pmatrix}1&\rho\\\rho&1\end{pmatrix}\right),\qquad |\rho|<1,
\]

the full conditionals are

\[
X_1\mid X_2=b\sim N(\rho b,1-\rho^2),\qquad
X_2\mid X_1=a\sim N(\rho a,1-\rho^2).
\]

With `rho=0.6`, `a=1`, and `b=0.75`, the means are `0.6*0.75=0.45` and `0.6*1=0.60`, while the common variance is `1-0.6^2=0.64`. Thus T01--T04, T16, the caption, and the two vertical reference lines all express the correct quantities.

For variance `0.64`, the normal-density coefficient is

\[
1/\sqrt{2\pi\cdot0.64}=0.498677851\ldots,
\]

and the exponent coefficient is `1/(2*0.64)=0.78125`. Source lines 19--22 use `0.498678` and `0.78125`, so both plotted curves are direct, correctly rounded evaluations of their labeled distributions.

## Geometry and relationships

- PDF-vector x coordinates map the blue and gold reference lines to data coordinates `0.450061` and `0.599976`, respectively; these agree with the labeled means to rendering precision.
- Each reference line reaches the maximum of its same-color curve. The two equal-variance curves have the same peak height and the expected horizontal displacement of `0.15`.
- The solid blue curve plus pale fill and the dashed gold curve provide redundant non-color encoding. The mean lines use dashed blue and dash-dot gold; grayscale preserves the curve and marker distinctions.
- The single curve-curve crossing and the four mean-reference/curve contacts are lawful data geometry, not collisions. Axis/tick/arrowhead contacts and the filled-region baseline closure are likewise structural. All 28 shared graphic-graphic pairs are individually adjudicated in `manual_critical_pair_review.csv` and `after_overlap_adjudication.md`.
- No text object shares native foreground pixels with any other text or graphic object. The minimum reviewed text clearance is `12 px` (T16/T17), above the applicable hard floor.
- Every one of the 32 objects is fully inside the final full-page/figure boundary. The plot-only standalone-equivalent crop has a minimum reader-element edge clearance of `9 px` at T14, and the caption is intentionally outside that plot-only crop while fully contained in the figure crop. No actual foreground is clipped.

## Object content and current-text consistency

- T01/T02 and G07/G10 form the `X_1|X_2=b` conditional with mean `0.45`; T03/T04 and G09/G11 form the `X_2|X_1=a` conditional with mean `0.60`.
- T16 states the shared variance `0.64`; T17 states the correct causal reading of the parameterized conditional mean.
- The caption explicitly introduces the local parameter choice `rho=.6, a=1, b=.75`, so it is self-contained. The nearby proposition and proof give the same generic full-conditionals and variance. The immediately preceding line calls the figure two normal full-conditional slices, which is exactly what is drawn.
- Earlier chapter material uses a separate demonstrative choice `b=4/5`; this figure explicitly supplies a new local `b=.75`, so there is no mathematical contradiction or silent reuse.
- Caption label `图33.6`, PDF text, source caption, source label, and current contextual reference agree.

## R168 font/glyph application

- Source metadata: plot labels/note/axis labels declare `9.2 pt`, ticks declare `8.5 pt`; PDF native spans are approximately `9.1656 pt`, `8.9664 pt`, and caption spans approximately `9.9626 pt`.
- These metadata values are not used as a hard failure under the dispatched R168 rule. The hard review instead covered every actual text object and all `147` visible PDF glyph IDs at native 300 dpi plus 8x nearest-neighbor inspection.
- No glyph is missing, tofu, replacement `U+FFFD`, wrong codepoint, or mathematically wrong. The PDF fonts on page 689 are embedded and have ToUnicode maps.
- Numerals render at 25--28 px ink height, mathematical italic `t` at 26 px, ordinary Chinese glyphs at 33--38 px, and legal subscripts at 19 px. Thin punctuation, the minus stroke, and Chinese `一` have small intrinsic ink heights but full correct glyph shapes and are not unreadable.
- Same-role figure objects are visually consistent: distribution labels `1.0000`, mean labels `1.0000`, annotations `1.0000`, x ticks at most `1.0400`, y ticks `1.0000`. Caption line-bbox ratio `1.1053` compares mixed Chinese/math with pure Chinese at the same PDF text size; it is recorded as advisory, not a severe imbalance.
- No actual unreadability or obvious severe font imbalance is present. Therefore the R168 hard font/glyph gate is clear.

## Manual gate outcome

`MATH_SEMANTICS`, `GEOMETRY`, `RELATIONSHIPS`, `OBJECT_CONTENT`, `CURRENT_TEXT_CONSISTENCY`, `FONT_GLYPH_R168`, `ACTUAL_READABILITY`, `TRUE_CLIP`, `ILLEGAL_OVERLAP`, `GRAYSCALE`, and `PAGE_INTEGRATION` have no hard blocker in this SA1 review.
