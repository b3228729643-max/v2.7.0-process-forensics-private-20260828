# FIG-P610-01 R104 fresh isolated SA3 — central acceptance

- Revision: 208
- UID: `FIG-P610-01`
- HANDOFF_ID: `C-FIG-P610-01-R104-SA3-FRESH-ISOLATED-V1`
- Role result: `C_LOCAL_PASS_ONLY`
- Central disposition: `ACCEPT_AS_A_LOCAL_PASS`
- Official candidate: R104, physical page 662, printed page 649, Figure 32.10
- Evidence root: `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\C_visual\evidence\FIG-P610-01\sa3_r104_fresh_isolated_v1`

## Mechanical acceptance

- Fresh SA3 denominator: 17 text/formula objects plus 21 graphic objects, `N=38`; all `703/703` unordered pairs are present.
- Glyphs `77/77`; closest/critical pairs `26/26`; object reviews `38/38`; clip reviews `17/17`; peer-role reviews `9/9`; multiview reviews `13/13`.
- Native pair overlap candidates, canonical illegal-overlap pixels, mask-contamination pixels, and clip pixels are all `0`.
- Manifest has 90 payload entries; actual ordinary-file count is 92, with only `SEALED_MANIFEST.json` and `WRITE_STOPPED` excluded. Path, bytes, SHA-256, and NTFS FILETIME mismatches are `0`.
- All 92 files are read-only; ADS/cache/pyc counts are `0`; `WRITE_STOPPED` is strictly latest by 293,304 ticks and declares zero post-marker writes.

## Denominator reconciliation

The accepted SA1 used `N=40` (18 text and 22 graphic). SA3 uses `N=38` because it excludes the caption from the diagram pair denominator and treats the two split vertical segments around the right rejection mark as one semantic proposal connector. The caption is explicitly reviewed in `figure_crop_with_caption_native_300dpi.png`, full-page views, and the semantic review; both connector segments and their gap/rejection relation are explicitly reviewed in the critical 1x/8x evidence. The difference is a documented semantic-granularity choice, not missing visible content. SA1's larger glyph denominator likewise includes caption glyphs; SA3's 77 diagram glyphs are complete for the standalone diagram.

## Central visual and semantic check

The root opened the full page, figure-plus-caption crop, grayscale standalone, state-arrow 8x crop, and rejection-connector 8x crop. The left panel correctly omits rejected `Y_2`; the MH panel repeats current state `Y_1`, yielding `Y_1 -> Y_1 -> Y_3`. Panel alignment, double ring, arrowheads, dashed proposal paths, rejection signs, notes, caption, and following example are complete and readable. Grayscale preserves the relationship encoding. The closest text-related clearance is 13.560220 px; the 3 px white gap from the right middle connector to the repeated-state border is a visible, zero-overlap connected-object endpoint and is advisory under R168.

The 8.5 pt annotation declaration, natural 4 px horizontal strokes, and minor font/peer metadata variations are R168 advisories only. There is no tofu, wrong codepoint, mathematical corruption, actual unreadability, severe visible imbalance, clipping, or illegal overlap.

## Verdict

`FIG-P610-01` is accepted as the twelfth centrally recorded `A_LOCAL_PASS`. This is not a 99/99, whole-book, release, or final PASS. The authoritative distribution becomes `35 SA1 / 52 SA2 / 0 SA3 / 12 A_LOCAL_PASS`; strict final remains `0/99`.
