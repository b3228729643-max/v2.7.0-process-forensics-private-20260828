# Manual geometry, readability, and hierarchy audit

## Native 300 dpi clearances

- Minimum independent text–text clearance: 7 px, between a node’s main label and its second math line; threshold 4 px.
- Minimum text/formula–line or arrow clearance: 15 px, between bottom `K=2` and its special-case line; threshold 3 px.
- Minimum node text/formula–border clearance: 12 px, in the Beta/binomial two-line nodes; threshold 5 px.
- Figure bottom to caption ink clearance: approximately 30 px; caption text remains a distinct page object.
- Minimum caption line separation: 13 px; no touching ascenders/descenders.
- `CLIP_PIXEL_COUNT=0`; no visible foreground reaches a page or crop boundary in the authoritative full-page image.

## Relation geometry

- The two conjugacy strokes are 1.00 pt and use filled 2.15 mm Stealth arrowheads.
- The five special-case strokes are 0.58 pt and use open 1.90 mm arrowheads.
- Stroke-width ratio is about 1.72:1, and the arrowhead fill/open distinction survives grayscale. This is a real structural encoding, not a color-only cue.
- Every relation starts and ends at the intended node border. There is no overshoot into node text, broken endpoint, accidental crossing, or ambiguous reverse direction.
- Parallel vertical relations remain aligned by column; three horizontal special-case relations keep a consistent left-to-right general→special reading order.

## Readability under R168

- Node/row CJK ink heights are 31–33 px; base math is 26–27 px; edge CJK is 29–30 px; edge math is 26–27 px.
- Same-class ratios are within `[0.9538,1.0385]` after the comma-bearing Bernoulli line is split into comparable K and N substrings.
- The 29 px legend “特殊情形” is a one-pixel threshold variation from its 30 px peers. It is fully readable at native1x and nearest8x, is not visibly imbalanced, and therefore is not a hard failure under R168.
- Edge labels are intentionally lighter/smaller than node text but remain crisp; row headings are bold blue without overwhelming the nodes.

Manual geometry/readability decision: `PASS`.

