# R4/R5 read-only root-cause comparison

| Check | R4 first attempt | R5 writable-cache retry | Evidence conclusion |
|---|---|---|---|
| Controller | latexmk PID 10084 | latexmk PID 16296 | one controller in each round |
| Controller exit | 12 | 12 | identical outer exit |
| Inner engine result | lualatex return code 1 | lualatex return code 1 | latexmk/runscript maps the failed engine rule to outer exit 12 |
| PDF | none | none | no candidate in either round |
| Controller-shell cache assignments | none | `TEXMFVAR=<R5>\texmf-var`; `TEXMFCACHE=<R5>\texmf-cache` | R5 command record contains the assignments |
| Actual latexmk/lualatex environment values | not captured | not captured | `UNKNOWN/NOT_CAPTURED`; default `Start-Process` inheritance must not be treated as observed child state |
| Cache directories | not created for R4 | both R5 directories exist and contain zero entries after exit | directory existence is observed; engine use is not |
| Directory ACL/current host state | not applicable | owner `LAPTOP-9T8MO0N8\ASUS`; owner FullControl; inherited Modify entries; zero children | current ACL permits the host user, but no child-token write probe was captured |
| Child-process write permission/probe | not captured | not captured | `UNKNOWN/NOT_CAPTURED` |
| `kpsewhich`/resolved cache path | not run/captured | not run/captured | `UNKNOWN/NOT_CAPTURED`; prohibited from being backfilled after failure |
| First fatal line | TeX log line 12: `luaotfload \| load : FATAL ERROR` | same, line 12 | identical first fatal |
| Detailed fatal | `no writeable cache path, quitting` while loading `basics-gen` | same | retry did not move the failure boundary |
| TeX source boundary | wrapper line 1 displayed; `ctexbook.cls` never loaded | same | failure remains at `\documentclass` before class/body and before target figure source input |
| Console/path trace | CP936 and Chinese path shown as replacement glyphs | same | possible encoding relevance is an inference only |
| Natural exit/postcheck | yes; four TeX process names NONE | yes; four TeX process names NONE | both slots released safely |

## Exit-12 chain

In both rounds, latexmk reports that its `lualatex` rule returned code 1. TeX Live's `runscript.tlu` then reports the latexmk command failed with exit code 12. Thus exit 12 is the controller-layer failure code following the inner LuaHBTeX fatal initialization error; it is not a P654 semantic or pixel-gate result.

## Root-cause boundary

Confirmed: both attempts stop before the business source is read, with the same luaotfload no-writable-cache fatal and no PDF.

Unknown: the actual environment strings visible inside latexmk/lualatex, the `kpsewhich`-resolved cache list, and whether the child token could create a file in either R5 directory. These were not captured during the authorized invocation and were not backfilled after the no-third-build prohibition.
