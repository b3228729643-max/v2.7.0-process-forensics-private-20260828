# FIG-P654-01 — R22 fresh isolated SA1 report on official R103

## assigned_scope

- `HANDOFF_ID=A-R103-P654-SA1-FRESH-20260825`
- Reviewer instance: `/root/p654_r103_fresh_sa1`
- UID: `FIG-P654-01`
- Sole candidate: official R103 full-book PDF, physical page 704.
- Read-only figure source: `fig_v5_c05_dependency_graph.tex`.
- Review standard: strict pixel/typography protocol and evidence schema, with the assignment's R168 override: geometry, content, seven relations, formula semantics, real clipping/overlap remain hard gates; micro ratios, peer taxonomy, font metadata micro-differences, and 1–2px raster differences are advisory alone.

Isolation was maintained. No old P654 evidence, old reviewer/root report, handoff, state, inventory, route log, task packet, central history, or Git history/diff was read. No TeX engine was invoked. Source, build, central state and inventory were not modified.

## completed

### Candidate identity and native views

- PDF: `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\build\strict_current_r103_fullbook\main_full.pdf`
- Identity: 817 A4 pages, 4,967,184 bytes, SHA-256 `9379A489E0C2A57A7DA670C98029BB27B3F1A385BF8E4C3BD14FE9B606AA0F23`.
- Physical page 704: `595.276001×841.890015 pt`.
- Native 300 dpi page: `2481×3508 px`; figure crop `[292,250,2234,900]` → `1942×650 px`.
- Native standalone crop: `[310,273,2218,900]` → `1908×627 px`.
- Native 200 dpi page: `1654×2339 px`.
- Full page, color crop, standalone crop and grayscale crop were all actually opened and reviewed.

### Complete objects and pair denominator

- Visible glyphs: `93/93`.
- Graphic objects: `16/16` = 8 final-visible node borders + 7 semantic relations + 1 fraction rule.
- PDF drawing/path coverage: `21/21` mapped to the 16 semantic graphic objects.
- Total objects: `109`; complete unordered pairs: `C(109,2)=5886`.
- Critical pairs: `23` = 9 same-formula fraction-rule pairs + 14 source relation endpoints.
- Ordinary mask PNGs opened by machine: `109/109`; ordinary object JSONs opened: `109/109`.
- All 12 glyph contact sheets, 4 graphic contact sheets, 6 critical 8× sheets, the 109×109 complete pair matrix, the text overlay and seven-relation overlay were actually opened before the manual result was written.

### Machine and manual gates

- Machine hard gate: PASS.
- Empty masks: 0; illegal overlap pairs: 0; hard-clearance pairs: 0; clip pixels: 0.
- All 93 protocol raw pixel thresholds pass: CJK ≥36px, Latin uppercase 29px, Latin lowercase 21px, base math/operators 27px, natural scripts 24–26px.
- Manual glyph ledger: `93/93` unique IDs, every row original-match/overlay-complete/mask-only-pure true, missing-stroke 0, foreign-pixel 0.
- Manual graphic ledger: `16/16` unique IDs, every row original-match/overlay-complete/mask-only-pure/nonempty true.
- `OVERLAP_PIXEL_COUNT=0`; `CLIP_PIXEL_COUNT=0`.
- Minimum independent clearances: text–text 47.0416px, text–relation 24.2982px, text–own-node-border 18px, text–other-node-border 18px, text–other-math-rule 69px; all exceed the applicable hard thresholds.
- `FONT_VISUAL_HARMONY_PASS=true`. Color, grayscale, standalone and page-fusion views are balanced, readable and unclipped.

### Semantics

The seven relations are complete and unambiguous: trial→families, gamma→families, families→posterior, posterior→predictive, families–simplex interpretation, posterior–mom interpretation, and dashed predictive→lda application. Text extraction matches all eight nodes and the application label.

Formula semantics pass: posterior `参数 𝛼 + 𝑛`; predictive numerator `𝛼ᵢ + 𝑛ᵢ`, denominator `𝛼₀ + N`; G016 is the separately accounted fraction rule. `N` is genuine U+004E and the binary operators are U+002B.

### R168 advisories

1. A coarse CJK taxonomy mixes the posterior 11.6pt formula word `参数` with the 10.1pt heading and yields 43/37=1.162. Correct role separation identifies valid formula emphasis; this is not a hard failure.
2. Extracted font sizes differ from declared sizes by about 0.4–0.6%; metadata-only advisory.
3. Two raw PDF character-bbox ownership cases existed: T002/T005 had 9 shared candidate pixels and T007/T008 had 1. Traceable connected-component ownership plus actual 8× review shows complete pure final contours and no physical glyph contact.

The first non-TeX machine-evidence run wrote its evidence successfully but returned a console-only GBK Unicode-print error. Only the final console JSON print was changed to ASCII escapes; the deterministic machine evidence was rerun once. Machine scripts never generated or overwrote reviewer, visual, boolean, decision or note fields.

## files_changed

- New sealed evidence root: `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P654-01\STRICT_R22_SA1_FRESH_R103_20260825`
- This formal report: `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\reports\P654_R22_R103_FRESH_SA1_REPORT.md`
- Immutable handoff: `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\handoff\A\A-R103-P654-SA1-FRESH-20260825.md`

No business source, PDF, central state, inventory or Git metadata was changed.

## decisions

- SA1 verdict: **PASS**.
- Required route: `SA1_PASS_AWAIT_FRESH_ISOLATED_SA3`.
- No source repair is requested from this review.

## unresolved

- A new fresh isolated SA3 review is still required by the workflow. It is outside this assignment and was not started here.
- No unresolved SA1 hard failure or evidence gap remains.

## validation

- Final pre-seal cross-check: official identity PASS; objects 109/109; masks 109/109; object JSON 109/109; drawing paths 21/21; manual glyphs 93/93; manual graphics 16/16; pairs 5886/5886; critical 23/23; overlaps/clip/empty masks 0.
- Evidence root sealed at `2026-08-25T17:58:32+08:00`.
- Payload files: 271; total sealed files: 274 (payload + two manifests + `WRITE_STOPPED`).
- `MANIFEST.json` SHA-256: `93BF562C05EBBB7BCDC30E7BBD87FF7DEC562525C53A0B0C86260182C2018329`.
- `MANIFEST.sha256` SHA-256: `6287C951A72C8E310BAEFA1C5E07321B40A0130169D43D041760CC033CCE179F`.
- Both manifests verify `271/271`; `WRITE_STOPPED` is the newest and final content write; post-seal writes allowed/observed: 0.
- Root and every file are read-only; ADS count 0; pyc/cache count 0.

## next_action

Parent/root should consume the immutable handoff and, without changing or reopening this sealed SA1 root, schedule a genuinely fresh isolated SA3 against the same official R103 candidate and physical page 704.
