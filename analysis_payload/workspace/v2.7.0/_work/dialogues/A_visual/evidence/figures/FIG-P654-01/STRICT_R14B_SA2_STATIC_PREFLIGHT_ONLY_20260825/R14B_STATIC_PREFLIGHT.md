# P654 R14B static preflight — ready for main review

- stage: `STATIC_PREFLIGHT_ONLY_UNEXECUTED`
- directory: `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P654-01\STRICT_R14B_SA2_STATIC_PREFLIGHT_ONLY_20260825`
- prior R14 static directory: frozen read-only, 5/5 files read-only
- future sealed root: absent
- terminal: `P654_R14B_STATIC_PREFLIGHT_READY_FOR_MAIN_REVIEW`

## Scope

R14B changes only the two static defects rejected by mainline. No draft was executed, R10 was not copied, and no manifest, preseal report, `WRITE_STOPPED.json`, future sealed root, source edit, TeX process, commit or fresh role was created.

## Reviewed draft byte binding

`R14B_COUNT_MODEL.json` freezes the exact reviewed draft identities and their future materialized names:

| reviewed draft | future script | bytes | SHA-256 |
|---|---|---:|---|
| `R14B_prepare_draft.ps1` | `R14_prepare.ps1` | 5570 | `8F2F87FB86AD4DBA56E81F3370FAD0D871616B348B9466F4265A731BA8018578` |
| `R14B_validator_draft.ps1` | `R14_preseal_validator.ps1` | 10010 | `549D2EBF28D77788CF3683512178BFBD592F6903B29FBD77A46ABC7C0EFB7F04` |
| `R14B_seal_draft.ps1` | `R14_seal.ps1` | 7463 | `089DE87EA6B1BFD5D9A81E64F0B84C2F4EF694B359BBA164140FA3AC873C29D1` |

The prepare draft requires the fresh future target to contain exactly those three future names and verifies each file's bytes and SHA-256 against the reviewed model before the first `Copy-Item`. Static ordering confirms Gate 0 precedes the first copy. The validator repeats the same three identity checks after preparation, detecting replacement between the prepare and validator phases.

## Independent CSV/JSON identity proof

The validator treats `R14_BASE_COPY_IDENTITY.csv` and `.json` as independent inputs and requires:

1. 1052 rows in each table;
2. unique source and destination relative paths in each table;
3. `source_relative_path == destination_relative_path` on every row;
4. CSV and JSON equality across all six fields: source path, destination path, bytes, SHA-256, ticks string and 7-digit UTC display;
5. each table's path set exactly equals the independently enumerated R10 base 1052 path set;
6. the future target pre-report payload is exactly 1058 files: six named R14 additions plus a 1052-file base whose path set exactly equals R10;
7. for every base path, actual R10 source and future target destination bytes/SHA/ticks/display equal each other and equal both normalized table rows;
8. missing, extra and duplicate paths are zero.

The pre-report six-file exclusion is fixed to the three materialized scripts, both identity tables and resolved provenance. It cannot hide any other target file.

## Preserved final count model

| set | files | JSON | CSV | extension sum |
|---|---:|---:|---:|---:|
| final payload | 1059 | 71 | 23 | 1059 |
| final controls | 3 | 2 | 1 | 3 |
| final ordinary | 1062 | 73 | 24 | 1062 |

All extension equations independently satisfy `ordinary = payload + control`; failures are 0. Validator still adds the future preseal report as payload JSON +1, seal still adds future WSTOP as control JSON +1, and WSTOP uses only `declared_final_*` extension objects.

## Static verification

- three PowerShell drafts: AST parse errors 0/0/0;
- all three reviewed identity bytes and SHA matches: true;
- prepare script identity gate occurs before first copy: true;
- validator CSV↔JSON all-field comparison present: true;
- independent uniqueness checks applied to both tables: 2;
- both table path sets checked against source: true;
- target base path set checked against source: true;
- per-file source/destination/two-table comparison: true;
- payload/control/ordinary extension sums: 1059/3/1062;
- per-extension equation failures: 0;
- explicit JSON/CSV values: true;
- validator report-self JSON +1 / seal WSTOP-self JSON +1: true/true;
- seal `actual_` occurrences: 0; `declared_final_` occurrences: 6;
- manifests/WSTOP in R14B: 0; future sealed root absent.

## Next action

Only mainline may perform the next read-only review. Until a new explicit copy/seal grant is issued, do not execute drafts, materialize scripts, copy R10, create the future root, generate controls, modify source, start TeX, commit or dispatch fresh SA1/SA3. P654 remains SA2.
