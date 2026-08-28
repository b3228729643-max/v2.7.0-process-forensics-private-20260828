# R1C metadata-only reseal provenance

Source package reused read-only: `STRICT_R1B_SA1_FRESH_R99_20260824` in the sibling FIG-P715-01 evidence directory.

R1C was initialized by copying the completed bottom-layer source files while excluding only R1B terminal wrapper artifacts with incorrect model metadata or non-strict final-marker timing:

- `machine_terminal_check.json`
- `evidence_manifest.json`
- `after_visual_acceptance.md`
- `SA1_HANDOFF.md`
- `RESULT.json`
- `WRITE_STOPPED`
- `after_model_route.md`

The copied `audit_fresh_r99.py` is changed only in its terminal metadata/sealing path: actual SA1 route is `gpt-5.6-terra/max`; terminal reports are included in the new manifest; and a 1.2-second delay precedes the last `WRITE_STOPPED` write. No `build` or `mark-reviewed` phase is run in R1C, no PDF is rendered, no source is changed, and no result field about the figure is relaxed.
