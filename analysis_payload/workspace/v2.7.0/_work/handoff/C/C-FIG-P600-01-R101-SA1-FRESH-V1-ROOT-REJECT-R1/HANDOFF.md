# P600 R101 fresh SA1 - root control rejection

Status: `P600_R101_SA1_ROOT_REJECT_CONTROL_ONLY_REQUEST_RESEAL`

## What is accepted and what is not

The content-level SA1 result is mechanically closed as a strict **FAIL**. R101 physical page 649 / printed page 636 says Figure 32.4 draws paired flows and the rejection self-loop separately. The figure's complete 22-object inventory contains no rejection self-loop. The failed IDs are `S07`, `H07_TEXT_CONSISTENCY`, and `H14_FINAL`.

The evidence package itself is **not accepted** because its `WRITE_STOPPED` marker is not strictly latest. `MANIFEST.json` has mtime `2026-08-25T09:21:10.2292507Z`; `WRITE_STOPPED` has mtime `2026-08-25T09:21:10.1158953Z`, which is 113,355,400 ns earlier. The seal script prewrote a temporary marker and renamed it last, but the rename preserved the earlier file mtime.

## Identity and closure

- PDF: 814 pages, 4,947,496 bytes, SHA-256 `0870FF226DC383875C4A1B6EABB06AAB942317DA294D90D2864B3030D46DF1A1`.
- Source: 2,497 bytes, SHA-256 `B1BCD4D10AA4FCCE86B11A8B5CFCEDD6AE231C0DC625AFD8B2AE95E93464F8E6`.
- Denominators: 22 objects, 133 glyphs, 231=`C(22,2)` unordered pairs, 24 critical candidates, 10 peer/role assignments, 4 peer comparisons, 22 clip objects, 6 views, and 14 hard gates.
- Manual ledger row/ID/note closure: zero count, uniqueness, blank-note, or duplicate-note failures.
- Pair closure: missing 0, extra 0, unique 231.
- True illegal overlap 0 px; mask contamination 10 px; clipping 0 px.
- Figure geometry, formulas, grayscale, readability under R168, clipping, overlap, and page fit passed independent root visual inspection.

## Root control audit

- Files: actual 52 / manifest model 52; missing 0; unlisted 0.
- Ordinary path/bytes/SHA/manifest-mtime mismatches: 0.
- Canonical recordset SHA-256: `E45CA624C987EB35E9677D120652C12760AC6432D47A51EDE8A6C187B3394985`, independently reproduced.
- Manifest SHA-256: `1D29CDF92F3BA630FA75E4459673785A8E72C3A3CAD5DC7DDBA9CC17EEB2D3C0`.
- Marker SHA-256: `444A5A6B9E63345E0BCA8C93AB3B8F1DDF93CF4E6E1651A4FEFFD3AC1143A070`.
- Complete 52-file snapshot SHA-256: `9AA00CB50BDD4729401B3EE65AE9BEA79CE27E538950B1C9F42F5DF29F82DB46`.
- All 52 files read-only; ADS 0; cache/pyc 0.

## Requested route

Keep the old evidence root permanently read-only. Grant an evidence-only reseal into a fresh root with lossless source provenance, a non-self-recursive manifest, and a `WRITE_STOPPED` marker created after the final manifest so its mtime is strictly latest. Do not alter any content conclusion, denominator, manual ledger, source, or PDF identity.

After the package is accepted, the business repair route requires a chapter-text single writer, not a figure-source writer. No chapter/source edit, TeX invocation, inventory/state update, `C_LOCAL_PASS`, or global PASS is authorized or claimed here.

Unresolved: `CONTROL_RESEAL_REQUIRED; CHAPTER_TEXT_MISMATCH_S07_REMAINS`.
