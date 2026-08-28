# R5 SA1 overlap and opaque-background review

Canonical evidence directory: `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\evidence\figures\FIG-P602-01\STRICT_R5_REQUAL_R96_SA1_CONT_20260824`.

## Complete foreground-pair coverage

The final-visible primary inventory contains 19 text objects and 16 graphic objects, for 35 objects and all `C(35,2) = 595` unordered TT/TG/GG pairs.  `after_overlap_report.csv` is the formal all-pair output, derived from direct native-300-dpi masks.

- 578 pairs: `PASS_NO_OVERLAP`.
- 5 pairs: `SAME_PARENT_LAYOUT`, each with raw ink intersection 0.
- 12 pairs: `INTENTIONAL_CONTACT`.
- 0 nonwhitelisted final-foreground overlaps.

The 12 intended contacts are G01--G08, G02--G10, G03--G04, G03--G12, G05--G14, G05--G15, G06--G14, G07--G15, G07--G16, G08--G09, G10--G11, and G12--G13.  Their whitelist reasons are retained per row: a connector attaches to its source/target boundary, a shaft joins its arrowhead, or the fraction rule is an internal formula component.  `intentional_contact_ledger.csv` and its three `pairs/intentional_contact_details/*review_sheet*_8x_nearest.png` sheets were manually inspected at 8x nearest; each contact is consistent with that stated geometry.

## Opaque edge-label backgrounds

The six white label backgrounds are deliberately excluded from the 35 foreground objects and are audited separately in `occlusion_inversion.csv`.

| Halo | Result | Basis |
|---|---|---|
| H01 proposal | PASS / no true occlusion | connector x is left of white label rectangle |
| H02 calculate | PASS / no true occlusion | connector x is left of white label rectangle |
| H03 decide | PASS / no true occlusion | connector x is left of white label rectangle |
| H04 accept | PASS / no true occlusion | diagonal branch reaches y=570 pt to the right of white rectangle |
| H05 reject | PASS / no true occlusion | diagonal branch reaches y=570 pt to the left of white rectangle |
| H06 self loop | PASS / no true occlusion | independent reverse render plus cubic vector gap |

For H06, `occlusion/H06_pre_occlusion_without_white_halo.pdf` is a one-page evidence copy only.  Its sole targeted operation changes the known H06 white-fill token from `f` to `n`; the frozen fullbook remains untouched.  Direct native 300 dpi re-rendering exposes no self-loop pixel inside the halo.  The cubic loop’s maximum y is 674.996 pt, while the white label begins at y=683.605 pt (8.609 pt vector gap before stroke allowance).  `occlusion_reverse_render_manifest.json` records the target token, input hash, copy hash, and raster hash.

## Gate conclusion

All-pair overlap, intent whitelist, and opaque-background/paint-order checks pass.  They are independent from the glyph-floor failures that determine the terminal status.
