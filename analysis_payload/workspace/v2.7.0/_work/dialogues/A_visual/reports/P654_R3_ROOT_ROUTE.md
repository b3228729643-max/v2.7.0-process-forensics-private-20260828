# FIG-P654-01 R100 fresh SA1 — root route

- `ROOT_DECISION`: `ACCEPT_FAIL_TO_SA2`
- `HANDOFF_ID`: `A-R100-P654-SA1-FRESH-20260825`
- `MODEL_ROUTE`: `SA1=gpt-5.6-sol/xhigh`
- `OFFICIAL_CANDIDATE`: `R100`
- `OFFICIAL_PDF`: `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\build\strict_current_r100_fullbook\main_full.pdf`
- `OFFICIAL_PDF_SHA256`: `5B1E4B4C5D64A0CA49833F38ED28C4397392BF5E50503431F3170614DF63D171`
- `EVIDENCE`: `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P654-01\STRICT_R3_SA1_FRESH_R100_20260825`

## Root verification

- R100 identity independently matched: 814 pages and 4,943,206 bytes; the figure is physical page 702, printed page 689, Figure 34.1.
- Object denominator closed at `N=116 = 95 glyphs + 21 foreground graphics`; IDs and safe filenames are unique.
- All `C(116,2)=6,670` unordered pairs occur exactly once. Pair, clearance, final-overlap and clip failures are zero.
- The sole hard failure is `FRM_TRIAL_005` (`𝑛`): native 300 dpi `H_INK=21px < 22px`. Its raw mask is complete and pure: 21×21 bbox, 262 pixels, pre=final=262, with zero ownership loss, missing stroke, foreign pixel or clip.
- Manual ledgers close at 95/95 glyphs, 21/21 graphics, 50/50 critical pairs and 5/5 required views. Explicit row decisions, contact sheets and pair bundles match one-to-one, with no pending or unknown value.
- Package integrity passed: 946 ordinary readable files; 943 payload entries match both manifests by file set, bytes and mtime; 860 PNGs decode, 59 JSON files parse and 20 CSV files import; ADS=0. `WRITE_STOPPED` is strictly latest by about 18.38 seconds and no later writes exist.
- Mainline P654 source SHA-256 is `8041DAF98B04D763958DA9C83AF3472FA346D003F0FDCEF13A42FE1AA046B5F8`; the A worktree has no P654 diff.
- Root directly inspected the full figure crop and the native/8× failure bundle; the failure mask is visibly complete and the hard threshold may not be overridden by visual harmony.

## Route

Accept `FAIL_TO_SA2`. Do not start SA3 and do not count FIG-P654-01 as `A_LOCAL_PASS`. Mainline should move P654 to the SA2 repair queue, preserving the R100 package as the accepted fresh-SA1 failure evidence.
