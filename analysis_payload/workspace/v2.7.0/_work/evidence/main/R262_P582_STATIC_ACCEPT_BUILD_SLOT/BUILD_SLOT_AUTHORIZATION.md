# Revision 262 — P582 static acceptance and unique local build slot

Timestamp: `2026-08-26T21:06:07+08:00`

- Accepted HANDOFF_ID: `A-R108-P582-SA2-STATIC-20260826`.
- Source identity: before SHA-256 `C075D4A44A60B95848614543D1D2DBCCCB53F1F776FFDD79A3BF1FEAE3F6550C`; after SHA-256 `4AB4E8D14252B20576F05BD1D5CB54BCB28F162B9E33EF439BD3ED6E01DBC65C`.
- Exact scope: one source, `12+ / 12-`; only 12 explicit font declarations below `9.5pt` were raised to `9.5pt/11.4pt`; two existing `9.6pt/11.5pt` declarations are unchanged. Normalizing font declarations leaves all other source text identical; data, running means, formulas, coordinates, curves, ticks, styles, colors, caption, label, and geometry are unchanged.
- Main independent checks: `git diff --check` PASS; after source SHA exact; only the authorized source is modified; TeX processes `0`.
- R108 native collision adjudication accepted: `.640` to the first down-arrow has zero shared ink and about `18.5858px` white clearance; `.380` to the second down-arrow has zero shared ink and about `3.5858px` white clearance. No geometry change was justified before build. Main opened crop, grayscale, and both 8x ROIs without finding a current hard collision.
- Static evidence audit: payload manifests `18/18`, ordinary files `21`, bytes/SHA mismatch `0`, readonly `21/21`, WSTOP strictly latest by `219,258,318` ticks.

## Unique build authorization

A is granted the current unique TeX slot for exactly one P582 standalone/direct LuaLaTeX invocation using the established figure wrapper, a new evidence root, and a new isolated `TEXMFVAR/TEXMFCACHE/TEXMFCONFIG`. The frozen after-source SHA and wrapper identity must be checked before and after. No `latexmk`, retry, second invocation, concurrent TeX, source edit during build, commit, fresh role, or second UID is authorized.

On natural completion—success or failure—A must first emit `P582_BUILD_SLOT_RELEASED` with controller/child identity, timestamps, exit, PDF identity or explicit no-candidate state, stable source/wrapper hashes, and post-exit TeX process count. If successful, continue only non-TeX from-zero evidence with priority on `.380`/down-arrow, numeric-label/marker, tick-label/axis, clip, all unordered pairs, grayscale, and true post-observation manual records. C/P609 remains readonly and may not use TeX.
