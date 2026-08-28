# FIG-P582-01 — official R109 fresh isolated SA1 report

## Verdict

`PASS`

This is the result of the sole fresh isolated SA1 identified by `A-R109-P582-SA1-FRESH-ISOLATED-20260826`. It is not an `A_LOCAL_PASS` claim. The requested next step is review by a **different fresh isolated SA3**; this SA1 did not launch that reviewer.

## Official identity and independent location

- Official PDF: `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\build\strict_current_r109_fullbook\main_full.pdf`
- Pages: `817`
- Size: `4,967,054` bytes
- SHA256: `936162A637DCE09EE02B3F83CB1C21A61A87EFBB9A7C8DDE2FB11A326EB552A9`
- Independently located figure: physical PDF page `632`, printed page `619`
- Location match was unique under the complete caption phrase set. No prior P582 page hint or old P582 evidence was used.

## Frozen denominator and exhaustive pairs

- Final-visible glyphs: `78`
- Final-visible semantic graphics: `27`
- Complete visible-object denominator: `N=105`
- Complete unordered-pair count: `C=105×104/2=5,460`
- Every pair is present exactly once in the exhaustive pair ledger.
- Source primitive `G016` (the second ycomb stem) is retained in the frozen source ledger but excluded from the visible denominator because the later-painted square marker completely occludes it in the official final pixels. This is why the final graphic count is 27 rather than the 28 source primitives.

## Machine gates

- Official identity: pass
- Native 300 dpi crop: `1313×684` px
- Empty masks: `0`
- Exhaustive illegal-overlap pairs under R168: `0`
- Overlap pixels: `0`
- Clip pixels: `0`
- Minimum object-to-crop-edge clearance: `30` px
- Same-class ratio failures: `0`
- Machine R168 direction: `PASS_CANDIDATE`

Legacy strict calibration flagged five glyphs (`T016`, `T019`, `T032`, `T059`, `T063`) and one pair (`P3464`). Manual 1x/8x review showed that the four low-profile marks are exact and visible decimal dots, `T032` is the exact and balanced equals sign in `h(U_i)=U_i^2`, and `P3464` has a visible 1 px white gap with zero intersection. Under R168 these are advisory microscopic taxonomy/clearance observations, not hard failures.

## Manual review

Manual review was recorded only after actually opening the final official-page, native crop, standalone, grayscale, and overlay renders; all four glyph 1x sheets and all four glyph 8x sheets; all four graphic 1x sheets and all twenty graphic 8x sheets; and all four 1x plus all four nearest-8x critical ROI sheets.

- Glyph ledger: `78/78` PASS
- Graphic ledger: `27/27` PASS
- Critical-pair ledger: `20/20` PASS
- Missing/tofu/wrong-codepoint glyphs: none
- Genuinely unreadable text or obvious severe imbalance: none
- True clipping or illegal overlap: none
- Substantive geometry or relationship error: none
- Math and caption semantics: correct
- Grayscale discrimination and page integration: pass

The fixed samples `0.8, 0.1, 0.7, 0.4` square to `.64, .01, .49, .16`; their cumulative means are `.64, .325, .38, .325`; and `E[U^2]=1/3`. The plotted down–up–down sequence correctly demonstrates that convergence need not be monotone.

## Sealed evidence

- Evidence root: `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P582-01\STRICT_R3_SA1_FRESH_ISOLATED_R109_20260826`
- Payload files: `383`
- Total root files after manifests and marker: `386`
- `PAYLOAD_MANIFEST.csv` SHA256: `7B712A3A357766DC42AAB5FC8E4F0B1067DF243E718ADB562D7F75B1D65462FA`
- `SEAL_MANIFEST.json` SHA256: `F824AC33005705C05E7A3F3C5F5756300F818AD2ABAA7305748CBA698031D0BE`
- `WRITE_STOPPED` SHA256: `6C678A5240A56B9B1534C0AB9DD253F8108C9C71A4FBDDDAF6500FB51D2C3EF1`

The normalized root-external read-only audit at `2026-08-26T23:07:13.9433159+08:00` verified:

- manifest/filesystem identity: pass, zero errors
- all 386 root files read-only: pass
- ADS: `0`
- `.pyc` / `__pycache__`: `0`
- reparse points: `0`
- unique root-level `WRITE_STOPPED`: pass
- `WRITE_STOPPED` strictly latest: pass
- post-marker files: `0`
- official PDF identity: pass

The sealed helper `machine/07_external_audit.py` performs the same checks but includes one overly strict raw equality comparison between CSV string fields and JSON typed fields; its first invocation therefore emitted the single spurious message `seal embedded payload rows differ`. A separate read-only external invocation normalized those primitive types and passed every invariant above. The sealed root was not modified to correct the helper, preserving the promised zero writes after `WRITE_STOPPED`.

## Handoff request

Please dispatch a different fresh isolated SA3 to inspect this immutable root independently. SA3 should treat the five glyph flags and `P3464` according to R168 and should independently confirm the final-visible exclusion of fully occluded `G016`.
