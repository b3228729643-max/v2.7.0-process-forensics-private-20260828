# R1B scope and standalone build

This independent SA1/R1B review read only the assigned official page, the assigned live figure source, the assigned chapter source, and standard TeX packages needed to compile an evidence-only harness. No project source, wrapper, public template, inventory, manifest, state file, or prior audit conclusion was read or changed.

## Direct source inventory

- Figure source: `fig_v2_c01_separator.tex`.
- Chapter insertion: `V2-C01.tex`, line 151; the immediately following reading sentence is line 152.
- The figure source itself has no `\input`, `\include`, `\usepackage`, or direct project-style import. Its directly used rendering interfaces are TikZ/PGFPlots keys plus the source-defined figure keys on lines 3--13.

## Evidence-only standalone build

`build/source_standalone.tex` imports the assigned live source verbatim. It provides only the symbols that source uses (`SLInk`, `SLBlue`, `SLTeal`, `SLGold`, and `slfig axis`) and neutralises the float caption so the source can be compiled standalone. It does not alter or copy the live source.

- Compiler: XeLaTeX.
- Result: success, one-page `build/source_standalone.pdf`.
- Review render: `build/source_standalone_300dpi.png`.
- Purpose: source syntax/standalone-build evidence only. Conformance geometry and typography are judged exclusively from the official full-book page raster below.

## No-write assertion

All files created by this review are below `STRICT_R1B`; no source or central-status file was changed.
