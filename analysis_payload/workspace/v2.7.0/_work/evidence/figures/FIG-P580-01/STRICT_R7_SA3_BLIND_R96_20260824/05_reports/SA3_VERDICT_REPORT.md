# FIG-P580-01 — STRICT R7 SA3 Blind R96 Verdict

## RESULT: PASS_TO_ROOT

This verdict is a fresh, isolated SA3 audit.  It relied only on the authority goal/instructions, the fixed final PDF, its direct FLS linkage, and the identified current figure source.  No prior FIG-P580-01 review, repair, root-acceptance evidence, inventory, or state record was consulted.

## Fixed identity and scope

- Figure: `FIG-P580-01` / Fig. 31.6.
- Candidate PDF: physical page 628 / printed page 615, 813 pages total.
- PDF SHA-256: `8EED8765A4856C4C197262DEA06E283790FBA8DA906C70C26FC7BD56F6F7E5E8`.
- Current source SHA-256: `F0ECC9B28361A2AE73AF085A4958AD09F8F94575D789B8F776C55631FD45E161`.
- FLS input/outputs, source path, scope boundary, and direct 300 dpi raster identity: `BUILD_IDENTITY_FLS.md`.

## Strict-gate outcome

| Gate | Independent result |
| --- | --- |
| Text glyph denominator / native inspection | 234 / 234 PASS; each has Original, Target-overlay, Mask-only, contact entry, native 1x and 8x-nearest review. |
| Source/effective font and size | PASS — ordinary labels/text final effective 9.5641 pt >= 9.5 pt; title/base hierarchy and CJK/Latin/math coordination pass. |
| Same-class and role ratios | PASS — all same-class and role-ratio checks pass (`same_class_ratio_audit.csv`, `role_ratio_audit.csv`). |
| Low-contour calibration | PASS — 9 / 9 final-PDF matched codepoint/font/size/weight controls pass. |
| Foreground inventory | 30 text + 15 graphic = 45 objects; object boundaries in `foreground_object_inventory.csv` and overlays. |
| Complete unordered pair universe | 990 pairs: TT 435, TG 450, GG 105; no class omitted. |
| Expected-contact control | 24 named source-semantic contacts only, each with source-line proof in `pair_universe.csv` and `FONT_MATH_AND_CONTACTS.md`; no inferred/unnamed whitelist. |
| Native 1x collision/clearance/cut inspection | PASS — 65 high-risk pairs manually checked at native 1x and 8x; zero unapproved foreground-ink overlap; illegal overlap pixels 0; clip pixels 0. |
| Pair clearance | Minimum TT bounding-box clearance 14 px; all non-manual pair bounding boxes at least 17 px. Conservative bounding-box relations under that lane were individually judged from physical ink, not blindly waived. |
| Scope/page clipping | PASS — scope-edge ink 0 px; page clip candidate count 0. |
| Four visual views | PASS — full page 300 dpi, exact scope 300 dpi, isolated body 300 dpi, grayscale 300 dpi, and full page 200 dpi. |
| Mathematical semantics / caption consistency | PASS — density/support relations, weights, panel labels, formula card and caption agree; see `FONT_MATH_AND_CONTACTS.md`. |

## Required terminal fields

```
SOURCE_FONT_PASS=true
PIXEL_HEIGHT_PASS=true
SAME_CLASS_RATIO_PASS=true
ROLE_RATIO_PASS=true
OVERLAP_PIXEL_COUNT=0  # illegal overlap; 24 named source-semantic contacts excluded
CLIP_PIXEL_COUNT=0
MIN_TEXT_TEXT_BBOX_CLEARANCE_PX=14
VISUAL_HARMONY_PASS=true
MATH_SEMANTICS_PASS=true
TEXT_CONSISTENCY_PASS=true
GRAYSCALE_PASS=true
PAGE_INTEGRATION_PASS=true
```

## Failure ledger

No failure was found.  Consequently there are no failure pixel coordinates or failure ROIs to report.  The retained per-glyph and per-pair pixel evidence, including all 1x/8x ROIs, is available for recheck; `glyph_ledger.csv`, `glyph_contact_table.csv`, `pair_universe.csv`, and `high_risk_manual_review.csv` provide the denominators, coordinates, and dispositions.
