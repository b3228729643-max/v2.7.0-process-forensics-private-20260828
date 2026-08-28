# FIG-P077-01 SA3 visible-object denominator freeze

- HANDOFF_ID: `A-R114-P077-SA3-FRESH-ISOLATED-20260828`
- Freeze time: `2026-08-28T01:17:49.2612086+08:00`
- Basis opened before freeze: full page native 300 dpi, full page grayscale 300 dpi, figure crop native 300 dpi, figure crop grayscale 300 dpi, raw span overlay, semantic object overlay, and five critical native1x/nearest8x ROI pairs.
- Frozen semantic/visible objects: `N=25` (`T01-T14`, `G01-G08`, `B01-B03`).
- Required unordered-pair universe: `C(25,2)=300`.
- Scope rule: every reader-visible text/formula has its own element ID except intentionally inseparable mixed runs; the automatically sized superscript `2` is separate as `T09`. Axis baseline, arrowhead, and its three matching tick strokes are one inseparable axis object. White opacity grounds are included as visible compositing objects even though they are not semantic foreground.
- Freeze state: final. No object was added, removed, regrouped, or renumbered after this file was written.
