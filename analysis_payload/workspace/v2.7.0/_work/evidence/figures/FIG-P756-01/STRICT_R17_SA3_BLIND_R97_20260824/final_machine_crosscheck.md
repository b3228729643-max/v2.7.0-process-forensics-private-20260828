# Final machine cross-check

Read-only cross-check after manual ledgers and report completion:

- Candidate/source SHA-256 exactly match the independently verified targets.
- 0 zero-byte files and 0 unresolved-status markers outside the retained audit script.
- Glyph manifest, pixel measurements, and manual glyph ledger each have 380
  rows; exactly one final glyph failure is GLY0215.
- 55/55 font rows pass, minimum effective size 9.6 pt.
- Object denominator is 113 = 55 text + 58 graphics; graphic ledger has 58.
- Pair denominator is 6,328 = 1,485 TT + 3,190 TG + 1,653 GG.
- Illegal competing-foreground intersections = 0; ordinary clearance failures
  = 0; clip failures = 0.
- Critical pairs = critical-ledger rows = all-opened rows = 129.
- Raw-glyph shared pixels after native ownership resolution = 0.

Cross-check terminal is FAIL_TO_SA2 solely because GLY0215 has the mandatory
same-codepoint area ratio 34/37 = 0.918918..., below 0.92.
