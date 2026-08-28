# Process evidence reconciliation

## Directly observed and identity-bound R7 facts

The following R7 artifacts were copied into `machine_reuse` and bound source-to-destination by bytes, mtime, and SHA-256 in `MACHINE_REUSE_IDENTITY_LEDGER.csv` (935 total reused files; zero identity mismatches):

| Artifact | Bytes | Source/destination mtime UTC | SHA-256 |
|---|---:|---|---|
| `run_direct_lualatex_once.ps1` | 3,228 | 2026-08-24T20:39:35.3142513Z | `71570BB825D00367FF423DA6943DBBCE46EE659FA3A3F158D596884DE2D442FC` |
| `DIRECT_INVOCATION_START.json` | 1,377 | 2026-08-24T20:40:07.7813053Z | `1240177E489D0D99A24B8973AB60EDC53207E993DDC8A465016CE7BDC38617C3` |
| `build/lualatex.stdout.log` | 28,296 | 2026-08-24T20:41:19.3233581Z | `E885303C4337AE8AEE347F317DE9ECE5873AB9EF0BA416C70E9A9182C846D97C` |
| `build/lualatex.stderr.log` | 0 | 2026-08-24T20:40:07.7219666Z | `E3B0C44298FC1C149AFBF4C8996FB92427AE41E4649B934CA495991B7852B855` |
| `build/v260_FIG-P654-01_standalone.pdf` | 43,385 | 2026-08-24T20:41:19.3199715Z | `A7DBDECEA7B54C1649CD341112B7BB37FF379600CB6A61B54EDDBAF154E9E5D6` |
| `DIRECT_INVOCATION_RESULT.json` | 1,740 | 2026-08-24T20:41:20.5942573Z | `E264F54829099CE685F564B265861EA95B6DC9F831A416AB44BFACED8AAE6B7A` |

The frozen start/result records state controller PID 12540, direct `lualatex`/LuaHBTeX PID 9932, one invocation, no `latexmk`, no retry, natural exit, exit code 0, start `2026-08-24T20:40:07.7135563Z`, end `2026-08-24T20:41:20.5294692Z`, and one PDF. The identity-bound stdout begins with `LuaHBTeX, Version 1.24.0 (TeX Live 2026)` and ends with one-page output of 43,385 bytes. These are observations encoded by the contemporaneous R7 artifacts; R7A did not execute them.

## Current R7A external observation

`CURRENT_EXTERNAL_STATE_R2.json` records a separate non-TeX parent/child observation: parent PID 20024, child PID 20292, child exit code 0, empty child stderr, and an observation timestamp of `2026-08-24T21:38:21.8694371Z`. At that instant, the exact names `latexmk`, `lualatex`, `luatex`, and `luahbtex` had process count 0. The same child observed the frozen source SHA `EA4A19FF940A177D4D754C4277896A2F38B75C1E6F252D8A374F418B84E31E6D`, wrapper SHA `FE44F2E6005D884A6916A11C6EBCB89CF40BD523A64D8F8C6BC8124DBABC0CA1`, one Git-changed path, numstat `1/1`, and `git diff --check` exit 0.

The first capture envelope (`CURRENT_EXTERNAL_STATE.json`) had a null parent-side exit-code field and progress CLIXML on stderr. It is retained as an unsuccessful envelope, not used as the successful process observation. R2 corrected only the capture mechanism. The child JSON renders non-ASCII path text with code-page mojibake; identity is therefore bound through ASCII basenames, hashes, byte counts, and Git quoted paths rather than the displayed Unicode path string.

## External authority, not locally machine-captured history

The pre-build process-NONE check and the grant/release sequencing for R7 were supplied by the main-line authority in the explicit `P654_R7_DIRECT_BUILD_SLOT_GRANTED` and subsequent release coordination. R7A treats those as external authority statements. It does not relabel them as local R7 machine captures.

## UNKNOWN / NOT_CAPTURED

- A structured R7 machine artifact containing the exact historical pre-build four-name process list was not captured locally: `NOT_CAPTURED`.
- A structured R7 machine artifact containing the exact historical post-build four-name process list was not captured locally: `NOT_CAPTURED`.
- Independent reconstruction of the historical process table from present process state is impossible: `UNKNOWN`.

Decision for this local package: the identity-bound one-invocation controller/start/result/log/PDF chain establishes what ran and its natural result; the authority statement establishes the slot context; the missing historical process snapshots remain explicit limitations. No historical probe is fabricated or backfilled.

