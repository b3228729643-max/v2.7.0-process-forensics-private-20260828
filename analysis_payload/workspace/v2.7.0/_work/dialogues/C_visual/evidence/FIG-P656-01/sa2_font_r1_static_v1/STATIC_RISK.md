# FIG-P656-01 source-font static risk ledger

Status: `STATIC_ACCEPTED_PENDING_ONE_DIRECT_BUILD`.

- Scope is exactly one source file and five fontsize/leading declarations: `9.2/11.0`, `9.4/11.3`, `8.8/10.5`, `9.2/11.0`, `9.2/11.0` become `9.5/11.4`.
- Text, formulas, coordinates, node dimensions, edges, colors, caption, label, and semantic relationships are byte-preserved outside those declarations.
- The largest change is the `同一计数` arrow label (`8.8pt` to `9.5pt`, about 7.95%). The candidate must check its clearance from the arrow and count box.
- Other increases are about 1.1% to 3.3%. The candidate must check circle-node contents, count box, constraint formula, warning box, coefficient box, clipping, and full-page fusion.
- Static analysis does not claim visual PASS. It only predicts that the explicit `effective_pt >= 9.5pt` source gate is closed without scaling or geometry edits.
- Build control is one direct LuaLaTeX invocation, no latexmk, no retry, wrapper cwd preserved, child cache confined below ASCII `TEXMFOUTPUT`, and failure stops after durable RESULT.
