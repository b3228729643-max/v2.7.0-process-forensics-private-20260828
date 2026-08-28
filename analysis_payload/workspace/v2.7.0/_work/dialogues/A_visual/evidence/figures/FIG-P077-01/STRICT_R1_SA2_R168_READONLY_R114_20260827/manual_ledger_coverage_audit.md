# Manual-ledger coverage audit

Observed and written after opening all required visual evidence.

- Frozen visible-object denominator: 20 objects (`O01`–`O20`).
- Manual object rows: 20; unique IDs: 20; missing IDs: 0; blank reviewer/decision/note fields: 0.
- Mathematical unordered-pair denominator: `20 × 19 / 2 = 190`.
- Machine pair denominator rows: 190.
- Manual pair rows: 190; unique pair IDs: 190; missing: 0; extra: 0.
- Pair-to-object mapping mismatches against the frozen denominator: 0.
- Blank manual reviewer/decision/note fields: 0.
- Machine scripts never write or overwrite reviewer, boolean, decision, or note fields; all such fields live only in the `manual_*` files authored after observation.

Coverage result: `COMPLETE`.
