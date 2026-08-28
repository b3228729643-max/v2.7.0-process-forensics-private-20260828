# FIG-P654-01 strict SA1 report

## Identity and scope

- Handoff: `A-R130-P654-SA1-RESUME-20260824`; owner dialogue: `DIALOGUE_A_VISUAL`; reviewer: `gpt-5.6-sol/xhigh SA1 A-R130-P654-SA1-RESUME-20260824`.
- Business source was read-only. Normalized-newline SHA-256: `01EA85F46A9567D7ED6CF88C92346F9BE317FAFDDCF1F7791C07B2A3ED3858EB` (R130 identity match).
- Evidence writes are confined to this A-local package.

## Evidence closure

- 103 visible glyphs and 21 foreground graphic/path objects, including one formula fraction rule: N=124.
- All `C(124,2)=7,626` unordered pairs rebuilt; unassigned text=0, coverage residual=0, coverage excess=0, empty glyph masks=0, empty graphic masks=0.
- All 103 glyph and 21 graphic objects were opened at native 1x and 8x. Per-object ledger rows record foreign=0/missing=0.
- All 37 critical pairs were opened at native 1x and 8x. Nineteen source-semantic edge contacts are whitelisted pair-by-pair; 17 independent title/formula bbox pairs fail.

## Hard-gate findings

- `SOURCE_FONT_PASS=true`: declared/effective visible sizes are 9.6pt and 11.8pt, both >=9.5pt, with uniform declared size within each role.
- `PIXEL_HEIGHT_PASS=false`: G0017 (`一`) is 4px <30px; G0059 and G0066 (`=`) are each 14px <22px.
- `LOW_PROFILE_REFERENCE_PASS=true`: G0063 comma and G0083 ideographic comma each match a same-codepoint/font/weight/color/size independent official-PDF reference at exact H and area ratios 1.0.
- `SAME_CLASS_RATIO_PASS=false`: D failures are E002, E004, E010, E014, E018.
- `ROLE_RATIO_PASS=false`: source formula/base ratio is 11.8/9.6=1.229166666667>1.18; E failures are E012, E014, E016, E017, E018.
- `FONT_VISUAL_HARMONY_PASS=false`: the formula blocks are visibly oversized relative to the base labels.
- `OVERLAP_PIXEL_COUNT=0`; `CLIP_PIXEL_COUNT=0`; `CLEARANCE_PASS=false` because 17 independent title/formula glyph bbox pairs measure 0–3px <4px.

## Route

`FAIL_TO_SA2`. SA2 must rebuild the candidate and regenerate all evidence; this package must not be promoted to SA3.
