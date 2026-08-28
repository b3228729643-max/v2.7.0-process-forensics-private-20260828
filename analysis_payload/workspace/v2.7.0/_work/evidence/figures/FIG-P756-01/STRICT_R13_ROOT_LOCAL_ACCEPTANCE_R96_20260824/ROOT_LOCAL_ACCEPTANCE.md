# FIG-P756-01 — R13 root local SA2 acceptance

- Root decision: **ACCEPT `LOCAL_PASS_TO_ROOT_BUILD`**.
- This accepts only the repaired local candidate for an official full-book build. It is not an SA1/SA3 review, not a final figure PASS, and not a strict closure.
- Sole business source: `src/绘图源码/第05册_采样方法主题模型与图排序/V5-C08/full_course_synthesis_map.tex`.
- Before SHA256: `75A691EF23E041AAD59A8C738A68E96427F2EC09B2BF0D48DFC2F3134E84358E`.
- Accepted source SHA256: `00213AE30379E4337830B1C4957BE4CB7B1E99BE88144E2D7D262998E1B6CAAA`.

## Root source and seal audit

- The current source is byte-identical to the sealed after-snapshot. The before-snapshot hash is also exact.
- Exactly five source lines changed: the two route nodes were separated vertically by 0.20 TikZ units in total, and three small-label phrases were replaced by semantically equivalent wording that avoids undersized `口` glyphs. No font size was enlarged and no public macro/build/central file was changed by SA2.
- `MANIFEST.sha256` contains 3,373 valid entries; root independently recomputed all entries: missing 0, malformed lines 0, SHA256 mismatch 0.
- Manifest SHA256 is `2F046D9A9573B8D88DC5BA6E574BD249AA52617BFB1288EDE37E3C8DE4626722`.
- Current package has 3,375 files. Four zero-byte files are expected local TeX `.idx` intermediates. Alternate data streams: 0. Files newer than `WRITE_STOPPED`: 0.
- Terminal order is intact: terminal status, then manifest, then `WRITE_STOPPED` at a strictly later filesystem tick.

## Root native-pixel and visual audit

- Root opened the before/after P1408 native 1× original, 8× nearest overlay, and 8× intersection evidence. Before repair the two independent route boxes visibly shared their full boundary; after repair the intersection image is empty and the exact final-visible separation is 20 px with zero overlap.
- Root opened before/after 8× nearest original and pure-mask evidence for G0208, G0212 and G0222. The old `口` targets were 29 px; the accepted wording produces pure `出`/`入` masks at 34/35/35 px, with no foreign or missing pixels and unchanged effective size 9.5641 pt.
- Root opened the native 300 dpi crop, standalone, grayscale, text-measurement overlay, and both 300/200 dpi page views. The repaired figure has no visible overlap, clipping, abrupt font scale, gray-tone failure, or page-integration anomaly; the two route boxes are visually distinct without excessive separation.
- Source wording and diagram semantics remain equivalent: supervised/unsupervised routes still enter a shared engine pool, then isolation validation, then a one-way reproducible report.

## Independent table checks

- Foreground relation objects: 55; all unordered pairs: 1,485 = 351 TT + 756 TG + 378 GG; failures 0. All 1,107 mandatory relations pass.
- P1408 is independently represented as `O-G016` vs `O-G017`, overlap 0 and exact clearance 20 px; no shared-boundary exception is used.
- Glyphs: 378. Final local ledger resolves 358 direct rows plus 20 independently calibrated low-profile rows to 378 PASS; font failures 0, pixel failures 0, mask-purity failures 0.
- Low-profile validation: 20/20 PASS across 10 exact embedded-font/CID groups; target/calibration height and area ratios are all 1.0.
- D/E final rows: 378 PASS. Clip rows: 55 PASS. Font-role audit: 19 same-panel roles PASS; the two comparable cross-panel roles PASS.
- The two local wrapper PDFs are valid A4 one-page PDFs with embedded/subset/Unicode fonts; their accepted SHA256 values match the sealed report. Only known template/package notices appear; fatal, overflow, missing-glyph and font-substitution hard categories are absent.

## Required next gate

Root must now build and freeze a new official full-book candidate through the single authoritative entry. FIG-P756-01 must then restart at a fresh independent SA1 on that official PDF, followed—only after SA1 PASS—by a fresh isolated SA3 and final root adjudication. Strict final status remains not closed.
