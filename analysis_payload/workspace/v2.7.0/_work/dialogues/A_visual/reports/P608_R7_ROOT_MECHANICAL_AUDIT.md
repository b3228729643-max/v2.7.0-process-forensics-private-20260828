# FIG-P608-01 R7 fresh R101 SA1 root mechanical audit

- Audit target: `STRICT_R7_SA1_FRESH_R101_20260825`
- Figure: `FIG-P608-01`
- Handoff: `A-R101-P608-SA1-FRESH-20260825`
- SA1 route: `gpt-5.6-sol/xhigh`
- Audit date: 2026-08-25 (Asia/Shanghai)
- Scope: only the fresh R101 evidence root named above. No older P608 evidence, old root report, old handoff, or prior conclusion was used as evidence or comparison baseline.

## Root verdict

`ROOT_REJECTED`

The PDF identity, N/C arithmetic, pair packets, exact-metadata peer calculation, payload manifest, parsing, and result routing are mechanically reproducible. The package nevertheless cannot receive `ROOT_ACCEPT_FAIL_TO_SA2`, because the mandatory human-ledger provenance is demonstrably bulk-generated, every preliminary-v1 row still carries unresolved manual missing/foreign fields, the source identity/read chain is not sealed, and peer-purity status conflicts across accepted artifacts. The valid `PEER-TXT-098` hard failure remains a true SA1 quality failure, but a correct hard-failure route does not cure evidence-mechanics failures.

## Governing basis

This audit read the complete current goal, `STRICT-PIXEL-TYPOGRAPHY-PROTOCOL.md`, and `STRICT_FIGURE_EVIDENCE_SCHEMA.md` before inspecting the fresh evidence. The decisive schema requirements are that every contact cell be actually opened and receive an individual reviewer row; a global/bulk boolean may not turn all rows into PASS; pending, missing, duplicated, polluted, or unclosed contour evidence is FAIL; source-declared typography must be read from the current source; and SA1 FAIL may route to SA2 but may not start SA3 or be counted as `A_LOCAL_PASS`.

## Blocking gaps

### R-01 - All seven "manual" ledgers were batch-serialized by one program

The seven CSVs have the expected superficial cardinalities and key coverage:

| Ledger | Rows | Key coverage | Nonblank/unique notes |
|---|---:|---|---|
| object | 172 | exact N=172 set | yes |
| critical pair | 102 | exact critical set | yes |
| preliminary | 64 | exact preliminary set | yes |
| low-profile peer | 13 | exact peer set | yes |
| panel/role/script | 35 | 35 unique role rows | yes |
| view | 4 | four expected views | yes |
| hard failure | 1 | `PEER-TXT-098` | yes |

Those counts do not establish manual review. `record_manual_reviews.py` reads a global event log and programmatically loops over the inventories to write every ledger in one run. In particular, it assigns:

- all 172 object rows: `ORIGINAL_MATCH=True`, `OVERLAY_COMPLETE=True`, `MASK_ONLY_PURE=True`, missing/foreign pixels `0`, crop/ownership `True`, decision `PASS`;
- all 102 critical rows: A/B complete and intersection match `True`, with the decision derived from machine fields;
- all 64 preliminary rows: before/after complete/pure `True` and missing/foreign pixels `0`;
- all 13 peer rows: target/peer complete and peer pure `True`, with PASS/FAIL derived from the metric;
- all 35 role rows: fixed crowding `NONE` and visual harmony `PASS_VISUALLY` except the known metric-driven failure;
- all four view rows: fixed opened/legibility/crowding values and hardcoded decisions/notes;
- the one hard-failure row: a hardcoded record.

The notes are unique only because IDs, cells, metrics, or role names are interpolated into templates. `MANUAL_REVIEW_EVENT_LOG.json` records only lists of sheet filenames and one global observation; it has no human-entered per-cell decisions. The terminal checker checks only row count, unique `DECISION_ID`, and nonempty `DECISION`/`NOTE`; it never tests independent per-row entry provenance or rejects bulk booleans. This directly violates the schema prohibition on using a global/bulk boolean to mark all glyphs or views PASS. Therefore manual completeness, purity, visual harmony, and individual critical-pair adjudication are not mechanically established even though the CSVs look complete.

### R-02 - Preliminary manual closure remains pending in both primary data forms

The frozen preliminary identity is real:

- fixed command: `python -X utf8 preliminary_algorithm_v1_replay.py`;
- replay script SHA-256: `3CEDC69DF0C5139AC54BF76DEFC00AD75B0CBA0D6A7A3139AEF3589BFA5C1428`;
- object inventory SHA-256: `C4FC308890D5F4638835793D660B52AE574E563C36DC4E6486CD1D59ED65AB6F`;
- PDF SHA-256: `0870FF226DC383875C4A1B6EABB06AAB942317DA294D90D2864B3030D46DF1A1`;
- independent in-memory replay result: 64 rows = 63 `RESOLVED` + 1 `REMAINS`.

However, all 64 rows in both `preliminary_64_failures.csv` and `preliminary_64_failures.json` still contain:

- `MISSING_STROKE_PX_MANUAL = PENDING_LEDGER` (64/64);
- `FOREIGN_PIXEL_PX_MANUAL = PENDING_LEDGER` (64/64).

The later `manual_preliminary_ledger.csv` changes both fields to zero only through the bulk generator described in R-01, so it cannot serve as an actual per-ID manual closure. The SA1 review statement that each of the 64 rows has a completed missing/foreign-pixel check is therefore false at the primary-row level.

There are 488 existing and unique preliminary image assets: 60 pair rows x 8 images plus 4 peer rows x 2 images. Every row has a contamination source, pixel counts where applicable, bbox/paint-order basis, and an unchanged-threshold statement. The JSON links all 488 assets. The CSV writer derives its header from the first peer row and silently drops the B/intersection/overlay reference fields from pair rows; consequently the CSV retains only the A before/after references while JSON contains the complete packet. This does not change the independently replayed 64=63+1 result, but it is an additional cross-format traceability defect.

### R-03 - Source identity and source-reading provenance are not sealed

The evidence freezes the PDF identity but not the source identity. `candidate_identity.json` contains no source path/bytes/SHA tuple, and no evidence artifact records an expected source SHA-256. `audit_pipeline.py` defines a `SOURCE` path once, but never dereferences, opens, hashes, or parses it. The source-line and declared/effective point-size rows are produced from hardcoded line/value knowledge, not from a mechanically demonstrated source read.

Current read-only observation of the named source at audit time was:

- path: `fig_v5_c03_trace_running_mean.tex` under the declared V5-C03 source directory;
- bytes: 3,429;
- SHA-256: `78C30F4A934F63E0EF1BBACF400A24F22477D38589F99503AE468F7024A35C05`;
- Git status for that exact path: clean.

Those current facts cannot repair the missing sealed expected identity. There is no trusted package value against which to compare them, and the package cannot prove that the source inspected for typography is the source that produced the frozen PDF.

### R-04 - Manual peer-purity status conflicts across accepted artifacts

For the two full-book targets, `fullbook_peer_calibration.csv` says `MASK_PURITY_MANUAL=PASS_LEDGER_CONFIRMED`, while the corresponding rows in `low_profile_peer_calibration.csv` still say `MASK_PURITY_MANUAL=PENDING_LEDGER`. The frozen full-book calibration generator itself emits `PENDING_LEDGER`; no package script explains or validates the later `PASS_LEDGER_CONFIRMED` mutation. The only purported confirming ledger is the bulk-generated peer ledger from R-01. Thus target/peer mask purity does not have one consistent, independently entered manual status.

### R-05 - Audit-process cache incident means the current directory metadata is no longer pristine

At the initial seal checkpoint, the evidence root had exactly 1,928 ordinary files and no ordinary file with mtime later than `WRITE_SEAL.json`. During this root audit, an attempted read-only Python import for deterministic replay inadvertently created `__pycache__/preliminary_algorithm_v1_replay.cpython-311.pyc`. The file and its otherwise empty directory were identified as audit-created and immediately removed; no original payload, manifest, terminal, or seal file was modified. The final ordinary-file set is again 1,928, the manifest SHA is unchanged, and zero ordinary files have mtime later than the seal. Nevertheless, the evidence-root directory mtime became `2026-08-24T20:32:47.4016476Z`, later than the seal. Therefore a literal directory-level claim of "no write of any kind after seal" is no longer certifiable on the current root. This incident is auditor-induced rather than a producer-package defect, but a fresh immutable copy/reseal is required before any later audit may treat the directory itself as pristine.

## Mechanically closed checks

### Candidate identity, page mapping, and current source observation

- R101 PDF: 814 pages, 4,947,496 bytes, SHA-256 `0870FF226DC383875C4A1B6EABB06AAB942317DA294D90D2864B3030D46DF1A1`.
- Target: physical page 659 (one-based), printed page 646, Figure 32.8; current page rectangle is A4-like `(0,0,595.2760009765625,841.8900146484375)` pt.
- Full page: 1654x2339 at 200 dpi and 2481x3508 at 300 dpi.
- Audit crop: `[70.08,220.8,515.04,450.0]` pt -> integer `(292,920,2146,1875)` -> 1854x955 px.
- The current source file was read only and Git-clean, but R-03 prevents sealed source-provenance acceptance.

### Complete denominator and masks

- Rawdict: 837 page characters = 120 in domain + 717 outside; domain 120 = 112 visible glyphs + 8 whitespace; visible nonspace 778 = 112 in domain + 666 outside.
- All 112 glyph inventory rows independently matched current PDF raw sequence, character, font, size, color, and bbox.
- Current PDF `get_drawings()` count: 89. Exact partition: 6 preceding-equation + 58 target explicit drawings + 2 page-corner + 2 following-prose rules + 21 following-figure = 89.
- The two hatch layers are visible but not emitted by `get_drawings()` and are counted exactly once as `PATTERN`, not double-counted with paths.
- N=172 = 112 `GLYPH` + 58 explicit PDF drawing objects + 2 hatch-pattern objects.
- Object IDs: 172 unique. Safe filenames: 172 unique. ID/filename map: exact bijection.
- Four mask trees (`pre_native`, `pre_8x_nearest`, `final_native`, `final_8x_nearest`) each contain 172 masks. All are nonempty; every native dimension and recorded pixel count matches; `raw - final = occluded`; every 8x mask is the exact nearest-neighbor repeat of its native mask. Seven objects have nonzero occluded pixels.
- These checks close machine nonemptiness, geometry, ownership, and 8x derivation. Human completeness/purity remains rejected under R-01/R-04.

### All unordered pairs and critical packets

- Expected C=`172 choose 2`=14,706; file rows=14,706; unique unordered object pairs=14,706; missing=0; extra=0.
- Pair decisions: 14,176 `CLEAR`, 487 `INTENDED_DESIGN_RELATION`, 43 `INTENDED_DESIGN_OVERLAP`.
- Unwhitelisted raw-overlap pairs=0; final-visible nonzero intersections=0; clip failures=0; clearance failures=0.
- Critical predicate independently reproduces exactly 102 pairs. Critical IDs are unique and match the saved set.
- Critical evidence references: 102 x 6 = 612; all paths are unique and exist. Independent image decoding verified actual A AND B equals the saved intersection and recorded pixel count for all 102.
- Critical mechanical minima: text/text 4 px, text/graphic 14 px, graphic/graphic nonwhitelist 5 px, same-parent internal 2.1622776601683795 px.
- The apparent manual split is 7 `PASS_CLEARANCE` + 95 `PASS_INTENDED_DESIGN_RELATION`; its human provenance is not accepted under R-01.

### Views and contact material

- Required native views exist with the recorded dimensions: full-page 200 dpi, figure crop 300 dpi, standalone 300 dpi, and grayscale 300 dpi.
- Object navigation comprises 10 glyph contact sheets and 3 graphic contact sheets; critical navigation comprises 13 sheets; preliminary navigation comprises 8 sheets.
- All 1,870 PNG files were independently decoded. Representative native glyph, exact-peer, and critical-pair sheets were also visually opened during this root audit.
- This confirms the material exists and is readable. It does not convert the script-generated ledger rows into actual per-row human review.

### Preliminary-v1 deterministic result

- Frozen command/script/inventory/PDF identities match their recorded values.
- A write-suppressed in-memory execution reproduced exactly 64 failures: 63 resolved and only `PEER-TXT-098` remaining.
- 60 pair failures and 4 peer failures are represented in JSON with 488 unique existing before/after assets.
- Contamination-source, contamination-pixel, bbox/paint-order, and unchanged 20/255/unchanged hard-gate explanations are nonblank for all rows.
- The replay result is accepted as a machine reconstruction; manual disappearance/purity is rejected under R-01/R-02.

### Frozen full-book exact-metadata peer rule

- Policy ID: `LP-PEER-R101-EXACTMETA-V1`; its file predates candidate enumeration/calibration and explicitly forbids ranking by H/area or fallback substitution.
- Independent full-814-page scan reproduced the exact candidate sets: `TXT-072`=99 and `TXT-098`=64.
- Deterministic peers: `TXT-072` -> physical page 17/rawdict sequence 251; `TXT-098` -> physical page 187/rawdict sequence 345.
- Metadata equality is exact for codepoint, font/weight, RGB color, and effective size tolerance; no different glyph, size, font, or context-polluted mask was substituted.
- Independent native-mask recomputation at unchanged 20/255:
  - `TXT-072`: H=7/7, area=41/41, ratios 1.0/1.0 -> PASS.
  - `TXT-098`: H=28/28, area=56/72, ratios 1.0/0.7777777777777778 -> FAIL because area is outside `[0.92,1.08]`.
- Saved target/peer masks equal the independently recomputed masks. The unique numerical hard failure `PEER-TXT-098` is valid. Manual purity status remains unaccepted under R-01/R-04.

### Manifest, parsing, ADS, and original seal ordering

- Manifest entries: 1,924; actual payload files excluding the four manifest/parse/stop/seal controls: 1,924.
- Every payload path, byte length, SHA-256, and mtime was independently recomputed: 0 mismatches.
- Manifest self SHA-256: `9359C7DEA3F78F7E018E7709F4A8F33409E62C515F54FF7E96BCDDF330E5A863`.
- Original ordinary-file count: 1,928; total bytes: 17,665,194.
- Independent parse/decode of all 1,928 files: 1,870 PNG, 22 JSON, 22 CSV (16,161 data rows), 7 Markdown, 6 Python, and 1 text; errors=0.
- Independent NTFS stream scan: 1,928 files, alternate data streams=0, scan errors=0.
- Original file-level ordering in UTC/ticks:
  - latest payload (`ads_scan.json`): `2026-08-24T20:08:14.7783033Z`;
  - manifest: `20:08:36.9009136Z`;
  - parse check: `20:08:39.0288855Z`;
  - terminal stop: `20:08:39.2109557Z`;
  - write seal: `20:08:39.2365793Z`.
- Thus the received ordinary-file set had strict payload < manifest < parse < stop < seal ordering and zero ordinary files later than the seal. R-05 records the later audit-induced directory-metadata exception.

### Terminal/status consistency

The following all agree on `FAIL_TO_SA2` with the sole hard failure `PEER-TXT-098`: `RESULT.txt`, `SA1_REVIEW.md`, `hard_failures.json`, `denominator_and_pair_summary.json`, `machine_preseal_check.json`, `manifest_parse_check.json`, `TERMINAL_STOP.json`, and `WRITE_SEAL.json`. The machine preseal report contains 39/39 recorded PASS checks, but its manual-ledger checks are insufficient as described in R-01/R-02/R-04.

The route is consistently `gpt-5.6-sol/xhigh`, handoff `A-R101-P608-SA1-FRESH-20260825`. `MODEL_ROUTE.md` and `SA1_REVIEW.md` explicitly state that SA3 was not started and this was not `A_LOCAL_PASS`.

## Required disposition

Do not treat this sealed package as root-accepted evidence and do not start SA3. The numerical `PEER-TXT-098` failure correctly demands SA2, but the package must first be replaced by a fresh evidence package that:

1. records genuinely individual human object/critical/preliminary/peer/role/view/hard decisions rather than generating them from machine rows or a global event list;
2. resolves every per-ID missing/foreign field in the primary preliminary CSV/JSON without `PENDING_LEDGER`, and preserves complete row-to-asset links consistently;
3. freezes source path, bytes, SHA-256, and read-only boundary, and mechanically parses the actual current source for declared/local/effective typography;
4. makes peer-purity status identical across full-book calibration, low-profile calibration, and the independent manual ledger;
5. is copied/rebuilt and sealed anew so that both ordinary-file and directory-level post-seal immutability can be audited from a pristine root.

The only permissible root conclusion for the current package is therefore `ROOT_REJECTED`, not `ROOT_ACCEPT_FAIL_TO_SA2`.
