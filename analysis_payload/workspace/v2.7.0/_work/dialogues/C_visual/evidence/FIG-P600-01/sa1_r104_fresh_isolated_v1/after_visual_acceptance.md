# FIG-P600-01 — SA1 manual visual acceptance

## Candidate and views actually opened

The official R104 candidate on physical page 651 / printed page 638 was independently located and identity-locked. I actually opened the full-page 200 dpi view, native 300 dpi figure+caption crop, official-PDF-derived standalone body, native grayscale view, and the all-glyph measurement overlay. Native dimensions and integer page crop coordinates are in `machine/candidate_identity_and_denominators.json`.

I also opened all 17 glyph contact sheets (197/197 glyphs), both graphic contact sheets (18/18 drawings), the enlarged native border/curve checks, and all 29 critical pair cards. Each glyph and graphic was adjudicated by ID in its manual ledger; all 406 unordered semantic-object pairs were separately adjudicated by pair ID.

## Denominators

- Visible glyphs: 197; whitespace exclusions: 16 explicit non-ink rows.
- Text semantic parents: 11.
- PDF visible foreground drawing objects: 18, drawing indexes 4–21.
- Total independent semantic objects: 29.
- All unordered pairs: `C(29,2)=406`, exactly 406 ledger rows.
- Critical pairs with raw/dual-mask/intersection/1×/8× artifacts: 29.
- Mathematical path-rule objects: 0. Source and PDF inventories contain no fraction bar, radical rule, overline, underline, accent, or cancellation path in this figure; arrows, curves and borders are among the 18 mapped graphics.

## Geometry and pixels

- `OVERLAP_PIXEL_COUNT=0`: no pair has a shared final-visible raw foreground pixel.
- `CLIP_PIXEL_COUNT=0`: all 29 objects were reviewed; none is clipped.
- Minimum independent `TEXT_TEXT` clearance: 8 px (`PAIR0154`), above the 4 px hard gate.
- Minimum `TEXT/FORMULA_LINE_ARROW` clearance: 36.4833 px, above the 3 px hard gate.
- Minimum `TEXT/FORMULA_NODE_BORDER` clearance: 9 px (`PAIR0235`), above the 5 px hard gate.
- Graphic-graphic clearances reach 0 px edge-to-edge only at intended curve–arrowhead, connector–arrowhead, and edge–node-anchor construction relationships. Their final-visible raw masks do not intersect. All such pairs were individually opened and explained in the pair ledger.
- All 197 glyph masks and 18 graphic masks are nonempty. Contact cards show original, unique target overlay, mask-only and 8× nearest views. Missing-stroke pixels and foreign pixels are zero in every manual row.

## Glyphs, font hierarchy and R168 disposition

There is no tofu, missing character, wrong codepoint, wrong mathematical glyph, or actually unreadable text. The current source has no graphical scale. The figure uses 9.2 pt for its principal labels/formulas and 8.6 pt for the intentionally subordinate top annotation; the official PDF produces clearly readable native ink (dominant CJK 32–34 px in the body, caption 35–38 px; mathematical lowercase 19–30 px with full-height delimiters 37–38 px).

Legacy numeric taxonomy flags on equals signs, right arrows, punctuation, and the naturally single-stroke CJK character `一` were manually inspected. Their contours and semantics are complete. Under the supplied R168 decision rule, these small-height or micro-ratio facts are advisory and cannot by themselves create a hard FAIL. `ledgers/manual_r168_advisory_ledger.csv` records each advisory group and its real contour evidence.

No visually obvious severe size imbalance exists. Proposal formulas are symmetric, both accepted-flow lines use the same source role, the two explanatory lines have identical 34 px dominant CJK height, and the caption hierarchy is natural on the page. Grayscale retains the structure.

## Mathematical and page semantics

The diagram correctly defines `a=π(x)q(x,y)` and `b=π(y)q(y,x)`, clips both accepted flows to `min(a,b)`, and states both directional equalities with the correct `α` arguments. Equal accepted flows give detailed balance; detailed balance is sufficient for stationarity of `π` but not necessary. The caption and adjacent chapter text (the detailed-balance derivation followed by Proposition 32.1) agree with the figure.

## Manual gate result

- Source identity: PASS.
- Object/glyph mapping: PASS.
- Font actual readability / no severe imbalance: PASS, with R168 advisories only.
- Geometry/relationships: PASS.
- Zero illegal overlap: PASS.
- Zero clip: PASS.
- Mathematical semantics and正文一致性: PASS.
- Full page / standalone / grayscale harmony: PASS.
- Manual evidence completeness: PASS.

SA1 result: `PASS — REQUEST_ANOTHER_COMPLETELY_FRESH_ISOLATED_SA3`.

This is an SA1 handoff only. It does not declare `C_LOCAL_PASS` or global PASS.
