# R102 official candidate freeze

- Mainline commit: `94d1b62b877e80000539879688e6209c09882833`
- Integrated P654 input: A commit `697dce292f2c1afca7d02554c3bad987ca84f825`, main commit `94d1b62b877e80000539879688e6209c09882833`
- Official candidate: `R102`
- PDF: `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\build\strict_current_r102_fullbook\main_full.pdf`
- Pages: `817`
- Bytes: `4,958,396`
- SHA-256: `60026DE5A4168D6F3B304D1AE59BE68E1F570CD22D992E43FCAD9828E25A1397`
- Final PDF/log mtime UTC: `2026-08-25T04:36:22Z`
- Final log bytes: `259,937`

## Build and log gates

- One mainline-owned `build_v2.7.0.ps1 -Engine lualatex -OutputDir src\build\strict_current_r102_fullbook -NoPublish` invocation exited `0` with `result=PASS` and `All targets ... are up-to-date`.
- Latexmk's own natural sequence was three LuaLaTeX passes plus its index passes; no second invocation or retry was started.
- Final log has exactly one `Output written on main_full.pdf` line.
- LaTeX/package error, undefined control/reference/citation, missing file, emergency/fatal/runaway/capacity/memory, rerun, overfull, underfull and missing-character counts are all `0`.
- The three pre-existing volume-5 PGF Lua `slpivtarget` fallback notices remain non-fatal.
- `main_full.idx`: 731 accepted, 0 rejected, 0 warnings.
- `symbols.idx`: 355 accepted, 0 rejected, 0 warnings.
- Terminal `latexmk/lualatex/luatex/luahbtex` processes are none; mainline worktree is clean.

## PDF, navigation and font gates

- PDF 1.7, unencrypted, not suspect, A4, rotation 0; all 817/817 pages are A4 and unrotated.
- 14 font entries; every entry is embedded, subset and Unicode-mapped.
- Navigation audit: `PASS`.
- Five volume bookmarks, 37 chapter bookmarks in exact order 1--37, symbol index and subject index present.
- 273 bookmarks, 4,958 internal named links, 7,421 named destinations; invalid bookmarks/links: 0.
- Metadata and visible version contain only `v2.7.0`; visible release version occurs on page 1.
- Machine payload: `navigation_audit.json` in this directory.

## Affected-page visual gate

Poppler 150 dpi renders were opened as four contact sheets for the accepted post-R101 content batches and their known pagination fixes:

- P05 anchors/fixes: 141, 152, 168, 202, 211--212, 232--233, 273, 311, 338, 454.
- P06 anchors/fixes: 492, 512, 534, 557--558, 604, 609, 633, 640, 662, 667.
- P07 anchors/fixes: 682, 717, 719--722, 751--753, 777--778.
- Intervening fifth-volume sample: 690.

All 35 contact-sheet pages passed for clipping, overlap, broken frames, orphan headings, abnormal vertical or horizontal stretch, malformed formulae, headers/footers and continuation flow. In particular, P05 exercise headings remain attached to their first exercises, P06 page 557 keeps the section title with example 28.1, and P07 page 719 no longer contains the former split self-check/large vertical gap.

P654 was additionally opened at 300 dpi on physical pages 703--704. Physical page 704 (printed 691) contains figure 34.1 / `FIG-P654-01`; the enlarged trial-count `n` is horizontal, legible and owned by its node, with intact arrows, node borders, labels, caption and following symbol table. No collision, clipping or adjacent-page regression was found.

## Route boundary

R102 is the sole current official common candidate. P654 must enter a completely fresh isolated SA1 that may read only R102, the current mainline P654 source, the current Goal/protocol/schema and necessary adjacent current text. It must not read any old P654 evidence, SA1/SA2/root reports, handoffs, state, inventory or chat conclusions, including R14F. PASS only routes to a separate fresh isolated SA3; FAIL routes back to SA2. R102 is not the final release and does not by itself close any figure.
