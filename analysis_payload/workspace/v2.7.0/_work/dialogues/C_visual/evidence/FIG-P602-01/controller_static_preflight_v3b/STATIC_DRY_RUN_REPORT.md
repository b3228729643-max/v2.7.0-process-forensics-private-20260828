# P602 controller v3B static full-branch dry run

Status: `STATIC_ONLY_NOT_EXECUTED`.

The controller, kpsewhich, texlua, LuaLaTeX, latexmk, luatex, and luahbtex were not executed. Neither the frozen future candidate root nor the v3B cache root was created.

## Frozen runtime paths

- Future candidate root: `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\C_visual\evidence\FIG-P602-01\sa2_r2_controlled_build_v3b`
- Future cache root and `TEXMFOUTPUT`: `C:\Users\ASUS\AppData\Local\Temp\codex_v270_p602_texcache_v3b`
- `TEXMFVAR`: `...\codex_v270_p602_texcache_v3b\texmf-var`
- `TEXMFCACHE`: `...\codex_v270_p602_texcache_v3b\texmf-cache`
- `TEXMFCONFIG`: `...\codex_v270_p602_texcache_v3b\texmf-config`
- Wrapper cwd remains `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\worktrees\dialogue_C_visual\src\讲义源码\合并总册`.

Frozen identities: source `2B15B4BEEA7A922FEE24259678DBAE2A54915955915E6714A350122A6251E349`; wrapper `AFE3464AEA950331908CD3C56DD0392A6D5010138C4EE9341B78F7FD3E9F7279`; LuaLaTeX `CC944A1DB010B47FCF5CCB5D1B184CBA208FE7FEA9F18BEC414940E6FD3E24A6`; kpsewhich `90E5BD3477FB1AF7F9D1F8C858DE31137AAB4DF57B29928BA82B7D00B2DD85DB`.

## PREBUILD_KPSE_GATE.json model

The controller first creates only the fresh ASCII cache tree. It runs five independent kpsewhich children through the single generic Process.Start site, each with the exact four future LuaLaTeX environment overrides and the unchanged wrapper cwd. Before any candidate root or invocation claim exists, it atomically writes this model to the cache root:

```json
{
  "schema": "P602_V3B_PREBUILD_KPSE_GATE_V1",
  "candidate_root_exists_when_gate_recorded": false,
  "working_directory": "<exact wrapper cwd>",
  "kpsewhich_path": "D:\\texlive\\2026\\bin\\windows\\kpsewhich.exe",
  "kpsewhich_sha256": "90E5BD...85DB",
  "child_environment": {
    "TEXMFOUTPUT": "<frozen cache root>",
    "TEXMFVAR": "<strict child>",
    "TEXMFCACHE": "<strict child>",
    "TEXMFCONFIG": "<strict child>"
  },
  "probes": ["four per-path write/read/delete results"],
  "resolutions": [
    {"name":"openout_any","resolved":"p","exit_code":0,"non_ascii_count":0,"pass":true},
    {"name":"TEXMFOUTPUT","resolved":"<exact normalized path>","exit_code":0,"non_ascii_count":0,"pass":true},
    {"name":"TEXMFVAR","resolved":"<exact normalized path>","exit_code":0,"non_ascii_count":0,"pass":true},
    {"name":"TEXMFCACHE","resolved":"<exact normalized path>","exit_code":0,"non_ascii_count":0,"pass":true},
    {"name":"TEXMFCONFIG","resolved":"<exact normalized path>","exit_code":0,"non_ascii_count":0,"pass":true}
  ],
  "gate_pass": true
}
```

All five children must start, naturally exit 0, return zero non-ASCII characters, and match exactly (`openout_any` case-sensitive `p`; paths case-insensitive after slash normalization). Failure writes the preclaim gate record in the cache root, leaves the candidate root absent, and never reaches LuaLaTeX.

On PASS only, the controller creates the candidate root, copies identical gate bytes to `00_control/PREBUILD_KPSE_GATE.json`, then atomically creates `INVOCATION_CLAIM.json`.

## Exact future LuaLaTeX ProcessStartInfo

```text
FileName               D:\texlive\2026\bin\windows\lualatex.exe
WorkingDirectory       <unchanged wrapper directory>
UseShellExecute         false
CreateNoWindow          true
RedirectStandardOutput true
RedirectStandardError  true
ArgumentList            -interaction=nonstopmode
                        -halt-on-error
                        -file-line-error
                        -recorder
                        -output-directory=<future root>\01_build
                        v260_FIG-P602-01_standalone.tex
Environment overrides   exact TEXMFOUTPUT/TEXMFVAR/TEXMFCACHE/TEXMFCONFIG above
```

## Full branch evaluation

1. **Identity/path/concurrency failure:** stops before cache/candidate creation and before any Process.Start.
2. **Cache probe failure:** stops before kpse/build; no candidate root.
3. **kpse start, exit, value, ASCII, or normalization failure:** atomically records the failed preclaim gate in cache root, stops with candidate root absent, and never invokes LuaLaTeX.
4. **Gate-copy or claim failure:** candidate control root may exist, but no LuaLaTeX start is reachable.
5. **LuaLaTeX Process.Start success:** the first callback action fixes ordinal 1/count 1 and atomically writes `DIRECT_INVOCATION_START.json` with PID, UTC, all identities, cwd, environment, ordered arguments, ordinal/limit, and retry count 0.
6. **LuaLaTeX Process.Start exception or false return:** no START is fabricated; `finally` performs the read-only post-TeX process scan and atomically writes RESULT with `started=false`, exception identity, null PID/exit as applicable, PDF absence/identity, and retry 0 before throwing.
7. **Natural nonzero exit or missing PDF:** RESULT first records started/PID/times/duration/natural exit/exit code/PDF identity/post-process count/retry 0; only then does the controller stop with `BUILD_FAIL_NO_CANDIDATE_RESULT_RECORDED`.
8. **Interrupted/runtime/control-record exception after start:** the process outcome and post-process scan are captured in RESULT before the controller stops; the start site is never re-entered.
9. **Natural exit 0 with PDF:** RESULT records the full PDF identity and post-process count. The controller returns only `CANDIDATE_PDF_CREATED_PENDING_NON_TEX_REVIEW`; it performs no evidence rebuild, further TeX, commit, central write, fresh role, or next-figure action.

Static lint target: one syntactic `$process.Start()` site inside `Invoke-ControlledProcessOnce`; one LuaLaTeX helper callsite; no `Start-Process`, `while`, `do`, recursion, or start call in catch/finally. Foreach iterations cover the five distinct kpse variables and are not retries.

