# FIG-P602-01 fresh root acceptance R1

- Acceptance status: `ROOT_ACCEPTED_STRICT_FAIL_G032_H06`.
- Evidence outcome: `STRICT_FAIL_G032_H06`; this is not a local or global PASS.
- Sealed source root ordinary files / manifest rows: 900 / 898.
- Source payload/control/self/seal: 882/16/1/1.
- Manifest mismatch counts: missing 0; bytes 0; SHA256 0; NTFS mtime-ns 0; duplicate paths 0.
- Unique unlisted files: `['09_manifest/evidence_file_manifest.csv', 'WRITE_STOPPED.json']`.
- Source manifest SHA256: `F26B3535E001550815A6616883FD3B9261F1D1B99A240AA956456047195D4F68`.
- Canonical listed recordset SHA256: `9DD45215B3ACF6DBD9AFD761004E827868C2BE04C19BE1861AEDC2A3C2923A85`.
- Source WRITE_STOPPED SHA256: `085F65EFA1167C07446ACA9E3AB18C0B813B45BD5AB02DBD0F300168E772F68D`.
- Source HANDOFF SHA256: `5D839DF81D93F3FE589F826D7BF8D56AD916D6C1326C3CDA94E4E6D4E05F91EB`.
- Parse/open/hygiene: CSV failures 0; JSON failures 0; PNG failures 0 across 864 PNG files; ADS 0; pyc/cache 0.
- Seal checks: all 900 files read-only; marker strictly latest; post-marker source writes zero by manifest/mtime identity.
- Denominators rechecked: objects 30; glyphs 154; unordered pairs 435; critical 16; peers 28; roles 3; clips 30; views 4; hard gates 12.
- Manual pair rows: 435 unique IDs; endpoints match; 435 nonblank unique observations.
- Sole strict failure: G032 (`一`) manual visual PASS but CJK_FULL 36×4px versus required 30px height; H06 FAIL.
- TeX processes at acceptance: 0; no TeX command was invoked by this acceptance.
- Acceptance-check failures: 0 `[]`.
