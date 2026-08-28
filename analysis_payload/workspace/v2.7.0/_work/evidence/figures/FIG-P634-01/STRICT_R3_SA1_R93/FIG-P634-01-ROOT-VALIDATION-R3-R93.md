# FIG-P634-01 ROOT VALIDATION R3 / R93

## Root verdict

- `RESULT: FAIL`
- `NEXT_ROLE: SA2`
- Frozen input: `strict_current_r93_fullbook/main_full.pdf`, physical page 682, printed page 669, figure 33.3.
- Root independently reopened the native color/grayscale crop, text overlay, literal operator/punctuation overlays, source, caption-style dependency, and the limiting clearance evidence.

## Confirmed hard failures

1. Thirty-one independently measured literal operator/punctuation glyphs fail their own native 300 dpi ink-height thresholds. Representative results are: base/script `−` = `3/22` or `3/15`; base `=` = `11/22`; ellipses = `5/22`; ASCII comma = `10/22`; fullwidth `＝` = `10/30`; fullwidth comma = `14/30` and `11/30`; caption-number dot = `6/22`. All are measured from their own PDF bbox and no-dilation raw mask; no parent formula height is substituted. All measured `+` instances pass.
2. The two same-role fullwidth commas in the same caption paragraph measure 14 px and 11 px. Their ratios to the 12.5 px class median are `1.1200` and `0.8800`, with max/min `1.2727`; this is the sole retained comparable same-class ratio failure after excluding unlike composite/script contents.

## Passing/nonblocking findings

- Source-font recovery passes. Local reader text is 9.6--10.6 pt and the caption dependency chain (`statlearnbook.sty:305`, 11 pt merged main) gives a 10.0 pt source base, consistent with about 9.96 pt in the final PDF.
- Role hierarchy, font visual harmony, mathematics, text consistency, grayscale, and page integration pass. The sequence and same-round/prior-round/terminal-sample semantics are correct.
- All 8,633 applicable independent geometry pairs have zero raw foreground overlap. Clip count is 0; minimum text--text bbox clearance is 30 px and minimum text--vector clearance is 14 px.
- Earlier draft evidence that reported caption `UNKNOWN`, composite-title heights, overlap 8, or cross-role ratio failures was methodologically corrected and is not accepted. The final report/CSVs/JSON are internally consistent.

The current candidate must not proceed to SA3. Dedicated SA2 must retain the exact system-scan semantics while redesigning typography/notation so every visible operator and punctuation substring passes its literal threshold and the caption comma class passes ratio limits, without introducing visual distortion, overlap, or source-size regression. A new frozen candidate and fresh independent SA1 are required.
