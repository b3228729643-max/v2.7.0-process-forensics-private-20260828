# Mathematical, state-index, caption, and neighbour-text review

Result: **PASS (semantic consistency)** on the official R95 page; this is separate from the final typography FAIL.

- The scan-order indicators and arrows give the intended left-to-right state transition from early coordinates through the omitted middle to the final coordinate. The diagram does not imply parallel update.
- At substep `j`, `x^{[j]}` represents the current partial system-scan state: the prefix through the current coordinate uses this-round values and the suffix retains prior-round values. The state cards and their labels preserve that split.
- `x^{[d]} = x^{(t)}` is the completed-round/terminal sample. The terminal card, scan sequence, caption, and adjacent explanatory paragraph agree that the end-of-round state is recorded as the round sample.
- The formula base/script units are semantic parents (`T030`/`T031`, `T037`/`T038`, `T039`/`T040`); scriptstyle is treated as natural TeX layout, not as an independent text-text clearance pair. The visible formula, arrows, borders, card textures, and caption were included in the 300 dpi / 8x review; no semantic collision or clipped formula was observed.
- Caption wording agrees with the state indexing: it distinguishes this-round prefix values from prior-round suffix values and identifies the final state/sample. No mismatch was found between the caption, nearby body text, title, or diagram labels.
