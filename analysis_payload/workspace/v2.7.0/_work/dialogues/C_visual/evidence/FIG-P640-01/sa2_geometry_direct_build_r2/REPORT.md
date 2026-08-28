# FIG-P640-01 SA2 geometry direct build R2

HANDOFF_ID: `C-FIG-P640-01-SA2-GEOMETRY-DIRECT-BUILD-R2`

Result: **LOCAL_SA2_PASS**. This is a C-local source-candidate decision only; it does not update central inventory and does not authorize a commit.

## Candidate identity

- Source: 2,717 bytes; SHA-256 `044431D3E6B2ABAFE786EB151B7F4B01585F8E83F158EADEF736E005F6161F38`.
- Wrapper: 402 bytes; SHA-256 `495C5D0D36BE60B82BDB44AF4E352960680416785F991F8F0A15F0E495ABDC5C`.
- Source change is confined to the right-panel lower bound `ymin=0` to `ymin=-.06` relative to worktree HEAD. The true point `(.99,0.0100499975)`, displayed `.99,.010` label, `.99` tick and tick label, functions, curves, mathematics, caption, panel sizes and left panel remain unchanged.
- Direct LuaLaTeX: PID25436; invocation1; retry0; natural exit0; post-process0.
- PDF: one A4 page; 40,363 bytes; SHA-256 `E404605401CF4FF4E1C1921460BBB1CDE198A8BC479DEF9661232614205E33E7`.
- Log: 146,480 bytes; hard error, undefined control sequence, missing character, overfull, underfull and luaotfload critical counts are all zero.

## New non-TeX denominators

- Objects: 40 unique: 30 text followed by 10 vector objects.
- Glyphs: 160 including spaces; 145 nonspace.
- Unordered pairs: all `C(40,2)=780` exactly once.
- Critical pairs: 76 selected by bbox intersection or gap at most 8pt; all 76 have per-ID manual PASS decisions.
- Clips: 40; minimum page-edge distance 71.781509pt.
- Views: full page; native and grayscale figure crops; right panel; PAIR_0779 native/overlay at 1x and 8x; three object sheets; five critical-pair sheets.

Machine outputs contain only extracted identities and measurements. Manual reviewer, decision and observation fields were authored after viewing the new R2 renders.

## PAIR_0779 closure

The R2 PDF keeps the `.99` tick and marker as separate semantic objects. Their broad PDF bboxes still intersect because G08 encloses the entire axes; the native pixel masks decide the actual collision gate:

- axis/marker shared foreground pixels: `0`;
- nearest foreground pixels: axis yx `[759,2090]`; marker yx `[755,2090]`;
- foreground-center distance: `4px`;
- intervening orthogonal blank pixels: exactly `3px`, meeting the required gate;
- native1x, native8x and blue/amber overlay all show a real blank band.

## Regression review

All other 75 critical relations remain legal: axes contain their curves; curve origins and endpoint connections are intentional; tick labels remain outside axes; annotations and legend samples remain separated and readable. All 40 objects are complete; no clip, semantic, formula, glyph, color/grayscale or page-integration hard failure was found. R168 review found no tofu, wrong codepoint, wrong mathematical meaning, unreadability, severe size imbalance, real clipping or illegal text overlap.

## Control anomaly outside the R2 root

The R2 machine wrapper reused only the frozen R1 algorithm and ID schema through Python `importlib`. That import unexpectedly wrote one bytecode cache file into the previously sealed R1 root at `02_nontex_evidence/__pycache__/build_p640_nontex_evidence.cpython-311.pyc` after the R1 write-stop marker. The file is 34,325 bytes with SHA-256 `4599928928FFF05C09F3AA3992A172C0E61DE36DC9396CC22CCB9725DC2E2CA1` and is the sole R1 unlisted extra. All 51 R1 manifest-listed payload identities still have zero mismatch; the R1 manifest and WSTOP hashes remain unchanged. Corrective deletion was not authorized, so the exact extra remains isolated for main adjudication. The R2 wrapper now sets `sys.dont_write_bytecode=True`; it will not be executed again.

This anomaly does not alter the new R2 PDF, R2 machine measurements or R2 manual PASS decisions, but it is explicitly unresolved at the control layer and is not concealed by the local content result.

No further TeX invocation, retry, source commit, fresh role, central state or inventory write is authorized by this root.
