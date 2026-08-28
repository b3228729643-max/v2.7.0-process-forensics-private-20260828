# FIG-P547-01 — R97 local SA2 root acceptance

- Root decision: **ACCEPT `LOCAL_PASS_TO_ROOT_BUILD`**.
- This is permission to use the current local source as the next official full-book build input only. It is not a figure PASS, does not close FIG-P547-01, and does not increase the strict-final count.
- Frozen official input candidate before this build remains R97 `main_full.pdf`, 813 pages, SHA-256 `062AD81020CB19A5C6688A45C73E00965F5060E0960A69AF820D7DC154DEE814`.
- Authorized figure source SHA-256 changed from `638CEA4285D3A9411251DA149963CC7AE4500FA5827F0A99A51FF1FC76640D1A` to `DF3D4415EDC56D02E056CAE0F3E38830DF28E781BC67ECDFB69863C5038F1600`.
- Root independently confirmed that the current source and the R7 source snapshot are byte-identical. The only business-source changes are local TikZ relation geometry, label padding/raising, bridge endpoints, and the semantically equivalent label rewrite `同一条` → `物理边`; no whole-figure scale or public style changed.

## Root native-pixel and visual review

Root opened and reviewed the complete local evidence views rather than accepting the SA2 summary alone:

- all 17 glyph contact sheets covering 193/193 glyphs;
- all 7 graphic contact sheets covering 65/65 foreground graphic objects, including the four native tiles replacing the oversized third sheet;
- both mathematical-relation sheets covering 12 geometric equals and 3 geometric arrows;
- all 40 critical/intentional native 1x plus 8x-nearest contact cards;
- all six named repair sets and both supplemental prior-failure cards;
- the corrected C0114 and C0153 current cards plus the historical-semicolon clean/calibration cards;
- native full-page, figure, standalone, grayscale, caption, low-profile calibration, and six reverse-occlusion views.

No new illegal overlap, clipping, missing stroke, foreign-pixel contamination, or visually abrupt font was found in those opened artifacts. The minimum explicit normal source size is 9.6 pt. Natural scripts remain separately classified and are not used to lower the normal-text floor.

The current local denominator is 193 glyphs plus 65 foreground graphic objects = 258 unique objects and `258 choose 2 = 33,153` unique unordered pairs. Root checked the closed classifications: 33,114 ordinary PASS plus 39 individually named intentional contacts, with zero unclassified or failing pair. The 12 geometric equals measure 26–30 px high and the three geometric arrows measure 23–24 px, all above their 22 px gate. The old 6 px CJK `一` is not relabelled as a pass; the wording was changed to `物理边`, whose three glyphs measure 44/41/43 px.

The four prior 1 px clearance failures now measure 31.0644, 13, 31.7805 and 10 px against the 3 px hard gate. The 10 px right focus-border clearance is below an optional 12 px preference but is visually natural and satisfies the applicable hard gate; this is recorded as a non-waived design note, not an exemption.

The GEN3 C0114 mask contamination was corrected through exact component ownership, and the current C0153 digit zero is kept in a separate namespace from the historical semicolon calibration. Root found no denominator mixing between those identities.

## R7 and R7A integrity

The original R7 package had a real seal-coverage defect: its Python path enumeration omitted 60 pre-seal, superseded LuaTeX/font-cache files from the claim that all superseded files were hash-covered. Root therefore rejected the original coverage claim until the independent R7A addendum was sealed. R7 itself and the business source remained immutable.

Root independently re-enumerated R7 with the Win32 extended-path prefix and verified:

- 6,732 actual files and 6,672 listed/seal-metadata paths;
- exact difference of 60 files, all confined to the two superseded `low_profile_calibration/texmfvar` trees, GEN2 30 and GEN3 30;
- ACTIVE omissions 0, stale listed paths 0, and files written after R7 `WRITE_STOPPED` 0;
- all 60 CSV rows match their actual relative path, byte count, SHA-256, CreationTime and LastWriteTime;
- all 6,670 original R7 MANIFEST rows rehash with parse, duplicate, missing-reference and SHA-256 errors all 0.

Bound R7 identities are:

- `evidence_manifest.json`: `9CDE425189C7149504C95DF4658B5572ED06EA2379CC6897178EC4E04AEE032E`;
- `MANIFEST.sha256`: `E09227E2B66CE15F76891ADF7F943AB90402F27DF0CEADC37DECA2A2232A2C0F`;
- `WRITE_STOPPED.md`: `01871051A57F9A64F0EE6D6935A41198D7350D74414EDB1B0A677643B8C4F80A`.

The separate R7A addendum closes as 9 actual nonzero files = 6 payload + evidence manifest + MANIFEST + final `WRITE_STOPPED`. Root rehashed every entry with zero mismatch and confirmed the stop file is the last write. Its evidence-manifest SHA-256 is `20728026B5FD8D794603BD119F4231EA6D7CC770B0F80D41122D476F71C682FB`; its MANIFEST SHA-256 is `E9AF131FD372BEBEC2BBC425EC54C41946E6A1069A4C2FA4A4A5032413AE68E8`.

## Required next role

Root may now build a new official full-book candidate through `build_v2.7.0.ps1 -NoPublish`. Only after that candidate passes full-book build gates and page-isolation checks may a fresh independent SA1 inspect FIG-P547-01 from the new official PDF. A subsequent fresh isolated SA3 and final root acceptance remain mandatory.
