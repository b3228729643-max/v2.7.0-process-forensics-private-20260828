# P049 R4 external root audit

Verdict: `ROOT_ACCEPT_R4_LOCAL_SA2_PASS_AWAIT_OFFICIAL_CANDIDATE_AND_FRESH_SA1`.

## Bound identities

- HANDOFF_ID: `A-R110-P049-SA2-DIRECT-BUILD-R4-20260827`
- Evidence root: `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P049-01\STRICT_R4_SA2_R3_GUIDE1_DIRECT_BUILD_R110_20260827`
- Source SHA-256: `27BF53A0673A2D57308A836827CC8F0463BE725A11D6826E6BB94CAA91A9BB7E`
- Wrapper SHA-256: `ABF070666B10C0FA5B492FFEF2228728108A2EBE85F6077E40615C9F37B67F61`
- Local PDF: 43,378 bytes, SHA-256 `DF2418922BA64F670443F509194588764D760E193B306D445E5EEFC78A5752D9`
- One-time seal controller: 4,074 bytes, SHA-256 `5E6AC114AD0A24EB174DA3E67EC1D4A3AF257248934FE8664B5477E6B3EF935F`, AST errors 0, invocation 1, exit 0.

## Content result

- Final denominator: N=27 (14 text + 13 graphic), all unordered pairs C=351.
- Focused critical relations: 45.
- Machine hard failures: 0 after one transparent object-specific mask adjudication.
- Manual closure: objects 27/27 PASS, focused relations 45/45 PASS, opened views 13/13 PASS.
- Guide1 endpoint: exact `c3` equality `49/625 + 576/625 = 1`.
- Guide1/Guide2 shared ink 0, clearance 72.591 px; Guide1 forbidden shared ink sum 0.
- Raw pair `P0110` retains four candidate mask pixels. Native 1x and nearest 8x inspection shows a continuous white gap between `c2` label ink and `c3`; final illegal overlap is 0.
- R168 hard defects: 0.

## Seal and filesystem audit

- Payload files: 69.
- Controls: 3 (`PAYLOAD_MANIFEST.csv`, `PAYLOAD_MANIFEST.json`, `WRITE_STOPPED.json`).
- Ordinary files: 72.
- CSV rows / JSON rows / enumerated payload: 69 / 69 / 69.
- CSV to JSON to filesystem path, bytes, SHA-256 and NTFS ticks mismatches: 0.
- Read-only ordinary files: 72/72; read-only directories including root: 6/6.
- JSON/CSV parse failures: 0.
- ADS / cache-or-pyc / reparse: 0 / 0 / 0.
- `WRITE_STOPPED` ticks: `639233818004154805`.
- Maximum other-file ticks: `639233818003127001`.
- Strict latest margin: 1,027,804 ticks; files at or after marker excluding marker: 0.
- Manifest CSV SHA-256: `D801983CCBEE18EC59BC1D84D96E635191B0C1336C802157BA0588A0C0A5817F`.
- Manifest JSON SHA-256: `CCB8A967140738CD1EDC7170AD711824371C6BCA03A56FE3FAFDE33F959AD54C`.
- `WRITE_STOPPED` SHA-256: `B4E7D3B2E8753EE9EC2AA6921F299DD358A72B2857C081137C4787D5CF9E8763`.
- TeX processes after all non-TeX review and seal: 0.

## Git boundary

The worktree has exactly one unstaged source modification and an empty index. The exact diff is one deletion and one insertion on Guide1 only:

`(s1.west)--(axis cs:3.72,2.66)--(axis cs:2.75,1.36)`

to

`(s1.west)--(axis cs:1.20,2.45)--(axis cs:.84,1.728)`.

`git diff --check` passes. No commit has been created. This root is accepted only as local SA2 evidence pending main commit authorization, main integration, a new official full-book candidate, and completely fresh isolated SA1.
