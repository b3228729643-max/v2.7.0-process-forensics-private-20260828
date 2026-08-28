# Object, relationship, and clipping coverage

- Visible semantic text/formula elements: 45 (`semantic_text_inventory_machine.csv`).
- Non-background graphic objects: 17 (`graphic_object_inventory.csv`), with final-visible/pre-occlusion/halo fields in `object_inventory.csv` and draw order in `draw_order_evidence.json`.
- Total audited objects: 62.
- All unordered pairs: 1891, recomputable as 62 choose 2 (`all_unordered_pairs.csv`).
- Required 9.2.1 relationships: 1686 (`mandatory_relationships.csv`).
- Text, text-to-graphic, and graphic relationships retain final-visible masks; opaque background/halo is never substituted for ink. This figure has no opaque text-label backgrounds.
- Clip pixels: 0; clip failures: 0 (`clip_report.csv`).

The only measured required-pair failure is `P0717` (`E014` down arrow against `E016` `.380`): 3 actual native 300dpi pixels overlap, its minimum clearance is 0.0px, and its required clearance is 4px. The direct raw/A/B/intersection/overlay 1:1 and nearest-8× files are in `roi_packages_r2_geometry_isolated/P0717_E014_E016/`.
