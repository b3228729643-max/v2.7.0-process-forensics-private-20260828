# FIG-P609-01 — R97 root failure acceptance

- Root decision: **ACCEPT `FAIL_TO_SA2`**.
- This accepts the independent SA1 failure for routing only; it is not a figure PASS and does not increase the strict-final count.
- Official candidate: R97 `main_full.pdf`, 813 pages, physical page 659 / printed page 646, figure 32.9.
- Official PDF SHA-256: `062AD81020CB19A5C6688A45C73E00965F5060E0960A69AF820D7DC154DEE814`.
- Read-only source SHA-256: `20687D1EE01AABA9B605591A61781CF688328026E0645AD51B6E02E921DC98A2`.

## Root native-pixel review

Root opened the official full-page, native 300 dpi figure, standalone, grayscale and measurement-overlay views. Root also opened the seven 8x-nearest glyph sheets containing every dispositive failure and checked their original/target-overlay/mask-only triplets. The masks identify the intended glyphs and the reported under-height strokes are visible at actual pixels.

The independent SA1 completed 148/148 rawdict ledger rows, including 144 reader-visible glyphs and four named zero-width combining controls. Its complete foreground denominator is 59 objects and `59 choose 2 = 1,711` unordered pairs; 40 critical/contact relations were individually card-reviewed. Two mathematical rules, five accent associations, 36 mapped foreground drawing paths, two excluded background fills, three crop-proximity cards, all z-order rows, four global views, grayscale, D/E and font harmony are closed. Those passing gates cannot offset a glyph hard failure.

## Dispositive hard failures

- GL024 `=`: 12 px < 22 px.
- GL026 `⋯`: no eligible exact same-codepoint/font/role reference for the required independent H/area `[0.92,1.08]` low-profile calibration.
- GL034 `F`: 23 px < 24 px.
- GL045 `：`: no eligible exact same-codepoint/font/role reference for the required independent H/area `[0.92,1.08]` low-profile calibration.
- GL065 `=`: 12 px < 22 px.
- GL072 `=`: 11 px < 22 px.
- GL076 `−`: 3 px < 22 px.
- GL088 `=`: 12 px < 22 px.
- GL109 `=`: 12 px < 22 px.

Each failing target has a pure native mask. Purity, source point size, pair clearance, global readability, or visual harmony does not cure an under-threshold glyph or an unavailable mandatory calibration.

## Independent package integrity

Root re-enumerated and rehashed the sealed package:

- actual files: 1,238;
- evidence-manifest entries: 1,236;
- MANIFEST rows: 1,235, with its path set exactly matching the evidence entries other than the MANIFEST self-entry;
- missing files, byte mismatches, SHA-256 mismatches and path-set differences: 0;
- zero-byte files: 0; non-default ADS: 0; ADS enumeration errors: 0;
- files newer than `WRITE_STOPPED`: 0, and `WRITE_STOPPED` is the final write.

The root-computed evidence-manifest SHA-256 is `420411153EABD7B8B44333DC8763CC142E3DEE9CC26C4EE4230CADF6E1FB5E93`; the MANIFEST SHA-256 is `A2D1C2096036877FB2A4CFD62ADA5BD1D203F707B20D0E254DB23A2404851B98`. Terminal and bottom tables agree on `SA1_FAIL_ROUTE_SA2` / `FAIL_TO_SA2`.

## Required next role

Route FIG-P609-01 to the unique serial SA2 queue. It must not modify source while another figure owns the single business-source writer slot. After a minimal repair, root must build a new official full-book candidate, then require a fresh independent SA1, a fresh isolated SA3 and root acceptance before this figure can close.
