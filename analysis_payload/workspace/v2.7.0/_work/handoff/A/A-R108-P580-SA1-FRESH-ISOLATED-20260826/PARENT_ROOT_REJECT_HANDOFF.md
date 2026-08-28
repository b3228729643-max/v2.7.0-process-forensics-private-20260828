# P580 R108 fresh SA1 parent root-reject handoff

Status: `ROOT_REJECT_CONTROL_TIME_TIE_CONTENT_PASS_DIRECTION_PRESERVED`

The fresh SA1 business/content result is PASS-direction (`N=32`, `C=496`, machine and manual R168 hard failures 0), and the 45-payload/48-ordinary manifest and read-only checks close with zero identity mismatch. However, the sealed root fails the explicitly required final-control ordering: `WRITE_STOPPED` and `PAYLOAD_MANIFEST.sha256` both have NTFS ticks `639233406896978700`.

The R2 root remains permanently read-only and was not modified after this discovery. SA3 was not started. Requested main route: accept the content PASS direction but either adjudicate the timestamp tie or authorize exactly one new evidence-only control reseal root with a strictly later `WRITE_STOPPED`.

Parent audit:
`D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\reports\FIG-P580-01\R108_SA1_FRESH_ISOLATED\PARENT_ROOT_AUDIT_REJECT.md`

Sealed evidence root:
`D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P580-01\STRICT_R2_SA1_FRESH_ISOLATED_R108_20260826`
