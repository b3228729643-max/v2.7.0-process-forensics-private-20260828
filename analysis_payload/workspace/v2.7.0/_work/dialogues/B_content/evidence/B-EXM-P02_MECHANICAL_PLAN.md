# B-EXM-P02 mechanical validation plan

- Status: `COMPLETED_BY_R7_RESUME`.
- Coordination: the main dialogue froze R99 and released the build lock before B resumed; B later released its own lock as `B_R7_BUILD_LOCK_RELEASED` after all TeX/latexmk processes exited.
- P02 source state: five modified chapter files, `60 insertions / 60 deletions`, `git diff --check` passes.
- Source/static evidence already complete: seven solution stages exactly once per object, one `SolAnswer` per object, no generic route hit, no engineering status token, relevant 9 unit tests pass, SA1 R2 passes with zero open findings.

## Pending mechanical gate

Completed route after the main dialogue reported `R99 frozen`:

1. Seeded a unique B-local R7 output from the frozen R99 auxiliary files and ran the B source with `-Resume`; interrupted R4 artifacts were not reused.
2. Recorded the terminal 814-page, 4,941,530-byte PDF, hard-error scan and layout diagnostics in `B-EXM-P02_MECHANICAL_EVIDENCE.md`.
3. Extracted exact P02 page coverage from the terminal PDF.
4. Rendered and visually inspected all ten covering pages: 133, 361--362, 502--503, 692--694 and 799--800.
5. Submitted the frozen source/PDF evidence to independent SA3 blind review.

## Baseline page map for targeting only

The valid P01 merged PDF has 814 pages. Its body locations provide approximate targets, not P02 acceptance evidence:

- Example 8.1, positive-definite quadratic Newton update: PDF page 133, possibly continuing on 134.
- Example 19.1, two-round AdaBoost calculation: PDF pages 361--362.
- Example 26.1, zero-matrix compact SVD: PDF page 503.
- Example 33.3, five-category Gibbs target: PDF page 693.
- Example 37.2, model/objective/solver layering: PDF page 800, possibly continuing on 801.

The interrupted R4 PDF and the partial cache copy under `B-EXM-P02/B-EXM-P01` are explicitly excluded from acceptance evidence.
