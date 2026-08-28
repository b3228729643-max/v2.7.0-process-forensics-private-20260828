# P608 R101 R7A SA1 test results

- Frozen R101 identity: PASS, 814 A4 pages / 4,947,496 bytes / expected SHA-256.
- Independent location: physical page 659 / printed page 646 / Figure 32.8.
- Source binding: PASS, 3,429 bytes / 58 lines / expected SHA-256.
- Machine reuse: PASS, 1,893 files with exact path/bytes/SHA/mtime identity and zero migrated R7 manual conclusions.
- Object denominator: PASS, N=172 = 112 glyphs + 58 explicit drawings + 2 patterns.
- Pair denominator: PASS, C=14,706 / 14,706.
- Manual ledger: PASS for authenticity and coverage, 391 unique decisions = 172 object + 102 critical + 64 preliminary + 13 peer + 35 role + 4 view + 1 hard.
- Root visual audit: PASS for required sampling and counterexample search; all 13 peer items, all 4 views and the hard case were opened.
- Pixel typography: FAIL, HARD-LOWPROFILE-TXT-098.
- Hard reconstruction: target H=28 area=56; frozen peer H=28 raw area=72; clean peer area=61; clean area ratio 0.9180327868852459 < 0.92.
- Geometry, final overlap, clipping and mask contamination: PASS.
- Manifest: PASS, 1,917 payload / 22,291,728 bytes / exact SHA and path set.
- Parse/open, ADS and PYC: PASS, zero failures/streams/cache artifacts.
- Seal order: PASS, payload < manifest < WRITE_STOPPED < SEAL and zero post-seal writes.
- Root verdict: ROOT_ACCEPT_R7A_FAIL_TO_SA2.
