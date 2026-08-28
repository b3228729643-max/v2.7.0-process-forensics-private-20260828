# P654 R14 static preflight — ready for main review

- authority: `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\evidence\main\A_P654_R146_R13_REJECT_R14_STATIC_PREFLIGHT\ROOT_REVIEW.md`
- stage: `STATIC_PREFLIGHT_ONLY_UNEXECUTED`
- preflight directory: `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P654-01\STRICT_R14_SA2_STATIC_PREFLIGHT_ONLY_20260825`
- future sealed root: `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P654-01\STRICT_R14_SA2_R10_EVIDENCE_ONLY_CONTROL_RESEAL_20260825`
- terminal: `P654_R14_STATIC_PREFLIGHT_READY_FOR_MAIN_REVIEW`

## Scope and separation

This directory is a nonsealed review package, not the future R14 evidence root. Its five files are not automatically part of the future payload. No draft was executed; R10 was not copied; no manifest, `WRITE_STOPPED.json`, preseal report or sealed root was created. R10/R11/R12/R13 and the P654 source were not modified, and no TeX process was started.

After a separate explicit mainline grant, the three reviewed drafts would be materialized in the fresh sealed root as `R14_prepare.ps1`, `R14_preseal_validator.ps1` and `R14_seal.ps1`. Together with identity CSV/JSON, resolved provenance JSON and the preseal report JSON, they form exactly seven R14-added payload files over the R10 base 1052, for final payload 1059.

## Forced final count model

| set | files | JSON | CSV | extension-value sum |
|---|---:|---:|---:|---:|
| final payload | 1059 | 71 | 23 | 1059 |
| final controls | 3 | 2 | 1 | 3 |
| final ordinary | 1062 | 73 | 24 | 1062 |

The complete payload/control/ordinary extension maps are in `R14_COUNT_MODEL.json`. Static recomputation gives zero failures across every extension for `ordinary = payload + control` and explicitly closes:

- files: `1059 + 3 = 1062`;
- JSON: `71 + 2 = 73`;
- CSV: `23 + 1 = 24`.

## Self-accounting design

The validator starts from the 1058 payload files that exist before its report. It increments the projected payload JSON snapshot by one for the future `R14_PRESEAL_VALIDATION.json`, then requires payload count 1059, JSON 71 and CSV 23 before writing. After writing, it re-enumerates read-only and requires the actual payload snapshot to equal that projection.

The seal draft starts from the final 1059 payload and writes the two manifests. It snapshots those two existing controls as CSV 1 + JSON 1, then increments control JSON by one for the future `WRITE_STOPPED.json` self. It therefore requires controls CSV 1 + JSON 2 = 3 and derives ordinary JSON 73 / CSV 24 / total 1062 before writing WSTOP.

WSTOP uses only:

- `declared_final_payload_extensions`;
- `declared_final_control_extensions`;
- `declared_final_ordinary_extensions`.

It contains no `actual_*` extension object describing a pre-self filesystem. After WSTOP is written, the draft performs only read-only comparison of those declarations to the final filesystem and writes nothing further under the root.

## Static verification performed

- PowerShell AST parse errors: prepare 0, validator 0, seal 0.
- Count-model sums: payload 1059, controls 3, ordinary 1062.
- Per-extension addition failures: 0.
- Explicit values: payload JSON/CSV 71/23, controls 2/1, ordinary 73/24.
- Seal-draft `actual_` occurrences: 0; `declared_final_` occurrences: 6.
- Validator contains explicit preseal-report payload JSON `+1`.
- Seal contains explicit future-WSTOP control JSON `+1`.
- Generated manifests/WSTOP present in this preflight directory: 0.
- Draft execution count, copy count and seal count: 0.

## Permission boundary and next action

Mainline may review these five static files only. Until a new explicit `P654_R14_COPY_SEAL_SCOPE_GRANTED`-equivalent grant is issued, do not execute any draft, copy R10, create a future sealed root, generate manifests/WSTOP, modify source, start TeX, commit, or dispatch fresh SA1/SA3. P654 remains SA2 and does not count as A_LOCAL_PASS.
