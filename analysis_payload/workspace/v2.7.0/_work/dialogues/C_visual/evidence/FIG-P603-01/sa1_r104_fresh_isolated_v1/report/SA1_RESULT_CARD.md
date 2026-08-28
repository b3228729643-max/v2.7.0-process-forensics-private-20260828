# FIG-P603-01 / R104 / fresh isolated SA1 result card

- HANDOFF_ID: `C-FIG-P603-01-R104-SA1-FRESH-ISOLATED-V1`
- Instance: `/root/sa1_fig_p603_r104_fresh_isolated`
- Result: `SA1_PASS`
- Scope of result: this SA1 evidence package only; this is not `C_LOCAL_PASS` and not a global PASS.
- Input identity: 817-page A4 R104 PDF, 4,967,222 bytes, SHA256 `E5C871642FBDDBEC6508BE1B61BD911FE281CA5ACFBD16B0449B13357770A641`.
- Independent location: physical PDF page 655 (1-based), printed page 642, `图32.6`.
- Object denominator: 24 = 11 text + 13 graphic foreground objects.
- Glyph denominator: 150 visible glyphs; 13 whitespace characters explicitly excluded.
- Pair denominator: all `C(24,2)=276` unordered pairs.
- Hard findings: illegal-overlap pixels 0; clipped pixels 0; missing/foreign glyph-mask pixels 0; below-required-clearance pairs 0; hard typography defects under R168 0.
- Advisories: five ordinary equality signs fall below a legacy operator ink-height metric; 8.5pt/9.2pt source declarations fall below a legacy 9.5pt threshold; four unique punctuation glyphs lack an exact internal peer. Every affected glyph was individually opened and found crisp, correct, readable, and harmonious, so these are advisory under R168.
- TeX: `DISABLED`; source-writer: `NONE`; source/PDF/body unchanged.
- Next request: `REQUEST_FRESH_ISOLATED_SA3` using no evidence, conclusions, page number, or denominator inherited from this SA1 except through the controller-authorized handoff.

Decision basis: every hard gate H01-H13 passes in `manual/hard_gate_ledger.jsonl`; all 150 glyphs, 24 objects, 276 pairs, and 28 required source/render/contact views have per-ID manual records.
