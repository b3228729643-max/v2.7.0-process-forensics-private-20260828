# P654 R10 root test results

- Build identity: PASS, one direct LuaLaTeX invocation, natural exit 0, no latexmk and no retry.
- Source/wrapper/PDF binding: PASS; source SHA `EA4A19FF...E31E6D`, wrapper SHA `FE44F2...C0CA1`, new PDF 43,385 bytes SHA `86712CDD...A87260`.
- Denominator: PASS, N=116 = 95 glyph + 21 graphic.
- All unordered pairs: PASS, C=6,670 / 6,670; independently rebuilt final intersections and nearest-clearance witnesses agree.
- Critical set: PASS, 50/50 across 11/11 relation classes; sampled shared-pixel boundaries are intended pre-mask contacts and final raw intersections are 0.
- Target FRM_TRIAL_005: PASS, H=22 px, area=297 px, missing/foreign/clip/ownership loss all 0.
- Taxonomy: PASS, predeclared R8 global taxonomy independently remaps 95/95 exactly once into 10 nonempty groups; D/E failures 0; source same-role and hierarchy failures 0.
- Manual ledgers: PASS, 95/21/50/5/3/10/4/4 = 192 unique decisions; empty/exact/normalized duplicate notes 0; no script writes manual ledgers.
- Visual root audit: PASS, full views, 16/16 glyph sheets, 21/21 graphics, 11/11 critical relation classes, target n and all 10 taxonomy groups were actually opened with no counterexample.
- Payload identity paths/bytes/SHA: PASS, 1052 payload files and 1055 ordinary files; missing/extra/duplicate/bytes/SHA differences 0.
- Payload mtime identity: FAIL. Exact NTFS 100 ns comparison gives 935/1052 unequal and 117 equal; maximum absolute difference 600 ns, with 12 entries above 0.5 microseconds. The manifests contain only six fractional digits and the seal script did not read-back file mtimes.
- Parse/open: PASS, 23 CSV, 70 JSON, 856 PNG and 1 PDF; failures 0.
- ADS/PYC/cache audit: PASS, non-default ADS 0, `.pyc` 0, Python cache directories 0.
- Seal order: PASS, `WRITE_STOPPED.json` is strictly latest by 1.4533382 s and post-seal writes are 0.
- Old-evidence migration: PASS. `FROZEN_R7A_GROUP_RECOMPUTE.csv` is independently traced to a current-R10 diagnostic recomputation and is not read by the consumer PASS path.
- Root verdict: ROOT_REJECT_R10.
