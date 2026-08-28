# Manual post-observation mathematics, text, and page review

- Reviewer identity: `A-R114-P092-SA2-R168-READONLY-20260828` / `/root/p092_r114_r168_sa2`.
- Current candidate observed: official R114 PDF, physical page 96 (printed page 83), plus the frozen current figure source and only the necessary V1-C06 text surrounding its inclusion.
- Views actually opened: full page at direct 200 dpi; full page at direct native 300 dpi; direct native 300 dpi figure crop; native-resolution grayscale crop; 21-object overlay; peak, left-endpoint, and right-endpoint critical ROIs at native1x and nearest-neighbor 8x.

## Mathematics and geometry

The plotted source expression is

`-(p ln p + (1-p) ln(1-p)) / ln 2`.

Independent numerical and analytic checks show:

- the continuous endpoint convention gives `H_2(0)=H_2(1)=0`;
- `H_2(1/2)=1` bit;
- `H_2(p)=H_2(1-p)`;
- the first derivative vanishes at `p=1/2`;
- the second derivative is negative throughout `0<p<1`, so the curve is strictly concave and the center is its unique maximum;
- the source samples the open interval and supplies the two exact endpoints as explicit markers, which is geometrically faithful.

The curve, guides, and markers seen in the official PDF agree with those facts. The horizontal guide is at 1, the vertical guide is at 1/2, and the endpoint markers lie at 0 and 1. No axis direction, endpoint, extremum, or symmetry error was observed.

`H_2(p)` on the axes/annotation and `H_b(p)` in the adjacent sentence are both conventional notations for the binary/base-2 entropy in this context. The plotted formula divides by `ln 2`, the annotation states bits, and the caption states the binary-entropy conclusion, so the meaning is unambiguous and not erroneous.

## Text and caption

All displayed tick labels, axis labels, Chinese annotations, mathematical symbols, caption characters, and the figure number are present and readable. No missing glyph, tofu box, replacement glyph, or wrong codepoint was observed. The hollow square above the plot is the proof-ending QED symbol, not a missing-glyph box.

The caption is a single accurate reading conclusion: binary entropy reaches 1 bit at `p=1/2` and tends to 0 at the deterministic endpoints. It agrees with the curve, markers, annotations, source, and adjacent V1-C06 explanation.

## R168 visual adjudication

The source contains numeric font declarations that would have been below older numeric thresholds. Under the supplied R168 policy those historic font-size/pixel/ratio/microgrid thresholds are advisory and cannot alone cause a hard fail or source return. In the current PDF the tick labels, axis labels, endpoint labels, symmetry formula, maximum annotation, and caption are actually readable and visually balanced at full-page and native views.

The complete 21-object denominator and all 210 unordered pairs were reviewed after opening the overlay and native evidence. Intended contacts are confined to axes/guides/curve/markers encoding the mathematical geometry. Critical text-to-curve/guide/marker pairs remain visibly separated; the endpoint annotation backgrounds prevent curve ink from entering glyph ink. No illegal visible-ink overlap, true clipping, actual unreadability, or obvious imbalance was found.

## Page integration

The plot and one-line caption occupy a stable block between the preceding proof and the following explanatory sentence. The subsequent section begins without an orphaned caption, collision, clipping, anomalous blank region, or cramped transition. The figure is neither oversized nor visually lost on the page; the data curve remains the primary visual object in both color and grayscale.

Manual hard-defect direction: **no current true R168 hard defect observed**.
