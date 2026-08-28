# P602 v3 controller static dry-run report

Status: `STATIC_ONLY_NOT_EXECUTED`.

This report is a hand-evaluated dry run of the frozen controller text. The controller was not invoked. No `lualatex`, `texlua`, `latexmk`, `luatex`, or `luahbtex` process was started, and the future candidate root was not created.

## Frozen identities

- Future candidate root: `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\C_visual\evidence\FIG-P602-01\sa2_r2_controlled_build_v3`
- Controller interpreter for any future authorized run: `D:\PowerShell7\pwsh.exe` (PowerShell 7.6.4; SHA-256 `DB6DD81183FE57D22E03B911EC9A30A2FD7C40542E97743615355A6FB44F458F`)
- Engine: `D:\texlive\2026\bin\windows\lualatex.exe` (SHA-256 `CC944A1DB010B47FCF5CCB5D1B184CBA208FE7FEA9F18BEC414940E6FD3E24A6`)
- Source: `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\worktrees\dialogue_C_visual\src\绘图源码\第05册_采样方法主题模型与图排序\V5-C03\fig_v5_c03_mh_accept_reject.tex` (2869 bytes; SHA-256 `2B15B4BEEA7A922FEE24259678DBAE2A54915955915E6714A350122A6251E349`)
- Wrapper: `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\worktrees\dialogue_C_visual\src\讲义源码\合并总册\v260_FIG-P602-01_standalone.tex` (397 bytes; SHA-256 `AFE3464AEA950331908CD3C56DD0392A6D5010138C4EE9341B78F7FD3E9F7279`)
- Frozen branch/HEAD at design time: `v2.7.0/dialogue-c-visual` / `eea4060c5229168e2b973bbaea81cf391e7a9dfd`.

## Exact path and environment graph

```text
C:\Users\ASUS\AppData\Local\Temp
└── codex_v270_p602_texcache_v3                 = TEXMFOUTPUT
    ├── texmf-var                               = TEXMFVAR
    ├── texmf-cache                             = TEXMFCACHE
    └── texmf-config                            = TEXMFCONFIG
```

All four values are absolute, task-specific, ASCII-only paths. `TEXMFVAR`, `TEXMFCACHE`, and `TEXMFCONFIG` are strict descendants of `TEXMFOUTPUT`; `TEXMFOUTPUT` is a strict descendant of the fixed user Temp directory. A future runtime must require the entire cache root to be absent before it creates the tree, reject reparse points, and pass independent write/read/delete probes in all four directories.

`openout_any` is not weakened. The controller rejects a non-empty inherited override unless it is exactly `p`; it never installs `a`, `r`, or another relaxed value. Main's authoritative static fact remains `openout_any=p`.

## Exact ProcessStartInfo

```text
FileName               D:\texlive\2026\bin\windows\lualatex.exe
WorkingDirectory       D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\worktrees\dialogue_C_visual\src\讲义源码\合并总册
UseShellExecute         false
CreateNoWindow          true
RedirectStandardOutput true
RedirectStandardError  true
```

ArgumentList, in order:

```text
1 -interaction=nonstopmode
2 -halt-on-error
3 -file-line-error
4 -recorder
5 -output-directory=D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\C_visual\evidence\FIG-P602-01\sa2_r2_controlled_build_v3\01_build
6 v260_FIG-P602-01_standalone.tex
```

Child-environment overrides, exactly:

```text
TEXMFOUTPUT=C:\Users\ASUS\AppData\Local\Temp\codex_v270_p602_texcache_v3
TEXMFVAR=C:\Users\ASUS\AppData\Local\Temp\codex_v270_p602_texcache_v3\texmf-var
TEXMFCACHE=C:\Users\ASUS\AppData\Local\Temp\codex_v270_p602_texcache_v3\texmf-cache
TEXMFCONFIG=C:\Users\ASUS\AppData\Local\Temp\codex_v270_p602_texcache_v3\texmf-config
```

The wrapper directory remains the child working directory, and the wrapper is still passed as a leaf filename. This preserves its existing `../common/statlearnbook` and `../../绘图源码/...` relative-input semantics. Moving the cwd to the evidence or cache root is expressly rejected.

## Static gates and stop behavior

Before any future engine start, the controller requires:

1. Exact future authorization token `P602_V3_ONE_DIRECT_LUALATEX_SLOT_GRANTED`.
2. Source, wrapper, and engine SHA-256 identities exactly matching the frozen values.
3. Future candidate root absent and fresh cache root absent.
4. Wrapper parent exactly equal to `WorkingDirectory`; output and cache containment assertions all true.
5. All four TEXMF paths ASCII-only and free of cache-tree reparse points after creation.
6. Write/read/delete probes pass in `TEXMFOUTPUT` and each of its three cache children.
7. Invocation limit exactly 1, in-memory invocation count 0, and no active `latexmk/lualatex/luatex/luahbtex` process.
8. An exclusive `CreateNew` invocation-claim file succeeds before `Process.Start`.

There is one syntactic `Process.Start()` site, no retry loop, and no automatic recovery branch. A pre-start gate failure stops before LuaLaTeX. A start exception, nonzero natural exit, or absent PDF ends as a build failure and cannot re-enter the start site. A successful PDF also stops the controller; native evidence, further TeX, commit, state/inventory writes, fresh roles, and next-figure work remain outside this controller and require separate authorization.

Static evaluation at `2026-08-25T06:03:34.4385785Z` found the future candidate root and this static package absent before creation, source/wrapper/engine hashes matching, and no forbidden TeX process. These are design-time observations only, not a future runtime PASS.

