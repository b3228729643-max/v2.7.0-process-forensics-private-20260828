# Native-pixel overlap, clipping, and clearance adjudication

## Evidence basis

The reviewer opened the 300 dpi official page, the 300 dpi internal subject, the 300 dpi subject with caption, the text/object/semantic overlays, the 300 dpi grayscale subject, the 200 dpi page-integration view, and each of six risk regions both at native1x and nearest-neighbor8x.

The complete 25-object denominator yields 300 unordered pairs. Manual review produced 19 proximity/contact candidates:

- 16 intended connector endpoint contacts: `P016`, `P040`, `P084`, `P139`, `P140`, `P141`, `P142`, `P145`, `P175`, `P176`, `P191`, `P192`, `P194`, `P219`, `P253`, `P254`;
- 3 bbox-only proximity candidates with no native foreground contact: `P025`, `P039`, `P223`.

Every candidate is individually explained in `manual_pair_ledger.md`. The intended endpoints touch only node borders at the source-defined connector anchors and remain away from reader text. The bbox-only candidates disappear when comparing native ink rather than encompassing vector bboxes. No candidate is unresolved.

## Canonical manual result

- visible semantic objects: `25`
- all unordered pairs: `300`
- manually adjudicated pair IDs: `300`
- intended legal endpoint-contact pairs: `16`
- bbox-only false-positive pairs: `3`
- hard illegal collision pairs: `0`
- hard illegal collision pixels: `0`
- unresolved pairs: `0`
- clipped reader-foreground pixels: `0`
- minimum observed text-to-containing-node-border clearance: `5 px` at the lower scripts of the Beta special-case node; native1x and NN8x show complete ink and no clipping
- note-to-caption bbox clearance: `22 px`
- lower-result-node-to-caption bbox clearance: `25 px`

The active R168 policy was applied: old small-type, outline, and ratio thresholds are advisory. None was used as a failure trigger. The hard-defect audit instead found zero missing glyphs, tofu, wrong codepoints, wrong mathematics, unreadable text, obvious imbalance, true clipping, illegal overlap, or semantic/geometric error.
