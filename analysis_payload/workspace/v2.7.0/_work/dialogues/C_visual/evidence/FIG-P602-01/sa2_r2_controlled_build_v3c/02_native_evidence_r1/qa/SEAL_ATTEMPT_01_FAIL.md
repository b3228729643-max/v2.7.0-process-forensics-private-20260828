# Native-root seal attempt 01 — pre-seal control FAIL

- Natural failure: `OSError: [Errno 9] Bad file descriptor` at the manifest durability call in `scripts/seal_native_root.py`.
- Failure position: after the manifest text had been written to the temporary `.render` path but before `os.replace`, before any read-only attribute change, and before creation of `WRITE_STOPPED.json`.
- Direct post-failure check: authoritative manifest absent; write-stop marker absent; read-only ordinary files zero.
- The temporary output is preserved verbatim as `qa/SEAL_ATTEMPT_01_PARTIAL_MANIFEST.csv`.
- Root cause: on this Windows runtime `fsync` was attempted on a descriptor reopened read-only. The correction keeps the existing writable manifest handle open, flushes it, and calls `fsync` before that handle closes.
- Correction scope: evidence-control script only. Candidate PDF, business source, machine evidence, manual ledgers, decisions, and thresholds were not modified.
- The next attempt must rerun the full native-root validator before sealing and must still refuse if a manifest or write-stop marker exists.
