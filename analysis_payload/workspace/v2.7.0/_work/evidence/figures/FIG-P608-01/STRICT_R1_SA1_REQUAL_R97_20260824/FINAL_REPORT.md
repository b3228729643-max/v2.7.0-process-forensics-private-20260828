# FIG-P608-01 — SA1 strict requalification R97

## Terminal recommendation

`FAIL_TO_SA2` — the candidate is frozen; no source change was made. The failures below remain after full enumeration, native-pixel review, semantic requalification, and evidence cleanup.

## Candidate identity and scope

- Candidate: `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\build\strict_current_r97_fullbook\main_full.pdf`
- SHA-256: `062AD81020CB19A5C6688A45C73E00965F5060E0960A69AF820D7DC154DEE814`; 813 pages.
- Figure: 32.8, physical PDF page 659, printed page 646; crop is P608 caption/frame only and excludes adjacent P609.
- Read-only declared source: `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\绘图源码\第05册_采样方法主题模型与图排序\V5-C03\fig_v5_c03_trace_running_mean.tex`; SHA-256 `DA035C1920CB900E54D3658851C1D71D9C6446531EFF50BEE6E089B567835AE4`.

## Complete audit coverage

- 36 text objects + 66 graphic objects (including independent math rules R001/R002) = 102 objects.
- 5,151 / 5,151 unordered TT/TG/GG pairs, exactly 102C2.
- 114 / 114 visible glyphs signed after native 1× and 8× nearest review, through 10 glyph sheets.
- 110 / 110 contact/critical cards signed through 10 pair sheets; 93 named individual semantic contacts, never a class exemption.
- 15 low-profile targets independently calibrated with H/area ratios in [0.92,1.08]; all 46 in-scope drawing paths accounted for and 0 unassigned visible foreground paths.

## Hard failures

| Gate | Objects | Native measurement / finding | Result |
|---|---|---|---|
| Pixel height | G008 `=` | H_INK 12px < 22px | FAIL |
| Pixel height | G019 `=` | H_INK 11px < 22px | FAIL |
| Legal-script pixel height | G027 `t` | H_INK 10px < 15px | FAIL |
| Legal-script pixel height | G058 `t` | H_INK 10px < 15px | FAIL |
| Glyph purity | G063 `运` | 16 foreign pixels from G005; no missing stroke | FAIL |
| Cross-panel TG | P2311 T027/G001 | 0px overlap, 2px clearance < 8px | FAIL |
| Cross-panel TG | P2315 T027/G005 | 16px overlap, 0px clearance < 8px | FAIL |
| Cross-panel GG | P3071 G001/R002 | pre-zorder shared 64px; final unique overlap 0px but clearance 0px < 8px | FAIL |

P3071 is not repaired by paint order: vector drawing geometry independently gives axis drawing[8] y=311.025024pt/0.647570pt and overbar drawing[62] y=311.670044pt/0.732000pt, centreline distance 0.645020pt versus half-width sum 0.689785pt (0.044765pt penetration). The four critical raw-mask/overlay cards are retained in `critical_barX_vs_upper_axis/`.

## Individual data-relation requalification

P5003, P5008, P5009, P5011, and P5012 are not hard failures. Each has a unique target-reference/marker semantic proof and a signed pixel card: t=10=1.9800, t=15=2.0200, t=16=2.0182, t=18=2.0077, and t=19=2.0071 against the separately drawn y=2 reference. Details are in `intentional_data_relation_review.csv` and `INTENTIONAL_DATA_RELATION_REVIEW.md`. No other cross-panel collision is whitelisted by that decision.

## Typography, D/E and visual review

Normal effective label/tick text is >=9.5pt and its same-role hierarchy is not oversized or visually reduced. Legal scripts receive their own pixel gate, which fails at G027/G058. Full-page 200dpi, native 300dpi 1×, standalone, grayscale, and 8× nearest views were opened. The lower title overbar reaching the upper x-axis breaks cross-panel coordination, so the visual D/E gate is also FAIL.

## Cleanup and closure status

A scoped stale-self-generated cleanup is documented separately: all 225 planned targets were Resolve-Path verified inside this exact R1 directory, and post-delete verification found zero surviving targets, zero missing final references, and zero remaining stale candidates. An initial Windows PowerShell BOM decoding failure caused no deletion and is retained as a fact record. Terminal, manifest, and write-stop are issued only after this report and final integrity checks.
