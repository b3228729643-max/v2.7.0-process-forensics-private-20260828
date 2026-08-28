# RESULT — FIG-P715-01 R106 SA1

- HANDOFF_ID: `A-R106-P715-SA1-FRESH-ISOLATED-20260826`
- Result: **FAIL**
- Route: **SA2**
- Identity: official R106 PDF, physical page 765 / printed page 752.
- Denominator: 216 glyphs + 43 paths = 259 objects; 33,411 unordered pairs.
- Primary hard evidence: `PAIR_08396`, node `j` border versus glyph “矩”, 37 native intersection pixels.
- Additional hard evidence: matrix/formula and note/matrix intersections of 20–97 px, text/panel clearance 3 px versus 6 px, and text/text clearance 0 px versus 4 px.
- Confirmed illegal intersection sum excluding contaminated-comma pairs: 888 native pixels. Clip count: 0.
- R168 advisory micro typography was not used as a failure trigger.
- `TXT_G0081` has a 13-pixel foreign mask component; this independently prevents evidence PASS.
- No `A_LOCAL_PASS` claim; SA3 is not authorized.
- Next action: SA2 repair, new build, then a new fresh isolated SA1.
