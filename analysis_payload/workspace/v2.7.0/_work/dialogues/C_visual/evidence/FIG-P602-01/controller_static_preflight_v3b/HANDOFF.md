# P602 controller v3B static-only handoff

Status: `P602_CONTROLLER_STATIC_PREFLIGHT_V3B_READY_FOR_MAIN_REVIEW`.

- Old v3 remains unchanged and is explicitly historical `STATIC_REJECT`.
- v3B controller and its kpse/TeX children were not executed.
- Future candidate root and future cache root were not created.
- The same-environment kpse gate model covers `openout_any=p` plus exact TEXMFOUTPUT/TEXMFVAR/TEXMFCACHE/TEXMFCONFIG resolution, exit, ASCII, and slash-normalization gates before candidate creation/claim/build.
- A successful build Process.Start immediately atomically persists START; start exception, interrupted execution, natural nonzero exit, missing PDF, and success all persist RESULT before any throw/return, including post-TeX process count and retry 0.
- The controller contains one syntactic Process.Start site and one build-helper callsite, with no restart/retry path.
- All five v3B package files, including the final marker, must be OS read-only after freeze.
- Main acceptance and a separate explicit slot grant are required before any execution.

