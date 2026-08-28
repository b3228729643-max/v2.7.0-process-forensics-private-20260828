# Confirmed strict failures (not execution blockers)

## I-001

- status: confirmed-fail
- severity: hard-gate
- description: 17/175 glyph IDs fail fixed height or calibrated punctuation thresholds.
- ids: G007, G013, G014, G021, G032, G044, G051, G062, G077, G081, G092, G104, G118, G132, G160, G164, G167
- evidence: `ledgers/manual_glyph_review.csv`

## I-002

- status: confirmed-fail
- severity: hard-gate
- description: 6/42 peer rows fall outside strict peer bounds.
- ids: PEER21, PEER22, PEER23, PEER24, PEER38, PEER39
- evidence: `ledgers/manual_peer_review.csv`

## I-003

- status: confirmed-fail
- severity: hard-gate
- description: FORMULA_BLOCK comparable height ratio is 1.22449 against allowed maximum 1.18.
- id: ROLE03
- evidence: `ledgers/manual_role_review.csv`

No evidence-generation blocker remains.

