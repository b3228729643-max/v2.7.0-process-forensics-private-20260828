# Revision 263 — P582 build release and P609 root rejection/reseal authorization

Timestamp: `2026-08-26T21:17:29+08:00`

## P582 build release

- Accepted build identity: `A-R108-P582-SA2-DIRECT-BUILD-20260826`.
- Exactly one PowerShell 7 controller (PID `19496`) and one direct LuaLaTeX child (PID `23084`) ran naturally from `2026-08-26T13:14:12.8569568Z` to `13:15:09.4964861Z`, duration `56.64s`, exit `0`, invocation `1`, retry `0`, latexmk `0`.
- New PDF exists and was independently rehashed: `31,330` bytes, SHA-256 `988E672096CC34E5A9B1634D84D150C644A0E07B049D81A92FACFE7276269F5B`.
- Source and wrapper before/after identities are stable. Post-exit TeX process count is `0`; the unique slot is released. A may continue only non-TeX evidence from this PDF.

## P609 root rejection

- Business direction is accepted as content PASS / `P609_SA2_NO_SOURCE_CHANGE_READY_FOR_FRESH_SA1`, but the original root is rejected as a sealed handoff.
- Main independent audit of the original root: ordinary `32 = 29 payload + 3 controls`; manifest rows `29`; duplicate/missing/extra/bytes/SHA mismatches `0`; JSON/CSV/ADS/cache/pyc/reparse gates have no contrary finding; WSTOP is strictly latest by `345,515,664` ticks; representative color/grayscale/overlay/axis/formula/arrow views pass.
- Decisive control defect: writable files `32/32`; root directory writable. The original root is permanently frozen as `CONTENT_PASS_DIRECTION / ROOT_REJECT_READONLY_FREEZE_MISSING`; it must not directly authorize fresh SA1 and must not be modified or resealed in place.

## One-time P609 evidence-only reseal authorization

C is authorized for one new root-external PowerShell 7 controller invocation only. The new root must be absent before start. Copy exactly the original 29 material payload files, excluding the old `evidence_manifest.json`, `SEAL.json`, and `WRITE_STOPPED`; preserve each copied file's relative path, bytes, SHA-256, and NTFS mtime ticks. Add exactly two new payload controls, resolved `COPY_IDENTITY.csv` and `COPY_PROVENANCE.json`, giving projected payload `31`. Write a new manifest and new seal control, then write the new WSTOP as the final root file: `31 payload + manifest + seal + WSTOP = 34 ordinary files`.

Before completion, assert manifest↔filesystem path/bytes/SHA/mtime equality, old controls copied `0`, all files readonly, all directories including root readonly, ADS/cache/pyc/reparse `0`, WSTOP strictly later than every other file, and post-marker file writes `0`. No business evidence, visual review, semantic calculation, manual ledger, source, TeX, Git, role, UID, or central state may be rerun or changed. Invocation `1`, retry `0`; any failure stops the chain and leaves that new root immutable.
