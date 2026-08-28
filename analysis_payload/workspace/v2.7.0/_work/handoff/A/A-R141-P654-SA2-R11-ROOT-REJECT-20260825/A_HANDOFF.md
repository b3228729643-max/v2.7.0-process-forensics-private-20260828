# Dialogue A handoff — FIG-P654-01 R11 root rejection

- HANDOFF_ID: A-R141-P654-SA2-R11-ROOT-REJECT-20260825
- STATUS: ROOT_REJECT_R11_EVIDENCE_CONTROL_RESEAL_REQUIRED_READY_FOR_MAIN_ACK
- FIGURE_ID: FIG-P654-01
- CENTRAL_ROLE_REQUEST: keep SA2
- SOURCE_SHA256: EA4A19FF940A177D4D754C4277896A2F38B75C1E6F252D8A374F418B84E31E6D
- SOURCE_CHANGE_IN_A_BRANCH: one uncommitted 1+/1- narrow patch; forbidden to integrate from this rejected handoff
- COMMIT_CREATED: no
- TEX_REQUIRED_FOR_THIS_HANDOFF: no

## Mainline request

Record the independent R11 root rejection and keep FIG-P654-01 in SA2. Do not integrate or commit the current source, do not start fresh SA1/SA3, and do not count local pass or A_LOCAL_PASS.

R11 successfully closes the R10 metadata defect: its 1052 copied base payload files are exactly identical to R10 by source/destination relative path, bytes, SHA-256 and NTFS LastWriteTimeUtc ticks, and its 1057 payload manifest is exactly identical to the current R11 filesystem by path, bytes, SHA-256 and decimal-string ticks. The root nevertheless remains rejected because two newly introduced control declarations are not self-consistent:

1. `R11_COPY_PROVENANCE.md` records `Source: $src` and `Target: $dst` as literal placeholders instead of the resolved R10/R11 roots.
2. `WRITE_STOPPED.json` records `json_excluding_write_stopped=69`, while the current root contains 71 JSON files and therefore 70 after excluding only `WRITE_STOPPED.json`; 69 is the payload-JSON count after also excluding `PAYLOAD_MANIFEST.json`.

The sealed R11 root must remain permanently read-only. Any correction requires a newly authorized evidence-only reseal root followed by another fresh independent root audit. No TeX or source change is needed for that correction.

## Evidence

- Sealed R11 package: `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P654-01\STRICT_R11_SA2_R10_EVIDENCE_ONLY_LOSSLESS_TICKS_RESEAL_20260825`
- Independent root report: `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\reports\P654_R11_ROOT_AUDIT.md`
- Root report SHA-256: `E07BFE7C2DB70E714A6E56CE9D0045BCA84144EBBEB6B8319C4ECA05BFCA9040`
- Report canonical-self SHA-256: `5D1943F971AC5FC469781D658C936F8821D556E4FB7BA9EF9D0CFC21C2030ED4`

The rejection is confined to the new provenance/terminal-control layer. It does not overturn the independently closed 1052-file lossless identity or the R10 content gates, but those facts do not authorize source integration from a rejected root.
