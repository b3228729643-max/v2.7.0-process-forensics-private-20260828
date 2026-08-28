# SUPERSEDED GEN2 audit snapshot

This byte-preserved snapshot binds source SHA-256
`027EC3A9B000FBB3D91C1273A289496F4CC69952757658FF823F046C9C4E2A05`
and the second local PDFs.  It is retained only as negative/algorithm-debug
evidence and is excluded from the active acceptance join.

At this point all six named repair relations, all 15 geometric semantic
relations, all 33,153 unordered foreground pairs, drawing-path reconciliation,
boundary/clip, font-floor, and occlusion gates had zero genuine hard failure.
The run remained unsealed for two identified audit defects:

1. `D_raw_pixel_object_role_audit.csv` and
   `D_same_role_scale_audit.csv` compared unlike characters or mixed semantic
   subroles by raw ink height.  Those rows are false D failures; D must use the
   same emitted point size, semantic role, concrete glyph/comparable outline,
   and baseline/script level.
2. Generic semicolon masks C0054/C0139 retained nearby foreign components.
   The already accepted independent C0153 proof establishes the exact
   two-component semicolon ownership and is used to rebuild pure native masks.

No terminal verdict, manifest, or WRITE_STOPPED marker was emitted from this
snapshot.
