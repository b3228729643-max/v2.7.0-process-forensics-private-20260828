# P670 replacement V2 evidence-only control reseal: static preflight

- Authorization: `MAIN_R434_P670_CONTENT_ACCEPTED_CONTROL_ROOT_REJECT_SINGLE_RESEAL_AUTHORIZATION`
- Operation: `P670_REPLACEMENT_V2_EVIDENCE_ONLY_CONTROL_RESEAL_V1`
- Controller: `controller/P670_CONTROL_RESEAL_V1.ps1`
  - bytes: `26504`
  - SHA-256: `D2FEF2F6756DA6016F0105BAF7C9C798FE775C1209BE2F33EC9F0F7E518A6581`
  - PowerShell 7 AST errors: `0`
- Auditor: `auditor/P670_CONTROL_RESEAL_AUDITOR_V1.ps1`
  - bytes: `20106`
  - SHA-256: `912FDA0AC32AD31B4A3A4FF6AA6B87AE2573912A492CCCCF483FDF6EB1025ECA`
  - PowerShell 7 AST errors: `0`
- Static lint across both scripts:
  - destructive delete sites: `0`
  - retry/while/do-loop sites: `0`
  - TeX/process-management sites: `0`
- New root immediately before static freeze:
  - Leaf: `false`
  - Container: `false`
  - Any: `false`
  - Parent: `true`
- Runtime artifacts immediately before static freeze:
  - `OLD_ROOT_BEFORE.csv`: absent
  - `WRITE_STOPPED.prepared`: absent
  - `CONTROLLER_RESULT.json`: absent
  - `AUDIT_RESULT.json`: absent

The controller is authorized for exactly one invocation with retry count zero. The auditor is root-external and read-only with respect to both evidence roots.
