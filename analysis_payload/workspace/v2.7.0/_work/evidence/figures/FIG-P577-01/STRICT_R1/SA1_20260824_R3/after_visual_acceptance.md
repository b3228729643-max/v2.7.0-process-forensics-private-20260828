# FIG-P577-01 — corrected R95 strict SA1 R3 visual acceptance

## Result

**FAIL.** Evidence integrity is evaluated separately from figure hard gates. The R95 page is the only authority; R94 is only a full-page/crop zero-delta bridge.

- Clean per-glyph masks: 345/345 manual R95 ledger rows, 0 missing >=20/255 target pixels, 0 terminal foreign target pixels.
- Text/text: 59,340/59,340 classified, 0 illegal overlap/clearance pairs after direct y-axis title mapping.
- Required relations: TG304 PASS (9.849>=3), TG317 PASS (5.000>=3), TG457 FAIL (2.000<5).
- Data curve visibility: five later opacity-1 label grounds cover G01 p(y), a hard visual failure: blue legend 302, min-gap label 304, shallow-fill note 609, acceptance card 1571, rejection card 1039 PRE pixels. Teal legend covers 0.
- Source base/font floor/D/E/four-view font harmony: PASS. Math semantics, grayscale distinction and page integration: PASS.
- The preliminary 430 / 392 / 17,690 colour-projection values are **SUPERSEDED_NONTERMINAL**, not terminal failures; see `INITIAL_PROJECTION_SUPERSEDED.md`.
