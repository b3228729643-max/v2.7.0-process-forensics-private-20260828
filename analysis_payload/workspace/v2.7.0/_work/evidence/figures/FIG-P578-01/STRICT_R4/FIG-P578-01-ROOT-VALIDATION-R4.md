# FIG-P578-01 — root validation of independent official-R91 SA1 R4

Root reviewed the independent report and the native 1:1 `precheck` and `countproposal` ROIs plus the formal-mask overlay.

- Seventeen base math/operator glyphs (`=`, `\sim`, `\infty`) measure only 11--18 px at native 300 dpi, below the mandatory 22 px floor. The independent ledger identifies every glyph by element ID, parent formula, source line, bbox, and H_ink.
- The bottom `precheck` formula has only 2 px pixel-edge clearance from its outgoing arrow, below the 3 px text/formula-to-arrow minimum.
- The central label visibly splits the lexical unit “立即” as “立 / 即令”, producing an abnormal wrap even though its border and arrow clearances pass.
- Illegal foreground overlap and clipping remain 0, and the algorithmic semantics remain correct; those passes do not override the pixel-height, clearance, and harmony failures.

Root decision: `RESULT: FAIL` is confirmed on official R91 physical page 626. The candidate must not enter SA3; the next role is the unique figure-specific SA2 source writer.
