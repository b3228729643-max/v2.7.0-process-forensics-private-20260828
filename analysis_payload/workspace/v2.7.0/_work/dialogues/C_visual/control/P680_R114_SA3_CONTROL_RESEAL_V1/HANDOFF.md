# P680 R114 SA3 evidence-only control reseal V1 handoff

- HANDOFF_ID: `C-FIG-P680-01-R114-SA3-FRESH-ISOLATED-CONTROL-RESEAL-V1`
- UID: `FIG-P680-01`
- OPERATION: `P680_R114_SA3_EVIDENCE_ONLY_CONTROL_RESEAL_V1`
- VERDICT: `SA3_PASS_AWAIT_MAIN_C_LOCAL_PASS_ACCEPTANCE`
- CONTROL_ONLY: `true`
- UNRESOLVED: `NONE`

## Roots

- Rejected source root: `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\C_visual\evidence\FIG-P680-01\sa3_r114_fresh_isolated_v1`
- Accepted-for-audit sibling root: `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\C_visual\evidence\FIG-P680-01\sa3_r114_fresh_isolated_v1_control_reseal_v1`
- Source root before/after identity mismatch: `0`

## Static controller identities

- Controller: `20,658` bytes; SHA-256 `532D8E3CE601E0995D2168759D4A4629B2637A2E69B9BD7F5CBFA3C4751D27ED`
- Auditor: `15,895` bytes; SHA-256 `0C76E341459635BB04066EB0A1DD2953CF90773D03C984FFC606E8D5B08CFCB8`
- Both: AST errors `0`, delete sites `0`, retry-loop sites `0`, TeX sites `0`, process-management sites `0`, StrictMode sites `1`.
- Controller exact final marker move sites: `1`; auditor move sites: `0`.

## Invocation identities

- Controller: invocation `1`, retry `0`, natural exit `0`, success `true`; result SHA-256 `15E4B8D36D79167DCA5121C9278063D143D49967BE6AFAB5920A7E79DE73CE2A`.
- Auditor: invocation `1`, retry `0`, natural exit `0`, success `true`; result SHA-256 `45CD3D00E8822D66FAED7B4699F8090AD9C2EBE8F056D5FC18280B9C9E223E53`.
- Source-before snapshot SHA-256: `42452AA1FDEE847EB46E13BAB129F95212856F0759F440CFA48FDE7DB7E0D544`.
- Post-marker root-state snapshot SHA-256: `53CB50FD2C37CB59F90FF7E19368C14300FCD3F4FC47D13E7404FCEEB494969C`.

## Copy and seal closure

- Source material / COPY_IDENTITY rows: `37 / 37`; relative path, resolved path, bytes, SHA-256, Creation FILETIME and LastWrite FILETIME mismatches: `0`.
- Payload: `39`; controls: `3`; ordinary files: `42`.
- Payload manifest rows / filesystem payload: `39 / 39`; duplicate, missing, extra, unlisted and identity mismatches: `0`.
- ReadOnly: files `42/42`; directories including root `5/5`.
- WRITE_STOPPED: `12` physical lines, `12` unique keys, bad lines `0`, required-field mismatches `0`, BOM `0`.
- Marker strict-latest margin: `297,278,304` FILETIME ticks; at-or-after excluding marker: `0`.
- Post-marker root-state mismatch: `0`.
- JSON/CSV parse failures, ADS, cache/pyc, reparse: `0 / 0 / 0 / 0 / 0`.

## Immutable root control identities

- `COPY_IDENTITY.csv`: SHA-256 `F2634F946DFE400CA4D9A241F1747779FC1F5B958D59C7A82F7C90F4930AD36F`
- `COPY_PROVENANCE.json`: SHA-256 `B78B61BA1447BF1D7EB490AFBA648EE92DDDEE7C90B87A230D8400575A537985`
- `PAYLOAD_MANIFEST.csv`: SHA-256 `4CC41E1B8BD9E405AF1B72BE5F82867AC927B1C7D6AA4F69B0FEC3874C01426D`
- `SEAL_AUDIT.json`: SHA-256 `8C6E577A862C13C8940324C22F15FC974C974D65043FD4AFE90ACD66AAB4A2FE`
- `WRITE_STOPPED`: SHA-256 `5F0E0F0F1A8DE0E0659E3A31F934B7529FE785FA98FB5F3FCFD1D122A22E6A4D`

No PDF/render/visual/object/pair/manual/math/semantic rerun occurred. No TeX, source, PDF, Git, central state, process-management, second-UID or second-role action occurred. This handoff requests Main's independent root acceptance and does not self-count C_LOCAL/global/final pass.
