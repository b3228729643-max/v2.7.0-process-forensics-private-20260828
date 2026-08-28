# FIG-P582-01 R2 local SA2 decision

Status: `LOCAL_SA2_PASS_AWAIT_OFFICIAL_CANDIDATE_AND_FRESH_SA1`.

The sole direct LuaLaTeX invocation exited naturally with code 0 and produced one one-page A4 PDF: 31,330 bytes, SHA-256 `988E672096CC34E5A9B1634D84D150C644A0E07B049D81A92FACFE7276269F5B`. Source and wrapper identities were unchanged across the invocation, and the post-exit TeX-process count was zero.

The new PDF was independently decomposed into 78 rendered nonblank glyph objects and 17 foreground graphic paths, so `N=95` and the complete unordered-pair denominator is `C=4,465`. All masks were nonempty, all pairs were enumerated exactly once, and page-edge clipping candidates were zero. The 29 shared-ink candidates are intentional axis/tick, stem/marker, line/marker, series/reference crossings, or the sample-1 equality where raw and running-mean values both equal `.640`. The four low-clearance glyph pairs were manually reviewed at native 300 dpi and 8x nearest-neighbor scale. No pair has a real R168 hard failure.

In particular, the `.380` terminal zero and the second down-arrow have zero shared pixels. Their pixel-level proximity is advisory under R168; the numeric label and direction label are plainly readable in color, grayscale, native1x, and 8x views. `.640`, both `.325` labels, markers, ticks, axes, and plot boundaries also remain readable and unclipped.

Source semantics remain exact: raw sequence `.64,.01,.49,.16`; running means `.640,.325,.380,.325`; truth reference `1/3`; formula `h(U_i)=U_i^2`; and axis meanings `i` / `N` / 数值. All 14 explicit visible fontsize declarations are at least 9.5pt, with no resize/scalebox/transform token. The patch changes only fontsize/leading declarations (12+/12-) in the sole authorized source.

Manual review was recorded only after opening the final figure, grayscale, four glyph sheets, one graphic sheet, three critical-relation sheets, and targeted `.640`, `.380`, truth, and axis ROIs. Machine scripts generated no manual reviewer, boolean, decision, or note fields. Final validation reports 27/27 checks PASS and zero hard failures.

No commit, fresh SA1/SA3, second UID, or second TeX invocation has been performed. Main integration and a new official full-book candidate remain prerequisites for the next fresh role.
