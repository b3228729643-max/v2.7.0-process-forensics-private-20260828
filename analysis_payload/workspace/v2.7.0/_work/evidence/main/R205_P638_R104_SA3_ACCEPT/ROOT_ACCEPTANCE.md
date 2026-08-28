# FIG-P638-01 R104 fresh isolated SA3 — central acceptance

- Revision: 205
- UID: `FIG-P638-01`
- HANDOFF_ID: `C-FIG-P638-01-R104-SA3-FRESH-ISOLATED-V1`
- Role result received: `C_LOCAL_PASS_ONLY`
- Central disposition: `ACCEPT_AS_A_LOCAL_PASS`
- Official candidate: R104, physical page 688, printed page 675, Figure 33.5
- Evidence root: `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\C_visual\evidence\FIG-P638-01\sa3_r104_fresh_isolated_v1`

## Mechanical acceptance

- Semantic foreground denominator: `N=14` (`T01--T05`, `F01--F03`, `G01--G06`).
- All unordered object pairs: `C=91/91`; native shared foreground pixels `0`.
- Glyph denominator: `107/107`; critical-pair ledger: `68/68`; multiview ledger: `9/9`.
- Manual object/pair/glyph/view ledgers contain unique IDs, no blank notes, and no non-PASS row.
- Manifest lists 42 payload files; actual ordinary files are 44, with the only excluded controls being `MANIFEST.json` and `WRITE_STOPPED`.
- Manifest-to-filesystem path, byte count, SHA-256, and NTFS FILETIME mismatches are all `0`; ADS/cache/pyc counts are `0`.
- Payload and manifest are read-only. `WRITE_STOPPED` is the declared Archive control marker and is strictly latest by 129,414,791 ticks; no post-seal payload write was found.

## Denominator reconciliation

The accepted SA1 used `N=16` and a 202-glyph audit because it included two caption text objects and their glyphs in the object/glyph denominator. This isolated SA3 uses a diagram-only semantic foreground denominator (`N=14`, 107 diagram glyphs) for the 91 unordered pairs. It does not omit the caption: `FIGURE_CROP_NATIVE` explicitly contains the complete diagram and both caption lines, while `FULL_PAGE_NATIVE` and `FULL_PAGE_CONTEXT` independently review caption, body transition, and following explanation. Both roles use the same R104 page and current source. The difference is therefore a documented granularity boundary, not missing visible content.

## Central visual and semantic check

The root opened the native full page, native figure-plus-caption crop, standalone-equivalent crop, grayscale view, object overlay, object contact sheet, and glyph contact sheet. The numbered `1 -> 2 -> 3` flow, exact conditional proposal, MH-ratio cancellation to `1`, `alpha=1`, direct acceptance, approximate-proposal correction and rejection self-loop are complete and consistent with the adjacent text. Warning arrows, separator, exception panel, fraction rule, borders, caption, and grayscale hierarchy are clear. No clipping, illegal overlap, unreadable glyph, wrong codepoint, or R168 hard typography failure is present.

Advisories only: the source declares 9.2 pt, several base math glyphs rasterize at 21 px, `G01` is a connector whose direction is fixed by visible numbering, and several graphic-only proximities are 1 px. Under R168 these do not constitute hard failures because actual readability, semantics, geometry, and native-pixel separation pass.

## Verdict

`FIG-P638-01` is accepted as the eleventh centrally recorded `A_LOCAL_PASS`. This is not a 99/99, whole-book, release, or final PASS. The authoritative distribution becomes `35 SA1 / 52 SA2 / 1 SA3 / 11 A_LOCAL_PASS`; strict final remains `0/99`.
