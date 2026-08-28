# FIG-P602-01 SA2 R2 controlled build

## Result

- `BUILD_FAIL_NO_CANDIDATE`
- `P602_BUILD_SLOT_RELEASED`
- Exactly one direct LuaLaTeX invocation was made. It exited naturally with code 1.
- No PDF was produced. No retry, latexmk, full-book build, source repair, native-PDF evidence generation, or second TeX invocation was performed.
- TeX was disabled again immediately after the process exited; the post-exit controlled-process count was zero.

## Invocation identity

- Started UTC: `2026-08-25T05:28:23.3347008Z`
- PID: `24408`
- Finished UTC: `2026-08-25T05:28:24.1153858Z`
- Executable: `D:\texlive\2026\bin\windows\lualatex.exe`
- Executable SHA-256: `CC944A1DB010B47FCF5CC5B1D184CBA208FE7FEA9F18BEC414940E6FD3E24A6`
- Input wrapper: `v260_FIG-P602-01_standalone.tex`
- Source SHA-256 remained `2B15B4BEEA7A922FEE24259678DBAE2A54915955915E6714A350122A6251E349`.
- Wrapper SHA-256 remained `AFE3464AEA950331908CD3C56DD0392A6D5010138C4EE9341B78F7FD3E9F7279`.

## Failure

The first fatal error occurred during `luaotfload` initialization before the document class could be loaded:

`system : no writeable cache path, quiting`

The command had isolated evidence-root values for `TEXMFVAR`, `TEXMFCACHE`, and `TEXMFCONFIG`, but LuaTeX did not accept a writable cache path in this sole invocation. The authorization explicitly forbids repair-and-retry, so this condition is recorded without attempting a workaround.

## Evidence

- `00_control/PREBUILD_CONTROL.json`
- `00_control/BUILD_CONTROL.json`
- `01_build/direct_lualatex_stdout.log`
- `01_build/direct_lualatex_stderr.log`
- `01_build/v260_FIG-P602-01_standalone.log`
- `01_build/v260_FIG-P602-01_standalone.fls`
