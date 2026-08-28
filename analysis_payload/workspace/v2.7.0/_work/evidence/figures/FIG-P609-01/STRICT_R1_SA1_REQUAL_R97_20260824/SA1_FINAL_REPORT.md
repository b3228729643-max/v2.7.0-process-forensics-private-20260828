# FIG-P609-01 R97 independent SA1 final report

## Terminal result

`SA1_FAIL_ROUTE_SA2` / `FAIL_TO_SA2`.

No source, macro, build candidate, central state, inventory, or sibling evidence was modified. The conclusion is based only on the frozen R97 candidate, current figure source/direct context, and this isolated R1 evidence package.

## Identity and scope — PASS

- Candidate SHA-256: `062AD81020CB19A5C6688A45C73E00965F5060E0960A69AF820D7DC154DEE814`; 813 physical pages.
- FIG-P609-01 / Fig. 32.9: physical page 659, printed page 646; aux label and fls input are recorded in `LOCATION_AUX_FLS_SOURCE_AUDIT.md`.
- Current source SHA-256: `20687D1EE01AABA9B605591A61781CF688328026E0645AD51B6E02E921DC98A2`.
- P609 scope is the strict native-300dpi rectangle `[291,2187,2125,2925]`; adjacent Fig. 32.8/caption/body are excluded.

## Glyph gate — HARD FAIL (route-determinative)

All 148 rawdict records were individually ledgered; 144 are visible reader glyphs and four are named zero-width combining controls. 13 native 8x glyph sheets and 35 individual candidate native 1x triplets were manually opened.

| Glyph | Observed gate | Result |
| --- | --- | --- |
| GL024 `=` | H_INK 12px vs 22px | hard fail |
| GL026 `⋯` | no eligible exact low-profile comparator for H/area `[0.92,1.08]` | hard evidence fail |
| GL034 `F` | H_INK 23px vs 24px | hard fail |
| GL045 `：` | no eligible exact low-profile comparator for H/area `[0.92,1.08]` | hard evidence fail |
| GL065 `=` | H_INK 12px vs 22px | hard fail |
| GL072 `=` | H_INK 11px vs 22px | hard fail |
| GL076 `−` | H_INK 3px vs 22px | hard fail |
| GL088 `=` | H_INK 12px vs 22px | hard fail |
| GL109 `=` | H_INK 12px vs 22px | hard fail |

Each listed target has a pure native mask and a human note in `glyph_ledger.csv`; purity does not cure an under-threshold glyph or a missing independent calibration. In particular, no source point-size or D/E visual result is substituted for the native hard pixel gate.

## Other required gates — PASS, but non-curative

- Objects/pairs: 59 visible foreground objects, all `59C2=1711` unordered pairs enumerated. 40 critical/contact rows have actual native review. Unwhitelisted-pair failures: 0. Seven tick–stem, seven axis–stem, and seven stem–marker relations are each source-anchored at their individual `k=0…6` coordinates; no category blanket exemption was used.
- Math/path: 2 independent `GRAPHIC/MATH_RULE` objects, 5 accent associations, 36 mapped foreground drawing paths plus 2 explicitly excluded background fills, and zero unassigned foreground paths. Rules/accents are manually reviewed in their separate cards.
- Clip/crop: all object rows pass; the three 20px crop-proximity cards were manually opened. No clip failure.
- Z-order/occlusion: 59 object rows audited; no unintended hiding or line-through-text. Expected construction contacts remain only in the named pair ledger.
- D/E and visual coordination: source effective roles are 9.6pt tick/annotation/formula, 9.8pt axis label, 10.4pt title; same-role/same-panel and cross-panel checks pass. Manual global 200dpi / native crop 300dpi / standalone 300dpi / grayscale 300dpi review records `FONT_VISUAL_HARMONY_PASS` and grayscale readability.

The pair, clipping, z-order, global-view, grayscale, D/E, and font-harmony passes do **not** offset any of the nine glyph hard failures. The only permitted SA1 routing is therefore `FAIL_TO_SA2`.

## Evidence completeness

- Referenced evidence paths checked: 1763; missing: 0.
- Pre-terminal zero-byte files: 0; non-default ADS check: 0 (recorded before sealing).
- Manifest procedure and self-exclusion rationale are recorded in `evidence_manifest.json`; `WRITE_STOPPED` is written last and intentionally is not inside the immutable manifest snapshot.
