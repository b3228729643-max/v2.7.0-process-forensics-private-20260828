# Denominator closure and foreground self-consistency gate

## Frozen denominators

| Review unit | Denominator |
|---|---:|
| semantic foreground objects | 32 |
| all unordered object pairs | 496 = C(32,2) |
| visible PDF text runs | 63 |
| visible glyph occurrences | 194 |
| PDF drawing primitives adjudicated | 28 |
| critical intersections | 24 |
| peer groups | 25 |
| role groups | 9 |
| object clip checks | 32 |
| mandatory/render views | 72 |
| hard gates | 20 |

## Object census

The initial mental grouping of the flowchart into large composite boxes was not accepted as the denominator. I decomposed every visible foreground element and froze 32 objects:

- `T01–T19`: every logical text/formula-bearing item, including six edge/self-loop labels and the caption.
- `B01–B06`: every visible node/border item; `B06` is one semantic compound double border because the two concentric strokes jointly encode one rejected-state frame and have no independent relation or content.
- `E01–E06`: every directed line/arrow/self-loop object; shafts and arrowheads are one semantic relation object apiece.
- `M01`: the independent visible rule of the acceptance-ratio fraction. It is not hidden inside `T06` or omitted as decoration.

All internal text, formula glyphs, borders, arrows, the self-loop, the caption, and the independent math rule therefore participate as foreground objects. The whole TikZ drawing/group is not treated as one object.

## Primitive inclusion and exclusions

All 28 PDF drawing primitives on the located page were individually examined in `manual/primitive_exclusion_ledger.csv`:

- primitive 0 is the printed page header outside the target figure;
- primitive 1 is a正文 equation rule outside the target figure;
- primitives 2–8 map to `B01–B06` and `M01`;
- primitive 9 is a white label-separation support surface;
- primitives 10–26 map shaft/head components to `E01–E06`;
- primitives 12, 15, 18, 21, 24, and 27 are white label background supports, excluded from foreground because their only function is to create actual line/text clearance.

No exclusion hides an independent semantic relation, text, formula rule, border, or visible graphic mark.

## Cross-ledger endpoint/parent closure

- 32 object IDs are unique.
- 496 pair rows are unique, ordered, and exactly match all `i<j` endpoints from the frozen object list.
- Unknown pair endpoints: 0.
- 63 text runs all have a parent in `T01–T19`.
- 194 glyph occurrences all have a parent in `T01–T19`; the manual ledger matches machine ID, parent, character, and codepoint at every row.
- 24 critical items, 25 peer groups, 9 roles, 32 clip rows, and all foreground primitive mappings reference only frozen objects.
- 72 manual view rows correspond one-to-one with the 72 render files.

The read-only alignment audit found `pair_mismatch=0`, `glyph_mismatch=0`, `view_missing=0`, and no duplicate manual note in any ledger. Machine integrity is recorded in `machine/denominator_integrity.json`.
