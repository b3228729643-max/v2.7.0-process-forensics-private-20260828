# P602 controller v3C static full-branch dry run

Status: `STATIC_ONLY_NOT_EXECUTED`; TeX remains disabled.

No controller, kpsewhich, texlua, LuaLaTeX, latexmk, luatex, or luahbtex process was executed. Future candidate root `sa2_r2_controlled_build_v3c` and ASCII cache root `codex_v270_p602_texcache_v3c` were not created.

v3C preserves v3B's accepted wrapper cwd, four-variable cache-containment graph, effective `openout_any=p` kpse gate, source/wrapper/engine identities, atomic claim and START, single generic Process.Start site, single LuaLaTeX helper callsite, and no-retry structure.

## Output-before-RESULT order

After the unique build outcome returns—or an outer controller exception is captured—the `finally` block performs this fixed order:

1. Read-only scan for `latexmk/lualatex/luatex/luahbtex`.
2. Atomically create `01_build/lualatex.stdout.txt` from the complete redirected stdout string.
3. Atomically create `01_build/lualatex.stderr.txt` from the complete redirected stderr string.
4. Read both files back and record resolved path, byte length and SHA-256; independently recompute each identity and compare.
5. Count all build-directory PDFs and identify the expected PDF, including bytes and SHA-256.
6. Compute every individual SUCCESS predicate and the combined hard gate.
7. Atomically write `00_control/DIRECT_INVOCATION_RESULT.json`.
8. Outside `finally`, throw the sole build-status failure only when RESULT is durable and the combined hard gate is false; otherwise return the pending-review candidate status.

The same order applies to start exception, false start, interrupted runtime, natural nonzero exit, missing/empty/multiple PDF, residual TeX process, START-record failure, output persistence failure, PDF identity failure, or success. Empty output is still persisted as a valid zero-byte file with the standard empty-file SHA-256, so its identity remains independently recomputable.

## RESULT exception separation

The RESULT model has separate fields for `start_exception`, `start_record_exception`, `runtime_exception`, `controller_exception`, `pdf_identity_exception`, and `output_persistence_exception`. Output persistence catches both atomic-write and subsequent identity/recomputation errors without suppressing them. No exception field is converted to PASS.

## SUCCESS hard gate

`success_hard_gate.all_pass` is true only when all of these are true:

- invocation count is exactly 1;
- Process.Start succeeded and START exists;
- natural exit is true and exit code is 0;
- the build directory contains exactly one PDF, it is the expected path, its byte length is positive, and its SHA-256 is non-empty;
- post-TeX process count is 0;
- all six exception fields listed above are null or empty;
- stdout and stderr files both exist and their path/bytes/SHA identities match an independent second read.

Any false predicate is recorded in RESULT and makes success impossible. There is no fallback, threshold relaxation, second start, or retry branch.

## Static branch outcomes

- Pre-cache identity/path/concurrency failure: no helper start and no runtime roots.
- Cache/kpse failure: preclaim kpse gate remains in cache root; no candidate root or LuaLaTeX.
- Claim failure: candidate control shell may exist; no LuaLaTeX.
- Build start success: START is attempted immediately before redirected-output reads and waiting.
- Build start exception: empty stdout/stderr files and RESULT are written; success gate fails.
- Natural failure or missing PDF: complete stdout/stderr files are written, then RESULT, then the final failure throw.
- Residual process or any recorded exception: RESULT is written and success gate fails even if exit is 0 and a PDF exists.
- Complete success: stdout/stderr and RESULT are durable; only the pending non-TeX review status returns.

Static lint must show: AST parse errors 0; one `$process.Start()` site; one build helper callsite; no `Start-Process`, `while`, `do`, recursion, or build invocation in catch/finally; stdout and stderr atomic writes precede RESULT; RESULT precedes the final build-status throw.

