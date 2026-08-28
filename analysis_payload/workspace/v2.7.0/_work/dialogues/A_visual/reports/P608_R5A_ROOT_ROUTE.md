# FIG-P608-01 R99 SA1 root route

- `HANDOFF_ID`: `A-R99-P608-SA1-FRESH-R5A-METADATA-RESEAL-20260824`
- `ROOT_STATUS`: `ACCEPTED_FAIL_TO_SA2`
- `OFFICIAL_CANDIDATE`: `R99`
- `OFFICIAL_PDF_SHA256`: `E8D76EEF0D120C518FA94A8F339BF6777AD18AA6AF0BCC17DFB46DF6DFC49EC6`
- `LOCATION`: physical PDF page 660 / printed page 647
- `ACCEPTED_PACKAGE`: `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P608-01\STRICT_R5A_SA1_FRESH_R99_METADATA_RESEAL_20260824`

## Root decision

The fresh isolated R99 SA1 is accepted as `FAIL_TO_SA2`. It does not authorize SA3 and does not count as `A_LOCAL_PASS`.

The accepted denominator is N=170 (112 glyphs + 58 foreground paths) and all 14,365 unordered pairs. The only design failures are `GLYPH_0025` and `GLYPH_0056`, both natural-script `t` glyphs with native 300 dpi ink height 10 px against the mandatory 15 px gate. Final illegal overlap, pair failure and clip counts are zero; D/E ratios, punctuation calibration, semantic consistency and all required views pass.

## Mechanical acceptance

- 794 R5 bottom-evidence files independently rehashed against R5A: zero byte/size/SHA mismatch.
- R5A package: 802 ordinary files; non-default NTFS ADS=0.
- Ledger closure: pair rows 14,365; objects 170; manual objects 170; critical pairs 13.
- Actual route: `gpt-5.6-terra/max`.
- `WRITE_STOPPED` is strictly newest by 1.7512011 seconds and no later write exists.

## Quarantine history

R5 bottom evidence and verdict are valid, but its stop marker timestamp tied with four terminal outputs. R5 remains unchanged as packaging-quarantine history. R5A is the accepted metadata-only reseal.

## Route

`FAIL_TO_SA2`. Repair only the two natural-script labels under the single-writer rule; after an accepted local SA2 change, a new official candidate and completely fresh SA1 are required.
