# FIG-P656-01 fresh isolated SA1 audit on official R108

## Identity and scope

- HANDOFF: `C-FIG-P656-01-R108-SA1-FRESH-ISOLATED-REPLACEMENT-V2`
- Agent: `/root/sa1_fig_p656_r108_fresh_isolated_replacement_v2`
- Actual route: `gpt-5.6-sol` / `xhigh` / `fork_turns=none`
- Scope: first blind, read-only visual and mathematical audit of FIG-P656-01 only.
- Official R108: 817 pages, 4,967,161 bytes, SHA256 `C2EC93425486A57DE4C6670E16FC7DA729649A183230C28E8A0652467D3B5B78`.
- Main figure source: 2,854 bytes, SHA256 `9D404ED0694D575DE89038D3D6485C49AA4C60DCC3238AD8318CADACF810B381`.
- Independent location: physical page **705**, printed page **692**, Figure **34.2**. The earlier Goal card's physical-page 764 was not inherited.

No source, PDF, chapter, central state, inventory, or other UID was changed. No TeX engine was invoked.

## Frozen visual evidence

The four principal views are:

1. `render/r108_p705_full_200dpi.png`
2. `render/r108_p705_figure_with_caption_300dpi.png`
3. `render/r108_p705_standalone_300dpi.png`
4. `render/r108_p705_grayscale_300dpi.png`

The object overlay and three independent mask views are also frozen. Four risk regions each have an exact native-300-dpi 1x crop and an 8x nearest-neighbor topology view: coefficient header/formula gap, warning lower clearance, first arrow/label/count-box endpoint, and second arrow/coefficient-box endpoint.

## Denominators

- 48 visible semantic objects: 25 text/formula + 23 graphic.
- 1128 unordered object pairs: all rows frozen.
- 90 visible glyphs, plus 8 layout spaces in the PDF extraction.
- 10 natural math-script glyphs explicitly measured.
- 12 critical semantic/geometry IDs independently adjudicated.
- 3 nonvisible PDF hatch/clip extraction artifacts disclosed and excluded.

Every object appears in `manual_object_adjudication.csv`; every critical ID appears in `manual_critical_adjudication.csv`. Pair closure uses three evidence-backed families, not bulk default booleans.

## Findings

### Typography

All reader-visible base text is 9.5 TeX pt or 9.9 TeX pt at graphics scale 1.0. PDF bp metadata is consistent with TeX-point conversion. Native pixels pass all applicable element/script thresholds. Token-label height variation is 26--27 px and same-role ratio is at most 1.038. R168-only outline/taxonomy differences do not create a hard defect.

### Math and text semantics

The three sequences are `(1,1,1,2,3,3)`, `(1,3,1,2,1,3)`, and `(3,1,2,1,3,1)`. Each yields `(n1,n2,n3)=(3,1,2)`. Thus `N=6`, the constraints are satisfied, and the multinomial coefficient is `60`. The warning that a count vector is not a probability vector is correct. Caption, nearby R108 prose, and diagram agree.

### Geometry, pixels, and harmony

All 1128 independent mask intersections are 0. Required category-specific minimum clearances are 6.000 px text-text, 22.472 px text/formula-arrow, 9.000 px internal text-border, and 16.000 px text-crop edge. No visible semantic object is clipped. Color-independent shape/hatch encoding survives grayscale. Page placement is balanced and readable.

## Decision

No R168 hard failure was found. The long two-line caption and intrinsic glyph-outline height differences are advisory only; neither causes unreadability or severe imbalance.

**Result: `SA1_PASS_AWAIT_FRESH_ISOLATED_SA3`.**

