# Fresh isolated SA1 visual acceptance

- HANDOFF_ID: `C-FIG-P662-01-R112-SA1-FRESH-ISOLATED-V1`
- UID: `FIG-P662-01`
- Canonical instance: `/root/sa1_fig_p662_r112_fresh_isolated_v1`
- Model: `gpt-5.6-sol`
- Reasoning: `xhigh`
- Official candidate: frozen R112 PDF identity exactly matched
- Current source identity: exactly matched
- Independent target location: physical page `710`, printed page `697`, figure `34.5`
- Visible-object denominator: `25`
- Text-element denominator: `21`
- All unordered pairs: `300`
- Manual pair decisions: `300`
- Intended legal endpoint contacts: `16`
- Bbox-only false positives: `3`
- Hard illegal collision pairs/pixels: `0 / 0`
- Clipped foreground pixels: `0`
- Unresolved candidates: `0`
- Missing glyph/tofu/wrong codepoint: `0 / 0 / 0`
- Wrong displayed math or semantic claim: `0`
- Opened final views: `20`
- Native risk ROIs: `6`
- NN8x risk ROIs: `6`
- Minimum observed text-to-containing-border clearance: `5 px`

## R168 decision matrix

| Criterion | Manual result |
|---|---|
| source and rendered text identity | clear |
| native text readability | clear |
| same-role visual consistency | clear; input formulas, badges, titles, notes, and baseline formulas are internally stable |
| role hierarchy / obvious imbalance | clear; main construction remains first visual focus |
| illegal overlap | zero hard collision pairs and zero illegal pixels |
| clipping | zero clipped reader-foreground pixels |
| grayscale | clear; nodes, arrows, dashed evidence, labels, and caption remain distinguishable |
| page integration | clear; figure neither crowds adjacent prose nor creates anomalous whitespace |
| mathematics | independently recomputed and correct |
| semantics / reading order | unambiguous left-to-right construction with subordinate consequences |
| caption consistency | exact substantive agreement with diagram and current source |

The source contains `9.2 pt` general node text and `8.5 pt` badges/notes. Those legacy numerical thresholds are recorded, but under active R168 they are advisory and cannot cause a source return by themselves. Native evidence shows the text is readable, complete, balanced, and free of the enumerated hard defects.

## Sealed-result candidate

`SA1_PASS_READY_FOR_FRESH_ISOLATED_SA3`
