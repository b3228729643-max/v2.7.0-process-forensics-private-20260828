# Source/PDF drawing-path and math-rule reconciliation

The source has nine explicit '\draw' instructions at lines 43--46, 50, and
76--79. It contains no '\overline', '\underline', '\sqrt', '\frac', or
'\cancel' construct. The native in-scope PDF extraction has 39 drawing
records; all 39 are represented by the semantic graphic/path ledgers.

Therefore:

- source visible drawing paths: 39
- PDF in-scope drawing records: 39
- mapped path records: 39
- unmapped paths: 0
- GRAPHIC/MATH_RULE objects required beyond those paths: 0

This is a 0-to-0 reconciliation for overline, underline, radical, fraction,
and cancellation rules; it is not inferred merely from rawdict.
