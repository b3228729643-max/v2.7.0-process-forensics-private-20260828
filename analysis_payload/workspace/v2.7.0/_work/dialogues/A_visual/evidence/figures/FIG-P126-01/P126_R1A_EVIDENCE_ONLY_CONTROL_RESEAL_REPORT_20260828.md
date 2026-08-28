# P126 R1A evidence-only control reseal report

HANDOFF_ID: `A-R115-P126-SA2-R168-READONLY-CONTROL-RESEAL-V1-20260828`

Operation: `P126_R115_SA2_EVIDENCE_ONLY_CONTROL_RESEAL_V1`

Status: `AUDIT_PASS_EVIDENCE_ONLY_CONTROL_RESEAL_AWAIT_MAIN_ACCEPTANCE`

Preserved substantive result: `FAIL_TO_MAIN_SOURCE_SCOPE`. This operation did not read or rerun PDF, rendering, visual, denominator, pair, manual, mathematical, semantic, or page evidence. It did not activate source scope or modify source.

## Invocation record

- Frozen V2 controller: 26,109 bytes; SHA-256 `899F9491F1C8FCCFECF0AF72922B3AEF434E2B9CC11605CA22F70AE8A04D6B7E`; invocation=1; retry=0; natural exit=0.
- Controller UTC: `2026-08-27T23:51:25.3664549Z` to `2026-08-27T23:51:27.5321604Z`.
- Frozen V2 auditor: 21,071 bytes; SHA-256 `948D6BA8247D06FADF35208CBFADCF2A693414D90950E09FE1EE4159A2BEE760`; invocation=1; retry=0; natural exit=0.
- Auditor UTC: `2026-08-27T23:51:38.0154320Z` to `2026-08-27T23:51:38.8360720Z`.
- V1 scripts remained frozen and were never invoked.

## Root and count model

- Source rejected root: `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P126-01\STRICT_R1_SA2_R168_READONLY_R115_20260828`
- Accepted-for-review sibling root: `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P126-01\STRICT_R1A_SA2_R168_READONLY_R115_EVIDENCE_ONLY_CONTROL_RESEAL_20260828`
- Source material copied: 52.
- Added payload: `COPY_IDENTITY.csv` and `COPY_PROVENANCE.md`.
- Payload: 54; controls: 3; ordinary files: 57; ordinary bytes: 2,485,105.
- Directories including root: 5.
- ReadOnly: files 57/57; directories 5/5.

## Identity closure

- Source-to-destination relative path, bytes, SHA-256, CreationTimeUtc ticks, and LastWriteTimeUtc ticks mismatches: 0.
- Payload manifest rows: 54; duplicate, missing, extra, identity, and canonical set differences: 0.
- Canonicalization: all manifest relative paths use forward slashes; the source manifest contained 40 backslash-path rows and canonicalized without duplicates or set differences.
- `COPY_IDENTITY.csv`: 10,085 bytes; SHA-256 `52C7CF4E559EC06EC7C8DA83F6E0C91120A4AA58661F3CF0248DF379F205AFA8`.
- `COPY_PROVENANCE.md`: 1,772 bytes; SHA-256 `49F2FC489459F3FCDD53F0F5E7DFF72FD50732BF6DE8EABEEAA9544E9737D57D`.
- `PAYLOAD_MANIFEST.csv`: 8,002 bytes; SHA-256 `14D0952FFC1F516B01915F7125B67F97EAD995FA444C4709337B4ACF11B5112E`.
- `SEAL_AUDIT.json`: 1,978 bytes; SHA-256 `FE071C4F5AE04C9527874567C33D254B32FB9165E65D2EB80B2B20C0BC81686D`.

## Marker and postmarker audit

- `WRITE_STOPPED`: 1,498 bytes; SHA-256 `193C1AF2BCF9378A3515A95917DACE4332532A4A5471F723AEA234D27741E89C`.
- Marker physical lines: 25; unique keys: 25; invalid or duplicate lines: 0.
- Marker LastWriteTimeUtc ticks: `639234720872913339`.
- Strict-latest margin including all nonmarker files, directories, and root: `5999607739` ticks.
- Items at or after marker excluding marker: 0.
- Postmarker root content or attribute writes: 0.
- Destination postmarker snapshot SHA-256: `839C5438C2EB538A133A56704BD31B68946280D712C32FC5478B5964E8153379`.
- Source root before/after snapshot SHA-256: `436F4108CB92A2EC2719BAB141786C49A8703066253C003CEFC56D654D036B14`; difference: 0.
- JSON parse failures: 0; CSV parse failures: 0; ADS: 0; cache/pyc: 0; reparse points: 0.

## Root-external results

- Controller result: 2,476 bytes; SHA-256 `2EC78DA3ABDEA7BE3891DD41090669E1ADEB4D33DB8BC3F471AEEE7C966AC30E`.
- Auditor result: 2,394 bytes; SHA-256 `79B53259244090A5746F562948C83B349ADA4B87E341FF8A27FFB2357768ED4F`.

P126 remains SA2. This report requests Main acceptance of the R1A control reseal only; it does not activate a source patch, build, fresh role, inventory transition, local pass, global pass, or final pass.
