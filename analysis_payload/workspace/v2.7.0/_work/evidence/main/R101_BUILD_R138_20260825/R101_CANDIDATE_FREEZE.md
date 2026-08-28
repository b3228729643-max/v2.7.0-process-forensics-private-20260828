# R101 official candidate freeze

- Freeze time: `2026-08-25T03:00:22+08:00`
- Mainline commit: `05a5f6e21ac025fccb03f256731c6060d0a19043`
- Integrated inputs: FIG-P608-01 local SA2 mainline commit `dc307eb1ef1d3c9d04dba0c91e05a2bb322234ff`; B-EXM-P04 mainline commit `05a5f6e21ac025fccb03f256731c6060d0a19043`.
- Official candidate: `R101`
- PDF: `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\build\strict_current_r101_fullbook\main_full.pdf`
- Pages: `814`
- Bytes: `4,947,496`
- SHA-256: `0870FF226DC383875C4A1B6EABB06AAB942317DA294D90D2864B3030D46DF1A1`

## Build and log gates

- `build_v2.7.0.ps1 -Engine lualatex -OutputDir src\build\strict_current_r101_fullbook -NoPublish` ran as one mainline-owned latexmk invocation and exited 0 with JSON `result=PASS` and `All targets ... are up-to-date`.
- The new output directory converged through latexmk's own three LuaLaTeX passes; no second TeX chain was started.
- `symbols.idx`: 355 accepted, 0 rejected, 0 warnings.
- `main_full.idx`: 731 accepted, 0 rejected, 0 warnings.
- Final `main_full.log` contains exactly one `Output written` line. LaTeX/package error, undefined control/reference/citation, duplicate, fatal/emergency, runaway, capacity, memory-exhausted, rerun, overfull, underfull and missing-character counts are all zero.
- Three pre-existing volume-5 PGF Lua `slpivtarget` notices remain non-fatal and fall back to TeX computation.
- The PDF is A4, rotation 0, PDF 1.7, unencrypted and not suspect. All 14 font entries are embedded, subset and Unicode-mapped.
- The mainline worktree is clean and terminal `latexmk/lualatex/luatex/luahbtex` processes are none.

## Navigation and identity gates

- Navigation audit: `PASS`.
- All 814/814 pages are A4 and unrotated.
- Five volume bookmarks, 37 chapter bookmarks, both indexes and all chapter numbers 1--37 are present.
- 273 bookmarks, 4,952 internal named links and 7,419 named destinations; invalid bookmarks/links: 0.
- Metadata and visible version contain only `v2.7.0`; the visible release version occurs on page 1.
- Audit payload: `navigation_audit.json` in this freeze directory.

## Affected-page visual gate

- B-EXM-P04: physical pages 223, 227--228, 247--248, 262--263, 291--292, 382, 389--390, 406--407, 416--417 and 437--438: 18/18 PASS.
- FIG-P608-01: physical page 659: PASS. Figure 32.8 has horizontal, legible y-axis labels, adequate left clearance, intact targets/ticks/legends/caption and no new collision or clipping.
- Mainline opened all three 150 dpi contact sheets and independently inspected pages 437, 438 and 659 at original render detail. No clipping, overlap, malformed formula, broken continuation, abnormal spacing, missing glyph or header/footer defect was found.
- Rendered evidence is in `affected_pages_150dpi/`.

## Route boundary

R101 is now the sole official candidate. Dispatch FIG-P608-01 to a completely fresh isolated SA1 that may read only R101, the current mainline P608 source, the current Goal/protocol/schema and necessary adjacent current text. It must not read any old P608 evidence, SA1/SA2/root report, handoff, state, inventory or chat conclusion. R101 does not itself make P608 `A_LOCAL_PASS`, does not close the 99-figure denominator and is not a final whole-book release.
