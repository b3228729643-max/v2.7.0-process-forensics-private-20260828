# A-R130-P608-SA2-RESUME｜FIG-P608-01｜SA2 R3

Status: `PARTIAL` — the SA2 local repair and evidence package is closed, but the official R99 build and fresh independent SA1/SA3 chain remain mandatory.

## Scope and decision

Only the authorised figure source was changed. The warm-up annotation was moved from the hatched zone to a clear upper-panel location and its translucent white background was removed. This eliminates the real label-to-hatch clearance risk without treating an occlusion layer as an exemption.

The local PDF replay utility was also corrected so an open stroked trace is not forcibly closed into a false diagonal. That correction is evidence-only and exposed the earlier apparent label-to-trace contact as mask contamination, not a source-level collision.

## Validation

- Local LuaLaTeX wrapper build: succeeded, one page.
- Direct native 300-dpi raster: 2481 x 3508 px; native 200-dpi page-fusion view also recorded.
- Objects / all unordered pairs: 91 / 4095.
- Ownership checks: foreign 0; missing 0 for every counted object.
- Illegal overlap: 0; required-clearance failures: 0.
- Rotated glyph page/local H/W: recorded for every glyph, including the two rotated mathematical `t` glyphs and rotated `U+2236`.
- Low-profile calibration: 11 same-codepoint, same-font, same-effective-size records, all within [0.92, 1.08].
- Hatch relations: both hatch objects against each visible glyph and the two equality-rule groups, 140 relations, all separate.
- Native glyph sheets actually opened: 13 at 1x and 13 at 8x nearest; figure crop was visually checked at original resolution.

## Required next action

Root must inspect this sealed local package, build the next official full-book candidate, and route FIG-P608-01 through a new independent SA1 followed by isolated SA3. Do not carry this local candidate forward as a strict final PASS.
