# R324 — FIG-P657-01 R111 SA2 root rejection and one read-only control-reseal authorization

- Time: `2026-08-27T11:30:57+08:00`
- UID: `FIG-P657-01`
- HANDOFF_ID: `C-FIG-P657-01-R111-SA2-R168-READONLY-ADJUDICATION-V1`
- Actual instance: `/root/sa2_fig_p657_r111_r168_readonly_v1`
- Rejected root: `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\C_visual\evidence\FIG-P657-01\sa2_r111_r168_readonly_adjudication_v1`

## Central decision

`CONTENT_PASS_DIRECTION_PRESERVED / ROOT_REJECT_READONLY_FREEZE_REQUIRED / NO_FRESH_SA1`.

The original root must remain byte- and metadata-unchanged. It must not be resumed, edited, retimestamped, frozen in place, or resealed in place, and it cannot authorize fresh SA1.

## Independently accepted content direction

- The official R111 PDF and current source hashes independently match `DAB1062500E39DD2C34C6B4A9FF51CAC2BE0A4C84B2F45F5FB8E645C4BC012D6` and `B2B3A8748133B55169F08A543DF39E238E2FB3DFFF67EA0067C543CD9FDE31D2`.
- The figure is independently localized at physical page 706 / printed page 693 / Fig. 34.3.
- Frozen foreground denominator is `N=210` (`186` glyphs + `24` foreground drawing primitives); six node fills are separately accounted backgrounds; all unordered pairs are `C=21945`.
- Critical relations are `36`; all `17` nonzero raw-mask pairs (`1378` pixels) are intentional arrow-to-own-node or shaft-to-own-arrowhead joins.
- Genuine manual coverage is glyph `186/186`, drawing `24/24`, critical `36/36`, views `8/8`, semantics `16/16`, and hard gates `12/12` after opening 19 glyph sheets, 6 drawing sheets, 36 native1x ROIs, 36 nearest8x ROIs, and all eight core views.
- Six nodes, seven relations, legend, caption, and prior-family/likelihood-family semantics are consistent. The 8.8/9.2/9.4 pt declarations are advisory by value alone under R168. Missing/tofu/wrong codepoint, unreadability, severe imbalance, clipping, illegal overlap, and semantic/geometric hard defects are all zero.
- Therefore the business route remains `SA2_NO_SOURCE_CHANGE_READY_FOR_FRESH_SA1`, subject to a valid sealed root.

## Independent root recomputation

- Manifest declared/rows/actual payload: `487/487/487`; ordinary files: `489`; directories excluding root: `9`.
- Duplicate/missing/extra/path-bytes-SHA mismatch: `0/0/0/0`.
- REPORT/HANDOFF/MANIFEST/WRITE_STOPPED hashes exactly match the handoff: `7D40F0A8...B9863D`, `951B4FBF...750F7`, `31124953...48700`, `E8B46E8C...CCD55`.
- JSON/CSV/PNG parsing, ADS, cache/pyc, reparse and terminal TeX findings are zero.
- `WRITE_STOPPED` is unique and strictly latest: marker ticks `639233926490970307`, maximum other-file ticks `639233925916240235`, margin `574730072`, files at-or-after excluding marker `0`.
- Decisive failure: read-only files `0/489`; read-only directories including root `0/10`; writable items `499/499`. The report's content seal is intact, but the mandatory read-only freeze is absent.

## Exactly-once evidence-only authorization

C may run exactly one root-external PowerShell 7 controller, invocation count one and retry count zero, into this startup-absent sibling root:

`D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\C_visual\evidence\FIG-P657-01\sa2_r111_r168_readonly_adjudication_reseal_v1`

The controller must:

1. Assert the new root is absent and the original root identities above still match, without writing the original root.
2. Copy only the 487 paths bound by the original manifest, preserving every relative path, byte count, SHA-256 and NTFS last-write tick; copy neither original control (`MANIFEST.json`, `WRITE_STOPPED`).
3. Add exactly `COPY_IDENTITY.csv` (487 source-to-destination rows) and resolved `COPY_PROVENANCE.json`; new payload is therefore exactly `489` files.
4. Create exactly three new controls: a `489`-row path/bytes/SHA/ticks payload manifest, a resolved seal audit, and one final `WRITE_STOPPED`; final ordinary-file count is exactly `492`.
5. Before the marker enters the new root, complete all payload/control identity, count, parse, ADS/cache/pyc/reparse checks and set all existing `491` files plus every directory including the root to Windows ReadOnly.
6. Prepare `WRITE_STOPPED` outside the new root, with all fields resolved, a last-write tick strictly later than every new-root file, and its ReadOnly attribute already set. Move that prepared marker into the new root as the sole final root-content operation. No file or directory attribute/content mutation is permitted after that move.
7. Run one root-external read-only auditor proving source-to-destination `487/487` identity, manifest `489/489` identity, ordinary `492`, every file/directory read-only, parse and hygiene gates zero, one strictly-latest WSTOP, at-or-after excluding marker zero, and post-marker root writes zero.

If the single controller cannot meet the sequence, it must stop and report failure without retry or workaround. PDF/render/object/pair/manual/semantic work must not be rerun or changed. TeX, source/PDF/Git/central-state writes, fresh SA1, second UID and second role remain forbidden. Only a successful new-root audit may restore `SA2_NO_SOURCE_CHANGE_READY_FOR_FRESH_SA1`, and Main must accept that root before any fresh SA1 starts.

Inventory remains `31 SA1 / 42 SA2 / 1 SA3 / 25 local pass`; strict final remains `0/99`.
