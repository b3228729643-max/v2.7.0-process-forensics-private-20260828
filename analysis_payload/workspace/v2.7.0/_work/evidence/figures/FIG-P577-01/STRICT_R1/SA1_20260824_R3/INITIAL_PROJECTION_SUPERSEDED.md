# Preliminary colour-projection outputs — SUPERSEDED_NONTERMINAL

The first R3 raw-pixel pass correctly rendered and inventoried R95-identity page pixels, but its broad residual=14 colour projection and advance-box crop were deliberately too permissive for terminal disposition. The following values are retained only so they cannot be silently mistaken for final defects:

| Preliminary diagnostic | Count | Why excluded from terminal gate |
|---|---:|---|
| Foreign target pixels | 430 | Nearby card/curve pixels fell inside advance-box colour projections, not final target masks. `T013/T014/T015=60/33/63`, `T194=1`, `T200=138`, `T245=135`. |
| Text--graphic rows | 392 | Broad same-colour / fill / grey projection conflated text and graphic roles. |
| Projected overlap pixels | 17,690 | Same nonterminal colour-projection artefact; never a terminal overlap count. |
| Old TG304/TG317 values | n/a | Replaced by direct R95 visible-contour replays: TG304=9.849px PASS; TG317=5.000px PASS. |
| Old T177 overlay | n/a | Its advance bbox contained the dashed cq line. `glyph_corrections/T177_G01_R95_*` provides the corrected target-only contour. |
| Old all-pair flag T292/T293 | 1 | Raw vertical y-axis title was split across semantic parents; R95 refined mapping makes all 59,340 text pairs legal. |

The raw full matrix remains in `text_graphic_relations.csv`, but every row now carries `TERMINAL_DISPOSITION=SUPERSEDED_NONTERMINAL`. It contributes **zero** to terminal contamination, overlap, clearance, or failure totals. Terminal relations are only `R95_REFINED_REQUIRED_RELATIONS.csv` and `occlusion_R95/P_CURVE_OPAQUE_GROUND_OCCLUSION.csv`.
