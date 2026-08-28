# FIG-P582-01 R110 R7A handoff

Verdict: `ROOT_ACCEPT_R7A_SA1_CONTENT_PASS_READY_FOR_FRESH_ISOLATED_SA3`.

One authorized PowerShell 7 controller invocation completed with exit 0 and no retry. It copied exactly the 140 R7 manifest-bound material files, copied none of R7's three old controls, and added only `COPY_IDENTITY.csv` and `COPY_PROVENANCE.json` as payload.

Final R7A root:

`D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P582-01\STRICT_R7A_SA1_R110_EVIDENCE_ONLY_CONTROL_RESEAL_20260827`

Final gates:

- source-to-destination path/bytes/SHA/NTFS ticks mismatch: 0;
- payload/control/ordinary: 142 / 3 / 145;
- manifest rows/unique paths: 142 / 142; duplicate/missing/extra/identity mismatch: 0;
- files read-only: 145 / 145;
- directories read-only: 5 / 5;
- parse/ADS/pyc/cache/reparse findings: 0;
- WRITE_STOPPED strict-latest margin: 2,184,335 ticks; at-or-after excluding marker: 0; post-marker root writes: 0.

Manifest SHA-256: `C51709AE19EBFEB7AE9EBC4680302DCB27F3BEFFD9B85512F18A305826156CE4`.

External auditor PASS JSON:

`D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\reports\FIG-P582-01_R110_R7A_EXTERNAL_ROOT_AUDIT_20260827.json`

Formal report:

`D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\reports\FIG-P582-01_R110_R7A_ROOT_ACCEPT_CONTROL_RESEAL_20260827.md`

R7/R7A must remain frozen. Mainline may now dispatch a different fresh isolated SA3; this role did not start one.
