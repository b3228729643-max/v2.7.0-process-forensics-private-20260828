# B-EXM-P02 mechanical evidence

## Scope

- Objects: examples 8.1, 19.1, 26.1, 33.3 and 37.2.
- Frozen source diff: five local chapter `.tex` files; `60 insertions / 60 deletions`.
- Excluded artifacts: interrupted R4 output and the partial cache copy under `B-EXM-P02/B-EXM-P01`.

## Build route

- Seed: copied the frozen main-dialogue R99 auxiliary/output files read-only from `D:/Users/ASUS/Desktop/机器学习/v2.7.0/_work/source/v2.7.0/src/build/strict_current_r99_fullbook` into a new B-local output directory.
- Logical command: `powershell -ExecutionPolicy Bypass -File .\build_v2.7.0.ps1 -Engine lualatex -OutputDir D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\worktrees\dialogue_B_content\build\dialogue_B_content\B-EXM-P02-R7-RESUME -NoPublish -Resume`.
- Output: `D:/Users/ASUS/Desktop/机器学习/v2.7.0/_work/worktrees/dialogue_B_content/build/dialogue_B_content/B-EXM-P02-R7-RESUME/main_full.pdf`.
- Terminal artifact: 814 pages, A4, 4,941,530 bytes, unencrypted, PDF 1.7.
- `main_full.log` terminates normally with `Output written on main_full.pdf (814 pages, 4941530 bytes)`.
- At terminal inspection, `latexmk`, `lualatex` and `luatex` process count was zero. The build lock was released as `B_R7_BUILD_LOCK_RELEASED`.

## Wrapper diagnostic

- The B-local outer wrapper wrote `exit_code.txt = 1` although LuaTeX and latexmk completed the terminal PDF.
- The wrapper's entire stderr is one Perl locale warning (`Setting locale failed`) serialized by Windows PowerShell as `NativeCommandError` at the wrapper invocation line.
- No TeX error accompanies it. Because the wrapper uses `$ErrorActionPreference = 'Stop'`, that non-fatal stderr record entered its catch block before it could retain the nested build command's real exit code.
- Classification: outer-wrapper false negative, recorded transparently; it does not invalidate the independently readable terminal PDF/log gates below. The wrapper control code is not reported as a clean command exit.

## Log and PDF gates

- `! LaTeX Error`: 0
- `Fatal error`: 0
- `Emergency stop`: 0
- `TeX capacity exceeded`: 0
- `memory exhausted`: 0
- `no output PDF file produced`: 0
- `Overfull \hbox`: 0
- `Overfull \vbox`: 0
- `Underfull \hbox`: 0
- `Underfull \vbox`: 0
- `pdfinfo`: 814 A4 pages, no encryption, no suspect flag; `Get-Item` byte size 4,941,530.

## Static gates already frozen for this source diff

- `python -m unittest src.tests.test_style_term_solution_contracts src.tests.test_layout_source_contracts`: 9 tests, OK.
- Five solution blocks: all seven stage macros exactly once; exactly one `SolAnswer`; no generic route hit, engineering status token or independent duplicate conclusion.
- `git diff --check`: PASS.

These gates were not repeated after the source was frozen because no chapter source changed during mechanical build or visual inspection.

## Visual inspection

Rendered at 150 dpi from the terminal R7 PDF and inspected at original image detail:

- Example 8.1: PDF page 133.
- Example 19.1: PDF pages 361--362.
- Example 26.1: PDF pages 502--503.
- Example 33.3: PDF pages 692--694.
- Example 37.2: PDF pages 799--800.

Result: PASS. All ten covering pages were inspected. Example headings, seven-stage solution typography, formulas, continuation headers/boxes, conclusions, page headers/footers and neighboring content are readable. No clipping, overlap, broken continuation, malformed formula, abnormal gap or content loss was found.

Rendered evidence: `D:/Users/ASUS/Desktop/机器学习/v2.7.0/_work/dialogues/B_content/evidence/B-EXM-P02-R7_VISUAL/page_*.png`.
