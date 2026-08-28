# R157 main acceptance and routing

## P602 retry failure

- Main accepts the immutable `sa2_r2_controlled_build_v2` package as a complete record of an environment failure, not as a figure result.
- Direct invocation: PID 16572, natural exit 1, no retry, no PDF, no business-source read, and zero post-exit TeX processes.
- Independent package check: 10 ordinary files, 8 manifest rows, exact unlisted paths `09_manifest/evidence_file_manifest.csv` and `WRITE_STOPPED.json`, path/bytes/SHA/100ns-mtime mismatch 0, ADS 0, post-marker writes 0.
- P602 remains SA2. A third TeX invocation is not authorized.

### Post-acceptance controller diagnosis

- The v2 controller set the three custom cache variables in the parent PowerShell process and launched LuaLaTeX with `Start-Process`; its working directory remained the source wrapper directory, while all custom cache paths were absolute paths outside that directory.
- Current TeX Live configuration reports `openout_any=p` and an empty `TEXMFOUTPUT`. A Lua-only probe can write the same ASCII cache directories from ordinary Lua, so filesystem ACL and ASCII spelling are not sufficient explanations.
- Main therefore records a high-confidence controller-level inference: LuaTeX's paranoid write policy rejected the external Lua cache target even though PowerShell and `kpsewhich` accepted it. This does not authorize another invocation and does not alter the immutable v2 failure report.
- Any future static controller proposal must preserve the wrapper's relative-input semantics while explicitly solving LuaTeX write authorization, preferably with a task-specific `TEXMFOUTPUT`/cache locality design. It must be reviewed without TeX before any new slot is considered; weakening `openout_any` is forbidden.

## P654 R16B static acceptance

- Accepted source: `src/绘图源码/第05册_采样方法主题模型与图排序/V5-C05/fig_v5_c05_dependency_graph.tex`.
- After SHA-256: `0A7CAAA49978AA6193BA4DC4CB90845981599DFC161F5A8BD6B9143A1EA4C2EB`.
- Scope: one file, 4 insertions, 4 deletions, `git diff --check` pass.
- The chapter-authoritative total-count symbol `N` is preserved; undefined `n_0` is absent. Three locally resized plus signs remain true math glyphs wrapped as binary operators; text plus is absent.
- A receives one direct LuaLaTeX slot using its previously successful R10 PowerShell7 controller/cache pattern. No latexmk, full-book build, concurrent invocation, automatic retry, commit, or fresh role is authorized.
