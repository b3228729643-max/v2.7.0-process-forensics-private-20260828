# Immutable handoff — FIG-P602-01 SA2 R2 v3C native evidence R1

- Review state: `SEALED_STRICT_FAIL_G032_H06` once `WRITE_STOPPED.json` is present.
- Candidate: v3C PDF SHA256 `203977543DB0F41686A955D33D83A55BA272A7AAE07599AED58227914019EE2C`, 41,240 bytes, one page.
- Source: SHA256 `2B15B4BEEA7A922FEE24259678DBAE2A54915955915E6714A350122A6251E349`.
- Fresh denominator: objects 30; glyphs 154; unordered pairs 435; critical 16; peers 28; roles 3; clips 30; views 4; hard gates 12.
- Manual ledgers: every expected ID present exactly once; pair endpoints match the machine table; observations are nonblank and unique.
- Sole strict failure: G032 (`一`) is visually complete but measures 36×4px against the unchanged 30px `CJK_FULL` height gate; H06 FAIL.
- Mechanical root validation: `qa/validation_report_r2.json` PASS with zero validation-check failures.
- Status prohibition: no `C_LOCAL_PASS`, no global PASS, no commit, no central inventory/state write, and no next figure authorization.
- TeX status: disabled; zero TeX invocations occurred during evidence generation/review.

The manifest and final write-stop marker are authoritative for the sealed byte identities and seal timing. A separate fresh root acceptance must verify this root without modifying it.
