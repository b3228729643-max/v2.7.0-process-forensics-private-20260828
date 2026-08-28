# P654 R14E execution test results

- materialized scripts: 3
- reviewed identity mismatches: 0
- host: PowerShell 7.6.4, NoProfile
- prepare invocation/exit: 1/0
- validator invocation/exit: 1/1
- seal invocation: 0
- retry: 0
- first fatal: Int64 1 cannot convert to IDictionary
- failure position: first Assert-Snapshot on validator line 83
- Assert-Snapshot exact no-write reproduction: exit 1, same Int64→IDictionary error
- Assert-Equations exact no-write reproduction: exit 1, Int64 71→IDictionary error
- failed-root ordinary: 1058
- CSV/JSON identity rows: 1052/1052
- preseal/manifests/WSTOP/controls: 0/0/0/0
- TeX/source edit/commit/fresh role: 0/0/0/0
- verdict: `EXECUTION_REJECT_R14E_VALIDATOR_TYPED_PARAMETER_COLLISION`

