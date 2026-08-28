# P654 R14F fresh isolated root audit

## 1. Audit identity and verdict

- Figure: `FIG-P654-01`
- Role: the sole fresh isolated R14F root acceptance instance
- Sealed root (read-only): `STRICT_R14F_SA2_R10_EVIDENCE_ONLY_CONTROL_RESEAL_20260825`
- Corrected frozen R10 root (read-only): `STRICT_R10_SA2_TAXONOMY_R100_DIRECT_BUILD_20260825`
- Static preflight (read-only): `STRICT_R14F_SA2_STATIC_PREFLIGHT_ONLY_20260825`
- Current figure source (read-only audit): `fig_v5_c05_dependency_graph.tex`
- TeX runs / source edits / commits / role dispatches: `0 / 0 / 0 / 0`
- Reads of prohibited R11--R14E root reports, handoffs, state, inventory, `CURRENT_STATE`, or `MODEL_ROUTE_LOG`: `0`

**Verdict: `ROOT_REJECT_R14F`.**

The payload, R10-copy identity, readability, hygiene, write-stop ordering, and retained R10 content all pass the independently repeated checks below. The rejection is nevertheless mandatory because the final dual payload manifests persist **five** fields, while this acceptance task explicitly requires CSV/JSON equality over **six fields**. Both manifest schemas are exactly:

`relative_path, bytes, sha256, mtime_utc_ticks, mtime_utc_7digit`

Thus observed field denominator is `5`, required denominator is `6`, and schema-width difference is `1` field in each final manifest. Equality over the five fields that actually exist is `0` differences, but that cannot prove the missing sixth field. The separate `R14_BASE_COPY_IDENTITY.csv/json` tables do have the required six fields (`source_relative_path`, `destination_relative_path`, plus four identity fields) and pass, but they cover 1052 base files rather than the required 1059-row final payload manifests. A base-identity pass cannot substitute for the final-manifest schema gate.

This verdict does not change central state: P654 remains SA2 and awaits mainline disposition. It is not `A_LOCAL_PASS`.

## 2. Count model and extension equations

Independent ordinary-file enumeration returned:

| class | observed | required | difference |
|---|---:|---:|---:|
| payload | 1059 | 1059 | 0 |
| manifest controls | 2 | 2 | 0 |
| `WRITE_STOPPED.json` control | 1 | 1 | 0 |
| all controls | 3 | 3 | 0 |
| ordinary files | 1062 | 1062 | 0 |

The required equations hold exactly: `1059 + 3 = 1062`, JSON `71 + 2 = 73`, and CSV `23 + 1 = 24`. Payload/control/ordinary extension sums are respectively `1059 / 3 / 1062`, with per-extension differences `0`:

- payload: aux 1, csv 23, fls 1, gz 24, idx 2, json 71, log 3, lua 21, luc 44, md 4, pdf 1, png 856, ps1 4, py 4;
- controls: csv 1, json 2;
- ordinary: aux 1, csv 24, fls 1, gz 24, idx 2, json 73, log 3, lua 21, luc 44, md 4, pdf 1, png 856, ps1 4, py 4.

## 3. Final manifests and payload filesystem

`PAYLOAD_MANIFEST.csv` and `PAYLOAD_MANIFEST.json` each contain 1059 rows. Duplicate relative paths are `0 / 0`; CSV-only paths `0`; JSON-only paths `0`. After normalizing only path separators and preserving case, all five persisted fields compare as follows:

| comparison | path/set | bytes | SHA-256 | NTFS ticks | 7-digit UTC display |
|---|---:|---:|---:|---:|---:|
| CSV vs JSON | 0 | 0 | 0 | 0 | 0 |
| CSV vs current 1059-file payload FS | 0 | 0 | 0 | 0 | 0 |

Payload filesystem duplicate paths are `0`. The seven additions over the 1052-file R10 base are exactly:

1. `R14_BASE_COPY_IDENTITY.csv`
2. `R14_BASE_COPY_IDENTITY.json`
3. `R14_COPY_PROVENANCE.json`
4. `R14_PRESEAL_VALIDATION.json`
5. `R14F_prepare.ps1`
6. `R14F_preseal_validator.ps1`
7. `R14F_seal.ps1`

Expected-versus-observed addition-set difference is `0`. Old R11--R14E control-layer path matches are `0`.

The decisive schema defect is not a data difference inside those five columns; it is the absent sixth column in both 1059-row final manifests. `R14F_seal.ps1` also independently confirms that `New-ManifestRows` emits exactly those five properties.

## 4. R10 base preservation

The corrected R10 root contains 1055 ordinary files: 1052 base files plus its three old sealing controls (`PAYLOAD_MANIFEST.csv`, `PAYLOAD_MANIFEST.json`, `WRITE_STOPPED.json`). Excluding those controls yields the required 1052-file base.

The R14F base-copy CSV and JSON each contain 1052 rows and six fields. Source-path duplicates, destination-path duplicates, source/destination path mismatches, and CSV/JSON path-set differences are all `0`. Their six-field CSV/JSON differences are all `0`.

Independent comparison of actual R10 base files to the tables and to the corresponding sealed R14F files produced:

| identity axis | R10 vs 1052-row tables | tables vs sealed base subset |
|---|---:|---:|
| relative path | 0 | 0 |
| bytes | 0 | 0 |
| SHA-256 | 0 | 0 |
| NTFS UTC ticks | 0 | 0 |
| 7-digit UTC display | 0 | 0 |

The sealed base subset has exactly the seven expected extra payload paths listed above and no other extra/missing path. This proves the retained R10 evidence bytes and timestamps rather than inheriting an old textual PASS.

## 5. Readability, ADS, cache hygiene, attributes, and terminal ordering

- JSON: `73 / 73` parsed; failures `0`.
- CSV: `24 / 24` parsed; failures `0`.
- PNG: `856 / 856` decoded with native dimensions and PNG format validation; failures `0` (observed dimensions ranged from `6x4` to `13112x2928`).
- PDF: `1 / 1` read by `pdfinfo`; failures `0`; one A4 page, `595.276 x 841.89 pt`.
- Non-default NTFS alternate data streams: `0` across 1062 files.
- `.pyc` files: `0`; `__pycache__` directories: `0`; `.pytest_cache/.mypy_cache/.ruff_cache/.cache` directories: `0`.
- The `texcache` subtree has 89 files in 7 directories, but all are members of the byte/tick-identical R10 base and manifest payload. They are deliberate build evidence, not audit-created cache pollution.
- Read-only ordinary files: `1062 / 1062`; non-read-only files: `0`.
- Mtime changes during repeated manifest, hash, parse, image, PDF, ADS, and content reads: `0`.

`WRITE_STOPPED.json` has filesystem mtime `2026-08-25T03:54:56.6686176Z` (`639232268966686176` ticks). The latest of the other 1061 files is `PAYLOAD_MANIFEST.json` at `2026-08-25T03:54:56.5858149Z` (`639232268965858149` ticks). Strict delta is `828027` ticks (`82.8027 ms`); files not strictly older than `WRITE_STOPPED.json` are `0 / 1061`. No post-seal write was observed.

## 6. Retained content gate: independent recomputation and counterexample searches

The current source is 3122 bytes with SHA-256 `EA4A19FF940A177D4D754C4277896A2F38B75C1E6F252D8A374F418B84E31E6D`, exactly matching `PREBUILD_IDENTITY.json`, both direct-invocation records, `R10_BUILD_IDENTITY_FREEZE.json`, and `RESULT.json`. The current chapter text at lines 78--95 describes the same count/Gamma-Beta to Dirichlet posterior/predictive chain and includes this exact figure source; no semantic contradiction was found.

Independent denominator and set reconstruction returned:

- objects `N=116`, unique IDs 116, safe-filename duplicates 0;
- object kinds: TEXT 80, FORMULA 15, NODE_BORDER 8, LINE_ARROW 7, ARROWHEAD 5, MATH_RULE 1; hence glyphs `95` and graphics `21`;
- pixel ledger `95`, exact glyph-ID set difference `0`;
- all unordered pairs `C=6670 = 116*115/2`, duplicate pair IDs/indexes/unordered keys `0/0/0`, unknown/self pairs `0`, missing expected pairs `0`;
- critical pairs `50`; exact manual-critical set difference `0`; 50 critical directories each contain the expected eight files;
- 464 expected object evidence files (raw, pre, 1x, 8x) present; missing `0`;
- machine object failures `0`, pixel failures `0`, heights below class threshold `0`, non-script effective point sizes below 9.5 pt `0`, missing-stroke/foreign-pixel/clip nonzero counts `0/0/0`;
- pair FAIL rows `0`, non-whitelisted final intersections above zero `0`, applicable clearance failures `0`; the 6019-row focused overlap report also has failures `0` while the complete 6670-row unordered ledger remains the denominator authority;
- typography mapping `95 -> 10` groups, duplicate mapped IDs `0`, pixel/taxonomy set difference `0`, group-member sum 95, duplicate members `0`, missing/extra members `0`, element/group failures `0/0`;
- source same-role groups `4 / 4 PASS`; source hierarchy groups `4 / 4 PASS`;
- target `FRM_TRIAL_005` (`n`): required height 22 px, observed height 22 px, ink area 297 px, decision PASS.

The manual denominator independently sums to `95 + 21 + 50 + 5 + 3 + 10 + 4 + 4 = 192`. All eight ledgers have zero bad decisions, zero missing/negative required review fields, zero entity duplicates, and zero missing referenced evidence. All 192 notes are nonblank and pairwise distinct.

Counterexample searches were run over the full machine tables for duplicate/missing IDs, incomplete unordered pairs, sub-threshold glyphs, low effective point sizes, nonzero missing/foreign/clip pixels, illegal intersections, clearance deficits, taxonomy omissions, and non-PASS/manual-empty states; all returned `0`. Deterministic spot checks included the threshold-edge `FRM_TRIAL_005`, a Latin glyph (`TXT_GAMMA_007`: 28 >= 24 px), the fraction rule (`GFX_MATH_RULE_PREDICTIVE_FRACTION`: area 576 px), first/critical/last pair rows, the 300 dpi figure crop, and critical bundle `PAIR_03345`. The crop is visually coherent and legible; the critical bundle is consistent with its intended node-edge endpoint classification, and its final raw intersection is 0. No independent content counterexample was found.

## 7. Disposition

All gates except the explicitly required six-field final-manifest schema pass. Because an absent required field is an evidence-schema failure and cannot be repaired by interpreting a five-field equality as six-field equality, the only valid local root verdict is:

`ROOT_REJECT_R14F`

No central inventory or status was changed. P654 remains central SA2 pending mainline acceptance/rework; this report does not declare `A_LOCAL_PASS`.

## 8. Report artifact identity

- `SELF_BYTES_DECIMAL`: `0000010387`
- `SELF_SHA256_CANONICAL_ZEROED`: `B9605493582C076E02D4D879FFC8FA56BD368A293E4E10D8EE5B22F256CEF13B`
- `READ_ONLY_AFTER_FREEZE`: `true`

Self-hash convention: the canonical SHA-256 is computed over the final report bytes after replacing only the 64 hexadecimal characters in `SELF_SHA256_CANONICAL_ZEROED` with 64 ASCII zeroes. This avoids an impossible literal cryptographic self-reference. The exact post-freeze artifact SHA-256 is reported externally in the root handoff/final message.
