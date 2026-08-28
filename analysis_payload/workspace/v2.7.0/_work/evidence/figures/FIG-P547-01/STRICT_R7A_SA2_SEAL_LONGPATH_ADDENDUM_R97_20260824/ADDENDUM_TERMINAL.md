# FIG-P547-01 R7A addendum terminal

ADDENDUM_RESULT: PASS_EXACT_60_LONGPATH_GAP_BOUND

RESULT: LOCAL_PASS_TO_ROOT_BUILD

FINAL_OFFICIAL_PASS: false

R7 is immutable and remains separately sealed. R7A corrects only the erroneous assertion that every superseded file was covered by the R7 manifests.

Long-path set closure: 6,732 actual R7 files = 6,672 R7-listed/seal-metadata paths + 60 omitted paths. All 60 omissions are pre-WSTOP LuaTeX/font-cache files under the exact superseded GEN2/GEN3 `low_profile_calibration/texmfvar/` prefixes, 30 per generation. ACTIVE missing is 0; files written after R7 WSTOP is 0.

R7's 6,670 MANIFEST rows were rehashed with 0 parse failure, 0 duplicate, 0 missing reference, and 0 hash mismatch. `R7_OMITTED_LONGPATH_60.csv` binds every omitted path, bytes, SHA256, CreationTime and LastWriteTime.

The authorized source remains SHA256 `DF3D4415EDC56D02E056CAE0F3E38830DF28E781BC67ECDFB69863C5038F1600`. No R7 file and no business source was modified.

This addendum does not declare final PASS and does not remove the requirement for a root official full-book build followed by fresh independent SA1 review.
