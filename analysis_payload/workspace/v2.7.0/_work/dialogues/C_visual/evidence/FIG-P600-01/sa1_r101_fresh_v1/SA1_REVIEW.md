# SA1 fresh read-only review — B51 / FIG-P600-01 / Figure 32.4

## Outcome

**FAIL — hard gate S07 / H07_TEXT_CONSISTENCY.** The figure itself accurately shows the two MH proposal masses, their common accepted mass `min(a,b)`, reciprocal accepted flows, and the implication “detailed balance ⇒ π stationary, not necessary.” However, the immediately adjacent chapter sentence says Figure 32.4 “把成对流与拒绝自环分开绘制” (draws paired flows and the rejection self-loop separately). The complete semantic-object denominator is 22 and contains no rejection self-loop. This is a real object-content/text mismatch, not a font-metadata advisory.

## Independent identity and page localization

- Official R101 PDF: 4,947,496 bytes; SHA256 `0870FF226DC383875C4A1B6EABB06AAB942317DA294D90D2864B3030D46DF1A1`; 814 A4 pages.
- Figure source: 2,497 bytes; SHA256 `B1BCD4D10AA4FCCE86B11A8B5CFCEDD6AE231C0DC625AFD8B2AE95E93464F8E6`.
- The exact Figure 32.4 caption was located by full-PDF layout extraction and form-feed counting, not by accepting the task packet's old page number. R101 location is **physical page 649, printed page 636**.

## Closed denominators

- semantic objects: 22 / 22 manually decided;
- unordered pairs: C(22,2) = 231 / 231 manually decided, 231 distinct notes;
- visible glyphs: 133 / 133 manually decided, 133 distinct notes;
- machine critical pair candidates: 24 / 24 manually adjudicated;
- peer/role assignments: 10 / 10; within-role peer comparisons: 4 / 4;
- clip objects: 22 / 22;
- views: 6 / 6 (full page 200/300, crop+caption 300, figure color 300, grayscale 300, direct 2400 = 8x);
- hard gates: 14 / 14.

## Per-gate findings

- Geometry/relationships: PASS. The graph has a single top-to-bottom reading path: states feed proposal masses, both masses feed `min(a,b)`, reciprocal blue flows and two equations state the accepted balance. Arrowheads end at node boundaries and do not cross labels.
- Formula semantics: PASS. `a=π(x)q(x,y)`, `b=π(y)q(y,x)`, and both accepted flows equal `min(a,b)` are correct MH balance identities.
- Glyph/readability under R168: PASS with advisory. Source metadata uses 9.2pt generally and 8.6pt for the gray heading, but every one of 133 glyphs was checked at native 300 dpi and direct 2400 dpi. No tofu, wrong code point, wrong mathematical glyph, actual unreadability, or obvious size imbalance was found. Metadata below the older 9.5pt line is advisory only under the controlling R168 rule.
- Overlap: PASS. One independent-object mask candidate P211 reported 10px because the mechanical arrowhead mask filled a path bounding rectangle. Direct 2400dpi pixels and vector coordinates show the two blue arcs are separated. Canonical true illegal overlap is 0; contamination is 10; unresolved is 0.
- Clipping: PASS. All 22 object crops and the full page were checked; `CLIP_PIXEL_COUNT=0`. The tightest review-crop margin is 18.21px below the conclusion box, while the PDF page bottom margin there is about 901px.
- Clearances: PASS. Tightest text-text bbox gap is 4.79px (O21/O22), tightest text-line bbox gap 30.96px, tightest contained text-border inset 7.54px.
- Grayscale/page integration: PASS. Direction and layer hierarchy remain legible without color; page width, caption wrap, vertical whitespace, and following proposition are balanced.
- Text consistency: **FAIL S07** for the nonexistent rejection self-loop claim.

## Required repair path

No current figure-source writer is required on the evidence reviewed here. A chapter-text/source single writer must correct the sentence at current V5-C03.tex line 222 so it describes what Figure 32.4 actually contains, or coordinate a deliberate semantic redesign of the figure and caption. Because the main line has an active R103 build lock, this SA1 neither requests nor starts a build. After a permitted correction, the main line must grant a future global TeX slot, freeze a new official candidate, and run a new fresh SA1; this R101 FAIL cannot be promoted to `C_LOCAL_PASS` or global PASS.
