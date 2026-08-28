# FIG-P580-01 — SA3 Blind R96 Evidence Manifest

## Terminal disposition

`PASS_TO_ROOT`, as issued in `SA3_VERDICT_REPORT.md`.  This manifest was prepared after the report and is the final evidence document before `WRITE_STOPPED`.

## Candidate identity

| Field | Value |
| --- | --- |
| Figure / target | `FIG-P580-01` / Fig. 31.6 |
| Final PDF page | physical 628 / printed 615 |
| Final PDF SHA-256 | `8EED8765A4856C4C197262DEA06E283790FBA8DA906C70C26FC7BD56F6F7E5E8` |
| Current source SHA-256 | `F0ECC9B28361A2AE73AF085A4958AD09F8F94575D789B8F776C55631FD45E161` |
| PDF identity/linkage | `05_reports/BUILD_IDENTITY_FLS.md` |
| Direct native render | 300 dpi, 2481 x 3508 px, final PDF page only, no resize |

## Evidence population at manifest creation

The pre-manifest population was 1,168 files.  Directory populations were:

| Directory | Files before manifest |
| --- | ---: |
| `02_native_render` | 15 |
| `03_glyph_evidence` | 950 |
| `04_object_evidence` | 186 |
| `05_reports` | 16 |
| `06_scripts` | 1 |

The evidence includes: full-page/scope/body/grayscale renders; 234 per-glyph Original/Target-overlay/Mask-only records and 1x/8x atlases; text/graphic/all-object overlays; 65 current high-risk pair ROI pairs (1x and 8x) and their atlases; nine low-contour final-PDF controls; CSV ledgers; and the source-identification, mathematical, visual, and terminal reports.

## Ledger denominators and outcome

| Ledger/result | Count or disposition |
| --- | --- |
| Visible glyphs | 234 / 234 PASS |
| Low-contour matched controls | 9 / 9 PASS |
| Text / graphic / foreground objects | 30 / 15 / 45 |
| Complete unordered pair universe | 990 = TT 435 + TG 450 + GG 105 |
| Named source-semantic contacts | 24 only |
| High-risk native-pixel manual reviews | 65 / 65 PASS at 1x and 8x-nearest |
| Illegal overlap / clipping pixels | 0 / 0 |
| Scope-edge ink / page clip candidates | 0 / 0 |

## Core artifact SHA-256

| Artifact | SHA-256 |
| --- | --- |
| `06_scripts/sa3_blind_visual_audit.py` | `7E65A7CCDA6A6951BA75520F3236F0A0962A1B7FFA42A04589C16F8D688C590F` |
| `05_reports/SA3_VERDICT_REPORT.md` | `9DA25FC71786E354A81D4749E300F1AFF6C72D616E8543CC0048BE169EBDFBB3` |
| `05_reports/FOUR_VIEW_VISUAL_REVIEW.md` | `7E0DD08892C3F9BA04C2430314C16973A2A4C792D49B226BF578D6F0DD6E457A` |
| `05_reports/BUILD_IDENTITY_FLS.md` | `892A8FA6AA18E1D91E3D5D8A84089A1446AA23B6721AF5EACC21F00D4A659B9B` |
| `05_reports/FONT_MATH_AND_CONTACTS.md` | `BBDFFCCCACEE63BF5C56C28F906CBBFC865E9407E80445A4B65C74822C4B0633` |
| `05_reports/analysis_summary.json` | `A775BF25E1A545FEEC4EB01AF94C193537110399242D805D424A92A043B2AA2E` |

## Recheck entry points

- `05_reports/SA3_VERDICT_REPORT.md`: terminal gate outcomes and failure ledger.
- `05_reports/FOUR_VIEW_VISUAL_REVIEW.md`: human visual review across all required views.
- `05_reports/FONT_MATH_AND_CONTACTS.md`: font/size/role evidence, mathematical semantics, all 24 named contacts and source lines.
- `05_reports/glyph_ledger.csv`, `glyph_contact_table.csv`, `foreground_object_inventory.csv`, `pair_universe.csv`, `high_risk_manual_review.csv`: denominators, boundaries, pixel coordinates/ROIs, and dispositions.
- `02_native_render`, `03_glyph_evidence`, `04_object_evidence`: native raster and review imagery.

No business source, template, build input, inventory, or central status file was modified by this SA3 audit.
