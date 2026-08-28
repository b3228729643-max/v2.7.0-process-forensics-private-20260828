# P126 R16 controlled direct-build failure report

- HANDOFF_ID: `A-R115-P126-SA2-DIRECT-BUILD-R16-20260828`
- Classification: `BUILD_FAIL_NO_CANDIDATE_PRE_TYPESET_CONTROLLER_ERROR`
- Controller invocation count: 1
- Direct LuaLaTeX child invocation count: 0
- Retry / latexmk / version-probe / second-invocation counts: 0 / 0 / 0 / 0
- Natural controller exit code: 1
- First error: frozen controller line 63, `New-Item -ItemType Directory -LiteralPath $root`, failed because this PowerShell7 `New-Item` command has no `LiteralPath` parameter.
- Failure boundary: before evidence-root creation, cache creation, BUILD_START, child start, auxiliary output, or PDF creation.
- Fixed R16 root after failure: Leaf=false, Container=false, Any=false.
- Candidate PDF count: 0 (`NO_CANDIDATE`).
- Parent command elapsed wall time reported by the execution host: 1.0262942 seconds. Exact controller PID/start/end timestamps were not recorded because the first error preceded the controller's first record write.
- Terminal TeX-family counts after failure: latexmk=0, lualatex=0, luatex=0, luahbtex=0.
- Source after failure: 4,686 bytes; SHA256 `2887758F5CC94987BE750E1EC53B555FB88CE8F71B7260CABBE0A17DDF237405`.
- Wrapper after failure: 395 bytes; SHA256 `706312FAED4A825F61E1517AFFFC852369845F9DAEA051B6E8FEB99335998124`.
- Engine after failure: 6,656 bytes; SHA256 `CC944A1DB010B47FCF5CCB5D1B184CBA208FE7FEA9F18BEC414940E6FD3E24A6`.
- Frozen controller: 7,460 bytes; SHA256 `6A492CC53285A9CD692C260FE89DB641C0BA49E8B1A97D67C7BB83F077795E81`; ReadOnly=true; PowerShell AST errors=0.
- Read-only closure observation: `2026-08-28T09:04:44.1089916Z`.

No controller edit, retry, second controller, direct typeset, TeX cache repair, source edit, commit, fresh role, second UID, central-state write, or non-TeX business review was performed after the first error.

Requested Main action: accept this first-error disclosure, classify and freeze the failed R16 controller attempt, and decide whether a new sibling build slot is authorized. This report does not request or assume such authorization.
