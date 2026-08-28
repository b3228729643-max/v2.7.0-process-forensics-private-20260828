# Complete unordered-pair resolution

- Strict final denominator: `85` separately extracted non-whitespace visible glyph atoms plus `11` separately extracted foreground PDF painted-path atoms, for `N=96`.
- Explicit background-only exclusions: `3` current PDF paint objects (pale subspace fill and two white label knockout masks); none contains a visible foreground stroke.
- Complete unordered-pair denominator: `C(96,2)=4,560`.
- Machine inventory: `4,560` unique pair IDs; reviewer/observed/decision/note/PASS cells remain blank by design.
- Conservative bbox-separated pairs with more than 4 native-300-dpi pixels between bboxes: `4,429`; shared foreground pixels are geometrically impossible.
- Near/intersection candidates: `131`; each has a genuine manual per-ID entry in `manual_pair_candidate_ledger.md` after native/NN8x inspection.
- Manual candidate outcomes: `131 PASS`, `0 TRUE_COLLISION`, `0 UNRESOLVED`.
- Canonical illegal overlap result: `OVERLAP_PIXEL_COUNT=0`.

The retained `manual_atomic_denominator.json` is the transparent pre-manual `N=19` semantic grouping that was superseded before adjudication. It is not used in any final count or decision.
