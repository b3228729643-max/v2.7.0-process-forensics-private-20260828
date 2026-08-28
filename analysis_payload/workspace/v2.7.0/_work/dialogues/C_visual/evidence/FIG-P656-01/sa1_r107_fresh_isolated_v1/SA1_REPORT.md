# SA1 report — FIG-P656-01 / Figure 34.2 / R107

## Assigned scope

Fresh isolated SA1 review of only `FIG-P656-01`, Figure 34.2, on official R107 under handoff `C-FIG-P656-01-R107-SA1-FRESH-ISOLATED-V1`. Evidence was created only in this assigned root. Source and official PDF were read-only. No TeX/build, source edit, PDF edit, Git/state write, other UID, old evidence, or delegation occurred.

## Candidate and location

Official PDF identity is 817 pages, 4,967,249 bytes, SHA-256 `8811950621E2D64A3C2A8F0F7A52DD0FAC2BDB12018F3EA052C1F58C94EF8DF3`. Independent caption/content location is physical page 705, printed page 692. Current source SHA-256 is `BC954A32F6FC8811F9557AD9A3147795CB6CB467DEAEF6195A3A0B1D9E855852`.

## Frozen evidence denominator

| Evidence family | Denominator | Manual ledger |
|---|---:|---:|
| Visible glyph leaves | 90 | 90 |
| Drawing/path leaves | 25 | 25 |
| Independent math-rule leaves | 0 | 0 |
| Total figure-body leaf objects | 115 | reconciled |
| All unordered leaf pairs | 6,555 | machine complete; nonzero relations individually adjudicated |
| Critical semantic relations | 34 | 34 |
| Clip objects | 115 | 115 machine rows |
| Core views | 10 | 10 |
| Source/font groups | 10 | 10 |
| Peer/role groups | 10 | 10 |
| Hard gates | 13 | 13 |
| Glyph contact sheets | 6/6 opened | 90 cells |
| Critical relation sheets | 6/6 opened | 34 relations |

`N` uses glyphs as leaf objects: each of the 90 visible glyphs is an independent foreground leaf, combined with 25 visible drawing/path leaves. The caption is outside the figure-body N and is reviewed as page integration. Machine, manual, and report counts use this same definition.

## Hard-gate result

- Real missing/tofu/wrong codepoint/math semantic error: none.
- Actual unreadability or visibly severe imbalance: none.
- Real clipping: none; 0 pixels.
- Illegal overlap: none; 0 pixels.
- Material geometry/semantic error: none.
- Raw graphic intersections: exactly three intentional connections, `P6539=18`, `P6541=41`, `P6555=38`, total 97 pixels.
- Empty raw masks: 0 glyph, 0 drawing.
- Mask contamination: 0 pixels.
- Pending, unknown, duplicate, or missing manual decisions: 0.

The earlier unsealed 4/252 diagnostic was corrected by tightening vector mask ownership from a 4px bbox pad to the actual 2px half-stroke/antialias allowance. `overlap_adjudication.md` records every changed pair and the final reopened ROIs. The later `G055` punctuation-row addition did not affect overlap masks.

## Decision

All source semantics, geometry, formula content, leaf masks, all-pair coverage, critical relations, clipping, grayscale, font harmony, and page integration pass the applicable hard gates. R168-only micro differences are advisory and are recorded rather than promoted to failure.

Outcome: `SA1_PASS_AWAIT_FRESH_ISOLATED_SA3`.

This SA1 result does not count a local/global acceptance and does not authorize or start SA3. The next action belongs to the coordinator: independently dispatch the required fresh isolated SA3, using no conclusions from this review as evidence.
