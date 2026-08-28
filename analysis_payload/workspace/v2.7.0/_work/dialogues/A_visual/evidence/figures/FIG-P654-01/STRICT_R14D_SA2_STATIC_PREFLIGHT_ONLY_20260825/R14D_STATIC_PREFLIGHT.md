# P654 R14D static preflight

- STATUS: `P654_R14D_STATIC_PREFLIGHT_REJECT_REMAINDER_EVALUATOR`
- FIGURE_ID: `FIG-P654-01`
- ROLE: SA2
- stage: static only; no R14D draft executed
- future root: `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P654-01\STRICT_R14D_SA2_R10_EVIDENCE_ONLY_CONTROL_RESEAL_20260825`
- future root exists: false
- TeX/source edit/commit/fresh role: 0/0/0/0

## Authorized R14C → R14D changes

The three R14D drafts are exact R14C transforms limited to:

1. round/root/draft/future names and the unique token `P654_R14D_COPY_SEAL_EXPLICITLY_GRANTED`;
2. `Assert-Unique` explicitly reading `IDictionary` keys or `PSObject` properties, rejecting missing/blank fields, then grouping the extracted real values.

All other validator/prepare/seal logic is unchanged.

Static transform checks:

- prepare exact: PASS
- validator exact: PASS
- seal exact: PASS
- AST errors: 0
- compact command-mode operator lint: 0 for all three scripts
- new R14D token: 3/3
- old R14C token: 0
- R14D persisted round: 2/2
- old R14C persisted round: 0
- count-model draft identity mismatches: 0
- payload/control/ordinary extension sums: 1059/3/1062
- JSON: 71 + 2 = 73
- CSV: 23 + 1 = 24
- per-extension equation mismatches: 0
- static controls: 0

## Frozen identities

| file | bytes | SHA-256 |
|---|---:|---|
| `R14D_prepare_draft.ps1` | 5581 | `E3D8FA322766C2320BC2691660A3350ABF206F09B8082E8A7F4BA235E597B2C5` |
| `R14D_validator_draft.ps1` | 10450 | `81578D18B9C8ADAE7C3845760E139272A49B900158E71B61538BD45C97F6FB67` |
| `R14D_seal_draft.ps1` | 7465 | `313A1216EA2AFF318236E34146F02DCAD307C4F1457F4FBE1F89990FB9E5889A` |
| `R14D_COUNT_MODEL.json` | 3275 | `1BACC08DD3E9C4F77D8DE2041FB144A74CDF80424C4A00A7C258261E1D92D9E1` |

This report's final bytes/SHA-256 are reported externally after freeze to avoid self-reference.

## Assert-Unique no-write tests

Host: PowerShell 7.6.4.

R14C failed-root actual identity data:

- CSV rows: 1052
- JSON rows: 1052
- CSV source uniqueness: PASS
- CSV destination uniqueness: PASS
- JSON source uniqueness: PASS
- JSON destination uniqueness: PASS

Synthetic gates:

- IDictionary duplicate: correctly throws `dict duplicate id`
- IDictionary missing: correctly throws `dict missing or blank id`
- IDictionary blank: correctly throws `dict missing or blank id`
- PSCustomObject unique: PASS
- PSCustomObject duplicate: correctly throws `ps duplicate id`
- PSCustomObject missing: correctly throws `ps missing or blank id`
- PSCustomObject blank: correctly throws `ps missing or blank id`

The authorized `Assert-Unique` change is correct.

## Required no-write remainder evaluator: FAIL

The evaluator used the existing R14C failed root as a read-only prepared fixture and did not write a preseal report.

### Blocker 1 — JSON ISO timestamp auto-conversion

After the four uniqueness gates pass, the unchanged R14C/R14D normalization path fails at the next validator gate:

```text
identity CSV/JSON full-field mismatch at 0
```

PowerShell 7.6.4 `ConvertFrom-Json` automatically converts the ISO `mtime_utc_7digit` string to `DateTime`. The unchanged `Normalize-Row` then interpolates that value using culture display, e.g.:

- CSV: `2026-08-24T23:08:33.6823344Z`
- JSON after default conversion and interpolation: `08/24/2026 23:08:33`

Observed denominators:

- CSV/JSON six-field mismatches: 1052/1052
- JSON display versus source mismatches: 1052/1052

A diagnostic-only, no-write read using `ConvertFrom-Json -DateKind String` yields:

- rows: 1052
- CSV/JSON six-field mismatches: 0
- JSON display versus source mismatches: 0

No such change was written to the R14D draft because it is outside the granted scope.

### Blocker 2 — hashtable mutation during key enumeration

The unchanged `Merge-Snapshot` contains:

```powershell
foreach($key in $out.Keys){
  $out[$key] = ...
}
```

Under `$ErrorActionPreference='Stop'`, PowerShell 7.6.4 raises:

```text
Collection was modified; enumeration operation may not execute.
```

This is a later latent failure after the timestamp gate. A diagnostic-only evaluator that snapshots the keys with `@($out.Keys)` confirms the remainder:

- source base / target base: 1052 / 1052
- target current payload / six additions: 1058 / 6
- script identity differences: 0
- source/target set differences: 0
- missing paths: 0
- bytes/SHA-256/ticks/path differences: 0
- provenance differences: 0
- projected payload/control/ordinary: 1059/3/1062
- payload/control/ordinary snapshot differences: 0/0/0
- per-extension equation differences: 0

The diagnostic workaround was not written to any draft.

## Formal static verdict

`P654_R14D_STATIC_PREFLIGHT_REJECT_REMAINDER_EVALUATOR`

R14D is not READY for execution. The new `Assert-Unique` logic passes, but the required remainder evaluator exposes two unchanged PowerShell 7 blockers outside the authorized edit scope. No R14D future root was created and no draft was executed. Any correction requires a new explicit mainline static scope.

