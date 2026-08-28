# FIG-P608-01 — R97 root rejection acceptance

- Root decision: **ACCEPT `FAIL_TO_SA2`**.
- This accepts the independent SA1 failure for routing only; it is not a figure PASS and does not increase the strict-final count.
- Official candidate: R97 `main_full.pdf`, 813 A4 pages, physical page 659 / printed page 646, figure 32.8.
- Official PDF SHA-256: `062AD81020CB19A5C6688A45C73E00965F5060E0960A69AF820D7DC154DEE814`.
- Read-only source SHA-256: `DA035C1920CB900E54D3658851C1D71D9C6446531EFF50BEE6E089B567835AE4`.

## Root pixel and denominator review

Root opened the native 300 dpi figure and the 8x nearest-neighbour critical overlays for the upper-panel x-axis versus the lower-panel `\overline X_{6:t}` title. The axis and overbar are visibly contiguous. The independent masks report 64 shared pre-z-order pixels, zero final-unique overlap after paint order, but zero final-visible clearance against the required 8 px; vector geometry independently reports 0.044765 pt penetration. Paint order therefore does not make this legal.

The final denominator is internally closed: 36 text objects + 66 graphic objects, including two separately inventoried `GRAPHIC/MATH_RULE` overbars, gives 102 objects and `102 choose 2 = 5,151` unordered pairs. All 46 in-scope drawing paths are assigned, with zero unassigned visible foreground paths. Root independently checked the following row counts and terminal classifications:

- glyph ledger: 114/114 rows; 109 manual PASS and 5 manual FAIL;
- critical/contact ledger: 110/110 manually reviewed rows;
- named intentional contacts: 93 individually reviewed rows, with no class-wide exemption;
- pair universe: 4,954 clearance PASS, 93 intended contacts, 101 background-occluder N/A, and 3 hard FAIL;
- mathematical rules: 2/2 manual rows complete;
- low-profile calibrations: 15/15 complete;
- full-page, native figure, standalone, grayscale and 8x critical visual rows: 5/5 complete, all correctly retain the global D/E failure.

## Dispositive hard failures

- `G008` `=`: 12 px < 22 px.
- `G019` `=`: 11 px < 22 px.
- `G027` and `G058` natural-script `t`: 10 px < the applicable 15 px script gate.
- `G063` `运`: 16 foreign pixels from upper tick object `G005`, caused by the cross-panel collision.
- `P2311` lower title `T027` versus upper x-axis `G001`: 2 px < 8 px.
- `P2315` lower title `T027` versus upper tick `G005`: 16 px overlap and 0 px clearance.
- `P3071` upper x-axis `G001` versus lower-title overbar `R002`: 64 pre-z-order shared pixels and 0 px final-visible clearance < 8 px.

The five y=2 target-reference/marker relations `P5003`, `P5008`, `P5009`, `P5011` and `P5012` are accepted only as five separately evidenced `INTENTIONAL_DATA_RELATION` cases tied to t=10/15/16/18/19. This decision is not a reusable class exemption.

Normal effective label sizes meet 9.5 pt, but `FONT_VISUAL_HARMONY_PASS` remains false because the lower title collides with the upper panel and the two script glyphs fail their native-pixel gate. Font-floor compliance cannot override overlap, purity, clearance or cross-panel coordination failures.

## Independent package integrity

- Manifest entries rehashed by root: 396; missing, byte mismatch and SHA-256 mismatch: 0.
- Actual sealed files: 399 = 396 manifest entries + `MANIFEST.sha256` + `evidence_manifest.json` + `WRITE_STOPPED`.
- Manifest JSON SHA-256 and manifest-text SHA-256 both exactly match the values recorded by `WRITE_STOPPED`.
- Zero-byte files: 0; non-default ADS: 0; files newer than `WRITE_STOPPED`: 0.
- Terminal order is intact and `WRITE_STOPPED` is the final write.

## Required next role

Route FIG-P608-01 to the unique serial **SA2** queue. It must not modify source while P547 owns the sole business-source writer slot. After a minimal repair, root must build a new official full-book candidate, then require a fresh independent SA1, a fresh isolated SA3 and root acceptance before this figure can close.
