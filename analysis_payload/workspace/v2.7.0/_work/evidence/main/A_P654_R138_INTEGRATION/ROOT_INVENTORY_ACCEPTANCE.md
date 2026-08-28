# FIG-P654-01 R100 fresh SA1 failure — mainline acceptance

- Timestamp: `2026-08-25T01:34:04+08:00`
- Mainline decision: `ACCEPT_FAIL_TO_SA2`
- Handoff: `A-R137-P654-SA1-FAIL-20260825`
- Fresh role identity: `A-R100-P654-SA1-FRESH-20260825`, `gpt-5.6-sol/xhigh`
- Official candidate: R100, 814 pages, 4,943,206 bytes, SHA-256 `5B1E4B4C5D64A0CA49833F38ED28C4397392BF5E50503431F3170614DF63D171`
- Mainline P654 source SHA-256: `8041DAF98B04D763958DA9C83AF3472FA346D003F0FDCEF13A42FE1AA046B5F8`

## Independent mechanical audit

- Ordinary files: 946.
- Manifest payload: 943; `MANIFEST.csv` and `MANIFEST.json` each contain 943 unique entries.
- File-set missing/extra: 0/0 for both manifests.
- Byte mismatches: 0/0; mtime mismatches: 0/0.
- Parse/decode: 59 JSON with 0 failures, 20 CSV with 0 failures, 860 PNG with 0 failures.
- NTFS alternate data streams: 0.
- `WRITE_STOPPED` is strictly newest; delta from the latest other file is 18,380.0932 ms.

## Accepted failure fact

- Object denominator: `N=116 = 95 glyphs + 21 foreground graphics`.
- Complete unordered-pair denominator: `C(116,2)=6,670/6,670`.
- Pair, final overlap, clearance, empty-mask, ownership-loss, missing-stroke, foreign-pixel and clip failures are all zero.
- The only hard failure is `FRM_TRIAL_005` (`𝑛`): native 300 dpi final-visible `H_INK=21px < 22px`.
- Its raw mask is complete and pure: 21×21 bbox, 262 pixels, pre=final=262, with ownership-loss/missing/foreign/clip all zero.
- Mainline opened the full-page view, figure crop, measurement overlay and native-nearest failure bundle. The mask is visibly complete; visual harmony cannot override the conjunctive height gate.

## Route

Move `FIG-P654-01` from fresh SA1 to SA2. Do not start SA3 and do not count it as `A_LOCAL_PASS`. Preserve the R100 package as the accepted failure evidence; the next repair must be narrowly scoped to `FRM_TRIAL_005`, followed by a new official candidate and another fully fresh isolated SA1.
