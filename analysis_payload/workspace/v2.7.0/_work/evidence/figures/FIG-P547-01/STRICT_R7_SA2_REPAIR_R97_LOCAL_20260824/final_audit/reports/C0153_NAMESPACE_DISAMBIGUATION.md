# C0153 namespace and generation disambiguation

Two independent enumeration domains reuse the ordinal `C0153`; the ordinal is local to its own PDF enumeration and is not a cross-generation identity.

1. `UPSTREAM_R97::C0153::UFF1B` is the historical R97 full-book glyph `；` in NotoSerifSC-ExtraLight 9.7633895874pt at full-book bbox `[400.22098,410.07031,409.98438,420.52689]`. Its evidence is confined to `before_r97/c0153/` and `final_audit/reports/C0153_clean_mask_binding.{json,md}`. The clean mask contains exactly the independently calibrated two semicolon components: H=28px, area=57px; the 45px neighbour component and 1px edge component remain foreign. This object is not a member of the GEN4 local object or pair denominator.
2. `GEN4_LOCAL_STANDALONE::C0153::U0030` is the current local standalone glyph `0` in STIXTwoText-Bold 9.9626pt, source span `SPAN_B18_L00_S01`, bbox `116.278,253.934,121.209,263.897`. Its evidence is `final_audit/glyphs/rois_1x/C0153_U0030_*`, its row is in `all_visible_glyph_raw_measurements.csv`, and this object alone occupies object ID `C0153` in the 193-glyph / 258-object / 33153-pair GEN4 denominator.

The current GEN4 visible semicolons are instead `GEN4_LOCAL_STANDALONE::C0054::UFF1B` and `GEN4_LOCAL_STANDALONE::C0139::UFF1B`. Their independently separated masks use the historical R97 proof only as a same-codepoint/font/size calibration method; they retain their own local IDs and own native pixels. No CSV joins, object inventory rows, glyph counts, pair IDs, D/E comparisons, or manual ledger rows alias `UPSTREAM_R97::C0153::UFF1B` to `GEN4_LOCAL_STANDALONE::C0153::U0030`.

Decision: `PASS_NAMESPACE_SEPARATED`. The two records must always be cited with namespace + codepoint and must never be compared, counted, or paired as one object.
