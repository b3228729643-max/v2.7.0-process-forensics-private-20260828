# Low-profile scope certificate

- Scope source: `machine_reuse/object_manifest.csv`, exactly 95 text/formula objects.
- Script-class partition observed: 73 `CJK_FULL`, 10 `BASE_MATH_OPERATOR_OR_GLYPH`, 7 `LATIN_GREEK_LOWER`, 2 `LATIN_CAP_DIGIT`, and 3 `NATURAL_TEX_SCRIPT`.
- The three natural-script objects are `FRM_PREDICTIVE_FORMULA_002` (`i`, 26 px), `FRM_PREDICTIVE_FORMULA_005` (`i`, 26 px), and `FRM_PREDICTIVE_FORMULA_007` (`0`, 24 px). Each is at or above the applicable 22 px ink-height floor, so none enters the low-profile exception population.
- Therefore the scoped low-profile peer set is empty (`peer_count=0`) and the scoped low-profile hard-gate set is empty (`hard_count=0`). This statement certifies only those two empty sets, cannot be extrapolated to the whole figure, and does not replace the 95 glyph decisions.
- Human evidence binding: `manual/GLYPH_MANUAL_DECISIONS.csv` contains 95 unique opened cells; `manual/SCHEMA_MANUAL_DECISIONS.csv` row `R7A-DE-008` records the zero-set adjudication.
