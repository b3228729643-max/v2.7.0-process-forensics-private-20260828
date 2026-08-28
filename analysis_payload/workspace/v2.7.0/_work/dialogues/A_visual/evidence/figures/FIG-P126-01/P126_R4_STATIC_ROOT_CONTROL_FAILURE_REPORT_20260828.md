# P126 R4 static-root control failure

- HANDOFF_ID: `A-R115-P126-SA2-STATIC-LEGEND-SEGMENT-PATCH-20260828`
- SUBSTANTIVE_STATUS: `STATIC_CONTENT_READY_NOT_RENDERED_NOT_PASS`
- CONTROL_STATUS: `UNSEALED_CONTROL_FAILURE_BEFORE_MARKER`
- P126 remains `SA2`.

## Source content preserved

- Sole source: `src/绘图源码/第01册_数学基础与统计学习基本理论/V1-C08/fig_v1_c08_coordinate.tex`
- Authorized before: 4224 bytes / SHA-256 `366C905854F0F3952225600D5BD66AAB706B637A453FD23DDF9611E4C002AC20`
- Static after: 4356 bytes / SHA-256 `3185834A7D4DEAC1595C244DA626FF52B5308E733AFD851E8FF508037C51ED75`
- Only the `x_2` legend-image declaration changed: four 0.08 cm segments separated by three 0.10 cm gaps in a 0.62 cm sample.
- Reconstructed authorized-before identity: exact PASS.
- TeX/build/commit/fresh role/second UID/central write: `0`.

## First error and frozen invocation

- Controller: `P126_R4_STATIC_SEAL_CONTROLLER_20260828.ps1`
- Identity: 11144 bytes / SHA-256 `BA3C40F54EC9B65E8A25F1010FB6523D157EE6142998ABDAE8DFAF042D08A67A` / ReadOnly.
- Invocation/retry: `1/0`.
- Natural exit: `1`.
- First error: line 101 attempted `$dir.IsReadOnly = $true`; the PowerShell directory object exposes no `IsReadOnly` property.
- Failure occurred after all eight existing files were set ReadOnly, before any directory ReadOnly freeze, external marker preparation, marker move, or postseal audit.
- No edit, retry, repair, reseal, rename, removal, or retimestamp was performed after the error.

## Frozen root state

- Root: `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P126-01\STRICT_R4_SA2_STATIC_LEGEND_SEGMENT_PATCH_R115_20260828`
- Ordinary files/bytes: `8 / 7176`
- Files ReadOnly: `8/8`
- Directories including root / ReadOnly: `1 / 0`
- Payload: `6`
- Premarker controls present: `PAYLOAD_MANIFEST.csv`, `SEAL_AUDIT.json`
- Marker/stage/external audit result: absent/absent/absent
- File-only canonical snapshot SHA-256: `B0453C866D5B0D3CA816FF0C423F6257EEA6B4CF5F3941F9049559792D61C7BD`
- `PAYLOAD_MANIFEST.csv`: 914 bytes / SHA-256 `4A80B3D2F355413061C698C91E2949B8EA803D8EF987518C0C8C00F498C6071C`
- `SEAL_AUDIT.json`: 545 bytes / SHA-256 `A4C9E9F7B77E491EF8CFD6B51CD87A9458EA331A0367C02EB1F062C3F72CA098`

## Requested route

Please classify R4 as an unsealed control failure while preserving the static source-content direction. Request one startup-absent evidence-only sibling control reseal authorization. Do not authorize build until that sibling is independently accepted.
