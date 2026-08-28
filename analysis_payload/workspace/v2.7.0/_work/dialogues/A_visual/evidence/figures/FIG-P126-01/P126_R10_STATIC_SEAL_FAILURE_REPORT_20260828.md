# P126 R10 static seal failure disclosure

HANDOFF_ID=`A-R115-P126-SA2-STATIC-TWO-HARD-PATCH-R10-20260828`  
ROOT_CLASSIFICATION=`UNSEALED_CONTROL_FAILURE_BEFORE_MARKER`  
STATIC_CONTENT_STATUS=`STATIC_ONLY_NOT_RENDERED_NOT_PASS / BLOCKED_BY_PREDICTED_DIGIT4_OCCLUSION`

The sole controller `P126_R10_STATIC_SEAL_CONTROLLER_20260828.ps1` (6,069 bytes/SHA256 `7C9A17C25D6BACC493387A635D1CA9013A2E1C4FF5D57ACE118EAAED9A851A77`, ReadOnly, AST0, one Move-Item site) was invoked exactly once. It wrote the payload manifest and seal audit and set the 12 present files plus root ReadOnly. Before marker staging, its RO-gate failure branch used the compressed token `throw'RO_GATE'`, which PowerShell interpreted as the nonexistent command `throwRO_GATE`; invocation exited1. The underlying branch was entered because the script tested pre-refresh FileInfo objects after setting attributes.

No marker stage was created, `WRITE_STOPPED` is absent, controller result is absent, auditor invocation count is zero, and no retry or correction was attempted. Current frozen root state is 12 files/1 directory including root, all ReadOnly; controls present are only `PAYLOAD_MANIFEST.csv` and `SEAL_AUDIT.json`. There were no post-failure root writes.

The source remains the two-token static candidate at 4,391 bytes/SHA256 `E8803BC9E2347840D7EA0D482D83C20F43FD62DA8023F37C49168241B48AAF81`; no TeX/build or commit occurred. Independently of the control failure, the static projection finds the authorized yshift=15pt scope unsafe because the moved opaque background would cover 88 current dark digit-4 pixels. Main adjudication is required before either an evidence-only reseal or a revised source scope; no build slot is requested.
