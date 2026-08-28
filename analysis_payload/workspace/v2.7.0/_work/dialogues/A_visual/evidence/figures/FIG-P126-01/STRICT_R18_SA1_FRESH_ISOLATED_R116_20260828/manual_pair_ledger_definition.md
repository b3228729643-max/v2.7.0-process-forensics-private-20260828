# Manual pair-ledger interpretation

Each row in `manual_pair_ledger.csv` is an individual manual verdict keyed to the object mapping in `machine_unordered_pairs.csv`.

- `PASS` means the pair was reviewed in the complete native figure/overlay and, where close or connected, in its native 1× and nearest-neighbor 8× ROI; it has no illegal reader-visible ink collision, true clipping, or ambiguity. Intended semantic contacts such as axis intersections, arrow-to-marker joins, the optimum marker covering the origin, and trajectory/contour crossings are included as PASS.
- `FAIL` means a true hard illegal visible-ink collision was manually confirmed.

Exactly two pair rows fail: `PAIR-0085` (`O003-O015`) and `PAIR-0189` (`O006-O020`). Their object mapping, classification, evidence filenames, and manual findings are recorded in `hard_defects.csv` and `SA1_MANUAL_VERDICT.md`.
