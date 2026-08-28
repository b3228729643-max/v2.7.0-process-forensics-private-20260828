# FIG-P715-01 R99 SA1 root route

- `HANDOFF_ID`: `A-R99-P715-SA1-FRESH-B-20260824`
- `ROOT_STATUS`: `ACCEPTED_FAIL_TO_SA2`
- `OFFICIAL_CANDIDATE`: `R99`
- `OFFICIAL_PDF_SHA256`: `E8D76EEF0D120C518FA94A8F339BF6777AD18AA6AF0BCC17DFB46DF6DFC49EC6`
- `LOCATION`: physical PDF page 763 / printed page 750
- `ACCEPTED_PACKAGE`: `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P715-01\STRICT_R1C_SA1_FRESH_R99_METADATA_RESEAL_20260824`

## Root decision

The fresh isolated SA1 evidence is accepted only as a routing failure. It does not establish `A_LOCAL_PASS` and does not authorize SA3. FIG-P715-01 must enter the single-writer SA2 repair queue.

The accepted denominator is 298 objects (255 glyphs and 43 paths) and all 44,253 unordered pairs. The package records 44 glyph failures, including `G0012` CJK_FULL `一` with native 300 dpi ink height 6 px against the mandatory 30 px threshold. It also records 19 non-whitelisted critical relations: 16 raw collisions totaling 943 native pixels and 3 clearance-only failures. Clip and mask-contamination counts are both zero.

## Mechanical acceptance

- Manifest: 833 declared rows / 833 rows; every declared byte count and SHA-256 recomputed with zero mismatches.
- Package: 835 ordinary files, exactly manifest entries plus the manifest itself and `WRITE_STOPPED`.
- NTFS alternate streams: zero non-default streams.
- Route metadata: corrected to the actual orchestrated SA1 route `gpt-5.6-terra/max`.
- Seal order: `WRITE_STOPPED` is strictly newest by 1,201.212 ms and no later write exists.
- Reused R1B bottom evidence: 825 files byte-identical according to the reseal reconciliation; the verdict and N/pair denominators were not changed.

## Quarantine history

The first P715 SA1 directory is invalid because that role read forbidden state-recovery files. R1B then produced the valid bottom evidence but its sealed metadata misreported the model route and gave `WRITE_STOPPED` a timestamp tied with four earlier outputs. R1B remains unchanged as quarantine history. R1C is the accepted packaging-only reseal.

## Route

`FAIL_TO_SA2`. Do not launch SA3. Do not modify the P715 source until it becomes the sole authorized business-source writer.
