# FIG-P640-01 SA2 annotation-background R3

## Result

`PASS / LOCAL_SA2_PASS_READY_FOR_MAIN`

This is a local SA2 candidate result only. It does not update central state or inventory and does not claim global or final PASS.

## Frozen identities

- Source before: 2717 bytes; SHA-256 `044431D3E6B2ABAFE786EB151B7F4B01585F8E83F158EADEF736E005F6161F38`.
- Source after: 2742 bytes; SHA-256 `A1CB852A7B433D3B3FB39EB4F4E0310FD1F76631F01F366AF9D4B1B1B2FF434B`.
- Exact source change: add `fill=white,inner sep=1pt` to the existing two-line right-limit annotation node.
- Wrapper: 402 bytes; SHA-256 `495C5D0D36BE60B82BDB44AF4E352960680416785F991F8F0A15F0E495ABDC5C`.
- Candidate PDF: 40389 bytes; SHA-256 `E2AE5C0DACA6C9D07B43D61D00E9FA5580E63417DE15871D8DC6BA3842F9F2D2`; one A4 page.

## Controlled build

- Exactly one PowerShell 7 direct LuaLaTeX invocation; PID 1664; retry 0; latexmk 0.
- Natural exit true; exit code 0; controller exit 0; `success_hard_gate=true`.
- RESULT post-TeX process count 0 and current post-build TeX process count 0.
- Build log hard-error / undefined-control / missing-character / overfull / underfull matches: 0.

## Fresh non-TeX evidence

- Objects: 40 unique (30 text plus 10 semantic vector objects).
- All unordered pairs: `C(40,2)=780` unique.
- Glyphs: 160 including spaces; 145 nonspace.
- Critical pairs: 76 (all bbox intersections plus bbox gap <=8pt).
- Clip rows: 40; clip failures 0.
- PDF drawing denominator: 20. The two opaque annotation backgrounds are assigned to their semantic text parents and are not double-counted as separate semantic objects.
- Manual rows: 40 objects; 76 critical pairs; 7 glyph groups covering 160 glyphs; 12 views; 15 hard gates. Every manual row was written after direct visual review and not by the machine evidence script.

## Decisive regressions

`PAIR_0688 / T026 right_limit_note vs G09 right_efficiency_curve`: PASS. The native 300dpi 1x crop and nearest-neighbor 8x crop show the visible curve ending left-below the first `N`; it does not enter `N`, the subscript `eff`, the division slash, or any other note glyph. The white node background is present and later in paint order. The ideal vector curve/background masks have zero shared pixels; final-visible visual review is therefore the decisive gate rather than a hidden-bbox assertion.

`PAIR_0779 / G08 axes vs G10 marker`: PASS. Independent 300dpi masks have zero shared foreground pixels; nearest foreground distance is 4px and the orthogonal blank gap is 3px. Native 1x and 8x views confirm the open marker remains above the `.99` tick.

The formulas, curves, true point, marker/tick geometry, axes, titles, caption and panel layout remain semantically intact. R168 hard font failures are zero. No TeX retry, source expansion, P639 access, fresh role, central-state write or inventory write occurred.

## Unresolved

`NONE` within this local candidate. Main acceptance and commit authorization remain external gates.
