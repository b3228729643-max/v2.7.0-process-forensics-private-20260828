# Evidence index

This root contains the sole fresh SA2 R168 read-only adjudication for `FIG-P660-01` under HANDOFF `C-FIG-P660-01-R111-SA2-R168-READONLY-ADJUDICATION-V1`.

- `01_input_identity/`: exact official PDF/source identity and the frozen 30-object denominator hash.
- `02_location/`: machine text extraction and the independent physical-page/printed-page location.
- `03_renders/`: full-page and adjacent-page integration renders, native 300 dpi figure crop, and grayscale.
- `04_overlays_masks/`: text/object overlays, separated masks, composite, and the all-pairs matrix.
- `05_roi/`: R01–R11 native1x and nearest-neighbor8x critical ROIs actually opened before manual judgment.
- `06_machine_tables/`: text/vector coordinates, native pixel metrics, source/PDF font audit, glyph codepoints, simplex calculations, crop-edge metrics, and the complete 435-pair enumeration. These files contain machine fields only.
- `07_manual/`: frozen denominator, 30 individualized object findings, 19 individualized candidate-pair adjudications, overlap accounting, model route, full read-only report, and final R168 disposition.
- `08_seal/`: final manifest/closure and the unique last `WRITE_STOPPED` marker.
- `scripts/`: machine-only evidence builders used for extraction and calculations; no script writes manual reviewer, verdict, decision, or note fields.

Final disposition: `SA2_NO_SOURCE_CHANGE_READY_FOR_FRESH_SA1`.
