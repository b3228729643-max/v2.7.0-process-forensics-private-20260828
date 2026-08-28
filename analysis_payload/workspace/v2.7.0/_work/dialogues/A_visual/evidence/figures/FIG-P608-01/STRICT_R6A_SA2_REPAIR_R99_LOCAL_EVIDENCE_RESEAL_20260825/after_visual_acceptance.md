# FIG-P608-01 SA2 R6A local evidence reseal

HANDOFF_ID: `A-R99-P608-SA2-NARROW-R6A-EVIDENCE-RESEAL-20260825`  
ROUTE: `SA2=gpt-5.6-sol/max`  
RESULT: `LOCAL_SA2_PASS_AWAIT_OFFICIAL_CANDIDATE_AND_FRESH_SA1`

R6A preserves the sealed direct-r6 PDF and bottom evidence, replaces the
rejected aggregate review mechanism with 199 explicit per-ID decisions, and
applies the root-adjudicated strict low-profile calibration. It does not rerun
TeX, alter the business source, review an official candidate, or assert
`A_LOCAL_PASS`.

## Root-adjudicated peer

The peer identity was frozen before metrics by the predeclared nearest exact
other-figure-number rule. The unique choice is the U+002E period in `图32.5`,
official R99 physical page 652, bbox `(180.941010, 702.317444, 183.690704,
712.280090)`, STIXTwoText-Bold 9.9626pt, RGB(31,35,40), horizontal. The one
300-dpi Poppler render initially contained four padded-bbox pixels belonging to
the adjacent digit `5`; the R6 bare-bbox/centre-distance ownership rule removed
them without changing the peer or raster. Final peer and GLYPH_0072 masks are
both H=7px, area=41px, one component, with identical translation-normalized
pixel sets. Strict target/peer H and area ratios are both 1.000000.

## Bottom-up closure

- N=170: 112 glyphs and 58 foreground paths.
- Complete C(N,2)=14,365 pair ledger; pair failures=0.
- Strict low-profile rows=15; true design failures=0.
- Final illegal overlap pixels=0; clip pixels=0; crop text clearance=72px.
- Explicit decisions: 170 objects, 13 critical pairs, 7 views, 9 roles.
- Reused byte-identical evidence files=813.
- Accepted payload inventory rows=835; expected final ordinary files=842.
- Non-default NTFS stream count=0.

## Source and local candidate identity

- HEAD `e392bd8e5f37dfd49f071f7251c281d46bb68ffd`; sole source diff +1/-0.
- Source SHA-256 `78C30F4A934F63E0EF1BBACF400A24F22477D38589F99503AE468F7024A35C05`.
- Local direct-r6 PDF SHA-256 `638A722CC86D848E6B0FDEB69F08BB6DDBD3F0AD33E262AB36690C2943FD03BB`; 42,989 bytes.
- Official R99 source PDF SHA-256 `E8D76EEF0D120C518FA94A8F339BF6777AD18AA6AF0BCC17DFB46DF6DFC49EC6`.

## Terminal boundary

`MACHINE_TERMINAL_RECALC.json` precedes the manifest, this report, result, and
handoff. `WRITE_STOPPED` is written strictly last. A new official candidate and
fresh isolated SA1 remain mandatory; SA1 and SA3 were not started here.
