# FIG-P109-01 R3 local SA2 report

- HANDOFF_ID: `A-R114-P109-SA2-DIRECT-BUILD-R3-20260828`
- Result: `LOCAL_SA2_PASS_READY_FOR_MAIN_REVIEW_AND_ATOMIC_COMMIT_AUTH`
- Scope: one controlled standalone/direct LuaLaTeX build followed by non-TeX evidence reconstruction; no commit and no fresh role.

## Frozen identities

- Source: `fig_v1_c07_convex_set.tex`, 1,922 bytes, SHA-256 `887326D54E8DD97AA6D580EFA7CCD21FA371A94CACD36EB7029E80FC4D2D9355`.
- Source change versus baseline: exactly one file, 1 insertion/1 deletion, adding only `fill=white,fill opacity=1,text opacity=1,inner sep=1.2pt` to the existing domain-label node. Coordinates, anchor, text, font, color, set path, segment, points, formulas and caption are unchanged. `git diff --check` passes.
- PDF: `build/v260_FIG-P109-01_standalone.pdf`, 26,500 bytes, SHA-256 `C615152183FCB524F2B4FBDFB4A69D43C134DCDE20F989BF0050C2D2776A199D`; one A4 page, PDF 1.7, unencrypted.
- Build: controller PID 25108, child PID 11468, one controller and one direct LuaLaTeX invocation, retry/latexmk/version-probe all zero, natural exit 0, terminal TeX-family counts all zero.

## Full non-TeX regression

- Final denominator: 10 drawing objects + 5 text objects = N=15; all unordered pairs C=105.
- Machine evidence: 105 pair rows, 52 visible glyph/codepoint rows, six critical ROI pairs, hard failures zero.
- Genuine post-observation ledgers: 15 object rows, 105 pair rows, 20 opened-view rows, 8 mathematics/semantic rows and 52 glyph/codepoint rows; all identifiers are unique, notes are nonblank and all decisions pass.
- Actual opened evidence: full-page 200 dpi and native 300 dpi, native figure crop, grayscale, object/text/semantic overlays, object contact sheet, and six critical ROIs at native1x and nearest8x (20 final views total).

The former hard relation `P013` (convex-set boundary O001 versus domain-label text O014) now has zero shared ink and a 9 px minimum visible-ink distance. The authorized white background O009 protects every domain-label glyph, including mathematical `C`. The blue outline is intentionally occluded only behind that label; its entry and exit edges remain clean and it reads as one continuous set boundary. Formula/segment, endpoint labels, interpolation markers, statement box, grayscale rendering and page integration show no new hard regression.

The exact frozen standalone wrapper suppresses captions by redefining `\caption` to empty. Therefore this standalone PDF contains no rendered caption; the business source caption is unchanged and no caption source token was modified.

## Verdict boundary

Under R168, machine and manual hard-failure counts are both zero: no missing/tofu/wrong codepoint or mathematical meaning, unreadability, severe imbalance, true clipping, illegal ink overlap, or semantic/geometric error was observed. This is a local SA2 result awaiting Main review and a separate atomic-commit authorization. It is not A_LOCAL/global/final PASS and no commit has been created.
