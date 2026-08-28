# Builder attempt 01 — natural stop

- Scope: non-TeX native evidence generation only.
- Result: stopped before glyph, object, or pair artifacts were generated.
- Exception: the drawing-accounting assertion concatenated two independently sorted index lists and compared the unsorted concatenation to `range(26)`.
- Candidate PDF and P602 source were read-only and passed their SHA-256 gates before this stop.
- Correction: sort the combined foreground-plus-excluded drawing index set before comparing it with the exact `0..25` denominator.
- No TeX process, candidate build, source edit, retry of the v3C controller, or manual adjudication occurred.
