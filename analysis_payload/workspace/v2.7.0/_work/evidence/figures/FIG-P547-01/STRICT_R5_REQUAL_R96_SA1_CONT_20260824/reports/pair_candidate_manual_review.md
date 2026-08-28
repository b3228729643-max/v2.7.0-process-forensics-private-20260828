# FIG-P547-01 SA1 manual review of failed pair candidates

## Review method

The reviewer independently opened all four native 1× candidate ROIs and their 8× nearest-neighbour contact views.  The evidence is derived from physical PDF page 591 rendered directly at 300 dpi; it is not a re-render of the TikZ source and no interpolation, morphology, or pixel repair was used.  The four rows below are the complete `FAIL` subset of `pairs/all_foreground_unordered_pairs.csv`; the full ledger still enumerates all 27,966 unordered pairs of the 237 foreground objects, including graphic–graphic pairs.

## Individual findings

| Pair | Native evidence | Manual finding | Result |
| --- | --- | --- | --- |
| `PAIR_C0026_G07` | `pairs/PAIR_C0026_G07_original_1x.png`; `pairs/PAIR_C0026_G07_contact_8x_nearest.png` | The left natural-script label `C0026` and focus-arrow shaft `G07` are visibly separate but have exactly 1 raw pixel of clearance.  The text-to-line/arrow/marker rule requires 3 px; it is not a permitted endpoint/contact. | FAIL |
| `PAIR_C0026_G09` | `pairs/PAIR_C0026_G09_original_1x.png`; `pairs/PAIR_C0026_G09_contact_8x_nearest.png` | The same left label and focus-label border `G09` are visibly separate but have exactly 1 raw pixel of clearance.  The 3 px rule applies and the whitelist has no matching intentional-contact entry. | FAIL |
| `PAIR_C0120_G24` | `pairs/PAIR_C0120_G24_original_1x.png`; `pairs/PAIR_C0120_G24_contact_8x_nearest.png` | The right natural-script label `C0120` and focus-arrow shaft `G24` are visibly separate but have exactly 1 raw pixel of clearance.  This is below 3 px and is not an intended contact. | FAIL |
| `PAIR_C0120_G26` | `pairs/PAIR_C0120_G26_original_1x.png`; `pairs/PAIR_C0120_G26_contact_8x_nearest.png` | The same right label and focus-label border `G26` are visibly separate but have exactly 1 raw pixel of clearance.  This is below 3 px and is not whitelisted. | FAIL |

All four findings are insufficient-clearance failures, not raw-pixel overlaps (`raw_overlap_px=0` in every case).  The manual visual reading corroborates rather than relaxes the raw-distance rule.
