# Dialogue A handoff — FIG-P654-01 R14E execution rejection

- HANDOFF_ID: `A-R146-P654-SA2-R14E-EXECUTION-REJECT-20260825`
- STATUS: `EXECUTION_REJECT_R14E_VALIDATOR_TYPED_PARAMETER_COLLISION_READY_FOR_MAIN_ACK`
- FIGURE_ID: `FIG-P654-01`
- CENTRAL_ROLE_REQUEST: keep `SA2`
- SOURCE_SHA256: `EA4A19FF940A177D4D754C4277896A2F38B75C1E6F252D8A374F418B84E31E6D`
- COMMIT_CREATED: no
- TEX_REQUIRED: no

## Mainline request

Accept the formal R14E execution rejection and keep P654 in SA2.

The one-time chain complied with the grant: 3/3 script identity binding passed; prepare invocation 1 exited 0; validator invocation 1 exited 1; seal invocation 0; retry 0.

The root cause is PowerShell's case-insensitive variable binding inside validator assertion helpers:

- typed parameters `$G/$E` are overwritten by integer locals `$g/$e` in `Assert-Snapshot`;
- typed parameters `$P/$C/$O` would be overwritten by integer locals `$p/$c/$o` in `Assert-Equations`.

The first conversion fails before the preseal report write. The failed future root remains nonsealed and policy write-stopped; it must not be patched or rerun.

## Evidence

- failed root: `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P654-01\STRICT_R14E_SA2_R10_EVIDENCE_ONLY_CONTROL_RESEAL_20260825`
- report: `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\reports\P654_R14E_EXECUTION_REJECT.md`
- report bytes: 3378
- report SHA-256: `C04AC7C87054AFC8A352F0DF513B0D629B8D2BA8D3BD1022883BC78658117D79`

No new static or execution round is requested automatically. Any continuation requires explicit mainline authorization.

