# FIG-P602-01 SA2 R2 controlled build v2 — failure report

Result: `BUILD_FAIL_NO_CANDIDATE`.

The authorized ASCII-cache retry passed every pre-build control gate:

- The R2 figure source SHA-256 was exactly `2B15B4BEEA7A922FEE24259678DBAE2A54915955915E6714A350122A6251E349`.
- The wrapper SHA-256 was `AFE3464AEA950331908CD3C56DD0392A6D5010138C4EE9341B78F7FD3E9F7279`.
- No `latexmk`, `lualatex`, `luatex`, or `luahbtex` process was active.
- Write/read/delete probes passed for all three authorized ASCII cache directories.
- Under the same requested child environment, `kpsewhich --var-value` resolved `TEXMFVAR`, `TEXMFCACHE`, and `TEXMFCONFIG` exactly after slash normalization; all three returned exit code 0 and contained zero non-ASCII characters.

Exactly one direct LuaLaTeX invocation was then started. PID 16572 ran from `2026-08-25T05:47:47.9459680Z` to `2026-08-25T05:47:48.5692390Z` and naturally exited with code 1. The post-call TeX-process count was zero, so the build slot was immediately released and TeX was disabled again.

The engine reported during luaotfload initialization:

`system : no writeable cache path, quiting`

The failure is recorded at wrapper line 1. The recorder file contains the standalone wrapper and TeX Live initialization inputs, but it does not contain the assigned P602 figure-source path. Therefore the attempt did not reach the business figure source, produced no PDF, and cannot support any new native render, object, glyph, pair, peer, role, clip, view, hard-gate, or manual judgment.

After natural exit, the three authorized ASCII cache directories still existed as ordinary directories and each contained zero descendants. This report does not infer a further root cause beyond the engine message. No second invocation, retry, source change, TeX workaround, commit, central-state write, inventory write, fresh role, or next-figure action was performed.

