# Dialogue A handoff — FIG-P654-01 R14C execution rejection

- HANDOFF_ID: `A-R146-P654-SA2-R14C-EXECUTION-REJECT-20260825`
- STATUS: `EXECUTION_REJECT_R14C_VALIDATOR_EXIT1_CHAIN_STOPPED_READY_FOR_MAIN_ACK`
- FIGURE_ID: `FIG-P654-01`
- CENTRAL_ROLE_REQUEST: keep `SA2`
- SOURCE_SHA256: `EA4A19FF940A177D4D754C4277896A2F38B75C1E6F252D8A374F418B84E31E6D`
- SOURCE_CHANGE_IN_A_BRANCH: pre-existing uncommitted 1+/1- narrow patch; unchanged by R14C
- COMMIT_CREATED: no
- TEX_REQUIRED_FOR_THIS_HANDOFF: no

## Mainline request

Accept the formal R14C execution rejection and keep FIG-P654-01 in SA2. Do not integrate or commit the source patch, create a candidate, run TeX, start fresh SA1/SA3, or count local pass/A_LOCAL_PASS.

The once-only chain was followed exactly:

- three reviewed future scripts materialized with 3/3 bytes/SHA match;
- prepare invocation 1 exited 0 and copied the R10 base;
- validator invocation 1 exited 1 at `identity duplicate source_relative_path`;
- seal invocation 0;
- retry 0 and post-failure writes to the failed root 0.

The generated raw CSV and JSON identity tables each contain 1052 rows and independently have zero duplicate source paths. The validator false-fails because `Normalize-Row` returns an `OrderedDictionary`, while `Group-Object -Property source_relative_path` treats that key as a missing property and creates one empty-name group of 1052 rows.

The failed R14C future root is nonsealed and policy write-stopped. It must not be repaired or rerun in place.

## Evidence

- Failed root: `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P654-01\STRICT_R14C_SA2_R10_EVIDENCE_ONLY_CONTROL_RESEAL_20260825`
- Formal rejection report: `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\reports\P654_R14C_EXECUTION_REJECT.md`
- Report bytes: 4464
- Report SHA-256: `835728F64EB26F04B428516FE23DD225BAFD32AFA18D606AB22104E02C86A40A`

Any continuation needs a new explicit static-preflight scope and a fresh future root. The current failed root, R10, R14/R14B/R14C static roots, source, and execution chain are not authorized for further writes.

