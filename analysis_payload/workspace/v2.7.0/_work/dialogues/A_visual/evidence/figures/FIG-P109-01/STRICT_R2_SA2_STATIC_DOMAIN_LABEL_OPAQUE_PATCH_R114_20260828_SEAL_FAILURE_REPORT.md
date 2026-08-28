# P109 R2 static seal failure report

- HANDOFF_ID: `A-R114-P109-SA2-STATIC-DOMAIN-LABEL-PATCH-20260828`
- Classification: `UNSEALED_CONTROL_FAILURE_BEFORE_ANY_CONTROL_WRITE`
- Controller: `P109_R2_STATIC_SEAL_20260828.ps1`
- Controller identity: 9,528 bytes; SHA-256 `3EDAA94638FC793FFCD06F9DC1BED16196D45A593C1EEC9910F59050965EC3DF`
- AST errors before invocation: 0
- Controller invocation count: 1
- Controller exit: 1
- Retry count: 0

First error: line 55 evaluated `.Count` directly on an empty `Compare-Object` result under StrictMode, producing `The property 'Count' cannot be found on this object`.

The failure occurred before any control write. The R2 root contains exactly the original five static payload files; `PAYLOAD_MANIFEST.json`, `SEAL_AUDIT.json`, and `WRITE_STOPPED.json` are all absent. No TeX/build/commit/fresh role/second UID occurred. The source remains the accepted static patch at 1,922 bytes and SHA-256 `887326D54E8DD97AA6D580EFA7CCD21FA371A94CACD36EB7029E80FC4D2D9355`, with one-file 1+/1- diff and `git diff --check` PASS.

No controller edit, retry, root repair, or in-place reseal was attempted. Main authorization is requested for one fresh sibling evidence-only static control reseal using an empty-safe controller.
