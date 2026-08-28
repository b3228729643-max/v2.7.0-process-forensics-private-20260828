# Manual unordered-pair adjudication

- Reviewer: `SA3_FRESH_ISOLATED`
- Review timing: written only after opening the current R114 full page at 300 dpi and 200 dpi, the figure native 300 dpi crop, nearest-neighbour 8x crop, grayscale crop, text-box overlay, critical contact sheet, and all three critical ROIs.
- Frozen denominator: 63 semantic visible objects, comprising 21 text/formula IDs and 42 graphical primitive/layer IDs.
- Frozen unordered universe: `63 choose 2 = 1953` pairs in `00_control/all_unordered_pairs_mechanical.csv`.
- Mechanical universe validation observed before this ledger: expected 1953; actual 1953; unique pair IDs 1953; unique unordered keys 1953; self-pairs 0; missing object references 0.
- This file and its reviewer/decision/note content were authored manually after visual observation. No machine builder generated or overwrote these fields.

## Manual disposition covering every PAIR_ID

- `MANUAL_REVIEWED_PAIR_COUNT = 1953`
- `MANUAL_CLEAR_SEPARATED_PAIR_COUNT = 1885`
- `MANUAL_LEGAL_COMPOSITION_OR_ALIGNMENT_PAIR_COUNT = 68`
- `MANUAL_TRUE_ILLEGAL_OVERLAP_PAIR_COUNT = 0`
- `MANUAL_UNRESOLVED_PAIR_COUNT = 0`
- `MANUAL_PAIR_DECISION = PASS`

Every pair not listed in the 68-ID legal-contact set below was visually separated in the opened native, 8x, grayscale, overlay, page, and relevant ROI evidence. The 68 listed pairs do contain an expected construction contact, coincidence, or guide crossing. Each was inspected at native 300 dpi and nearest-neighbour 8x and is a semantic composition/alignment, not a collision between unrelated reader objects.

## Exact legal-contact PAIR_ID ledger

Upper axes and ticks — legal axis construction:

`PAIR-1093`, `PAIR-1134`, `PAIR-1135`, `PAIR-1136`, `PAIR-1137`.

Upper CDF curve with its markers and alignment guides — legal curve/marker composition or intended guide crossing:

`PAIR-1324`, `PAIR-1325`, `PAIR-1326`, `PAIR-1327`, `PAIR-1328`, `PAIR-1329`, `PAIR-1330`, `PAIR-1331`, `PAIR-1332`, `PAIR-1333`, `PAIR-1334`, `PAIR-1335`, `PAIR-1336`.

Upper marker/guide and guide/guide alignment — legal support-point or terminal-level alignment:

`PAIR-1367`, `PAIR-1401`, `PAIR-1434`, `PAIR-1462`, `PAIR-1466`, `PAIR-1493`, `PAIR-1523`, `PAIR-1552`, `PAIR-1580`, `PAIR-1603`, `PAIR-1604`, `PAIR-1605`, `PAIR-1606`.

Lower axes/ticks/stem baselines — legal axis construction and support attachment:

`PAIR-1723`, `PAIR-1724`, `PAIR-1725`, `PAIR-1726`, `PAIR-1727`, `PAIR-1732`, `PAIR-1733`, `PAIR-1734`, `PAIR-1735`, `PAIR-1740`, `PAIR-1741`, `PAIR-1742`, `PAIR-1743`, `PAIR-1748`, `PAIR-1749`, `PAIR-1750`, `PAIR-1751`, `PAIR-1771`, `PAIR-1779`, `PAIR-1790`, `PAIR-1798`, `PAIR-1808`, `PAIR-1816`, `PAIR-1825`, `PAIR-1833`.

Lower PMF stem/marker/guide composition — legal mass-glyph construction and shared support alignment:

`PAIR-1891`, `PAIR-1895`, `PAIR-1902`, `PAIR-1906`, `PAIR-1912`, `PAIR-1916`, `PAIR-1921`, `PAIR-1925`, `PAIR-1929`, `PAIR-1936`, `PAIR-1942`, `PAIR-1947`.

## R168 hard-failure adjudication

- Text/formula ink never intersects unrelated text/formula ink.
- Text/formula ink never intersects an unrelated curve, line, marker, border, or arrowhead.
- The white backing behind `p_1` interrupts the nearby CDF segment before the glyph ink; no curve passes through the label.
- `p_2`, `p_3`, and `p_4` remain separated from the plateau and marker ink.
- The lower annotation remains separated from the `t=4` PMF marker/stem.
- Intended contacts among axes, ticks, curve components, stems, markers, and guides preserve rather than corrupt the probability semantics.
- No candidate is unresolved and no genuine illegal overlap is present.

Canonical manual result: `OVERLAP_PIXEL_COUNT = 0`; `PIXEL_ADJUDICATION_STATUS = CLEAR`; no dispute routing is required.
