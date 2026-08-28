# Pair manual-review binding

`all_foreground_unordered_pairs.csv` is the immutable 33,153-row machine denominator. Its final `manual_review` field was emitted as a placeholder for the 40 selected critical/intentional rows and is not an acceptance decision.

The active row-by-row human decisions are in `critical_and_intentional_pair_manual_review_ledger.csv`. That signed ledger contains exactly 40 unique pair IDs; each ID exists once in the full machine denominator; every referenced native 1x original and 8x contact card was opened; all 40 manual decisions are `PASS` or `PASS_INTENTIONAL`. No machine hard failure was overridden.
