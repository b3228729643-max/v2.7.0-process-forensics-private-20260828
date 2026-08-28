# v2 to v3 exact controller difference

The only necessary functional change is the cache-authorization topology:

```text
v2
TEXMFOUTPUT = unset
TEXMFVAR    = C:\Users\ASUS\AppData\Local\Temp\codex_v270_p602_texcache_preflight\texmf-var
TEXMFCACHE  = C:\Users\ASUS\AppData\Local\Temp\codex_v270_p602_texcache_preflight\texmf-cache
TEXMFCONFIG = C:\Users\ASUS\AppData\Local\Temp\codex_v270_p602_texcache_preflight\texmf-config

v3 proposal
TEXMFOUTPUT = C:\Users\ASUS\AppData\Local\Temp\codex_v270_p602_texcache_v3
TEXMFVAR    = C:\Users\ASUS\AppData\Local\Temp\codex_v270_p602_texcache_v3\texmf-var
TEXMFCACHE  = C:\Users\ASUS\AppData\Local\Temp\codex_v270_p602_texcache_v3\texmf-cache
TEXMFCONFIG = C:\Users\ASUS\AppData\Local\Temp\codex_v270_p602_texcache_v3\texmf-config
```

Thus v3 adds the task-specific `TEXMFOUTPUT` parent and relocates the other three task-specific cache paths beneath that exact parent. This is one compound locality change aimed at satisfying paranoid Lua output-name checks. It does not claim runtime success before a separately authorized invocation.

Unchanged from v2:

- `openout_any=p`; no security relaxation.
- LuaLaTeX executable and engine SHA.
- Wrapper working directory.
- Wrapper leaf-name argument and therefore all relative-input semantics.
- Interaction, halt-on-error, file-line-error, recorder, and output-directory argument structure.
- Source SHA and wrapper SHA gates.
- One-invocation limit, zero-concurrency gate, natural-exit recording, no retry, and fail-stop semantics.
- No business-source edit, latexmk, full-book build, commit, central state/inventory write, fresh role, or next-figure action.

Using `ProcessStartInfo.ArgumentList` instead of `Start-Process -ArgumentList` is control hardening that makes argument boundaries explicit; it does not alter the child executable, working directory, ordered arguments, or business semantics.

