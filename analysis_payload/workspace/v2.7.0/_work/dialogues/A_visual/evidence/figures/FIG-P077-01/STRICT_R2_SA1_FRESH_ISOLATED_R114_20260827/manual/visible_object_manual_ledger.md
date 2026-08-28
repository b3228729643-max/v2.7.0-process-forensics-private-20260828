# FIG-P077-01 fresh SA1 visible-object denominator and manual ledger

- Reviewer role: fresh isolated SA1
- Model / reasoning: gpt-5.6-sol / xhigh
- Handoff: `A-R114-P077-SA1-FRESH-ISOLATED-20260827`
- Official candidate: R114, independently located at physical PDF page 79 (printed page 66)
- Observation basis: the official-PDF full page at 200 dpi and native 300 dpi, the direct native-300-dpi figure crop, native grayscale, text and denominator overlays, source lines 1-57, current V1-C05 context lines 136-151, and native1x/nearest8x critical ROIs were opened before these decisions were written.
- R168 rule applied: legacy source-size, pixel-height, and ratio thresholds are advisory. A hard failure is recorded only for a current-PDF missing/tofu/wrong codepoint or wrong mathematical meaning, unreadability/obvious imbalance, true clipping, illegal visible-ink overlap, or semantic/geometric error.
- Denominator freeze: 30 source-construct-level visible objects: 13 text/formula/caption objects and 17 graphical/background objects. The three repeated x ticks and three repeated y ticks are individually enumerated. Radical bars and the natural superscript are integral glyph components of T09/T10 rather than separate semantic objects.

| ID | Visible object | Manual post-observation finding | Hard issue | Decision |
|---|---|---|---|---|
| T01 | x-axis title `x` | Correct variable, centered below the zero tick, fully formed and readable; no clipping or competing weight. | false | PASS |
| T02 | y-axis title `密度` | Both Chinese glyphs are correct, vertically oriented and readable; no missing/tofu glyph or collision. | false | PASS |
| T03 | x tick `−4` | Proper mathematical minus and digit; aligned to its tick and separated from the axis. | false | PASS |
| T04 | x tick `0` | Correct center tick label; clear separation from area annotation and x title. | false | PASS |
| T05 | x tick `4` | Correct right tick label; no clipping at plot edge. | false | PASS |
| T06 | y tick `0` | Correct baseline density tick; separated from vertical axis/curve ink. | false | PASS |
| T07 | y tick `0.2` | Correct value and consistent visual size with T06/T08. | false | PASS |
| T08 | y tick `0.4` | Correct value at the narrow-density peak scale; no top clipping. | false | PASS |
| T09 | `N(0,1)` peak label | Formula, punctuation, Chinese label and radical bar are complete; peak `1/sqrt(2pi)` is mathematically correct and visually linked to the solid narrow curve. | false | PASS |
| T10 | `N(0,2^2)` peak label | Natural superscript `2` is present and legible; peak `1/(2sqrt(2pi))` is correct for sigma=2 and visually linked to the dashed wide curve. | false | PASS |
| T11 | area label | `两条曲线：面积 = 1` is complete and readable; white carrier separates the text from brace/axis. Tight center-tick ROI confirms the residual tick ink is below, not through, the label ink. | false | PASS |
| T12 | figure number `图 5.1` | Complete, bold, and clean; separated from T13. | false | PASS |
| T13 | caption conclusion | Exactly states wider/lower/unit-area conclusion; one line, no clipping, no wrong codepoint. | false | PASS |
| G01 | x axis and arrowhead | Continuous visible axis on both sides of the central label carrier; arrowhead is intact and correctly oriented. | false | PASS |
| G02 | y axis and arrowhead | Continuous and vertical; arrowhead intact; correct density-axis orientation. | false | PASS |
| G03 | x tick at −4 | Proper structural joint with G01 and alignment with T03. | false | PASS |
| G04 | x tick at 0 | Central tick is partly hidden by the intentional white area-label carrier and resumes below it; nearest8x evidence shows no text-ink collision. | false | PASS |
| G05 | x tick at 4 | Proper structural joint with G01 and alignment with T05. | false | PASS |
| G06 | y tick at 0 | Proper structural joint with G02 and alignment with T06. | false | PASS |
| G07 | y tick at 0.2 | Proper structural joint with G02 and alignment with T07. | false | PASS |
| G08 | y tick at 0.4 | Proper structural joint with G02 and alignment with T08. | false | PASS |
| G09 | solid narrow Gaussian curve | Symmetric about x=0, peak near 0.4, narrower than G11, smooth and unbroken; correct N(0,1) geometry. | false | PASS |
| G10 | narrow Gaussian fill | Light, subordinate fill under G09; supports area comparison without hiding linework or text. | false | PASS |
| G11 | dashed wide Gaussian curve | Symmetric about x=0, peak near 0.2, wider than G09; dash pattern remains distinct in grayscale. | false | PASS |
| G12 | wide Gaussian fill | Light, subordinate fill under G11; overlap with G10 is an intended density-area comparison. | false | PASS |
| G13 | x=0 reference line | Correctly passes through both distribution peaks; lighter/dashed and subordinate to the two data curves. | false | PASS |
| G14 | unit-area brace | Spans the comparison region, is fully visible, and points to T11 without touching its ink. | false | PASS |
| G15 | narrow-label white carrier | Legitimate background carrier; keeps T09 readable and does not create an illegal foreground collision. | false | PASS |
| G16 | wide-label white carrier | Legitimate background carrier; separates T10 from the nearby dashed curve while preserving the curve's reading path. | false | PASS |
| G17 | area-label white carrier | Legitimate background carrier; masks the underlying central axis/tick/brace segment so T11 retains visible clearance. | false | PASS |

Manual denominator result: 30/30 observed after rendering; 30 PASS, 0 hard issue, 0 unknown, 0 omitted.
