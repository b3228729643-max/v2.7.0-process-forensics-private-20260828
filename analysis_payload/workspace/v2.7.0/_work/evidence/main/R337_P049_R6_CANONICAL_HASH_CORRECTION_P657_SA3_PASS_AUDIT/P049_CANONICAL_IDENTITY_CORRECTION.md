# R337 — P049 R6 canonical identity hash correction

- Correction time: `2026-08-27T13:15:30+08:00`
- Original R6 root remains zero-write and unchanged: 34 files, 4,333,519 bytes.
- R6A root remains absent; controller invocation count remains 0.

R336 described the canonical bytes as ordinal relative paths with true TAB separators, uppercase SHA-256, UTF-8 without BOM, and one final LF, but its PowerShell diagnostic accidentally used a single-quoted format string containing literal `` `t `` sequences. Single-quoted PowerShell strings do not expand backtick escapes. Therefore:

- `72FF48C16BBAC7D4DA57E9555480230BDB493FE0E23F9FBC01E9BA1C126F1D3B` is exactly the hash of the unintended two-character backtick-plus-`t` separators and is superseded.
- The corrected authorized hash using actual byte `0x09` TAB separators is `B77ADA737922FFA781C84AC7101F707E70C79C60EF33BA031729E8324D2830A9`.

Correct canonical algorithm:

1. Enumerate the 34 R6 ordinary files recursively.
2. Form forward-slash relative paths from the R6 root.
3. Sort rows with `.NET StringComparer.Ordinal` by relative path.
4. For each row emit `relative_path`, decimal bytes, uppercase SHA-256, decimal `LastWriteTimeUtc.Ticks`, joined by actual TAB byte `0x09`.
5. Join rows by LF byte `0x0A`, append exactly one final LF, and encode UTF-8 without BOM.
6. The canonical byte length is 4,071 bytes and SHA-256 is the corrected value above.

First row:

`atomic_overlay_native1x.png<TAB>139646<TAB>DD4EBA83CFF477E17573BCDC5C43084A78C25A91DB87FABD29028A5C192B1A09<TAB>639234030232812499`

Last row:

`relation_hotspots_nearest8x_part05.png<TAB>10001<TAB>1708B91E64BD7FAA399B0BD9A01679AEE488C7CAD66D676E672DD01EF0C465A1<TAB>639234030241740618`

All other R336 control-reseal requirements remain unchanged. This correction does not authorize a retry: the original one authorized controller invocation remains unconsumed and may now proceed once.
