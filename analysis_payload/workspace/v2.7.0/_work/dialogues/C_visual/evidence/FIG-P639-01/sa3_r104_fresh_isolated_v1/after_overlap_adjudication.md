# Independent overlap and clearance adjudication

- REVIEWER_TYPE: `AI_SA3_VISUAL_REVIEW`
- HUMAN_CERTIFICATION: `false`
- native denominator: official R104 physical page 689 rendered directly at 300 dpi, 2481 × 3508 px, with no post-render resize
- semantic denominator: 20 text/formula elements + 9 graphical objects = 29 actual objects
- complete unordered-pair denominator: `406 = C(29,2)`
- protocol-critical denominator: `368` non-natural-script pairs having at least one TEXT side
- natural-script attachments excluded from collision semantics: `E01–E02`, `E03–E04`

I viewed the native figure crop, the standalone-equivalent crop, the grayscale crop, the ID overlay, the color-coded semantic masks, and the actual 1x/nearest-neighbour 8x critical glyph crops. The complete numeric pair table was then sorted by foreground distance. The nearest independently meaningful cases were adjudicated individually:

| pair | actual minimum px | manual finding |
|---|---:|---|
| E16–E17 | 12 | two separate note lines; no shared antialias pixel and text–text clearance exceeds 4 px |
| E19–E20 | 14 | two caption baselines remain separate; no shared glyph pixel |
| E10–O03 | 16 | x=0 label remains below its tick mark |
| E11–O03 | 16 | x=1 label remains below its tick mark |
| E12–O03 | 16 | x=2 label remains below its tick mark |
| E13–O03 | 16 | x=3 label remains below its tick mark and arrow |
| E05–O04 | 18.028 | y=0.5 text remains left of its tick |
| E06–O04 | 18 | y=0.25 text remains left of its tick |
| E07–O04 | 18 | y=0 text remains left of its tick |
| E09–O03 | 18.788 | x=-1 text remains below its tick |
| E16–O09 | 19 | first note line has legal interior padding |
| E17–O09 | 19 | second note line has legal interior padding |
| E08–O03 | 19.235 | x=-2 text remains below its tick |
| E18–E20 | 19.026 | caption prefix and wrapped continuation do not touch |
| E13–O01 | 21.471 | rightmost tick text remains below the axis foreground |

Every other critical pair has a larger measured separation than the cases above. The all-pair CSV preserves every object-pair ID and numeric result; no decision column was machine-generated.

- OVERLAP_CANDIDATE_PIXEL_COUNT: `0`
- MASK_CONTAMINATION_PIXEL_COUNT: `0`
- OVERLAP_PIXEL_COUNT: `0`
- PIXEL_ADJUDICATION_STATUS: `CLEAR`
- MIN_TEXT_CLEARANCE_PX: `12`
- CLIP_PIXEL_COUNT: `0`
- PIXEL_DISPUTE_REQUIRED: `false`
- PIXEL_ARBITER_MODEL: `NOT_USED`
- PIXEL_ARBITER_REASONING: `NOT_USED`

There is no candidate cluster to classify as TRUE_COLLISION, MASK_CONTAMINATION, or UNRESOLVED. The earlier broad note-border color mask was corrected before adjudication by restricting the mask to the actual rounded-border stroke; final CSVs and masks contain that corrected denominator.

