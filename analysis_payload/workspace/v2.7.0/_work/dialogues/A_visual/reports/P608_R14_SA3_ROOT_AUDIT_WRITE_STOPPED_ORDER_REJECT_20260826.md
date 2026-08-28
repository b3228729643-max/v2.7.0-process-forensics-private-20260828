# P608 R14 fresh SA3 root audit

Formal verdict: `CONTENT_PASS_DIRECTION / ROOT_REJECT_WRITE_STOPPED_NOT_LAST / A_LOCAL_PASS_BLOCKED`

## Accepted content direction

- HANDOFF_ID: `A-R105-P608-SA3-FRESH-ISOLATED-20260826`
- Candidate: official R105, physical page 661.
- SA3 result reports N=128 and C=8,128/8,128.
- Glyph denominator 68; math-rule denominator 6.
- Machine cross-check errors, hard overlaps, hard clearance failures, clip pixels, and R168 hard typography failures: all zero.
- Formula/content checks preserve the final recomputed mean `2.0000`.
- Business direction is `SA3_PASS_READY_FOR_MAIN_A_LOCAL_PASS_ACCEPTANCE`, but central A_LOCAL_PASS is not claimed here.

## Mechanical root check

- Evidence root ordinary files: 193.
- `SEALED_MANIFEST.csv`: 192 rows, exactly matching all ordinary files other than the manifest itself.
- Manifest path/bytes/SHA-256 duplicate, missing, extra, and identity mismatch counts: 0/0/0/0.
- Read-only nonconforming files: 0; ADS, pyc/pyo, and Python cache directories: 0/0/0.
- External handoff is read-only and matches SHA-256 `E587560571EA891070CF89FAF462B4C7535047C9C0459CC3C8C1E3DD9EF3BD23`.
- TeX process count during root audit: 0.

## Decisive seal-order failure

`WRITE_STOPPED` was written at `2026-08-25T23:15:02.2083733Z`, but four evidence-root files have later LastWriteTimeUtc values:

1. `seal_evidence.ps1` — `2026-08-25T23:16:15.4876935Z`
2. `SEAL_AUDIT.json` — `2026-08-25T23:17:10.0772791Z`
3. `POSTSEAL_WRITE_CHECKS.json` — `2026-08-25T23:17:10.1525034Z`
4. `SEALED_MANIFEST.csv` — `2026-08-25T23:17:10.6523504Z`

The last file trails `WRITE_STOPPED` by 1,284,397,708 ticks. Therefore the root does not prove “write stopped” or post-seal zero writes under the established strict-last marker contract. Read-only attributes and a valid final manifest do not repair that temporal contradiction.

## Routing

- R14 remains permanently read-only; no file was changed or regenerated during this audit.
- Do not count the R14 root as complete mechanical SA3 evidence and do not declare A_LOCAL_PASS from it.
- Await main-thread direction for a new evidence-only control reseal or a replacement fresh isolated SA3. No role is started here.
