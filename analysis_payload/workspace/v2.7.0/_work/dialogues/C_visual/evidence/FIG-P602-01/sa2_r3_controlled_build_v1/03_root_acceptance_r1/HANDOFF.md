# FIG-P602-01 R3 fresh root acceptance handoff

Token: `P602_R3_NATIVE_EVIDENCE_SEALED_FRESH_ROOT_ACCEPTED_LOCAL_PASS_CANDIDATE`

The independent C-root audit accepts the sealed evidence root as `C_LOCAL_PASS_CANDIDATE_PENDING_MAIN_ACCEPTANCE`. This is not a central inventory write or a global PASS.

## Immutable identities

- Candidate PDF: 41,653 bytes; SHA256 `68188DAAAF9B3C4233D5A032C3D8BE20A73B51D5E6058D0E1C12FDE6471093E7`.
- Source: 2,869 bytes; SHA256 `6C4E8F156709C0FF384F9E7B7F2BD5D9CB586E24206BF0BCD2E58933ED3DB47D`.
- Sealed evidence manifest: SHA256 `517A70CB6C3A15253133348C6EEB5214BFFB0FD038480A1FBFBED01B04809D05`.
- Sealed evidence WRITE_STOPPED: SHA256 `1420591BE0672AC4580D8C1551E131E4DD2D82F8FFE96BF4EC9A9E8C52B206C6`.
- Canonical manifest recordset: SHA256 `100A570015E6F749624465C59464E4E14EEE00432A97E026BA56B457DFD697C3`.
- Complete sealed-root snapshot: SHA256 `E4C86F24E49EE5CF89C1CEC09D5E37ED188563083F61B83F5DEC729CEACFE72F`.
- Fresh root acceptance report: 7,181 bytes; SHA256 `03C72281DED4F501294CDF801F5DA301A90134591ABE537E70F9F3EB359D3339`.

## Root result

The evidence root contains 896 ordinary files and 894 manifest rows. Its only unlisted files are the manifest itself and `identity/WRITE_STOPPED.json`. Path duplicates, missing paths, bytes mismatches, SHA256 mismatches, and NTFS 100 ns mtime mismatches are all zero. All 896 files are read-only; WRITE_STOPPED is strictly latest; the audit observed zero evidence-root writes.

The fresh audit parsed 19 CSV files and 7 JSON files, opened all 864 PNGs, found ADS0 and pyc/cache0, and confirmed TeX-family processes0. Worktree HEAD is `eea4060c5229168e2b973bbaea81cf391e7a9dfd`; branch is `v2.7.0/dialogue-c-visual`; the sole changed path is the authorized P602 source.

Fresh current denominators are 30 objects, 154 glyphs, 435=C(30,2) unordered pairs, 16 critical pairs, 28 peer rows, 3 role rows, 30 clip rows, 4 views, and 12 hard gates. Machine failures0 and manual failures0. All manual IDs and notes are unique and nonblank; every pair endpoint matches its machine row. G032 `范` independently closes at 37x34 ink with machine/manual/hard PASS.

No commit, shared-state write, inventory write, fresh role, next figure, or further TeX invocation occurred. P654 R20 holds the global build lock; C neither starts nor manages that build.
