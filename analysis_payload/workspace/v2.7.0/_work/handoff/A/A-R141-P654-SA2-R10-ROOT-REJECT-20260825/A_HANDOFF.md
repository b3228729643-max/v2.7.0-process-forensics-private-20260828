# Dialogue A handoff — FIG-P654-01 R10 root rejection

- HANDOFF_ID: A-R141-P654-SA2-R10-ROOT-REJECT-20260825
- STATUS: ROOT_REJECT_R10_EVIDENCE_RESEAL_REQUIRED_READY_FOR_MAIN_ACK
- FIGURE_ID: FIG-P654-01
- CENTRAL_ROLE_REQUEST: keep SA2
- SOURCE_SHA256: EA4A19FF940A177D4D754C4277896A2F38B75C1E6F252D8A374F418B84E31E6D
- SOURCE_CHANGE_IN_A_BRANCH: one uncommitted 1+/1- narrow patch; forbidden to integrate from this rejected handoff
- COMMIT_CREATED: no
- TEX_REQUIRED_FOR_THIS_HANDOFF: no

## Mainline request

Record the independent R10 root rejection and keep FIG-P654-01 in SA2. Do not integrate or commit the current source, do not start fresh SA1/SA3, and do not count local pass or A_LOCAL_PASS.

The only deciding defect is evidence-seal metadata precision: the payload manifests serialize mtime to six fractional digits and therefore do not preserve the sealed NTFS 100 ns file times exactly. Any correction must use a new evidence-reseal root and a manifest format that losslessly records and read-backs the original file times, or a precision rule explicitly approved before resealing. The sealed R10 root must not be modified.

No TeX or source change is needed for the mechanical reseal itself. A new reseal attempt requires explicit mainline authorization and must remain evidence-only.

## Evidence

- Sealed R10 package: D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P654-01\STRICT_R10_SA2_TAXONOMY_R100_DIRECT_BUILD_20260825
- Independent root report: D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\reports\P654_R10_ROOT_AUDIT.md
- Root report SHA-256: B1460FC9416C21471FA005DE6F23645C7C34BA384CF3C1578993B19A140C7727

The sealed R10 root is permanently read-only. Its build, PDF, machine, taxonomy, manual and seal-order facts remain auditable, but the root package is rejected because its file-level mtime identity is not exact.
