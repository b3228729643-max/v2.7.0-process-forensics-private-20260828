# R10 process evidence reconciliation

## Recorded invocation

- `DIRECT_INVOCATION_START.json` and `DIRECT_INVOCATION_RESULT.json` bind one direct `lualatex` invocation: parent PID 11356, child PID 9700, start `2026-08-24T23:09:08.4089195Z`, natural end `2026-08-24T23:10:17.2383848Z`, exit code 0.
- The result records `invocation_count=1`, `latexmk_invoked=false`, `automatic_retry_count=0`, `natural_exit=true`, and `interrupted_or_terminated=false`.
- Source and wrapper bytes/SHA-256 are identical before and after the invocation. The three TeX cache variables are recorded with one common R10-local `texcache` path.
- The one result PDF is `build/v260_FIG-P654-01_standalone.pdf`, 43,385 bytes, SHA-256 `86712CDD98EC92AF1A2D274D4E4E987E6AE8338064FD4A3339D2761737A87260`.

## Log observations

- A bounded read at `2026-08-24T23:31:35.9876778Z` found one `Output written on` marker, zero matched fatal/emergency markers, and zero `latexmk` text in the 28,299-byte stdout log.
- The stderr log has zero bytes and zero non-whitespace characters.
- These observations support the recorded exit/result; they do not invent process telemetry that was not captured at invocation time.

## Current process observation

- At `2026-08-24T23:31:35.9876778Z`, the running-process set for `latexmk`, `lualatex`, `luatex`, and `luahbtex` was empty.
- This is a current post-build observation only. It is not presented as continuous historical monitoring.

## Non-TeX evidence boundary

All machine render, taxonomy recomputation, manual opening/review, consumer validation, and sealing work after the direct invocation is non-TeX. The controller was not rerun, and no additional TeX process was started.
