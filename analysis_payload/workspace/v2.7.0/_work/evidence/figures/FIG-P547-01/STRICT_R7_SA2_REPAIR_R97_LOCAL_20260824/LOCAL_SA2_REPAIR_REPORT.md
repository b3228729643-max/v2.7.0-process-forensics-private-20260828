# FIG-P547-01 strict local SA2 repair report

## Terminal recommendation

`LOCAL_PASS_TO_ROOT_BUILD`. This is a local white-list repair recommendation only. It is not an official or final figure PASS. Root must build the next full-book candidate and commission a fresh independent SA1 review.

## Bound identities and source diff

- Authority candidate: R97 full book SHA256 `062AD81020CB19A5C6688A45C73E00965F5060E0960A69AF820D7DC154DEE814`.
- Verified before-source snapshot: SHA256 `638CEA4285D3A9411251DA149963CC7AE4500FA5827F0A99A51FF1FC76640D1A`.
- Current authorized source and exact snapshot: SHA256 `DF3D4415EDC56D02E056CAE0F3E38830DF28E781BC67ECDFB69863C5038F1600`.
- Exact before/after patch: `source_identity/baseline_to_current.patch`. No v2.6.0, R1, or mismatched historical source was used as the baseline.
- Final local page PDF: SHA256 `EA9904BF008275BB7E6840F3FC5A0D390F463F52B437C35AAAD840FE0CA9DEA1`.
- Final local standalone PDF: SHA256 `4CD804E17A607767E7B740B9B170A463708B675C8DBF383F13B4312315BB6BD1`.

The only business-source change is the authorized transition-graph TeX. It defines compact local TikZ geometry for relation symbols; replaces all 12 visible equals and all 3 visible right arrows; changes `同一条` to the semantically equivalent `物理边`; separates/raises the focus labels; gives lower labels vertical padding; and moves the two gold bridge endpoints to x=±2.82cm. PageRank in the caption remains normal weight. There is no whole-figure scaling, vertical glyph stretching, common-macro/body edit, or normal text below 9.5pt.

## Object universes, drawings and pairs

The GEN4 current local enumeration contains 193 unique text glyphs and 65 unique foreground graphic objects. Their ID sets are disjoint, so their union contains exactly 258 pair-denominator objects with no duplicate. The 15 relation composites are review abstractions over existing component graphic masks and are deliberately not added again to the denominator.

The PDF contains 71 drawing paths inside the figure crop:

- 63 foreground-only drawings;
- 2 drawings whose foreground stroke and occlusion fill are both explicitly accounted;
- 6 occlusion-background-only drawings.

Thus 63+2=65 unique foreground drawing indices map to the 65 graphic objects, while the 6 occlusion-only drawings stay outside the foreground pair denominator. There are no unassigned or duplicate-primary drawing indices.

The complete unordered denominator is 258×257/2 = 33153. All 33153 normalized unordered keys are unique, and every object has degree 257. Machine decisions are 33114 `PASS` plus 39 `PASS_INTENTIONAL`, with zero failure and zero empty-mask distance. Group counts are 16751 TT, 1777 text-internal, 12545 TG, 2041 GG, and 39 named intentional-whitelist pairs.

## Original failures and repair values

The 12 geometric equals have native 300dpi composite heights 26, 29, 29, 30, 29, 30, 29, 26, 29, 29, 29, and 29px; every value exceeds the 22px gate. Each mask shows two complete parallel rules and still reads as an equals sign. The 3 geometric right arrows have heights 24, 24, and 23px against the 22px gate; their shaft/head joins are the only intentional contact and remain visually coordinated.

Legacy C0073 `一` at 6px was not reclassified. The whole label was rewritten without information loss to `物理边 i→j`. Current `物/理/边` measure 44/41/43px against the 30px CJK gate. Current local C0073 is instead the unrelated natural subscript `j`, H=33px against its 15px script gate.

Legacy C0198 was the final prose `n` in caption word `PageRank`, not a mathematical base glyph. In the current enumeration it is C0183, STIXTwoText-Regular 9.9626pt, H=21px against the authoritative `PROSE_LATIN_X_HEIGHT` gate of 17px. It passes without local bolding and the caption remains visually even.

The four accepted 1px non-whitelist failures now map to:

- old C0026-G07 → current C0024-G07: 31.0644px;
- old C0026-G09 → current C0022-G09: 13px;
- old C0120-G24 → current C0109-G24: 31.7805px;
- old C0120-G26 → current C0107-G26: 10px.

All exceed the hard 3px gate. The last value does not reach the optional 12px safety target; this is not a hard-gate exemption. Native 1×, 8× and global review shows the 10px right focus-label gap is uncramped and visually natural.

Additional intermediate failures are also closed: left gold bridge to matrix 19.1050px, right gold bridge to P formula 25.4951px, left lower `0` to return shaft 12.6491px, and right lower `0` to return shaft 13px. All masks are pure, intersections are empty where noncontact is intended, and no arrow crosses formula foreground.

## C0153 and C0114 mask causality

The name C0153 occurs in two unrelated enumeration domains. `UPSTREAM_R97::C0153::UFF1B` is the historical full-book semicolon used only in `before_r97/c0153/` calibration evidence. Its exact two-component native mask is H=28px, area=57px; the independent calibration is H=28px, area=58px. The 45px neighbouring component and 1px edge component remain in the foreign mask. No morphology, interpolation, or contour repair was used.

`GEN4_LOCAL_STANDALONE::C0153::U0030` is a current bold digit `0` and is the only C0153 in the 193/258/33153 current denominators. The current local semicolons are C0054 and C0139. The historical proof informs their same-codepoint/font/size separation method but is never joined or counted as the current digit. `final_audit/reports/C0153_NAMESPACE_DISAMBIGUATION.md` binds this distinction.

GEN3 C0114 `1` was visibly polluted by an upper short rule, two side pixels, and a bottom geometric rule, giving false H=33px/area=164px. GEN4 exact connected-component ownership retains only the native digit: H=23px/area=122px, exactly matching peers C0023, C0030 and C0109 at U0031/STIXTwoMath-Regular/8.0896pt/NATURAL_SCRIPT.

## Typography, visual review and manual ledgers

The source minimum explicit size is 9.6pt. Current normal PDF text has no font-floor failure; 28 smaller emissions are only natural TeX scripts traced to valid ≥9.5pt base formulas. D raw-outline comparison uses only same role + exact glyph + font + emitted pt + baseline cohort, and D scale uses emitted pt; GEN1/GEN2 false comparisons of unlike outlines remain superseded. D raw has 136 PASS and 57 no-comparable-peer rows; D scale has 191 PASS and 2 no-comparable-peer rows; E has 9 PASS roles.

SA2 opened the page and standalone at 200/300dpi, both 300dpi grayscale views, the native figure/caption crop and crop grayscale. There is zero clipping, overlap, bridge/matrix collision, formula crossing, or intrusive type scaling. All 17 glyph sheets (193 glyphs), all 7 graphic sheets (65 graphics), both relation sheets (15 relations), 24 low-profile cards, 40 critical/intentional 1×+8× pair cards, 6 named repair sets, 6 reverse-occlusion sets, and the C0153/C0114 causality cards were opened. Active signed ledgers have zero pending and zero manual failure.

The pre-review JSON intentionally records the generator's placeholder state. It is superseded for manual status only by `final_audit/machine/manual_review_completion.json`; machine measurements themselves remain immutable.

## Scope, superseded material and seal

No official full-book build was run. No common macro, body text, central inventory/status, other figure source, official build candidate, or other evidence directory was written. Six superseded directories remain hash-covered for traceability but are excluded from acceptance by `SUPERSEDED_INVENTORY.md` and their own markers. Twelve zero-byte LaTeX index intermediates were explicitly removed; the pre-seal package contains zero zero-byte files.

`LOCAL_SA2_GATE_REGISTER.csv` and `LOCAL_SA2_PRIOR_FAILURE_REMEASUREMENT.csv` are the compact bottom tables. After these reports and `LOCAL_SA2_TERMINAL.md` are complete, `seal_local_package.py` generates `evidence_manifest.json`, then `MANIFEST.sha256`, verifies their payload, and writes `WRITE_STOPPED.md` as the final filesystem write.
