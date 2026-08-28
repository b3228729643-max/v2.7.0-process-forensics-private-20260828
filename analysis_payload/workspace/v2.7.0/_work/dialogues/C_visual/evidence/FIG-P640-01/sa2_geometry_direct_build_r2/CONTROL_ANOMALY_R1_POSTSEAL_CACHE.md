# R1 post-seal cache anomaly observed during R2

- AFFECTED_ROOT: `sa2_geometry_direct_build_r1`
- R1_EXPECTED_ORDINARY_FILES: `53`
- R1_CURRENT_ORDINARY_FILES: `54`
- R1_MANIFEST_ROWS: `51`
- R1_LISTED_PATH_BYTES_SHA_MISMATCHES: `0`
- R1_UNLISTED_EXTRA_COUNT: `1`
- EXTRA_PATH: `02_nontex_evidence/__pycache__/build_p640_nontex_evidence.cpython-311.pyc`
- EXTRA_BYTES: `34325`
- EXTRA_SHA256: `4599928928FFF05C09F3AA3992A172C0E61DE36DC9396CC22CCB9725DC2E2CA1`
- EXTRA_MTIME_UTC: `2026-08-25T21:08:45.777530Z`
- R1_MANIFEST_SHA256_UNCHANGED: `33550E2058EA47D3965DD2BAAFB511F1538BCB2A7B43F45BF9D080543C114419`
- R1_WSTOP_SHA256_UNCHANGED: `EEB8F2CDDA333294BED7F35F1006FC30DC02E455017C11FD660FA0E66515DC5B`
- CLEANUP_STATUS: `NOT_AUTHORIZED_AND_NOT_PERFORMED`

Cause: the new R2 wrapper loaded the frozen R1 machine-builder source using Python `importlib`. Python emitted one compiled bytecode cache beside that source. No R1 manifest-listed file was edited and no R1 conclusion was reused. An exact cleanup of only the generated pyc and the resulting empty cache directory was requested but not authorized; no workaround was attempted.

Containment: the R2 wrapper was changed before R2 sealing to set `sys.dont_write_bytecode=True`. It will not be executed again. The R2 evidence root itself contains no `__pycache__`, pyc or pyo artifact. Main must adjudicate the R1 control-layer anomaly independently from the R2 content-layer result.
