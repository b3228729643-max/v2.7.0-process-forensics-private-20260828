# P654 R14C execution rejection

- FIGURE_ID: `FIG-P654-01`
- VERDICT: `EXECUTION_REJECT_R14C_VALIDATOR_EXIT1_CHAIN_STOPPED`
- CENTRAL_ROLE_REQUEST: keep `SA2`
- TeX: not started
- source modified in this stage: no
- commit created: no
- fresh SA1/SA3: not started

## Authorized chain ledger

The mainline grant `P654_R14C_COPY_SEAL_EXPLICITLY_GRANTED` was consumed once.

1. A fresh future root was created at `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P654-01\STRICT_R14C_SA2_R10_EVIDENCE_ONLY_CONTROL_RESEAL_20260825`.
2. Before execution it contained exactly the three reviewed future scripts:
   - `R14C_prepare.ps1`: 5581 bytes, SHA-256 `69029D0736396CA19AD19E1FF5526A8ED426A48777C0288E0C8EC519C1FEB73B`
   - `R14C_preseal_validator.ps1`: 10023 bytes, SHA-256 `43784C57CE01AE83597B5F043923241AEFB8336C901D11A8BC93116C290B1D0E`
   - `R14C_seal.ps1`: 7465 bytes, SHA-256 `20A99AB090A0C14409B014DC2E30B4AAD6BFB2F9C35444B0B0D6585EA11EB803`
   Identity mismatches: 0.
3. `prepare`: invocation 1, `D:\PowerShell7\pwsh.exe -NoProfile`, exit 0. Output:
   `{"status":"PREPARED_AWAIT_INDEPENDENT_PRESEAL_VALIDATOR","base_payload":1052,"current_payload":1058,"script_identity_gate":"3_OF_3_BYTES_SHA_PASS"}`
4. `validator`: invocation 1, same PowerShell 7 host and grant, exit 1.
5. `seal`: invocation 0. It was not started after validator failure.
6. No retry, in-place patch, TeX, source edit, commit, manifest generation, WSTOP generation, or fresh role was performed.

The execution chain stopped immediately at the validator failure as required.

## Exact failure

The first fatal is at `R14C_preseal_validator.ps1:22`:

```text
identity duplicate source_relative_path
```

The failing function is:

```powershell
function Assert-Unique([object[]]$Rows,[string]$Field,[string]$Label){
  if(@($Rows|Group-Object -Property $Field|Where-Object { $_.Count -ne 1 }).Count-ne0){
    throw "$Label duplicate $Field"
  }
}
```

## Read-only root-cause audit

The failure is not a duplicate in the generated identity data.

- `R14_BASE_COPY_IDENTITY.json`: 1052 rows, duplicate `source_relative_path` groups 0.
- `R14_BASE_COPY_IDENTITY.csv`: 1052 rows, duplicate `source_relative_path` groups 0.
- Both tables expose the same six fields:
  `source_relative_path`, `destination_relative_path`, `bytes`, `sha256`, `mtime_utc_ticks`, `mtime_utc_7digit`.

The validator first maps every row through `Normalize-Row`, which returns `[ordered]@{...}`, i.e. `System.Collections.Specialized.OrderedDictionary`. In PowerShell 7, the current `Group-Object -Property source_relative_path` over those normalized dictionaries does not resolve the dictionary key as a property. The independent read-only reproduction yields:

- normalized row type: `System.Collections.Specialized.OrderedDictionary`
- group count: 1
- first group name: empty
- first group count: 1052
- nonunique groups: 1

Therefore the validator raises a false duplicate before the remaining identity/set/count gates. A future correction must be statically reviewed in a new directory and use a grouping/access form that explicitly reads dictionary keys, or normalize to objects whose fields are actual properties. This failed future root must not be repaired or rerun in place.

## Failed-root facts at stop

- ordinary files: 1058
- reviewed scripts: 3
- R10 base payload copied: 1052
- identity CSV/JSON: present, 1052 rows each
- resolved provenance: present
- preseal report: absent
- payload manifests: absent
- WRITE_STOPPED: absent
- controls present: 0
- read-only files: 3
- writable files: 1055
- root status: nonsealed failed root; policy write-stopped after validator failure

The root was only read after the failure. It was not modified, patched, retried, or passed to seal.

## Source boundary

The only pre-existing P654 source diff remains unchanged:

- source: `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\worktrees\dialogue_A_visual\src\绘图源码\第05册_采样方法主题模型与图排序\V5-C05\fig_v5_c05_dependency_graph.tex`
- bytes: 3122
- SHA-256: `EA4A19FF940A177D4D754C4277896A2F38B75C1E6F252D8A374F418B84E31E6D`
- commit: none

## Formal decision

`EXECUTION_REJECT_R14C_VALIDATOR_EXIT1_CHAIN_STOPPED`

P654 remains SA2. This rejection does not authorize a new static round, a new future root, execution, source modification, TeX, commit, fresh SA1/SA3, or A_LOCAL_PASS. Any continuation requires a new explicit mainline scope.

