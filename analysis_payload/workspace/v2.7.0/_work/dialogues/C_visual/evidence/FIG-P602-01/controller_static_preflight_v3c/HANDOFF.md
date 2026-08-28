# P602 controller v3C static handoff

Status: `P602_CONTROLLER_V3C_STATIC_READY_FOR_MAIN_REVIEW`.

- Old v3B remains permanently read-only and is historical `STATIC_REJECT_NO_EXECUTION`.
- v3C was not executed; kpsewhich and all TeX engines remain disabled.
- Future candidate/cache roots do not exist.
- Redirected stdout and stderr are atomically persisted and identity-recomputed before RESULT on all build branches.
- RESULT precedes the sole final build-status throw and distinguishes start-record, runtime, controller, PDF-identity and output-persistence exceptions.
- SUCCESS requires the full compound hard gate, including zero residual TeX processes and recomputable output identities.
- There is one syntactic Process.Start site, one LuaLaTeX build-helper callsite, and no restart/retry branch.
- Main review and a separate explicit grant remain mandatory before execution.

