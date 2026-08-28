# FIG-P067-01 — fresh isolated SA2 report

## Assignment

- HANDOFF_ID: `A-R111-P067-SA2-R168-READONLY-20260827`
- Canonical instance: `/root/p067_r111_r168_sa2`
- Model / effort: `gpt-5.6-sol / xhigh`
- Scope: read-only review of the official R111 PDF and the current `fig_v1_c04_cdf.tex`, with only necessary current V1-C04 body/caption context.
- Evidence root: `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P067-01\STRICT_R1_SA2_R168_READONLY_R111_20260827`

## Input and locator result

The authorized UID parent and evidence root were independently observed absent before creation. The PDF matched 4,967,076 bytes and SHA-256 `DAB1062500E39DD2C34C6B4A9FF51CAC2BE0A4C84B2F45F5FB8E645C4BC012D6`; the source matched 3,866 bytes and SHA-256 `03372740AB8015EFFB7BC6CFBBDC669A1E8FBF52246291491B1B0C506513B864`.

An exact live-caption substring search across the official PDF located a unique hit on current physical page 69. No historical physical-page hint was used to select the page.

## Independent review

The PMF masses are `0.15, 0.30, 0.35, 0.20`, all nonnegative and summing to 1. The CDF levels are the correct cumulative values `0.15, 0.45, 0.80, 1.00`. The staircase is monotone; filled points give post-jump values and open points give pre-jump values, so right continuity is correctly encoded. The four abscissae align across panels. Axis meanings, annotations, caption, and current body text agree. Grayscale retains the open/filled and stem/stair structural encodings. There is no clipping, missing glyph, tofu, replacement character, or wrong codepoint.

The current lower PMF y-axis has one hard defect: the distinct tick labels `0.35` and `0.3` visibly overprint. At native 300 dpi their word boxes overlap in a 51 by 18 pixel region containing 327 foreground pixels. The nearest-neighbour 8x view preserves the same defect as a 408 by 144 pixel region containing 20,928 foreground pixels. This causes actual numerical-label misreading and is not a source-size-only, taxonomy, or micropixel objection.

## Denominator and gates

The final denominator contains all 95 non-whitespace body/caption glyph atoms and 50 foreground path atoms, `N=145`. Exactly five white-fill, no-stroke label-background rectangles were rationalized as background exclusions. All `C(145,2)=10,440` unordered pairs were enumerated exactly once with native1x and nearest8x geometry/foreground data; duplicate pairs 0 and self-pairs 0. The manual ledger covers 145/145 IDs and 16 critical relationships with object-specific observations.

Hard-gate outcome: `REL006=FAIL_TRUE_COLLISION`; all other reviewed semantic, endpoint, clipping, caption, grayscale-encoding, and page-integration relationships pass. R168 advisory source sizes 8.6/8.8/9.2/9.4 pt were recorded without being used as an independent failure.

## Verdict

`FAIL_TO_MAIN_SOURCE_SCOPE`

Narrow source-scope request: adjust only the lower PMF y-axis tick presentation in `fig_v1_c04_cdf.tex` so `0.30` and `0.35` are separately readable with real clearance—for example, remove one redundant adjacent tick label or place them explicitly without overlap. Preserve the four PMF masses, cumulative CDF levels, right-continuous open/closed endpoints, axes, annotations, and caption. Rebuild and submit a new native 300 dpi crop plus nearest-neighbour 8x critical ROI to a fresh SA1.

No source, TeX, Git, central state, other UID, or process was modified or run by this SA2.

## Seal and immutable audit

The evidence root was sealed once. Every sealed file and directory, including the root and sole `WRITE_STOPPED` marker, has the Windows ReadOnly attribute. The marker is unique and strictly latest. The root-external audit reports 42 files, 5 directories including root, manifest-vs-filesystem duplicate/missing/extra counts 0, bytes/SHA-256/NTFS-tick mismatches 0, parse errors 0, named ADS 0, cache/pyc 0, reparse points 0, non-readonly files/directories 0, nonmarker items at-or-after the marker 0, and postmarker content-or-attribute changes 0. Audit status: `SEALED_ROOT_CLOSED`.

- Root-external audit SHA-256: `A7B922E33AF03E79DD35EAFD846E1E11AB42D60F37E813DCCED6CF38D8FCB1ED`
- Sealed-root manifest SHA-256: `97A73B259A84E0C348D58F6561306C921134547A175BD8EF05B74BBFAD53C6A1`

