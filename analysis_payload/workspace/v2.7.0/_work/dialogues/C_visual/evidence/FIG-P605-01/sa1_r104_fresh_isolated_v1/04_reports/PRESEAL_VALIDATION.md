# Pre-seal validation

Read-only cross-checks were run after all manual ledgers and reports were authored.

- glyph machine/manual/unique: 150 / 150 / 150; missing 0; extra 0; all reviewers and per-glyph notes present.
- object machine/manual/unique: 32 / 32 / 32; missing 0; all masks nonempty; all crop-edge touches 0.
- pair expected/machine/manual/unique: 496 / 496 / 496 / 496; machine-to-manual object mapping mismatches 0; missing 0; extra 0; empty reviewer/decision/note fields 0.
- pair manual classifications: CLEAR_SEPARATE 484; DESIGN_CONNECTION 10; MASK_CONTAMINATION_CONFIRMED 2.
- critical pair rows/unique: 14 / 14; each ROI directory contains exactly six evidence files; raw/design/contamination/illegal partition is 86 / 80 / 6 / 0 px.
- view rows: 4; all four marked actually opened and hard-pass.
- source-font rows: 4; all actual-readable and no severe imbalance.
- semantic rows: 7; all source-checked, PDF-checked and hard-pass.
- alternate data streams: 0.
- `__pycache__` directories: 0; `.pyc` files: 0.
- pre-seal manifest exists: false; pre-seal marker exists: false.

This validation was read-only and did not generate or change any manual decision.
