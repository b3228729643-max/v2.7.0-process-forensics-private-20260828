# FIG-P067-01 manual relationship ledger

- Reviewer: `/root/p067_r113_fresh_sa1`
- Final frozen visible-object denominator: `N=130` (`95` glyphs + `35` foreground drawings).
- Separately tracked paint-order supports: `5` real opaque white text backgrounds; they are not visible foreground denominator objects.
- Expected unordered pairs: `C(130,2)=8385`.
- Enumerated in `after_overlap_report.csv`: `8385/8385`, unique IDs R00001-R08385.

## Full-denominator manual disposition

The 8,286 pairs not present in `machine_critical_pair_index.csv` were checked against the complete machine pair ledger, the text/drawing overlays and the native figure. They are spatially separated beyond the near-pair trigger or are same-parent internal typography/intended geometry; no hard interaction exists. Manual decision for every such pair ID: `PASS_DISTANT_OR_INTERNAL`.

The following 99 independent near/overlap-candidate IDs were all opened in the five pair overview sheets and manually decided `PASS`:

- GRAPHIC_GRAPHIC (23): R07796, R07806, R07807, R07829, R07830, R07859, R07861, R07871, R07892, R07922, R07923, R07951, R07952, R07980, R08008, R08009, R08010, R08011, R08015, R08136, R08286, R08309, R08311.
- INDEPENDENT_TEXT_TEXT (23): R00003, R00004, R00005, R03744, R03745, R03839, R03840, R03933, R03934, R03935, R04026, R04027, R04028, R05070, R05071, R05072, R05073, R05150, R05151, R05152, R05153, R05231, R05232.
- TEXT_OR_FORMULA_TO_GRAPHIC (53): R00096, R00229, R00230, R00356, R00357, R00726, R00854, R00976, R01097, R01217, R01219, R01336, R01338, R01454, R01571, R01687, R01802, R01916, R02029, R02252, R02260, R02471, R02996, R03307, R03314, R03318, R03407, R03500, R03502, R03506, R03598, R03600, R03604, R03696, R04094, R04098, R04191, R04282, R04372, R04376, R04380, R04461, R04465, R04469, R04636, R04974, R05291, R05816, R05957, R06025, R06093, R06160, R06226.

## Explicit intersection/low-clearance adjudication

| Pair | Manual observation at native/8x | Decision |
|---|---|---|
| R00229 G002/D007 | `p_4` is visually separated from the solid top CDF step; the one-pixel machine result is bbox/color-fringe. | PASS_R168_ADVISORY |
| R00230 G002/D008 | `p_4` is below the dashed `y=1` guide; the reported mask intersection is gray antialias/context contamination, not final-visible contact. | PASS_R168_ADVISORY |
| R01219 G010/D009 | The punctuation colon lies left of the `x=1` guide; the guide leaked into the gray glyph bbox mask. Original and 8x show real separation. | PASS_R168_ADVISORY |
| R07806, R07871 | The open CDF marker at `(1,0)` intentionally sits on the axis/tick location. | PASS_INTENDED_GEOMETRY |
| R07859, R08309 | Orthogonal x/y axes intentionally meet at their origins. | PASS_INTENDED_GEOMETRY |
| R07980 | The CDF top plateau intentionally equals and overpaints the `y=1` reference guide. | PASS_INTENDED_SEMANTICS |
| R08008, R08009, R08010 | Vertical support guides intentionally cross the horizontal `y=1` guide. | PASS_INTENDED_GEOMETRY |
| R08015 | The filled `x=4` CDF marker intentionally lies at `F=1`. | PASS_INTENDED_SEMANTICS |

All other near pairs show visible separation or intended plot construction in their opened overview cells. No independent text-text pair collides; no annotation or label is crossed in the final image; no marker obscures a label; and no caption object approaches a crop edge.

- `OVERLAP_PIXEL_COUNT=0` for illegal independent-object overlaps after manual semantic adjudication.
- `CLIP_PIXEL_COUNT=0` in the page and both native crops.
- `PAIR_ENUMERATION_COMPLETE=true` (`8385/8385`).
- Hard relationship result under R168: `PASS`.

