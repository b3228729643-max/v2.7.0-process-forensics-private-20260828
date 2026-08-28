# Dialogue A handoff — FIG-P654-01 R13 root rejection

- HANDOFF_ID: A-R145-P654-SA2-R13-ROOT-REJECT-20260825
- STATUS: ROOT_REJECT_R13_EXTENSION_SNAPSHOT_SELF_ACCOUNTING_REQUIRED_READY_FOR_MAIN_ACK
- FIGURE_ID: FIG-P654-01
- CENTRAL_ROLE_REQUEST: keep SA2
- SOURCE_SHA256: EA4A19FF940A177D4D754C4277896A2F38B75C1E6F252D8A374F418B84E31E6D
- SOURCE_CHANGE_IN_A_BRANCH: one uncommitted 1+/1- narrow patch; forbidden to integrate from this rejected handoff
- COMMIT_CREATED: no
- TEX_REQUIRED_FOR_THIS_HANDOFF: no

## Mainline request

Record the fresh independent R13 root rejection and keep FIG-P654-01 in SA2. Do not integrate or commit the source patch, create an official candidate, start fresh SA1/SA3, or count local pass/A_LOCAL_PASS.

R13 correctly rebuilt the R10 base and repaired R12's total ordinary count and mixed-scope denominator naming. It remains rejected because both terminal declaration files omit their own final JSON files from the three extension snapshots:

- payload JSON is declared 70 but is 71 because `R13_PRESEAL_VALIDATION.json` is itself final payload;
- control JSON is declared 1 but is 2 because `WRITE_STOPPED.json` is itself a final control;
- ordinary JSON is declared 72 but is 73.

These three differences appear in both the preseal expected objects and the WSTOP actual objects. Correct file totals cannot substitute for incorrect per-extension snapshots. The sealed R13 root is permanently read-only and must not be patched in place.

## Evidence

- Sealed R13 package: `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P654-01\STRICT_R13_SA2_R10_EVIDENCE_ONLY_CONTROL_RESEAL_20260825`
- Independent root report: `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\reports\P654_R13_ROOT_AUDIT.md`
- Root report SHA-256: `F92555C0BED0039A55E99D50A30BA43EFE85F67D574D85A9CCA4B0E6824EF5E7`

The rejection is confined to self-accounting in the R13 extension snapshots. R10→R13 base identity, manifests, resolved provenance, parsing, per-file ADS, cache, read-only/seal order and differential content evidence otherwise passed independently, but those facts do not authorize integration from a rejected root.
