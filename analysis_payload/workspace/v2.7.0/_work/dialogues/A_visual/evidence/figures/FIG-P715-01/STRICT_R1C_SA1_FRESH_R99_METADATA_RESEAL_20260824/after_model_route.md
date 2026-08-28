# FIG-P715-01 — R1C actual model route

HANDOFF_ID: `A-R99-P715-SA1-FRESH-B-20260824`

| Stage | Model | Reasoning | Status |
|---|---|---|---|
| SA1 fresh isolated audit / R1C metadata reseal | gpt-5.6-terra | max | completed; actual orchestrated route |
| SA2 source repair | NOT_USED | NOT_USED | required next because the reused bottom evidence is a hard FAIL |
| SA3 isolated confirmation | NOT_STARTED | NOT_STARTED | not permitted before a new SA2 candidate and a new SA1 PASS |

R1C changes metadata and terminal sealing only. It does not change R99, the source, the 298-object ledger, the 44,253-pair denominator, raw masks, visual-review facts, or the `FAIL_TO_SA2` verdict.
