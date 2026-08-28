# FIG-P582-01 — R109 strict R4 fresh-isolated SA3 report

**Handoff ID:** `A-R109-P582-SA3-FRESH-ISOLATED-20260826`  
**SA3 result:** **FAIL**  
**Acceptance consequence:** This R109 figure candidate is not eligible for `A_LOCAL_PASS`.

## Scope and immutable inputs

- Official R109 PDF: `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\build\strict_current_r109_fullbook\main_full.pdf`
  - 817 physical pages
  - 4,967,054 bytes
  - SHA256 `936162A637DCE09EE02B3F83CB1C21A61A87EFBB9A7C8DDE2FB11A326EB552A9`
  - Last write UTC `2026-08-26T14:08:23.1327162Z`
- Sole current drawing source: `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\绘图源码\第05册_采样方法主题模型与图排序\V5-C02\fig_v5_c02_running_mean.tex`
  - 2,627 bytes
  - SHA256 `4AB4E8D14252B20576F05BD1D5CB54BCB28F162B9E33EF439BD3ED6E01DBC65C`
  - Last write UTC `2026-08-26T13:52:23.3858559Z`
- PDF and source remained read-only. No TeX engine, LaTeX build, source edit, commit, second UID/role, central-state write, or inventory migration occurred.
- No old P582 evidence, role, report, handoff, state, inventory, chat conclusion, or Git history was read.

## Independent location and semantics

- Unique figure location: physical page **632**, printed page **619**, Figure **31.7**.
- Current sample sequence: `U=(0.8,0.1,0.7,0.4)`.
- Independent squares: `(0.64,0.01,0.49,0.16)`.
- Independent cumulative sums: `(0.64,0.65,1.14,1.30)`.
- Independent running means: `(0.64,0.325,0.38,0.325)`.
- Trend: down, up, down.
- Reference: `E[U^2]=1/3` for uniform `U` on `[0,1]`.
- Plotted sample coordinates, running-mean vertices, visible values, annotations, formula `h(U_i)=U_i^2`, dashed reference, and current caption all match. Semantic result: **PASS**.
- The active-goal card text describing importance-sampling support is stale/misassigned for this figure and was rejected as semantic authority.

## Frozen denominator and machine gates

- Visible denominator: **156 objects** = 139 text glyphs + 17 independently replayed drawing/path objects.
- Complete unordered-pair universe: **12,090** = `156×155/2`; all pairs enumerated exactly once.
- Native 300 dpi page: 2481×3508 pixels.
- Object masks: 156 expected, 156 present, 156 non-empty and openable.
- Formula math-rule paths: 0; the visible formula is glyph-based.
- Source effective-point-size gate: PASS.
- R168-aware glyph pixel gate: PASS.
- Complete 1× glyph sheets opened: 6/6.
- Complete nearest-neighbor 8× glyph sheets opened: 12/12.
- Graphic 1× sheet opened: 1/1.
- Full graphic 8× native-mask coverage: all 33 authoritative tile sheets opened across G001–G017; coverage gate PASS.
- Denominator CSV SHA256: `A7C5E5F500D9C70FBBD9D92D6C0F735B20C23E980C20DFCE2FDF6E41530E5F57`.
- All-pairs CSV SHA256: `3D2856828DB76968C3E458DB0134F9A92C9F24B6534857D39E1C7DC9EBC915F3`.
- Freeze time: `2026-08-26T15:41:38.276073+00:00`.

## Genuine manual adjudication

Manual observation completed at `2026-08-26T15:48:00Z`, before reviewer-ledger creation. The external auditor independently confirmed that no manual observation timestamp is in the future and no manual file mtime precedes its observations.

- Glyph ledger: 139/139 individual rows; every isolated mask matches its target, is complete, and contains no foreign strokes.
- Graphic ledger: 17/17 rows; every replayed path is complete and pure at 1× and authoritative tiled 8×.
- Critical-pair ledger: 6/6 rows.
- View ledger: full page, 300 dpi crop, standalone, and grayscale all opened.
- Math-rule ledger: one explicit N/A record for zero visible formula-rule paths.
- Overall clipping: 0. Mask contamination: 0. Missing/tofu/wrong-codepoint errors: 0.
- Overall balance, grayscale behavior, and page integration are acceptable apart from the localized collision below.

### Binding hard failure

`P05555`: T042 (`↓` in “↓再下降”) versus T062 (terminal `0` in `.380`).

- Native 300 dpi raw-mask intersection: **14 pixels**.
- Raw-mask clearance: **0 px**.
- Vector-bbox clearance: **0 px**.
- The 1× context and nearest-neighbor 8× ROI visibly confirm that the arrow tip intrudes into the top of the digit `0`.
- Classification: `TRUE_ILLEGAL_OVERLAP`.
- R168 consequence: hard FAIL because this is real glyph contact, not a microscopic stylistic or taxonomy difference.

### R168 advisory-only findings

- `P04848` T036/T054: 0 intersection pixels and 13.1421 px raw clearance; bbox-only contact, visibly separated.
- `P05554` T042/T061: 0 intersection pixels and 6.6158 px raw clearance; close but visibly separated.
- T032 equals sign: 12 px low-profile glyph, readable and semantically correct; advisory only.
- Microscopic font/pixel/taxonomy differences and single-pixel white-gap questions were not promoted to hard failures.

## Superseded preliminary artifacts

`_superseded_preliminary_color_bbox_maskrun` is retained recoverably inside the evidence root but is explicitly non-authoritative. That pre-manual run used color-plus-bbox graphic masks and produced false intersections; none of its counts, decisions, or hashes contributes to this result. The final authoritative graphics masks replay each PDF drawing/path independently.

The two oversized monolithic graphic 8× navigation sheets were not viewable because their canvases approached 980 megapixels. They are explicitly non-authoritative; the 33 opened 8× tiles provide complete machine-proved native-mask coverage instead.

## Seal and external audit

Sealed evidence root:

`D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P582-01\STRICT_R4_SA3_FRESH_ISOLATED_R109_20260826`

- Seal executed exactly once at `2026-08-26T15:56:09.3063027Z`.
- Payload rows: 563; final actual files: 568.
- Payload-manifest SHA256: `EE07986A7385A5C49661BACFB74E4CCF08E816D8F4AF8F55DA913BAD986C50A3`.
- Seal-manifest SHA256: `050046F83982C79134C1790CB1B1603C45F076E5BF753DB275C0395CD6D9AF38`.
- `WRITE_STOPPED`: exactly one; strict latest file mtime `2026-08-26T15:56:12.7712928Z`.
- Max non-marker mtime: `2026-08-26T15:56:11.6129397Z` (`08_seal/MANIFEST_SEAL.sha256`).

Root-external read-only auditor at `2026-08-26T15:57:42.9712799Z`: **PASS**.

- Exact file set: true.
- Manifest hashes, file hashes, sizes, and payload mtimes: all exact.
- All 568 files read-only: true.
- ADS: 0.
- `.pyc`: 0.
- `__pycache__`: 0.
- Reparse points: 0.
- Post-marker files: 0.
- Manual timestamp errors: 0.
- Numeric manifest-size comparison was independently normalized to `UInt64`; no type-comparison false alarm occurred.
- Auditor root writes: 0.

An initial auditor command had a PowerShell interpolation parse error and terminated before reading or writing the root. The corrected root-external read-only auditor produced the PASS above; the sealed root was not modified.

## Disposition

Final SA3 decision: **FAIL**. Keep R109 and the sealed evidence immutable. Do not migrate central state or launch another UID/role from this handoff. A future corrected candidate should reposition the second downward annotation or the `.380` label to create positive visible separation, rebuild under the authorized main flow, and undergo a new independent acceptance cycle.
