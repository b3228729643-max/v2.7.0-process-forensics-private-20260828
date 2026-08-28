# Full C(N,2) overlap, clearance, and z-order audit

Object denominator: N = 113 (55 TEXT + 58 GRAPHIC), so C(N,2) = 6,328
unordered relationships. The complete base table is 'after_overlap_report.csv'.
Its partitions are TT = 1,485; TG = 3,190; GG = 1,653; total = 6,328.
Masks and all counts use native 300 dpi 1x coordinates. Nearest-neighbor 8x
cards are visual evidence only; no enlarged/resampled count was used.

| Final decision | Pairs |
| --- | ---: |
| PASS | 4,236 |
| PASS_SAME_SEMANTIC_TEXT_PARENT | 9 |
| PASS_INTENTIONAL_CONTACT | 33 |
| PASS_NONCOMPETING_OPAQUE_BACKGROUND | 2,050 |
| total | 6,328 |

Final-visible intersections total 113: 17 intentional foreground-anchor/arrow
intersections and 96 documented noncompeting opaque-background intersections.
There are zero illegal competing-foreground intersection pixels, zero ordinary
clearance failures, and zero clipping failures. The only zero-clearance text
subspan case is the caption's source composition at figure-source line 83
(including PAIR_052_053); after unique native raw-mask ownership its physical
intersection is zero.

All 129 critical cards were manually opened at native 1x with both unique masks,
overlay, and 8x nearest view. The individual ledger is
'critical_relation_manual_ledger.csv'. Exact source anchor and contact-pixel
evidence for every intentional pair is retained in the corresponding pair-table
row. In particular:

- main stations/heads use lines 43--46: station east/west anchors and same-arrow
  shaft/head joins;
- badges use line 48 with each stated north-west x/y-shift anchor;
- the feedback loop uses lines 50--53, including boundary.north and
  problem.north, and its deliberately white label;
- supervised/unsupervised ingress uses lines 76--77; pool-to-validation and
  validation-to-report use lines 78--79;
- report double-border/white separator is the deliberate report construction,
  captured as PAIR_104_105.

Opaque objects were not blanket-exempted. Each is an object in
'object_manifest.csv' and 'graphic_manual_ledger.csv': station, badge, route,
pool, engine-chip, validation, and report fills; the feedback white label; and
the report white separator. For every such relationship the pair table records
layer and z-order. Review confirmed that these layers only form their own
noncompeting background/interior geometry and do not hide competitor text or
extend beyond their intended borders.

OVERLAP_HARD_GATE: PASS
CLEARANCE_HARD_GATE: PASS
CLIPPING_HARD_GATE: PASS
