# FIG-P608-01 R6A local SA2 — mainline acceptance

- Timestamp: `2026-08-25T02:23:05+08:00`
- Mainline decision: `ACCEPT_LOCAL_SA2_PASS_AWAIT_OFFICIAL_CANDIDATE_AND_FRESH_SA1`
- Handoff: `A-R138-P608-SA2-CLOSE-20260825`
- Source commit: `738e079d8e85621b23f30e71017eafde37681711`
- Source SHA-256: `78C30F4A934F63E0EF1BBACF400A24F22477D38589F99503AE468F7024A35C05`
- Accepted evidence: `STRICT_R6A_SA2_REPAIR_R99_LOCAL_EVIDENCE_RESEAL_20260825`; the rejected R6 package remains quarantined.

## Independent mechanical audit

- Ordinary files: 842; inventory payload: 835 unique entries.
- Inventory path, byte-size and SHA-256 mismatches: 0; allowed extras are exactly the inventory and six terminal/seal files.
- Reused payload: 813 entries; source/destination paths, sizes, declared hashes and recomputed hashes all match.
- Parse/decode: 14 JSON, 22 CSV and 784 PNG files, with 0 failures.
- NTFS alternate data streams: 0.
- `WRITE_STOPPED` is strictly newest; delta from the latest other file is 1,750.8101 ms.
- The explicit manual ledger has 199 per-ID decisions: 170 objects, 13 critical pairs, 7 views and 9 semantic roles. It contains no default/global-boolean decision and no pending or unknown result.

## Accepted local repair fact

- Object denominator: `N=170 = 112 glyphs + 58 paths`.
- Complete unordered-pair denominator: `C(170,2)=14,365/14,365`.
- Machine-pixel, illegal-pair overlap, clearance, empty-mask and clip failures are all zero.
- Both repaired natural-script `t` glyphs have native 300 dpi `H_INK=21px >= 15px`; minimum clearances are 115.430 px and 86.000 px.
- The strict low-profile set passes 15/15. For `GLYPH_0072`, the peer was predeclared as the nearest non-target exact-identity period in official R99 page 652, Figure 32.5; peer and target are both H=7/area=41, and translation-normalized mask symmetric difference is zero.
- Mainline opened the final crop, overlay and target/peer native-nearest views and found no unresolved visual defect.

## Source-scope audit

The commit changes exactly one P608 drawing source and adds only the y-label placement rule:

`ylabel style={rotate=-90,anchor=east,at={(axis description cs:-0.12,0.5)}},`

The current mainline file equals the commit parent version, so the single-file cherry-pick is conflict-safe.

## Route

Integrate the single-file source commit. This is not `A_LOCAL_PASS` and does not change the strict final count. Freeze the next official candidate only after the pending B-P04 sealed handoff is integrated, then dispatch a completely fresh isolated SA1 for FIG-P608-01. That SA1 must not read any prior P608 evidence, SA2/root report, handoff, state or inventory conclusion.
