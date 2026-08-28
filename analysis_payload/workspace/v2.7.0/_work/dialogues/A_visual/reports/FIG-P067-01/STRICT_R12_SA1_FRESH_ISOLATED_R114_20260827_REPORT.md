# FIG-P067-01 strict R12 fresh isolated R114 SA1 report

HANDOFF_ID: `A-R114-P067-SA1-FRESH-ISOLATED-20260827`  
Result: `PASS`  
Scope: fresh isolated SA1 only; no SA2/SA3 work and no local/book completion count.

## Startup and identity

The exact evidence-root path was absent as both a file and a directory before its one successful creation. The official PDF matched `4,967,122` bytes and SHA-256 `C3BB9B1C7FC9D7AF9178CD33F227F24899AA505FAB81840DB6E3AD8BD6CE78A6`. The current source matched `4,014` bytes and SHA-256 `11BF3681D069F6A38C479B3074F39F93E8EB6144FF155AC543508E3589A51144`. Both remained read-only.

The figure was independently located from its current caption at physical page 69. The first pre-manual crop was rejected because it cut the left ordinate labels; the widened final crop was reopened before the denominator was frozen.

## Evidence and manual closure

The corrected native1x 300 dpi crop, nearest8x overview and 12 focused nearest8x tiles, grayscale 300 dpi crop, complete 200 dpi page, and direct 300 dpi page were actually opened. The visible-object denominator was frozen at 69 objects: 23 text objects and 46 graphical objects. The complete unordered-pair universe contains 2,346 pairs.

Post-observation manual coverage is 69/69 object IDs and 97/97 mechanical candidate pair IDs. The 97 candidates cover all 17,244 over-inclusive composite foreground pixels sampled in intersecting bbox envelopes. Per-ID adjudication found 0 true illegal-overlap pixels and 0 unresolved candidates. Clip pixels are 0.

## Mathematical and visual decision

The PMF `(0.15,0.30,0.35,0.20)` sums to 1. The CDF jump differences are exactly the same four masses. The CDF is nondecreasing and right-continuous: filled markers give post-jump values and open markers give left limits; it begins at 0 and terminates at/stays at 1. Ticks, labels, caption, adjacent-page explanation, grayscale structure, and page placement agree.

The locally declared 8.6/8.8/9.2/9.4 pt values are retained as an R168 font advisory rather than falsely reported as meeting the older 9.5 pt source threshold. Native evidence is readable and contains no missing glyph, tofu, wrong codepoint, semantic error, obvious imbalance, clipping, or illegal overlap. `T21-G46` retains a measured one-native-pixel blank clearance with zero shared foreground; it is an explicit R168 micro-clearance advisory and not a hidden threshold pass.

## Seal

One seal call was used. After all root content and the manifest were complete, `WRITE_STOPPED` was prepared outside the root, assigned a strictly later mtime, and made read-only. All 46 existing destination items including the root were made and verified read-only before the already-read-only marker was moved once into the root as the sole final root operation. Post-move audit found 47/47 items read-only, `WRITE_STOPPED` uniquely strict-latest, 0 non-marker items at-or-after it, and identical double-snapshot digests `4A3107709F8896C2F30CE8D7F641D93443EEDE496FB35F7C8009556F027B7F3F`; postmarker root content/attribute writes were 0.

## Routing

This honest SA1 `PASS` requests only a **different fresh isolated R114 SA3**. It does not count `A_LOCAL_PASS` and does not authorize reuse of this reviewer as SA3.
