# FIG-P126-01 R14 local SA2 review

- Handoff: `A-R115-P126-SA2-DIRECT-BUILD-R14-20260828`
- Candidate: the single successful R14 standalone PDF, 34,054 bytes, SHA-256 `204CC34980BF059DFFA4016314C1FBFEFC94A0066C01FF7E77A4A26946B65F3D`.
- Source: 4,626 bytes, SHA-256 `6CBAEBE50574E541A04B2FDCC74B432C49AF2590B579C6A85721EDF536912502`.
- Build: controller/direct child `1/1`, retry/latexmk/version-probe/second invocation `0/0/0/0`, natural exit `0/0`, terminal TeX-family counts zero. The build slot was released before this review.

## Current-PDF denominator and manual coverage

- Reader-visible objects: `N=60` (`25` text glyphs and `35` graphic components).
- All unordered pairs: `C=1770=C(60,2)`; unique IDs and tuples, self/duplicate/missing/extra zero.
- Manual post-observation ledgers: objects `60`, pairs `1770`, views `15`, glyph/codepoint `25`, math/semantic `10`.
- Pairwise illegal visible-ink overlap/clip/semantic relation failures: zero.
- Labels 6 and 7: shared ink zero; conservative complete blank clearances `7px` and `4px` at the documented native300 threshold.
- The positive-definite rotated quadratic, the alternating exact coordinate minimizers, the strictly decreasing objective sequence, the optimum, text/codepoints, caption meaning, grayscale readability outside the legend defect, and page integration are coherent.

## Decisive hard failure

`HARD-LEGEND-X2-CONTINUOUS` is confirmed. In the current native300 Poppler rendering, the x2 legend sample has exactly one occupied horizontal run from x=1258 through x=1330 (`73px`) and zero internal blank runs. The intended four disconnected sample subpaths are absent in both color and grayscale; the x2 key remains visually continuous like the x1 key. This is a real role-encoding/semantic visual failure, not an R168 numeric threshold advisory.

## Verdict

`LOCAL_SA2_FAIL_RETURN_TO_MAIN_SOURCE_SCOPE`

No source edit, commit, TeX/build retry, fresh role, second UID, or next source scope was performed or authorized by this review.
