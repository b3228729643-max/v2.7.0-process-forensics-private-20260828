# P654 R14F static preflight

- STATUS: `P654_R14F_STATIC_PREFLIGHT_READY_FOR_MAIN_REVIEW`
- FIGURE_ID: `FIG-P654-01`
- ROLE: SA2
- stage: static only; no R14F draft executed
- future root: `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P654-01\STRICT_R14F_SA2_R10_EVIDENCE_ONLY_CONTROL_RESEAL_20260825`
- future root exists: false
- TeX/source edit/commit/fresh role: 0/0/0/0

## Exact R14E → R14F delta

The three drafts are exact transforms limited to:

1. round/root/draft/future names and unique token `P654_R14F_COPY_SEAL_EXPLICITLY_GRANTED`;
2. validator `Assert-Snapshot` parameters renamed to `GotSnapshot/ExpectedSnapshot/Label` and value locals to `gotValue/expectedValue`;
3. validator `Assert-Equations` parameters renamed to `PayloadSnapshot/ControlSnapshot/OrdinarySnapshot` and value locals to `payloadValue/controlValue/ordinaryValue`.

Seal helpers and all other accepted R14E logic are unchanged.

- prepare exact transform: PASS
- validator exact transform: PASS
- seal exact transform: PASS
- AST parse errors: 0
- command-mode compact-operator lint: 0
- new token: 3/3
- old R14E token: 0
- R14F persisted round: 2/2
- old R14E round: 0
- identity `-DateKind String`: 1
- live-key mutation loops: 0
- draft identity mismatches: 0
- payload/control/ordinary: 1059/3/1062
- JSON: 71/2/73
- CSV: 23/1/24
- per-extension equation mismatches: 0
- static controls: 0

## Frozen identities

| file | bytes | SHA-256 |
|---|---:|---|
| `R14F_prepare_draft.ps1` | 5581 | `EDB222E0ED06CD7A677CB388FE4262DBD81F73CA4FFE7D277171D85F26D77BC1` |
| `R14F_validator_draft.ps1` | 10875 | `71997E3A65D7245EAC5153AB8B3C12308061D00C3DAF9A1ED68B7B35C565CDA9` |
| `R14F_seal_draft.ps1` | 7468 | `C28DAFE416FF609CD685C0765F2DB8D10AAF02B2040DF001AD58B7A9BC9589E2` |
| `R14F_COUNT_MODEL.json` | 3275 | `85A48BB26FA88DADBA85C1B93752FEAC5B99A99E51D4BB3ABDC466A24BBAF79A` |

This report's final bytes/SHA-256 are reported externally after freeze.

## Full-function AST collision audit

Method: for each `FunctionDefinitionAst`, compare parameter variable names with direct `AssignmentStatementAst.Left` variable names using `StringComparer.OrdinalIgnoreCase`. Indexed/member assignments are not treated as direct variable replacement.

Totals:

- functions: 26
- parameters: 47
- direct assignment statements: 34
- collisions: 0

| script | function | params | direct assignments | unique direct LHS | collisions |
|---|---|---:|---:|---:|---:|
| prepare | Get-Rel | 2 | 0 | 0 | 0 |
| prepare | Get-Sha | 1 | 0 | 0 | 0 |
| prepare | Get-Display | 1 | 0 | 0 | 0 |
| seal | Get-Rel | 2 | 0 | 0 | 0 |
| seal | Get-Ext | 1 | 0 | 0 | 0 |
| seal | Get-Snapshot | 1 | 3 | 3 | 0 |
| seal | Add-Ext | 3 | 0 | 0 | 0 |
| seal | Merge-Snapshot | 2 | 2 | 2 | 0 |
| seal | Sum-Snapshot | 1 | 0 | 0 | 0 |
| seal | Assert-Snapshot | 3 | 3 | 3 | 0 |
| seal | Assert-Equations | 3 | 4 | 4 | 0 |
| seal | New-ManifestRows | 1 | 1 | 1 | 0 |
| validator | Get-Rel | 2 | 0 | 0 | 0 |
| validator | Get-Sha | 1 | 0 | 0 | 0 |
| validator | Get-Display | 1 | 0 | 0 | 0 |
| validator | Normalize-Row | 1 | 0 | 0 | 0 |
| validator | Assert-Unique | 3 | 9 | 5 | 0 |
| validator | Assert-Set | 3 | 0 | 0 | 0 |
| validator | Row-Key | 1 | 0 | 0 | 0 |
| validator | Get-Ext | 1 | 0 | 0 | 0 |
| validator | Get-Snapshot | 1 | 3 | 3 | 0 |
| validator | Add-Ext | 3 | 0 | 0 | 0 |
| validator | Merge-Snapshot | 2 | 2 | 2 | 0 |
| validator | Sum-Snapshot | 1 | 0 | 0 | 0 |
| validator | Assert-Snapshot | 3 | 3 | 3 | 0 |
| validator | Assert-Equations | 3 | 4 | 4 | 0 |

## Exact helper-body execution

The following bodies were extracted directly from the R14F validator draft's AST extents and executed without copying or rewriting their locals:

- `Assert-Snapshot`: 477 characters, SHA-256 `8D44289D2DBC3F554BBB221D212EC7155729574E33A9862DADFCE20F0496CB95`
- `Assert-Equations`: 631 characters, SHA-256 `006933B3F0986E0845EB7DA4F17BEC7D1FD65796DE05665A555FE0C80AE927FC`

Actual final-extension dictionaries:

- payload snapshot: PASS
- control snapshot: PASS
- ordinary snapshot: PASS
- payload + control = ordinary: PASS

Synthetic mismatch branches:

- snapshot: `synthetic extension json expected 2 got 1`
- equation: `ordinary != payload + control for json`

Both mismatch branches threw the exact expected errors.

`Normalize-Row` and `Assert-Unique` were likewise extracted directly from the draft AST:

- actual CSV/JSON rows: 1052/1052
- four source/destination uniqueness gates: PASS
- IDictionary duplicate/missing/blank: expected errors
- PSCustomObject unique: PASS
- PSCustomObject duplicate: expected error

## Exact no-write validator remainder

The evaluator used:

- all R14F validator function definitions extracted directly from AST extents;
- the exact R14F top-level statement range from `$csvRows=` through the statement immediately before `$report=`;
- the existing R14C prepared failed root as a read-only fixture;
- no preseal write.

Results:

| gate | result |
|---|---:|
| source base | 1052 |
| target current payload | 1058 |
| target base | 1052 |
| six additions | 6 |
| CSV/JSON rows | 1052/1052 |
| six-field differences | 0 |
| source-set differences | 0 |
| target-set differences | 0 |
| path/bytes/SHA/ticks/display differences | 0 |
| script identity differences | 0 |
| provenance differences | 0 |
| projected payload/control/ordinary | 1059/3/1062 |
| JSON triplet | 71/2/73 |
| CSV triplet | 23/1/24 |
| snapshot differences | 0 |
| per-extension differences | 0 |
| preseal written | false |

## Exact seal-helper projection

`Merge-Snapshot`, `Sum-Snapshot`, `Assert-Snapshot`, and `Assert-Equations` were extracted directly from the R14F seal draft AST.

Actual final dictionaries:

- payload/control/ordinary: 1059/3/1062
- snapshot differences: 0
- equation differences: 0
- collection mutation errors: 0

Synthetic extra-key projection:

- input A: alpha=2, shared=3
- input B: beta=5, shared=7
- output: alpha=2, beta=5, shared=10
- snapshot/equation differences: 0/0
- exact synthetic snapshot/equation mismatch branches: expected errors

## Final verdict

`P654_R14F_STATIC_PREFLIGHT_READY_FOR_MAIN_REVIEW`

R14F is ready only for mainline static review. The future root does not exist and no draft has been executed. A new explicit one-time execution grant is required.

