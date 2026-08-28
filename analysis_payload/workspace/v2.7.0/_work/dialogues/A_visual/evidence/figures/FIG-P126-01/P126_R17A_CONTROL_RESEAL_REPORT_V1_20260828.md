# P126 R17A evidence-only control reseal audit

HANDOFF_ID=A-R115-P126-SA2-DIRECT-BUILD-R17-CONTROL-RESEAL-V1-20260828
OPERATION=P126_R115_R17_SA2_EVIDENCE_ONLY_CONTROL_RESEAL_V1
VERDICT=LOCAL_SA2_PASS_READY_FOR_MAIN_REVIEW_AND_ATOMIC_COMMIT_AUTH
BUSINESS_EVIDENCE_RERUN=0

- copy=145, payload=147, controls=3, ordinary=150, dirs including root=11
- old controls copied=0; five-field source-to-destination mismatch=0
- all files/directories/root ReadOnly; WSTOP unique and strictly latest including root
- at-or-after excluding marker=0; postmarker content/attribute drift=0; source-root drift=0
- CSV/JSON parse failures=0; ADS/cache/pyc/reparse failures=0

This operation reseals preserved R17 material only. It does not rerun or readjudicate visual, object, pair, glyph, mathematical, semantic, or page evidence.
