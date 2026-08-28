# P126 R4 static failure handoff

`P126_STATIC_CONTENT_READY_ROOT_CONTROL_FAILURE_REQUEST_EVIDENCE_ONLY_RESEAL`

- HANDOFF_ID: `A-R115-P126-SA2-STATIC-LEGEND-SEGMENT-PATCH-20260828`
- Source after: 4356 bytes / SHA-256 `3185834A7D4DEAC1595C244DA626FF52B5308E733AFD851E8FF508037C51ED75`
- Static scope: only the `x_2` legend sample declaration; four disconnected teal segments with three 0.10 cm gaps.
- Static status: `STATIC_ONLY_NOT_RENDERED_NOT_PASS`.
- R4 control status: `UNSEALED_CONTROL_FAILURE_BEFORE_MARKER`.
- Controller invocation/retry/exit: `1/0/1`; frozen SHA-256 `BA3C40F54EC9B65E8A25F1010FB6523D157EE6142998ABDAE8DFAF042D08A67A`.
- First error: directory `IsReadOnly` property unavailable at line 101.
- Frozen R4: 8 files / 7176 bytes; files ReadOnly 8/8; root ReadOnly 0/1; marker/stage/result absent; snapshot SHA-256 `B0453C866D5B0D3CA816FF0C423F6257EEA6B4CF5F3941F9049559792D61C7BD`.
- No retry, repair, TeX, build, commit, role, UID, or central action.
- Full report: `P126_R4_STATIC_ROOT_CONTROL_FAILURE_REPORT_20260828.md`, 2550 bytes / SHA-256 `3F6F6499AB3F7BFC4D050A1AA88DB52798A538928E49E6494DFC38ACD59855DC`.

REQUEST: Main preserve the accepted static source-content direction and authorize exactly one startup-absent evidence-only sibling control reseal. P126 remains SA2; build remains unauthorized.
