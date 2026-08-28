# P654 R14E execution rejection

- FIGURE_ID: `FIG-P654-01`
- VERDICT: `EXECUTION_REJECT_R14E_VALIDATOR_TYPED_PARAMETER_COLLISION`
- CENTRAL_ROLE_REQUEST: keep `SA2`
- TeX/source edit/commit/fresh role: 0/0/0/0

## One-time execution ledger

The grant `P654_R14E_COPY_SEAL_EXPLICITLY_GRANTED` was consumed exactly once.

1. A fresh R14E future root was created.
2. Before execution it contained exactly three reviewed scripts; bytes/SHA identity mismatches were 0.
3. `prepare`: invocation 1, PowerShell 7.6.4 `-NoProfile`, exit 0.
4. `validator`: invocation 1, same host and grant, exit 1.
5. `seal`: invocation 0.
6. retry/in-place patch/post-failure root write: 0/0/0.

Prepare output:

```json
{"status":"PREPARED_AWAIT_INDEPENDENT_PRESEAL_VALIDATOR","base_payload":1052,"current_payload":1058,"script_identity_gate":"3_OF_3_BYTES_SHA_PASS"}
```

Validator fatal:

```text
Cannot convert the "1" value of type "System.Int64" to type "System.Collections.IDictionary".
```

The failure occurs at the first `Assert-Snapshot` call on validator line 83, before `R14_PRESEAL_VALIDATION.json` is written.

## Exact read-only root cause

PowerShell variable names are case-insensitive. The validator defines:

```powershell
function Assert-Snapshot(
  [Collections.IDictionary]$G,
  [Collections.IDictionary]$E,
  [string]$L
){
  ...
  $g = ...
  $e = ...
}
```

The local assignments `$g` and `$e` are the same variables as typed parameters `$G` and `$E`. Assigning the first integer extension count to `$g` therefore attempts to replace an `IDictionary`-typed parameter with `Int64`, producing the fatal conversion error. A no-write reproduction against the R14E payload extension dictionary yields the same error with value `1`.

The next validator function has the same latent defect:

```powershell
function Assert-Equations(
  [Collections.IDictionary]$P,
  [Collections.IDictionary]$C,
  [Collections.IDictionary]$O
){
  ...
  $p = ...
  $c = ...
  $o = ...
}
```

A no-write reproduction fails when assigning payload JSON `71` to typed parameter `$P`.

The seal script does not have this exact collision: its typed parameters are `$Got/$Expected` and `$Payload/$Control/$Ordinary`, while locals are `$g/$e` and `$p/$c/$o`.

The accepted R14E static no-write evaluator already used distinct local names and proved that after these assertion helpers, all remaining preseal and seal projection gates are 0-difference. No change was applied to the failed root or frozen R14E static drafts.

## Failed-root facts at stop

- root: `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P654-01\STRICT_R14E_SA2_R10_EVIDENCE_ONLY_CONTROL_RESEAL_20260825`
- ordinary files: 1058
- reviewed scripts: 3
- R10 base payload: 1052
- identity CSV rows: 1052
- identity JSON rows: 1052
- provenance round: R14E
- preseal report: absent
- manifests: absent
- WRITE_STOPPED: absent
- controls: 0
- read-only files: 3
- writable files: 1055
- status: nonsealed failed root; policy write-stopped after validator failure

## Formal decision

`EXECUTION_REJECT_R14E_VALIDATOR_TYPED_PARAMETER_COLLISION`

P654 remains SA2. The failed R14E root must not be modified or rerun. Any continuation requires a fresh static directory, fresh future root, and new explicit mainline scope. No TeX, source modification, commit, fresh SA1/SA3, or A_LOCAL_PASS is authorized.

