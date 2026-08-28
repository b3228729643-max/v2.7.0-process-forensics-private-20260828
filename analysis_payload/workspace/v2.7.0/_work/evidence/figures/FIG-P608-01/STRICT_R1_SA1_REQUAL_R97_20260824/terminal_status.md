# Terminal status — FIG-P608-01 SA1 R97

## `FAIL_TO_SA2`

This is a terminal evidence finding, not a source edit. Candidate/source identity is hash-rechecked and unchanged.

- Candidate SHA-256: `062AD81020CB19A5C6688A45C73E00965F5060E0960A69AF820D7DC154DEE814` (813 pages)
- Source SHA-256: `DA035C1920CB900E54D3658851C1D71D9C6446531EFF50BEE6E089B567835AE4`
- Scope: Figure 32.8, PDF physical 659 / printed 646, P608-only crop.
- Completed: 102 objects; 5,151/5,151 pairs; 114/114 signed glyph cards; 110/110 signed contact/critical cards; 93 individual intent records; R001/R002 independently reviewed; 15 low-profile calibrations.

### Dispositive failures

- Glyph gates: G008, G019, G027, G058, G063.
- Cross-panel pair gates: P2311, P2315, P3071.
- P3071 is R002 lower-title overbar to G001 upper x-axis: pre-zorder shared 64px; final unique overlap 0px; final clearance 0px < 8px.
- Normal labels meet >=9.5pt, but D/E visual coordination still fails at that title/axis relationship.

Five target-reference/data-marker pairs are individually justified `INTENTIONAL_DATA_RELATION` entries, not residual pair failures; see `intentional_data_relation_review.csv`.

Manifest and `WRITE_STOPPED` follow this terminal file.
