# FIG-P634-01 root validation — R94 / strict R5

- Official candidate: `strict_current_r94_fullbook/main_full.pdf`
- Physical page / printed page / figure: 682 / 669 / 33.3
- Audit source: `STRICT_R5_SA1_R94`
- Root decision: **FAIL → SA2**

## Root-independent checks

- Reconciled `audit_summary.json`, terminal CSV/JSON/Markdown, object manifest, pair table, glyph packs, and critical-pair packs.
- Terminal closure passes: 452 unique nonempty raw masks; 307 literal glyphs; 106 semantic text elements; 39 graphic/background objects; 145 foreground pair objects; 10,440 unordered pairs.
- Pair result: one real clearance failure, zero illegal-overlap failures, zero clip failures.
- Inspected the failed border pair at native 300dpi/1:1 and the nearest-pixel evidence: `EL-035-CARD1_STATE-MATH_SCRIPT` to `G-CARD1-BORDER` has overlap 0 but final-visible raw gap 2.162px, below the 5px text-to-node-border minimum. Nearest pixels are A(1094,2149), B(1093,2146).
- Inspected representative raw glyph masks and 8x nearest-neighbour human-review views. Eleven literal CJK glyphs `一` have raw ink height below the 30px CJK threshold: one is 21px and ten are 4px. The Goal provides no low-stroke CJK exception.
- D same-class failures: 23. E role-to-BASE failures: 3.
- Source-font floor passes: figure minimum 9.6pt and caption chain 10pt. Font visual harmony, global visual harmony, mathematics, text consistency, grayscale, and page integration pass.

## Routing

Only the following route is permitted: dedicated SA2 targeted repair → root-built new official candidate → new independent SA1. SA2 must preserve the 9.5pt minimum and improve, not degrade, whole-figure font harmony and viewing comfort.
