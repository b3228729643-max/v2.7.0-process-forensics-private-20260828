# C-FIG-P602-01-R101-SA3-FRESH-ISOLATED-V1

## Decision

- Root gate: `ROOT_MECHANICAL_ACCEPT`
- SA3 package completeness: `PASS`
- Figure strict result: `FAIL`
- This accepts a complete, internally consistent SA3 evidence package whose substantive result is FAIL. It does not establish `C_LOCAL_PASS`, `A_LOCAL_PASS`, global PASS, or authorization to start another figure.
- Root audit completed UTC: `2026-08-25T04:50:15.2464123Z`

## Freshness and isolation boundary

- Exactly one fresh SA3 was launched with `fork_turns=none`: `/root/sa3_fig_p602_r101_fresh_isolated`.
- The SA3 project-input whitelist was limited to the official R101 PDF, the current single P602 figure source, necessary adjacent current chapter text, Goal, the strict pixel/typography protocol, and the strict evidence schema. System-required skill files were procedural only.
- The SA3 attests it did not read any prior/sibling P602 evidence, SA1 report or ledger, root/reseal/handoff, C or central state/inventory, historical chat conclusion, other-agent output, or other-figure evidence.
- Business sources were read-only. No TeX engine, LuaLaTeX, latexmk, build, or compilation was invoked. No source, chapter, macro, state, inventory, or central file was written.
- All SA3 writes are confined to the new root below; the C root audited that root read-only after its final marker.

## Evidence root and official identity

- Evidence root: `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\C_visual\evidence\FIG-P602-01\sa3_r101_fresh_isolated_v1`
- Final report: `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\C_visual\evidence\FIG-P602-01\sa3_r101_fresh_isolated_v1\SA3_REVIEW.md`
- Official PDF: 4,947,496 bytes; 814 A4 pages; SHA-256 `0870FF226DC383875C4A1B6EABB06AAB942317DA294D90D2864B3030D46DF1A1`.
- Independently located target: physical PDF page 651, printed page 638, figure 32.5.
- Current figure source: 2,711 bytes; SHA-256 `18B88F4BC48A21D3FD1A246AC5B6909DEEB19900A3D0721C65F9A44369444084`.
- Adjacent current chapter: 105,168 bytes; SHA-256 `00F3537AE9DD6738F1BAB414D587F18870A6B08D64663283C6F9A3F3048E6BA7`.
- Worktree remained clean on branch `v2.7.0/dialogue-c-visual`, HEAD `eea4060c5229168e2b973bbaea81cf391e7a9dfd`.

## Independent denominators and results

| Gate family | Total | PASS | FAIL |
|---|---:|---:|---:|
| semantic objects | 32 | 32 | 0 |
| visible glyphs | 175 | 158 | 17 |
| all unordered object pairs | 496 | 496 | 0 |
| critical pairs | 17 | 17 | 0 |
| peer rows | 42 | 36 | 6 |
| role rows | 3 | 2 | 1 |
| clipping rows | 32 | 32 | 0 |
| mandatory views | 4 | 4 | 0 |
| hard gates | 12 | 8 | 4 |

- The object denominator is independently decomposed as 19 text/formula objects plus 13 `GRAPHIC/MATH_RULE` objects. The visible acceptance-ratio fraction rule is the independent object `O-G04`.
- The pair set is exactly all 496 unique unordered combinations, with no missing/extra pair and no self-pair: `C(32,2)=496`.
- All 496 machine pair rows and 496 per-ID manual pair rows are PASS; summed illegal-overlap pixels are 0. All 17 machine critical flags match the 17-entry critical index and manual ledger.
- All 32 clipping rows are PASS with summed clip pixels 0. Empty object masks and empty glyph masks are both 0.
- Source-font audit has 19 rows, no failure, and minimum effective size 9.6 pt.

## Dispositive strict failures

- Glyph FAIL IDs (17): `G007,G013,G014,G021,G032,G044,G051,G062,G077,G081,G092,G104,G118,G132,G160,G164,G167`.
- Fixed-threshold failures include the 12/14-pixel equals signs against the 22-pixel operator floor, the 5-pixel `U+4E00` CJK glyph against the 30-pixel CJK floor, and other operator/accent failures. Calibrated punctuation failures use the protocol's same-codepoint/font/size height and area ratio range `[0.92,1.08]`.
- Peer FAIL IDs (6): `PEER21,PEER22,PEER23,PEER24,PEER38,PEER39`.
- Role FAIL ID (1): `ROLE03`; formula-block/base ratio `1.2244897959183674` exceeds the strict maximum `1.18`.
- Hard-gate FAIL IDs (4): `HARD03` glyph thresholds, `HARD07` peer consistency, `HARD08` role consistency, and aggregate `HARD12`.
- Machine failure sets and manual failure sets match exactly for glyph, peer, and role ledgers.

## Root mechanical audit

- Ordinary files: 1,020. Manifest rows: 1,018. The exact unlisted set is only `evidence_manifest.csv` and strictly-final `WRITE_STOPPED.json`.
- Manifest rows have 0 duplicate paths, 0 escaping/bad paths, 0 missing files, 0 byte mismatches, 0 SHA-256 mismatches, 0 NTFS 100-ns mtime mismatches, and 0 `mtime_ns` mismatches.
- `evidence_manifest.csv`: 165,191 bytes; SHA-256 `98A0431433333EE55DB8531C2EF8BE8C605A84CC57301D69F42B538F496F2C81`; mtime UTC `2026-08-25T04:43:04.2515450Z`.
- `WRITE_STOPPED.json`: 2,619 bytes; SHA-256 `13A9A1E9667DC1F1621F881E4C6D8E5A26EBDE8010A85CA6B8B19B396761E23C`; mtime UTC `2026-08-25T04:43:25.0453490Z`.
- The manifest is the latest pre-marker file; files later than the marker: 0.
- Parse results: CSV 21/21, JSON 5/5, PNG 981/981. ADS: 0. `pyc/__pycache__/cache`: 0.
- All nine manual ledgers have their exact machine denominator, unique IDs, nonblank evidence, nonblank per-ID reasons, and zero completely duplicated reason groups. All 496 pair evidence references are unique and every pair-specific reason names both member object IDs.
- All object, glyph, pair, and critical machine evidence paths exist. Four mandatory views, selected failure/calibration cards, an object sheet containing `O-G04`, and a critical contact card were independently opened by the C root.
- Independent PDF tools confirm 814 A4 pages and page-651 text containing printed page 638, figure 32.5, its Metropolis-Hastings caption, and the reading-order paragraph.
- Post-SA3 source/PDF/chapter hashes match the marker. Worktree remains clean. The old SA1 root remains 492 files; the accepted reseal root remains 494 files with marker SHA-256 `7A3B3F2BD128B8162795928878F0A0B6B107C181172D67239679A54E608A2C87`; its prior handoff remains SHA-256 `27CD4094FF7893A9170C32FB82F7611D8F4ABA57F92A1C92A48706230970DBA7`.

## Acceptance boundary and next control

- Mainline may independently verify and accept this handoff as a complete fresh-isolated SA3 FAIL package.
- No central inventory/state update is authorized by this handoff. No next figure may start under this task.
- Any remediation requires a separately authorized business-source writer and a separately explicit mainline TeX slot, followed by a new official candidate and a fresh evidence run. This handoff does not grant either authorization.
