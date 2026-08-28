# Controlled retry invocation

- `CONTROLLER`: `D:\texlive\2026\bin\windows\latexmk.exe -lualatex`
- `ENTRY`: read-only `v260_FIG-P654-01_standalone.tex`
- `OPTIONS`: unchanged `-lualatex -interaction=nonstopmode -halt-on-error -file-line-error -outdir=<R5>\build`
- `CONTROLLER_SHELL_TEXMFVAR_ASSIGNMENT`: `<R5>\texmf-var`
- `CONTROLLER_SHELL_TEXMFCACHE_ASSIGNMENT`: `<R5>\texmf-cache`
- `WRAPPER_ENV_INHERITANCE_MODE`: PowerShell `Start-Process` was launched after the two shell assignments and without an explicit `-Environment` override; default inheritance was intended.
- `ACTUAL_LATEXMK_ENV_VISIBLE_VALUES`: `NOT_CAPTURED`
- `ACTUAL_LUALATEX_ENV_VISIBLE_VALUES`: `NOT_CAPTURED`
- `KPSEWHICH_OR_ENGINE_CACHE_RESOLUTION_QUERY`: `NOT_RUN / NOT_CAPTURED`
- `LATEXMK_PID`: `16296`
- `LATEXMK_EXIT`: `12`
- `NATURAL_EXIT`: true
- `INTERRUPTED_OR_TERMINATED`: false
- `CONTROLLER_COUNT`: exactly one in R5
- `THIRD_BUILD_STARTED`: false
- `POSTCHECK`: latexmk/lualatex/luatex/luahbtex all `NONE`
- `SLOT_RELEASE`: `P654_RETRY_BUILD_SLOT_RELEASED` reported immediately after postcheck and PDF presence check

No Git commit, SA1 or SA3 was started.
