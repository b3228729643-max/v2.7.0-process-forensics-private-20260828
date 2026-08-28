# Controlled build attempt 01

- `BUILD_SLOT`: explicitly granted by mainline as `P654_BUILD_SLOT_GRANTED`.
- `PRECHECK`: `Get-Process -Name latexmk,lualatex,luatex,luahbtex` returned `TEX_PROCESSES=NONE`.
- `INVOCATION_COUNT`: exactly one.
- `ENTRY`: read-only `v260_FIG-P654-01_standalone.tex`.
- `ENGINE_CONTROLLER`: `D:\texlive\2026\bin\windows\latexmk.exe -lualatex`.
- `LATEXMK_PID`: `10084`.
- `LATEXMK_EXIT`: `12`.
- `NATURAL_EXIT`: yes; no interruption, termination or retry.
- `POSTCHECK`: `Get-Process -Name latexmk,lualatex,luatex,luahbtex` returned `TEX_PROCESSES=NONE`.
- `SLOT_RELEASE`: `P654_BUILD_SLOT_RELEASED` reported to root immediately after the postcheck.

## Result and root cause

No PDF was produced. LuaHBTeX failed before processing the document body because `luaotfload` could not find a writable cache path:

```text
luaotfload | load : FATAL ERROR
Failed to load "fontloader" module "basics-gen".
system : no writeable cache path, quitting
```

This is an execution-environment/cache-path failure, not evidence of a P654 source syntax failure. The only generated files are the controller/engine logs and partial `aux`, `fdb_latexmk`, and `fls` files in `build/`.

## Gate consequence

- New PDF identity: unavailable.
- Native 300 dpi render: not available.
- Object denominator, complete unordered pairs, target `FRM_TRIAL_005` height, ownership, overlap, clearance, clip and manual ledgers: not run because no new candidate exists.
- Decision: `BUILD_FAIL_NO_CANDIDATE_CONTINUE_SA2`; not SA2 PASS.

Any retry requires a new explicit build-slot grant. A corrected invocation should set `TEXMFVAR` and `TEXMFCACHE` to a writable directory inside this evidence root before starting the single allowed controller process. No retry has been started.
