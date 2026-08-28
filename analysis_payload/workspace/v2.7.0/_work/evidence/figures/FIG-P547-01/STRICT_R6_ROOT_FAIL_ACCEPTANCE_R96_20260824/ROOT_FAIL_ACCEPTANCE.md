# FIG-P547-01 — R96 root rejection acceptance

- Root decision: **ACCEPT `FAIL_TO_SA2`**.
- This is a routing acceptance of a failed SA1 review, not a figure pass and not a strict closure.
- Official binding: R96 `main_full.pdf`, physical page 591 / printed page 578, figure 30.2.
- Figure source SHA256: `638CEA4285D3A9411251DA149963CC7AE4500FA5827F0A99A51FF1FC76640D1A`.
- Official PDF SHA256: `8EED8765A4856C4C197262DEA06E283790FBA8DA906C70C26FC7BD56F6F7E5E8`.

## Root manual pixel review

Root opened all 18 glyph contact sheets, then individually opened the native 1× ORIGINAL, native 1× TARGET OVERLAY, native 1× MASK ONLY, and 8× nearest-neighbour contact card for every one of the 18 reported glyph failures. Root also opened both the native 1× ROI and 8× nearest-neighbour contact card for each of the four failed object pairs. The 300 dpi full page, 200 dpi full page, native 300 dpi figure/caption crop, standalone crop, and grayscale crop were opened as global controls.

The unambiguous raw-height failures are real: twelve `=` glyphs measure 12–14 px, three `→` glyphs measure 18–19 px, C0073 `一` measures 6 px, and C0198 `n` measures 21 px. These 17 targets are below their applicable 22 px or 30 px hard gate. The four unwhitelisted text/graphic pairs below have zero raw overlap but only 1 px exact foreground clearance against a 3 px requirement:

- `PAIR_C0026_G07`
- `PAIR_C0026_G09`
- `PAIR_C0120_G24`
- `PAIR_C0120_G26`

The figure therefore fails even without relying on the low-profile C0153 result.

## Additional root evidence defect finding

The SA1 ledger's blanket mask-purity PASS is not accepted for C0153 (`；`). Its native 1× and 8× MASK ONLY evidence visibly contains a third, spatially separate foreign component at the lower-right edge; the measurement row itself reports `assigned_raw_component_count=3`, whereas the semicolon has two intended components. That foreign component expands the reported ink box to 36×33 px and invalidates the claimed independent low-profile comparison as a clean measurement. SA2 must not repair the source solely from that contaminated C0153 metric; the next evidence loop must first correct/reconcile scope and segmentation and then remeasure it. This defect strengthens the rejection and prevents reuse of the SA1 manual-purity claim.

## Independent count and seal checks

- Glyph rows: 208; reported size failures: 18 (17 unambiguous hard-height failures plus the contaminated C0153 low-profile row).
- Low-profile rows: 36; reported failures: 1, subject to the C0153 defect above.
- Foreground objects: 237.
- Unordered pairs: 27,966 = 27,934 PASS + 28 intentional-contact PASS + 4 FAIL.
- D same-role rows: 208, failures 0; E hierarchy rows: 8, failures 0; occlusion/reverse rows: 6, failures 0.
- Non-natural-script font-floor rows pass; 28 smaller emitted glyphs are documented natural-script exceptions. Global font harmony is visually acceptable, but this cannot override pixel-size or clearance failures.
- Preterminal inventory: 1,218 files independently rehashed; missing 0, byte mismatch 0, SHA256 mismatch 0.
- Current package: 1,222 files / 1,080 PNG; only two zero-byte TeX `.idx` intermediates; files newer than `WRITE_STOPPED`: 0.
- Terminal write order and sealed no-write condition are intact.

## Required next role

Route FIG-P547-01 to a dedicated **SA2** repair/reconciliation pass after the current single business-source writer is released. After any source change, use a new official full-book build and restart the required fresh SA1 → isolated SA3 → root chain. Strict final status remains not closed.
