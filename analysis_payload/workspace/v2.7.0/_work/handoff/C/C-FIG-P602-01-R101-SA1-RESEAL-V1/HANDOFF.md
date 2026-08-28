# C-FIG-P602-01-R101-SA1-RESEAL-V1

## Status

- root mechanical result: ACCEPT
- mainline acceptance: PENDING
- SA3 authorized: no
- local/global PASS accounting: not advanced by this reseal
- source writer: none
- TeX slot: disabled
- business/source files changed: NONE

This handoff accepts only the new evidence-package control closure.  It does not alter the existing FIG-P602-01 content-layer SA1 conclusion and does not authorize SA3 before mainline acceptance.

## Roots and provenance

- rejected old root, permanently read-only: D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\C_visual\evidence\FIG-P602-01\sa1_r101_initial
- new sealed root: D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\C_visual\evidence\FIG-P602-01\sa1_r101_resealed_v1
- old ordinary files: 492
- old manifest data rows: 490
- old unmanifested files: _audit_tools/build_p602_r101_measurements.py; _audit_tools/inspect_p602_page.py
- old manifest self-size mismatch: recorded 22692 bytes; actual 22780 bytes
- old rejected controls excluded from copy:
  - 00_identity/WRITE_STOPPED.json
  - 09_manifest/evidence_file_manifest.csv
- copied payload: 490 files, byte-identical and exact-mtime-identical to old-root sources
- copied payload identity mismatches: 0

Resolved source paths, destination paths, bytes, SHA-256, exact UTC mtime, mtime nanoseconds and source/destination match flags are recorded per payload row in the new manifest.  RESEAL_PROVENANCE.json records the resolved roots, rejected-control audit, old inventory identity, worktree gate and forbidden-action confirmation.

## Closed manifest model

- payload rows: 490
- control rows: 2
  - _reseal_tools/reseal_fig_p602_evidence.py
  - 00_identity/RESEAL_PROVENANCE.json
- seal rows: 1
  - 00_identity/WRITE_STOPPED.json, predeclared by exact path/bytes/SHA/mtime and written strictly last
- manifest-self rows: 1
  - 09_manifest/evidence_file_manifest.csv is the sole formal self-exclusion
- manifest entries: 493
- manifest physical lines: 494 including header
- total ordinary files: 494
- manifest missing listed targets: 0
- unlisted ordinary files: exactly the manifest itself

The marker authenticates the canonical payload/control recordset SHA-256 and declares the expected manifest entry and total-file denominators.  The manifest includes the exact identity of the final marker.  This external immutable handoff identifies the manifest self, eliminating the rejected self-referential rewrite model.

## Exact control identities

- payload/control canonical recordset SHA-256: 23AD73AA27BF8AC57DD3A7B57EF2BF307923D1C52A15446275AB6D9B1443AC39
- manifest:
  - path: 09_manifest/evidence_file_manifest.csv
  - bytes: 253663
  - SHA-256: 65919E39FDBE2CB392116D12F2E2181A314521B026D61DA17D833F164A91298B
  - mtimeUTC: 2026-08-25T03:41:40.8307748Z
- final marker:
  - path: 00_identity/WRITE_STOPPED.json
  - bytes: 2241
  - SHA-256: 7A3B3F2BD128B8162795928878F0A0B6B107C181172D67239679A54E608A2C87
  - exact predeclared mtimeUTC: 2026-08-25T03:42:40.0000000Z
  - strictly newest: true

The marker mtime was predeclared and applied as part of the final marker write so its exact identity could already be represented by the preceding manifest.  No file in the sealed root was written after that operation.

## Root mechanical acceptance

- JSON parse: PASS
- CSV parse: PASS
- manifest rows: 493/493
- ordinary files: 494/494
- per-destination path/bytes/SHA/mtime mismatches: 0
- per-source copy path/bytes/SHA/mtime mismatches: 0
- nondefault ADS: 0
- .pyc/.pyo files: 0
- __pycache__ directories: 0
- files at or after marker mtime other than marker: 0
- marker strictly newest: true
- old root ordinary files after reseal: 492
- C worktree clean: true
- branch: v2.7.0/dialogue-c-visual
- HEAD: eea4060c5229168e2b973bbaea81cf391e7a9dfd
- source SHA-256: 18B88F4BC48A21D3FD1A246AC5B6909DEEB19900A3D0721C65F9A44369444084
- R101 PDF SHA-256: 0870FF226DC383875C4A1B6EABB06AAB942317DA294D90D2864B3030D46DF1A1
- R101 page identity: PDF page 651 / printed page 638
- native page PNG SHA-256: 8E0DCE21A10BFCAAA5A5BE40627110E262459C0BE586626C9AF4EC8CAEC03C71

## Preserved content-layer state

- manual ledger state in the new marker: ADJUDICATED_PASS
- objects: 26/26
- glyph ledger: 175 rows / 175 unique / 175 explicit PASS
- pair ledger: 325 rows / 325 unique / 325 explicit PASS
- critical intersections: 8/8
- peers: 27/27
- roles: 50/50
- clipping: 26/26
- NEEDS_SOURCE_WRITER: no
- NEEDS_TEX_SLOT: no

No machine denominator was regenerated and no manual conclusion was edited.  These are preserved content facts, not new local/global accounting.

## Forbidden actions confirmation

- old root modified: no
- source or chapter modified: no
- machine evidence rerun: no
- manual result changed: no
- TeX/LuaLaTeX/latexmk/build run: no
- SA3 started: no

## Mainline next action

Read-only verify the exact manifest and marker identities above, then either accept or reject this reseal.  Until explicit mainline acceptance, keep SA3 disabled and do not increment local/global PASS counts.
