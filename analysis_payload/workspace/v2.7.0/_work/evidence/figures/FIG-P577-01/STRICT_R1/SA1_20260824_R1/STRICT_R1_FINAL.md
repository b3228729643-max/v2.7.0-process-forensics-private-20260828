# FIG-P577-01 — SA1 strict R1 final verdict

## RESULT: `FAIL→SA2`

Candidate: frozen R94 `main_full.pdf`, SHA-256 `CA76A41334ACA3587B9FE742C3D3B8BCBE598A505E58929C82B478FFF4F6A7A3`.

- Official localisation: physical PDF page **625**, printed page **612**; uniquely anchored by the caption/title, not by a legacy page number.
- Native visual basis: direct 300-dpi `2481×3508` raster; integer page coordinates; no resize.
- Final-visible coverage: 158 visible text primitives in 22 semantic text/font elements; 342 raw glyph traces; 13 graphics (12 non-background); 495 exhaustive semantic relation rows (`495/495` expected). One source-extracted y=`0.4` tick is recorded as fully occluded by a real later white callout and is not falsely audited as visible text.

## Gate ledger

| Gate | Result | Evidence |
| --- | --- | --- |
| Source effective font | PASS | 22/22 semantic elements, 0 source failures; `after_font_audit.csv` |
| Raw pixel height | FAIL | 67/342 glyph traces; e.g. `T004_G01` `=` is 12px `<22px`; `glyph_measurements.csv` and package |
| D same-panel/role/script | FAIL (separate) | 152/342; does **not** alter raw pixel-height count |
| E same-script relative BASE | FAIL (separate) | 3/158 comparable rows; all others PASS/N/A; no cross-script BASE |
| Text/graphic relations | FAIL | 3 real clearance failures, 0px overlap, 0px clip |
| Mathematical/content | PASS | `MATH_CONTENT_AUDIT.md` |
| Whole figure/page/grayscale | visual PASS subject to strict failures | `VISUAL_HUMAN_REVIEW.md` |
| Evidence/machine integrity | PASS | 23/23 terminal cross-checks; `machine_crosscheck.*` |

The terminal glyph-failure ID set is exactly `67` IDs in `machine_terminal.json`, matches `glyph_measurements.csv`, and has one complete raw/1:1/8× package per ID. D (`152`) and E (`3`) remain independent diagnostics and are not propagated into that raw-pixel count.

## Real strict failures requiring SA2

1. `T004_G01`: visible `=` raw height `12px`, threshold `22px` (single-glyph raw evidence; no D/E propagation).
2. `TG304`: `P_LEGEND_BLUE` ↔ `G01_P_CURVE`, `1px < 3px` required.
3. `TG317`: `P_LEGEND_TEAL` ↔ `G02_CQ_ENVELOPE`, `1px < 3px` required.
4. `TG457`: `P_TICK_Y_0_8` ↔ `G10_ACCEPT_BORDER`, `2px < 5px` required.

Each relation failure has complete raw/A/B/intersection/overlay/1:1/8× and nearest-focus evidence. Opaque covers preserve pre-vector, real final halo, and final-visible raw-mask triplets under `halos/`. Intentional graphic-to-graphic guide/marker connections were not misclassified as illegal text relations.

No business source, central status, inventory, build entry, or candidate PDF was modified; all writes are confined to this SA1 evidence directory.
