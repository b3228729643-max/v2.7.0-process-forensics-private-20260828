# P654 R14E static preflight

- STATUS: `P654_R14E_STATIC_PREFLIGHT_READY_FOR_MAIN_REVIEW`
- FIGURE_ID: `FIG-P654-01`
- ROLE: SA2
- stage: static only; no R14E draft executed
- future root: `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P654-01\STRICT_R14E_SA2_R10_EVIDENCE_ONLY_CONTROL_RESEAL_20260825`
- future root exists: false
- TeX/source edit/commit/fresh role: 0/0/0/0

## Authorized R14D → R14E delta

The three R14E drafts are exact R14D transforms limited to:

1. round/root/draft/future names and unique token `P654_R14E_COPY_SEAL_EXPLICITLY_GRANTED`;
2. the identity-JSON read uses `ConvertFrom-Json -DateKind String` exactly once;
3. validator and seal `Merge-Snapshot` each enumerate a frozen key snapshot before assigning values.

All other logic is unchanged.

Static identity and syntax gates:

- prepare exact transform: PASS
- validator exact transform: PASS
- seal exact transform: PASS
- AST errors: 0
- command-mode compact-operator lint: 0 for all three scripts
- new R14E token: 3/3
- old R14D token: 0
- R14E persisted round: 2/2
- old R14D persisted round: 0
- identity JSON `-DateKind String` occurrences: 1
- validator frozen-key merge occurrences: 1
- seal frozen-key merge occurrences: 1
- live-key mutation loops: 0
- count-model draft identity mismatches: 0
- payload/control/ordinary extension sums: 1059/3/1062
- JSON: 71 + 2 = 73
- CSV: 23 + 1 = 24
- per-extension equation mismatches: 0
- static controls: 0

## Frozen identities

| file | bytes | SHA-256 |
|---|---:|---|
| `R14E_prepare_draft.ps1` | 5581 | `7D747804413C10DBFD2C48F2D02787B77F4C8340A6C850829BAF8499F6BC03EA` |
| `R14E_validator_draft.ps1` | 10470 | `981106E2D0B9012697957D35967ABBC1DEF9A9F4F558E10783E11A5947B9EEBD` |
| `R14E_seal_draft.ps1` | 7468 | `AB57BAAC84A477A3FBFCE611988E6F44C249DABF3646FB548D1E041018D93A95` |
| `R14E_COUNT_MODEL.json` | 3275 | `C912F162BA031E0218A660DFCB93B7CCFA8A13DD9B75473EC942D7127F2147A7` |

This report's final bytes/SHA-256 are reported externally after freeze to avoid self-reference.

## Assert-Unique actual and synthetic tests

Host: PowerShell 7.6.4.

R14C failed-root prepared fixture:

- CSV rows: 1052
- JSON rows: 1052
- CSV source uniqueness: PASS
- CSV destination uniqueness: PASS
- JSON source uniqueness: PASS
- JSON destination uniqueness: PASS
- IDictionary duplicate: throws expected duplicate error
- IDictionary missing: throws expected missing/blank error
- IDictionary blank: throws expected missing/blank error
- PSCustomObject unique: PASS
- PSCustomObject duplicate: throws expected duplicate error

## Full no-write validator remainder

The evaluator used the existing R14C failed root as a read-only prepared fixture and stopped before writing a preseal report.

| gate | result |
|---|---:|
| source base | 1052 |
| current target payload | 1058 |
| target base | 1052 |
| six pre-report additions | 6 |
| script identity differences | 0 |
| CSV rows | 1052 |
| JSON rows | 1052 |
| CSV/JSON six-field differences | 0 |
| CSV vs source set differences | 0 |
| JSON vs source set differences | 0 |
| six-addition set differences | 0 |
| source vs target-base set differences | 0 |
| missing paths | 0 |
| bytes differences | 0 |
| SHA-256 differences | 0 |
| NTFS ticks differences | 0 |
| seven-digit display differences | 0 |
| table path differences | 0 |
| provenance differences | 0 |
| projected payload/control/ordinary | 1059/3/1062 |
| payload/control/ordinary snapshot differences | 0/0/0 |
| per-extension equation differences | 0 |
| preseal report written | false |

## Validator and seal merge projections

Both corrected `Merge-Snapshot` implementations were independently exercised without file writes.

Actual final-extension dictionaries:

- payload sum: 1059
- control sum: 3
- validator ordinary sum: 1062
- seal ordinary sum: 1062
- validator actual snapshot differences: 0
- seal actual snapshot differences: 0
- validator per-extension equation differences: 0
- seal per-extension equation differences: 0

Synthetic extra-key case:

- A: `alpha=2, shared=3`
- B: `beta=5, shared=7`
- validator output: `alpha=2, beta=5, shared=10`
- seal output: `alpha=2, beta=5, shared=10`
- validator synthetic differences: 0
- seal synthetic differences: 0
- collection-mutation errors: 0

## Final static verdict

`P654_R14E_STATIC_PREFLIGHT_READY_FOR_MAIN_REVIEW`

R14E is static-ready for mainline review only. No future root exists and no prepare/validator/seal draft has been executed. A new explicit mainline grant is required before any materialization or execution.

