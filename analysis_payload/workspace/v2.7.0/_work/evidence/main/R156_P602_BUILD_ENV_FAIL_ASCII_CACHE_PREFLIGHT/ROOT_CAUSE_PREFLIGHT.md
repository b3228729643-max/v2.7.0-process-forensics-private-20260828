# R156 P602 build environment failure and ASCII cache preflight

- Status: `MAIN_PREFLIGHT_PASS_READY_FOR_ONE_FRESH_ROOT_RETRY`
- The first C-P602 direct LuaLaTeX invocation exited naturally with code 1 before documentclass and produced no PDF.
- The first fatal was `luaotfload ... no writeable cache path`; no P602 source or TeX syntax failure was reached.
- When `TEXMFVAR`, `TEXMFCACHE`, and `TEXMFCONFIG` point below the Chinese workspace path, TeX Live `kpsewhich` returns a mangled path segment for `机器学习`.
- Preflight base: `C:\Users\ASUS\AppData\Local\Temp\codex_v270_p602_texcache_preflight`.
- The base path is ASCII-only; write/read/delete probe passed.
- Requested and `kpsewhich`-resolved values:
  - `TEXMFVAR=C:/Users/ASUS/AppData/Local/Temp/codex_v270_p602_texcache_preflight/texmf-var`
  - `TEXMFCACHE=C:/Users/ASUS/AppData/Local/Temp/codex_v270_p602_texcache_preflight/texmf-cache`
  - `TEXMFCONFIG=C:/Users/ASUS/AppData/Local/Temp/codex_v270_p602_texcache_preflight/texmf-config`
- Resolved non-ASCII character count: `0`.
- Authorization boundary: one new evidence root and one direct LuaLaTeX invocation only; no latexmk, full-book build, concurrent invocation, or automatic retry. The child control must repeat and persist the write probe and exact `kpsewhich` gates before invoking LuaLaTeX.
