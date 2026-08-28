# P608 R7A sealed package — independent root mechanical and sampled visual audit

Audit date: 2026-08-25 (Asia/Shanghai)  
Auditor role: independent root, read-only  
Sealed evidence root: `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P608-01\STRICT_R7A_SA1_FRESH_R101_EVIDENCE_RESEAL_20260825`

## Root verdict

`ROOT_ACCEPT_R7A_FAIL_TO_SA2`

The R7A reseal closes the R7 root gaps and contains one independently reproducible hard failure, `HARD-LOWPROFILE-TXT-098`. The correct next route is SA2 repair. This acceptance does not turn any sampled observation into a global visual PASS, does not start SA3, and does not modify the sealed package's terminal string `FAIL_TO_SA2_AWAIT_ROOT`.

No R7 manual decision was used as an R7A answer. The audit read the current Goal, strict pixel/typography protocol, strict evidence schema, and prior R7 root gap report in full before inspecting R7A. The sealed root, business source, state and Git were not modified or executed. Sealed Python files were read as text only and were never imported. Every audit-side Python process ran from the external reports directory with `PYTHONDONTWRITEBYTECODE=1` and `-B`. The only write made by this audit is this external report.

## 1. Frozen identity and source binding

- R101 was independently opened from the bound external path: 814 pages, 4,947,496 bytes, SHA-256 `0870FF226DC383875C4A1B6EABB06AAB942317DA294D90D2864B3030D46DF1A1`. The target is physical page 659 (printed page 646), Fig. 32.8.
- The current P608 TeX source was independently opened and hashed: ordinary file, 3,429 bytes, 58 lines, SHA-256 `78C30F4A934F63E0EF1BBACF400A24F22477D38589F99503AE468F7024A35C05`.
- `source_identity_and_parse.json` binds those exact identities, paths and physical page. The source declares 9.6 pt node/tick/annotation/caption text, 10.8 pt labels/titles, and only the two intended natural `\scriptstyle t` uses. No build tool was invoked during reseal or root audit.

Result: identity and source binding closed.

## 2. R7 machine-only reuse

`reuse_identity_ledger.json` declares 1,893 entries. I independently enumerated the ledger, the R7 source files and R7A destinations:

- 1,893 unique source relative paths and 1,893 unique destination relative paths;
- actual `machine_reuse` files = 1,893, with no missing or extra file;
- every source and destination is an ordinary file;
- all 1,893 path mappings, byte counts, SHA-256 values and mtimes agree exactly;
- every binding names the frozen R101 identity, physical page 659 and frozen P608 source identity;
- reused R7 manual ledgers, `SA1_REVIEW`, `RESULT`, handoff, `after_visual`, hard-failure decision, terminal controls and seal artifacts = 0.

The four sealed `.py` files were statically inspected. `build_r7a_machine_reuse.py` copies only the allowed machine layer and creates reuse/source provenance; `build_payload_manifest.py` creates only the manifest; `consumer_validate_r7a.py` reads the seven R7A manual CSVs and writes only `consumer_validation.json`. None creates or rewrites any `manual_ledgers/*.csv` decision/reviewer/note/manual-pixel field.

One apparent exception was explicitly investigated: copied `machine_reuse/preliminary_algorithm_v1_replay.py` can write the old machine preliminary replay with `PENDING_LEDGER` placeholder fields. It is hash-bound machine provenance, is classified `PRELIMINARY_NOT_ACCEPTED`, has no path to `manual_ledgers` or the accepted 64-row primary CSV/JSON, and was neither run nor imported. The accepted R7A preliminary rows contain numeric manual values and are rejected by the consumer if `PENDING` appears. It therefore does not bulk-generate or mutate the R7A manual decisions.

Result: machine-only reuse closed; no R7 manual conclusion was migrated.

## 3. Denominator, masks, pair closure and bottom-layer consistency

- `N=172 = 112 GLYPH + 58 explicit drawing + 2 PATTERN`.
- Object types independently counted: 112 `GLYPH`, 4 `AXIS_TICK`, 10 `LINE_ARROW`, 2 `DATA_CURVE`, 6 `MATH_RULE`, 35 `MARKER`, 1 `REFERENCE_LINE`, 2 `PATTERN`.
- Safe-name map: 172 IDs and 172 case-insensitively unique filenames, exact object-set equality.
- Four mask trees each contain exactly 172 PNGs. Every PNG decoded. For every object, native dimensions match the recorded bbox; raw/final nonzero counts match; `raw-final=occluded`; recorded H/area agree; every 8× file is exact nearest-neighbour repetition of the corresponding native mask. Errors = 0.
- Independent denominator conservation agrees with the package: rawdict `837=120 domain+717 outside`; domain `120=112 non-space glyph+8 whitespace`; drawings `89=6 preceding equation+58 target explicit+2 corner artifacts+2 following-prose rules+21 following-figure`; the two hatch patterns are separately represented.
- `all_unordered_pairs.csv` is the exact unordered set `C(172,2)=14,706`, with unique IDs/endpoints and no missing/extra pair. Class counts are `CLEAR=14,176`, `INTENDED_DESIGN_RELATION=487`, `INTENDED_DESIGN_OVERLAP=43`.
- The critical set is exactly 102 in machine ledger, evidence ledger and R7A manual ledger. All 612 referenced packet assets exist and are unique. For all 102 packets I decoded `A_raw`, `B_raw` and `intersection`; saved intersection equals independently computed `A&B` and the recorded raw-overlap count. Final overlap is zero for all 14,706 pairs.

Result: N/C, masks and critical bottom layer closed.

## 4. The 391-row manual layer and anti-bulk/anti-template audit

Exact row counts and sets:

| Ledger | Required/actual | Exact machine or semantic set |
|---|---:|---|
| object | 172 | all object IDs |
| critical | 102 | all critical pair IDs |
| preliminary | 64 | all preliminary failure IDs |
| peer | 13 | all low-profile peer IDs |
| role | 35 | all unique panel/role/script groups |
| view | 4 | all four required views |
| hard | 1 | `HARD-LOWPROFILE-TXT-098` |
| **Total** | **391** | **exact** |

Independent text/statistical checks found:

- decision IDs: 391/391 unique;
- blank notes: 0;
- exact duplicate notes: 0;
- duplicates after normalizing IDs and all numeric literals: 0;
- forbidden placeholder/default/bulk tokens in accepted manual ledgers: 0;
- notes inspected below name concrete glyphs, relations, bboxes, H/area, geometry or visual semantics; no fixed sentence was substituted for object review;
- all seven manual CSV mtimes precede `consumer_validation.json`, in the order object → critical → preliminary → peer → role → view → hard → consumer;
- static search found no loop/template/default/global-boolean generator for the seven manual ledgers. The consumer is read-only with respect to them.

Preliminary closure was also independently checked. The copied preliminary failure set is 64; the accepted CSV and JSON contain the same 64 IDs and decisions (`63 PASS`, `1 FAIL`). Every accepted row has numeric `manual_missing_px=0` and `manual_foreign_px=0`; `PENDING` count is zero. Pair rows contain A/B before-and-after, intersection before-and-after, and overlay before-and-after references. Peer rows contain target before/after, peer-after and contact overlay references. Every referenced asset exists.

Peer/role consistency is not flattened to all-PASS: peer decisions are 12 PASS/pure and one FAIL/impure (`TXT-098`); role decisions include the corresponding caption-low-profile FAIL. There is no accepted PASS/PENDING conflict.

Result: no evidence of fictitious, bulk, templated or script-manufactured R7A manual decisions.

## 5. Independent visual sampling and counterexample search

This section records only artifacts actually opened by this root audit. The audit actively looked for mask contamination, missing strokes, clipping, note/image mismatch and misuse of the intended-design whitelist.

### 5.1 Object ledger — 26 deterministic review IDs; all 13 sheets opened

All 10 glyph and 3 graphic contact sheets were opened. Each contact cell provides original, red target overlay and mask-only evidence. The deterministic recorded sample was:

- glyphs (16): `TXT-001`, `TXT-004`, `TXT-007`, `TXT-009`, `TXT-010`, `TXT-019`, `TXT-024`, `TXT-034`, `TXT-048`, `TXT-055`, `TXT-069`, `TXT-072`, `TXT-080`, `TXT-098`, `TXT-105`, `TXT-112`;
- explicit drawings (8): `G-TOP-X-AXIS`, `G-TOP-Y-ARROWHEAD`, `G-TOP-DATA-CURVE`, `G-TOP-MARKER-T01`, `G-BOTTOM-X-AXIS`, `G-BOTTOM-DATA-CURVE`, `G-BOTTOM-MARKER-T06`, `G-BOTTOM-TARGET-LINE`;
- patterns (2): `G-TOP-BURNIN-HATCH`, `G-BOTTOM-BURNIN-HATCH`.

Observed: sampled CJK radicals/enclosures, Latin/math contours and low-profile punctuation were complete; target overlays did not claim neighbouring digits, punctuation, axes or curve pixels. The target `TXT-098` itself has two complete components and a pure 28×7 native mask; its peer calibration is a separate gate. Axis/curve masks follow reader-visible paint ownership around markers/ticks. Both hatch masks end at the orange burn-in separator and contain the expected curve/marker cutouts. No sampled object note contradicted its sheet/cell or mask.

### 5.2 Critical ledger — 24 cells opened; 18 deterministic IDs recorded

Navigation sheets 01, 02 and 08 were opened (24 cells). The deterministic recorded set is:

`PAIR-004-008`, `PAIR-005-008`, `PAIR-005-009`, `PAIR-005-010`, `PAIR-006-010`, `PAIR-006-011`, `PAIR-006-012`, `PAIR-007-121`, `PAIR-007-122`, `PAIR-008-121`, `PAIR-008-122`, `PAIR-009-121`, `PAIR-009-122`, `PAIR-010-121`, `PAIR-010-122`, `PAIR-011-121`, `PAIR-117-125`, `PAIR-118-125`.

For representative clear, formula-design and both marker-axis cases I additionally opened original 1×, overlay 1×, nearest 8× and raw A/B masks. The first seven clear text pairs show the stated 4 px or greater separation with no foreground mixing. Formula members are visibly distinct and have ample clearance. At the special start point, `PAIR-117-125` and `PAIR-118-125` do show raw magenta contact, so they were not accepted merely because the ledger says “design”: the full panel, 1×/8× overlays and raw masks show the source-declared first circular marker centred at the y-axis/domain start, immediately below the arrowhead. Final-visible ownership preserves the disk, shaft and pointed arrowhead with zero final shared pixel. This is a line-marker/assembled-axis relationship, not an accidental collision. No whitelist counterexample was found in the opened cells.

### 5.3 Preliminary ledger — 16 deterministic IDs opened

`preliminary_navigation_01.png` and `preliminary_navigation_02.png` were opened, covering:

`PEER-TXT-019`, `PEER-TXT-072`, `PEER-TXT-098`, `PEER-TXT-105`, `PAIR-004-119`, `PAIR-005-006`, `PAIR-005-119`, `PAIR-006-119`, `PAIR-007-119`, `PAIR-008-119`, `PAIR-009-119`, `PAIR-010-119`, `PAIR-011-119`, `PAIR-012-119`, `PAIR-013-014`, `PAIR-013-119`.

The first sheet includes the sole `REMAINS` row (`PEER-TXT-098`); the other 15 recorded cells are `RESOLVED`. Before/after evidence visibly removes the preliminary colour-family overclaims without deleting the target glyph/curve. The semicolon target remains complete, but its mandatory peer fails calibration. Sheet/cell assignments and object/relation-specific notes matched the images.

### 5.4 Peer ledger — all 13 opened

All required peer contacts were opened:

`TXT-009`, `TXT-010`, `TXT-011`, `TXT-019`, `TXT-020`, `TXT-021`, `TXT-039`, `TXT-042`, `TXT-046`, `TXT-080`, `TXT-105`, full-book `TXT-072`, and full-book `TXT-098`.

The 11 same-page contacts show complete comma/ellipsis/period/fullwidth-comma peer shapes with clean mask-only panels. Full-book `TXT-072` is a single pure dot matching target H7/area41. Full-book `TXT-098` visibly contains a disconnected vertical foreign component at the far right; it is correctly marked `peer_pure=NO` and FAIL. Thus the opened evidence supports 12 peer passes and the one hard failure; no additional low-profile hard failure or PASS/PENDING contradiction was found.

### 5.5 Role ledger — 18 deterministic groups correlated to opened evidence

The sampled role decisions were `R7A-ROLE-001`, `003`, `004`, `005`, `006`, `007`, `008`, `009`, `011`, `014`, `016`, `017`, `019`, `024`, `027`, `031`, `032`, `035`. They span TOP/BOTTOM/CAPTION, annotation, axis label, natural script, axis tick, hatch, data curve, arrow, marker, panel title, reference line, low-profile tick, caption, math rule and numeric tick.

The opened full/crop/grayscale views and object sheets support their reported hierarchy and geometry: 10.8 pt titles/labels are prominent without crowding; natural scripts remain naturally smaller; burn-in hatches are subordinate; top circles and bottom squares remain distinguishable; dashed target and separators retain their styles. `R7A-ROLE-019` is correctly FAIL rather than silently promoted to PASS because it contains `TXT-098`.

### 5.6 Four required views — all opened

- `FULL_PAGE_200DPI`: Fig. 32.8 fits between surrounding text and Fig. 32.9 with no page collision or clipping.
- `FIGURE_CROP_300DPI`: both panels and the entire caption are present; axes, labels and endpoints have whitespace.
- `STANDALONE_300DPI`: separately reopened at native detail; it is byte-identical to the crop. A transient blank viewer preview was disproved by the independent byte identity and successful reopen, not counted as evidence loss.
- `GRAYSCALE_300DPI`: hatch, solid trajectories, dashed separator/target, circle/square marker distinction and text remain legible.

### 5.7 Visual counterexample result

Within the concrete artifacts above, no mask pollution, unaccounted missing stroke, clipping, object-specific note mismatch or intended-design whitelist abuse was found. One real adverse example was found and retained rather than waived: the `TXT-098` peer is impure and remains below the fixed area threshold even after correct foreign-component subtraction.

## 6. Independent reconstruction of `HARD-LOWPROFILE-TXT-098`

### 6.1 Frozen peer choice

`FULLBOOK_PEER_SELECTION_POLICY.json` predates the candidate CSV/JSON and peer assets. The fixed rules require the same Unicode codepoint, PDF font name/weight, RGB colour and size within 0.25 pt; ranking uses page/rawdict order and explicitly excludes H, area, mask cleanliness and PASS/FAIL. No fallback is allowed after seeing pixels.

I directly rescanned rawdict characters on all 814 frozen R101 pages and independently rebuilt both candidate sets from the fixed codepoint/font/RGB/size rules. The rebuilt ordered tuples `(page, rawdict sequence, block, line, span, char)` exactly equal the saved CSV in both set and deterministic order, with no scan-only or CSV-only row:

- `TXT-072`: independently rebuilt 99 = saved 99, unique deterministic ranks 1…99, same-page alternatives 0; selected rank 1 is physical page 17/rawdict 251.
- `TXT-098`: independently rebuilt 64 = saved 64, unique deterministic ranks 1…64, same-page alternatives 0; selected rank 1 is physical page 187/rawdict 345.
- The selected `TXT-098` peer exactly matches codepoint U+FF1B, font `NotoSerifSC-ExtraLight`, RGB `[31,35,40]` and size 9.9626398 pt.

### 6.2 Pixel reconstruction

At the fixed native threshold (20/255), I independently decoded and counted the saved masks using 8-connectivity:

| Mask | Shape | Components (area; exclusive bbox x0,y0,x1,y1) | H | Area |
|---|---:|---|---:|---:|
| target final | 28×7 | 37 `(0,17,7,28)`; 19 `(2,0,7,5)` | 28 | 56 |
| peer raw | 45×43 | 40 `(5,27,12,38)`; 21 `(7,10,12,15)`; 11 `(42,14,43,25)` | 28 | 72 |

The third peer component is exactly 1×11 and is separated from the two semicolon components by about 30 blank columns. R101 page-187 rawdict provides an independent semantic separation basis: selected U+FF1B occupies PDF bbox x=431.185…441.148 pt; the next span begins with Latin `C` (`STIXTwoText-Regular`) at x=440.684…447.225 pt. The peer crop therefore catches a raster fragment of the adjacent `C` at its far-right edge. It is not a semicolon stroke. Because the component is disconnected and traceable to the next rawdict character, subtracting it does not erase target ink and is not a bbox/context/paint-order excuse.

The resulting clean peer has the two intact semicolon components, `40+21=61` pixels and H=28. Therefore:

- H ratio = `28/28 = 1.0`, within `[0.92,1.08]`;
- clean area ratio = `56/61 = 0.9180327868852459`, which is strictly below `0.92` by `0.0019672131147541`;
- unclean raw ratio = `56/72 = 0.7777777777777778`, also failing;
- the raw peer is independently impure, and cleaning cannot rescue the fixed metric.

The proximity to the threshold is not a basis to widen it. Candidate, threshold, coordinate system and interval remain frozen. `TXT-072` independently recomputes to H7/area41 for both target and peer. All other 11 same-page low-profile peers recompute to their ledgers and fall within the interval; no second hard failure was found.

Result: `HARD-LOWPROFILE-TXT-098` is genuine and reproducible.

## 7. Payload manifest, parse/open audit and terminal seal

Independent whole-package verification found:

- `PAYLOAD_MANIFEST.json`: 1,917 entries, 22,291,728 total bytes, SHA-256 `03A56E9146F089FC5DD17E800083EF48CE7D774D085871B5074419284E4CBCA4`;
- actual payload excluding manifest/`WRITE_STOPPED`/`SEAL.json`: exact same 1,917 paths, with zero path/size/SHA/mtime mismatch;
- payload types opened/parsed: 1,870 PNG, 19 JSON, 20 CSV, 4 MD and 4 PY; failures = 0;
- actual ordinary files including terminal controls: 1,920;
- `.pyc` files = 0; `__pycache__` directories = 0;
- independent NTFS stream enumeration over all 1,920 files: ADS = 0, errors = 0.

Strict mtime ordering (ns) is:

`max payload 1787606231116641700 < manifest 1787606271800257000 < WRITE_STOPPED 1787606292409970400 < SEAL 1787606368166913000`.

`SEAL.json` is the unique latest ordinary file; files written after it = 0. A final post-audit read-only enumeration still found 1,920 ordinary files, no pyc/cache, and `SEAL.json` as latest.

`RESULT.json`, `R7A_SA1_AUDIT_REPORT.md`, `after_visual_acceptance.md`, `consumer_validation.json`, manifest controls, `WRITE_STOPPED` and `SEAL.json` consistently retain `FAIL_TO_SA2_AWAIT_ROOT`, identify one hard failure, report no SA3 start, and do not claim central `FAIL_TO_SA2` or `A_LOCAL_PASS` inside the sealed package.

Result: manifest, parse/open, ADS and terminal-seal closure passed.

## Final disposition

The resealed R7A package is mechanically coherent, its 391-row manual layer is not bulk/template-generated, the required root visual samples do not expose a contradictory counterexample, and the sole hard failure survives independent metadata, context and pixel reconstruction. Root therefore accepts the evidence as a valid failure package:

`ROOT_ACCEPT_R7A_FAIL_TO_SA2`

SA2 must repair the `TXT-098` low-profile peer calibration failure under the unchanged protocol and then regenerate the required evidence chain. SA3 remains prohibited until a later SA1 pass.
