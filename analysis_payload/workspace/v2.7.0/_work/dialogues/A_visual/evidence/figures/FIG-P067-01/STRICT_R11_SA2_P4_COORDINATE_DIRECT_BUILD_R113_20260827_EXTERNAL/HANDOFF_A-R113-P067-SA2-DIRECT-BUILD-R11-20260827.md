# P067 R11 direct-build failure handoff

- Status: `BUILD_FAIL_NO_CANDIDATE_PRE_TYPESET_CONTROLLER_ERROR`.
- The one authorized root-external controller invocation exited 1 before `Start-Process`; therefore direct LuaLaTeX typeset invocation count is 0, retry count is 0, latexmk invocation count is 0, and PDF count is 0.
- First fatal: controller line 64 used `Split-Path -LiteralPath $wrapper -Parent`; PowerShell 7 rejected that parameter combination before the child process was created.
- The failure root contains zero files and exactly three directories including `build` and `texcache`; it has not been retried or repurposed.
- Source remains 4014 bytes / SHA-256 `11BF3681D069F6A38C479B3074F39F93E8EB6144FF155AC543508E3589A51144`.
- Wrapper remains 388 bytes / SHA-256 `ADDF75D1C82DAB9AB4D5A76E6B241DA1CEB7AED9C2E536106ECFD7710B2D14BF`.
- Frozen controller identity: 6154 bytes / SHA-256 `D9AD484721F3E86B5258FE99EDA4035B978113965AA7AA4D94F1F7AE244232CA`.
- Terminal process observation: lualatex=0, luatex=0, luahbtex=0, latexmk=1. The visible latexmk was external to this failed controller; no ownership query, management, or interruption was attempted.
- Controller PID and exact controller start/end UTC were not persisted because the first error occurred before `START.json`; this absence is disclosed rather than reconstructed. Root creation time is `2026-08-27T11:52:48.1876528Z` and failure was observed before `2026-08-27T11:53:44.0333413Z`.
- No automatic retry, source write, commit, fresh role, second UID/source, or central-state write occurred.
- Next action: Main decides whether a separate corrected-controller/new-root authorization is appropriate after the currently visible external latexmk releases. This branch will not retry automatically.
