# Manual grayscale and page-integration audit

## Grayscale

- `G01 PASS` — all six node boundaries remain visible; the two gray special-case nodes remain distinguishable by border shade and position.
- `G02 PASS` — thick filled conjugacy arrows remain visibly heavier than thin open special-case arrows after color removal.
- `G03 PASS` — the two legend samples preserve the same thickness and arrowhead distinction seen in the diagram.
- `G04 PASS` — text contrast stays high; no row heading, node label, edge label, or math line fades into a fill.

## Full-page integration

- `P01 PASS` — figure 34.3 sits immediately after its introducing paragraph; the prose and caption both name the same category/multinomial, Bernoulli/binomial, and Dirichlet/Beta relationships.
- `P02 PASS` — the figure width fits the text block without entering margins or page navigation furniture.
- `P03 PASS` — the two-line caption is complete, aligned with the figure, and followed by a comfortable gap before heading 34.2.
- `P04 PASS` — the next section heading, objective box, derivation target, and preparation box remain balanced on the page; the figure creates no orphan line or abnormal white block.
- `P05 PASS` — the visual reading order is row heading→general node→special-case node, while the two thick vertical arrows separately communicate prior→likelihood conjugacy.

Manual grayscale decision: `PASS`. Manual page-integration decision: `PASS`.

