# R5 preterminal integrity check

**RESULT = PASS**

| Gate | Result | Detail |
|---|---|---|
| FROZEN_SOURCE_SHA256 | PASS | {"actual": "F0ECC9B28361A2AE73AF085A4958AD09F8F94575D789B8F776C55631FD45E161", "expected": "F0ECC9B28361A2AE73AF085A4958AD09F8F94575D789B8F776C55631FD45E161"} |
| AUTHORITY_PDF_PRESENT | PASS | {"pdf": "D:\\Users\\ASUS\\Desktop\\机器学习\\v2.7.0\\_work\\source\\v2.7.0\\src\\build\\strict_current_r96_fullbook\\main_full.pdf", "sha256": "8EED8765A4856C4C197262DEA06E283790FBA8DA906C70C26FC7BD56F6F7E5E8"} |
| FLS_AND_SCOPE_RECORD | PASS | "identity record preserves FLS, page, and source identity" |
| FONT_AUDIT_235_ALL_PASS | PASS | {"rows": 235} |
| GLYPH_ENUMERATION_235_UNIQUE | PASS | {"map_rows": 235, "unique_ids": 235} |
| MANUAL_GLYPH_TRI_VIEW_235_OF_235 | PASS | {"ledger_rows": 235} |
| CONTACT_SHEET_COVERAGE_30 | PASS | {"sheets": 30} |
| NATIVE_MASKS_235_PLUS_25_NONEMPTY | PASS | {"glyph_masks": 235, "nonempty": 260, "vector_masks": 25} |
| ALL_UNORDERED_PAIRS_INCLUDING_GG | PASS | {"gg_pairs": 300, "objects": 260, "pairs": 33670} |
| RAW_OVERLAP_CLASSIFICATION_48_NAMED_GG | PASS | {"non_GG": 0, "raw_overlap_rows": 48, "same_parent": 0, "unlisted": 0} |
| MANUAL_CRITICAL_RELATIONS_212_OF_212 | PASS | {"classes": {"GG": 59, "TG": 1, "TT": 152}, "modes": {"COMPONENT_100PCT_TRI_VIEW": 152, "DIRECT_8X_OVERLAY": 60}, "rows": 212} |
| SAME_PARENT_ALLOCATION_RECORD | PASS | {"allocations": 4} |
| LOW_PROFILE_MANUAL_CALIBRATION | PASS | "G0199 manual calibration record present" |
| FOUR_VIEW_MATH_COORDINATION_MANUAL | PASS | "four-view/manual-semantic closure present" |
| MACHINE_NATIVE_GATE_SUMMARY | PASS | {"clearance_failure_pair_count": 0, "critical_pair_count": 212, "empty_mask_pair_count": 0, "gg_pair_count": 300, "illegal_overlap_pair_count": 0, "illegal_overlap_pixel_count": 0, "intentional_overlap_pair_count": 48, "intentional_overlap_pixel_count": 2471, "object_count": 260, "pair_count": 33670} |
| NO_PREMATURE_WRITE_STOPPED | PASS | "terminal stop marker absent before terminal decision" |

This record is non-terminal. A terminal SA1 decision may be written only when RESULT is PASS.
