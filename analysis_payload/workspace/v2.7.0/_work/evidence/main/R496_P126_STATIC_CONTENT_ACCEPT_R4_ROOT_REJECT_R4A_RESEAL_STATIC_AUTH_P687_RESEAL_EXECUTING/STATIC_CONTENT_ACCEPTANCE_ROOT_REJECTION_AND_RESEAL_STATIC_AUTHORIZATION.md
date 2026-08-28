# R496 — P126 static content acceptance, R4 root rejection, and R4A static authorization

- Time: `2026-08-28T10:33:18+08:00`
- Existing content handoff: `A-R115-P126-SA2-STATIC-LEGEND-SEGMENT-PATCH-20260828`
- P126 remains `SA2`; build remains forbidden.

Main independently confirmed the live source is 4,356 bytes/SHA-256 `3185834A7D4DEAC1595C244DA626FF52B5308E733AFD851E8FF508037C51ED75`. A single regex match covers the new custom legend-image block; replacing only that block in memory with the authorized prior declaration reconstructs exactly 4,224 bytes/SHA-256 `366C905854F0F3952225600D5BD66AAB706B637A453FD23DDF9611E4C002AC20`. The custom image contains four 0.08 cm teal segments and three 0.10 cm gaps. Conservatively subtracting the full 1.05 pt stroke width leaves 0.06310 cm or 7.452 px at 300 dpi, above the required 0.05 cm or 5.906 px. This accepts only the STATIC_ONLY content direction, not render PASS.

The frozen R4 controller is 11,144 bytes/SHA-256 `BA3C40F54EC9B65E8A25F1010FB6523D157EE6142998ABDAE8DFAF042D08A67A`, ReadOnly. Its unique invocation failed at line 101 because a PowerShell directory object has no `IsReadOnly` property. Main confirmed the failure scene has eight files, all ReadOnly, one directory/root still writable, no marker, and a six-row manifest with zero missing/hash mismatch. R4 is classified `UNSEALED_CONTROL_FAILURE_BEFORE_MARKER` and frozen without repair.

Only STATIC PREPARATION is authorized for a new sibling:

- HANDOFF: `A-R115-P126-SA2-STATIC-LEGEND-SEGMENT-PATCH-CONTROL-RESEAL-V1-20260828`
- Operation: `P126_R115_R4_STATIC_EVIDENCE_ONLY_CONTROL_RESEAL_V1`
- Destination: `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P126-01\STRICT_R4A_SA2_STATIC_LEGEND_SEGMENT_PATCH_CONTROL_RESEAL_R115_20260828`
- Copy exactly the six manifest-bound material files; copy the old manifest and audit zero times.
- Add `COPY_IDENTITY` and resolved provenance for payload 8; create exactly three controls for ordinary file count 11.
- Bind canonical relative/resolved path, bytes, SHA-256, Creation and LastWrite FILETIME; enforce full-tree ReadOnly; prebuild a multiline no-BOM marker outside the root with a sufficiently future FILETIME and move it as the sole final root operation; independently audit source-before/after, postmarker zero-change, strict latest including root, parse/ADS/cache-pyc/reparse.

Return frozen ReadOnly controller/auditor identities, AST/site checks, empty-safe/canonical microtests, new-root/stage/result absence, and invocation0/0, then pause. Execution, repair, business rerun, TeX/build, commit, and role migration are not authorized.
