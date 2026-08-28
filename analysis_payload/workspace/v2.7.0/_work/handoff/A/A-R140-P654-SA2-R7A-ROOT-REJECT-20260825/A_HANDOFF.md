# Dialogue A handoff — FIG-P654-01 R7A root rejection

- HANDOFF_ID: A-R140-P654-SA2-R7A-ROOT-REJECT-20260825
- STATUS: ROOT_REJECT_R7A_FAIL_TO_SA2_CONTINUE_READY_FOR_MAIN_ACK
- FIGURE_ID: FIG-P654-01
- CENTRAL_ROLE_REQUEST: keep SA2
- SOURCE_SHA256: EA4A19FF940A177D4D754C4277896A2F38B75C1E6F252D8A374F418B84E31E6D
- SOURCE_CHANGE_IN_A_BRANCH: one uncommitted 1+/1- narrow patch; forbidden to integrate from this handoff
- COMMIT_CREATED: no
- TEX_REQUIRED_FOR_THIS_HANDOFF: no

## Mainline request

Record the independent R7A root rejection and keep FIG-P654-01 in SA2. Do not integrate or commit the current source, do not start fresh SA1/SA3, and do not count local pass or A_LOCAL_PASS.

Any further source repair or evidence build requires explicit mainline single-writer scope and a separately granted TeX slot.

## Evidence

- Sealed R7A package: D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P654-01\STRICT_R7A_SA2_NARROW_R100_EVIDENCE_RESEAL_20260825
- Independent root report: D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\reports\P654_R7A_ROOT_AUDIT.md
- Root report SHA-256: 3CCE18AD5596C502DD4F0B8F757EE8C654D3405CCEA36F11DA00B86F275079D8

The sealed R7A root is permanently read-only. Its machine/manual/seal facts remain auditable, but its local verification conclusion is rejected by the strict D/E hard gate.
