# P608 local SA2 test results

- Source scope: PASS, exactly one P608 drawing source and one insertion.
- Frozen local PDF: PASS, 42,989 bytes / one A4 page / SHA-256 `638A722C...03BB`.
- Objects: PASS, `N=170 = 112 glyphs + 58 paths`.
- Pairs: PASS, `14,365 / 14,365`, all unique.
- Repaired targets: PASS, `GLYPH_0025` and `GLYPH_0056` each 21px >= 15px, with 115.430px / 86.000px clearance.
- Strict low-profile gate: PASS, 15/15; disputed `GLYPH_0072` and predeclared Figure 32.5 peer are both H=7px / area=41px, ratios 1.0 / 1.0.
- Pair / illegal visible overlap / clearance / clip / empty-mask failures: all zero.
- Explicit human review: PASS, 170 objects + 13 critical pairs + 7 views + 9 roles = 199, with no default/global/pending/unknown/empty accepted entry.
- Inventory: PASS, 835 accepted rows / zero path-byte-SHA mismatch; actual package 842 files / unexpected extras 0 / ADS 0.
- Reused evidence: PASS, 813 rows / zero source-destination byte or SHA mismatch.
- File parsing: PASS, 842 readable files / 784 PNG / 14 JSON / 22 CSV, zero failures.
- Seal: PASS, `WRITE_STOPPED` strictly latest by 1.750810 seconds and zero later writes.
- Route: `LOCAL_SA2_PASS_AWAIT_OFFICIAL_CANDIDATE_AND_FRESH_SA1`.
