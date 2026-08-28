# Preliminary-v1 provenance

- Classification: `PRELIMINARY_NOT_ACCEPTED`.
- Frozen R101: 4,947,496 bytes; SHA-256 `0870FF226DC383875C4A1B6EABB06AAB942317DA294D90D2864B3030D46DF1A1`; physical page 659.
- Reused replay script: `machine_reuse/preliminary_algorithm_v1_replay.py`; 18,586 bytes; SHA-256 `3CEDC69DF0C5139AC54BF76DEFC00AD75B0CBA0D6A7A3139AEF3589BFA5C1428`.
- The frozen machine replay identity records 64 preliminary rows and no accepted threshold change. R7A did not execute or import the sealed R7 script; the copied script and its replay products are covered by per-file reuse hashes.
- R7A independently opened all eight preliminary navigation sheets. The 64 accepted manual rows are `manual_ledgers/preliminary_manual.csv`; the sole accepted primary machine-readable pair is `preliminary_run/preliminary_64_accepted.csv` and `.json`.
- Every accepted primary row has numeric manual missing/foreign values, never `PENDING`; every pair row includes A/B before/after, intersection before/after, and overlay before/after references.
- The 20/255 threshold, zero illegal-overlap gate, and `[0.92,1.08]` peer interval were not changed.

