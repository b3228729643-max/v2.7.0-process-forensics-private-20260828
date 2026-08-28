# Single direct LuaLaTeX invocation plan

- `PARENT`: PowerShell 7 runs `run_direct_lualatex_once.ps1`.
- `CHILD`: one `D:\texlive\2026\bin\windows\lualatex.exe` process.
- `WORKING_DIRECTORY`: the frozen wrapper directory.
- `ENTRY`: `v260_FIG-P654-01_standalone.tex`.
- `OPTIONS`: `-interaction=nonstopmode -halt-on-error -file-line-error -recorder -output-directory=<R7>/build`.
- `CACHE_BINDING`: parent sets `TEXMFVAR`, `TEXMFCACHE`, and `TEXMFCONFIG` to the same absolute forward-slash path `<R7>/texcache`; the direct child inherits the parent process environment without an override.
- `RETRY_POLICY`: no retry, irrespective of exit status.

After natural child exit, the controller records the PIDs, exit code, exact binding, timestamps and any output-PDF identity in `DIRECT_INVOCATION_RESULT.json`.
