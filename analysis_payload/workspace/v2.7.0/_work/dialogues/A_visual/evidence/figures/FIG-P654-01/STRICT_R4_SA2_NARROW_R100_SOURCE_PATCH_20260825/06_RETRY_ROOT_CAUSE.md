# Retry root cause and narrow environment correction

- `STATE`: `SA2 / BUILD_FAIL_NO_CANDIDATE`
- `FAILED_CONTROLLER`: one `latexmk -lualatex` invocation, PID `10084`, exit `12`
- `PDF_PRODUCED`: no
- `FAILURE_PHASE`: LuaHBTeX initialization, before the document class/body and before the patched P654 source was read
- `ROOT_CAUSE`: `luaotfload` found no writable cache path and aborted while loading `basics-gen`
- `SOURCE_SYNTAX_CONCLUSION`: not tested by this invocation; the environment failure cannot be attributed to the one-line P654 patch

## Minimum retry environment

Only after a new explicit mainline build-slot grant, create a fresh retry evidence root and two writable subdirectories inside it, then set the child build environment as follows before launching the one authorized controller process:

```powershell
$env:TEXMFVAR = '<fresh-retry-evidence-root>\texmf-var'
$env:TEXMFCACHE = '<fresh-retry-evidence-root>\texmf-cache'
```

Keep the standalone wrapper, worktree, target source and `latexmk -lualatex` options otherwise unchanged. The two cache directories and all build output must belong to the fresh retry evidence root; this sealed failure package must never be reopened for writes. The locale warning is non-fatal and does not justify a source change or a second invocation.

After a successful retry, the new PDF still needs a native 300 dpi complete `N=116`, `C(116,2)=6,670` local gate, 1x/8x evidence, full manual ledgers, and explicit confirmation that `FRM_TRIAL_005` reaches `H_INK>=22px` with no regression.

`P654_RETRY_ROOT_CAUSE_READY_REQUEST_BUILD_SLOT`
