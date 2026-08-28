# Dialogue A handoff — FIG-P654-01 R12 root rejection

- HANDOFF_ID: A-R141-P654-SA2-R12-ROOT-REJECT-20260825
- STATUS: ROOT_REJECT_R12_CONTROL_DECLARATION_RESEAL_REQUIRED_READY_FOR_MAIN_ACK
- FIGURE_ID: FIG-P654-01
- CENTRAL_ROLE_REQUEST: keep SA2
- SOURCE_SHA256: EA4A19FF940A177D4D754C4277896A2F38B75C1E6F252D8A374F418B84E31E6D
- SOURCE_CHANGE_IN_A_BRANCH: one uncommitted 1+/1- narrow patch; forbidden to integrate from this rejected handoff
- COMMIT_CREATED: no
- TEX_REQUIRED_FOR_THIS_HANDOFF: no

## Mainline request

Record the fresh independent R12 root rejection and keep FIG-P654-01 in SA2. Do not integrate or commit the current source, start fresh SA1/SA3, or count local pass/A_LOCAL_PASS.

R12 correctly rebuilt directly from the R10 base and closes the R11 provenance and terminal JSON/CSV-count defects. The root nevertheless remains rejected because two newly generated declarations are not self-consistent:

1. `WRITE_STOPPED.json` declares `ordinary_file_count=1059`, while the sealed filesystem contains 1062 ordinary files: 1059 payload plus 3 controls.
2. `R12_PRESEAL_VALIDATION.json.ordinary_extension_denominator` mixes collection scopes. Its JSON value 71 is the payload count, while its CSV value 24 is the ordinary count; actual ordinary JSON/CSV counts are 73/24 and payload counts are 71/23.

The sealed R12 root is permanently read-only and must not be patched in place. Any correction requires a newly authorized evidence-only control reseal followed by another fresh independent root audit. No TeX or source change is needed for that correction.

## Evidence

- Sealed R12 package: `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P654-01\STRICT_R12_SA2_R10_EVIDENCE_ONLY_CONTROL_RESEAL_20260825`
- Independent root report: `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\reports\P654_R12_ROOT_AUDIT.md`
- Root report SHA-256: `15C9104BAD871CD15CE0A5E14DAAABFC2452F8A6D6CDFB1DF6E9FDFBF8861C08`

The rejection is confined to the R12 terminal/preseal declaration layer. It does not overturn the independently closed R10→R12 1052-file identity, the 1059-entry manifests, or the content-layer evidence, but those passed facts cannot authorize integration from a rejected root.
