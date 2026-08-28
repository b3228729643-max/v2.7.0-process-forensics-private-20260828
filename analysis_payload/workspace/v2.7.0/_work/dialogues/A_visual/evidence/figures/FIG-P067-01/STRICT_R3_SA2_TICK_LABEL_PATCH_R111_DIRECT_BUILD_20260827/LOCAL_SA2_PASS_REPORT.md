# FIG-P067-01 R3 local SA2 result

Verdict: `LOCAL_SA2_PASS_AWAIT_OFFICIAL_CANDIDATE_AND_FRESH_SA1`.

The only authorized source change suppresses the automatic lower-PMF `0.30` label and replays the same visible `0.3` text at the same tick with a local `xshift=-2pt,yshift=-4.5pt`. All probabilities, tick positions, PMF/CDF coordinates, open/closed endpoints, panel order, labels, styles, and caption semantics remain unchanged.

The single authorized direct LuaLaTeX typeset completed naturally with exit 0 and produced exactly one PDF, 34,208 bytes, SHA-256 `C1C06D877227E407F85678C0842182EE3629AEC78B62A4418C94A1D81860609E`. The earlier `--version` call is disclosed separately as one engine-version probe and is not counted as a typeset invocation. Typeset invocation count is 1, retry count 0, latexmk count 0, and terminal TeX-family process count 0.

From the new PDF, the final denominator is `N=115` (65 glyphs and 50 foreground paths, with five white-fill/no-stroke background rectangles rationally excluded), giving all `C(115,2)=6,555` unordered pairs. Duplicate and self-pair counts are zero. Machine hard failures, clipping, empty foreground atoms, and unresolved assignments are zero.

The final images were actually opened before the manual ledgers were written: the full standalone page, native figure, grayscale figure, atomic overlay, both critical tick crops, all three glyph sheets, and all three path sheets. The object ledger covers 115/115 unique objects with object-specific notes. The relationship ledger covers 16/16 unique critical relations with relation-specific notes. Machine scripts generated or overwrote no manual reviewer, timestamp, state, decision, or note fields.

The former `0.35`↔`0.3` collision is removed: foreground intersection is 0, native rounded bbox clearance is 1 px, and nearest-8x clearance is 8 px. The `0.3`↔`0.15` regression has the same zero-intersection/1 px/8 px result. Under R168, these small rounded bbox gaps are advisory only because all three labels are complete, plainly readable, and visually separated. The remaining PMF/CDF mathematics, monotonic/right-continuous CDF behavior, endpoint semantics, axes, guides, notes, grayscale encoding, caption, and page integration have no hard failure.

No commit or fresh role is claimed or authorized by this report.
