# Revision 539 — P126 R17A static acceptance and conditional execution authorization

- Goal authority SHA-256: `4FB8A2B615AC7EDA635D0F8DACACE9CF88692153A049D4A04BE06B56BCB53F1A`
- Inventory remains: `30 SA1 / 30 SA2 / 0 SA3 / 40 local pass`; strict final `0/99`; B `66/66`.
- P689 remains permanently frozen as accepted `C_LOCAL_PASS`.
- P126 remains SA2. This record does not accept a local pass or authorize a commit.

## Frozen package reviewed in full

Main read every line of both new root-external scripts:

1. Controller: `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P126-01\P126_R17A_CONTROL_RESEAL_CONTROLLER_V1_20260828.ps1`
   - 18,655 bytes
   - SHA-256 `96520D7AFC5056B3B7C1D3C5E6C4F7F9CDA11E9AEA6B4B974B6B65318A2F15D7`
   - ReadOnly; PowerShell7 AST errors `0`; invocation `0`.
2. Auditor: `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P126-01\P126_R17A_CONTROL_RESEAL_AUDITOR_V1_20260828.ps1`
   - 24,425 bytes
   - SHA-256 `EB53C90FF836ED085F4ACD07D3F92011831E9910E95CAA04E24C996A28235F9A`
   - ReadOnly; PowerShell7 AST errors `0`; invocation `0`.

Static site recomputation:

- Controller: `[IO.File]::Move` `1` (the staged future marker's sole final root move); `Move-Item=0`, `New-Item=0`, destructive sites `0`, process-management sites `0`, TeX-engine sites `0`.
- Auditor: move/create/destructive/process-management/TeX-engine sites all `0`; all result/report/handoff writes are root-external.
- The former `DirectoryInfo.op_Addition` expression is absent. Each frozen tree function separately materializes root and child arrays, combines them in a separate array statement, and only then filters.

## Main independent no-write checks

- Frozen controller tree function on the real rejected R17 root: `158` items = `147` files + `11` directories including root.
- ADS: `147` streams, nondefault ADS `0`.
- Source snapshot SHA-256: `BDE4D4BC9BD905C681EE7395852405B28F3786CB151380BBE5CD785912EC2943`; frozen auditor independently produced the same snapshot.
- Old rejected manifest: `145` rows. Compared with actual material after excluding only the two rejected top-level controls: missing `0`, extra `0`, canonical duplicates `0`, bytes/SHA/CreationTimeUtc ticks/LastWriteTimeUtc ticks mismatch `0`, control rows `0`.
- StrictMode array merge microtest: empty/scalar/multiple = `0/1/3`; no addition, scalar Count, or empty-filter error.
- Exact in-memory marker expression: `30` physical lines, bad `0`, duplicate keys `0`.
- Frozen auditor ordinal maps: empty/one/two = `0/1/2`; duplicate path rejected.
- Existing R17 hygiene: CSV `5`/parse failures `0`; JSON `7`/parse failures `0`; pyc `0`; `__pycache__` `0`; designated `texcache` `1`; reparse `0`.
- Future destination, staged marker, controller result, auditor result, report and handoff are all absent.

## Conditional execution grant

Authorized external token: `MAIN_R539_P126_R17A_STATIC_ACCEPTED_EXECUTE_ONCE_GRANTED`.

1. Execute the exact frozen controller once, with `invocation=1`, `retry=0`, and first-error stop.
2. Do not run the auditor unless the controller exits naturally with exit `0` and the exact root-external result parses as `success=true` while matching the frozen HANDOFF/operation/script identity, invocation/retry budgets, counts `145/147/3/150/11`, source-before/source-after identity, equal destination snapshots, absent stage, zero ReadOnly failures, positive strict-latest margin, `at-or-after=0`, and `postmarker=0`.
3. Only after that gate, execute the exact frozen auditor once with `invocation=1`, `retry=0`.
4. Any controller, result-gate, or auditor error freezes the scene immediately. No edit, second call, retry, repair, cleanup, continuation, replacement, or reseal is authorized.
5. On dual natural success, return the sealed root plus all root controls and root-external result/report/handoff identities for Main independent acceptance.

Business evidence read/rerun, TeX/build, source editing, Git/commit, central-state writing, fresh role, and second UID are not authorized.
